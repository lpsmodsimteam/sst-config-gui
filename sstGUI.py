#!/usr/bin/env python3

# This is a model development script to help you develop,
# integrate and run a new model in SST. There should be
# a sstGUI.ui file, a logo.png file, several other .png files
# and several help files in the resources directory.
# Templates can be found in the templates directory

import sys
import os
import subprocess
import cgi
import xml.etree.ElementTree as ET
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import sstSHELL

# Load the UI
Ui_MainWindow, QtBaseClass = uic.loadUiType('resources/sstGUI.ui')

####################################################################################
##### Main Application Class
class MyApp(QMainWindow, Ui_MainWindow):
	
	############################################################################
	### Initialization Function
	def __init__(self):
		QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		# Main buttons
		self.generate.clicked.connect(self.generateOpenFiles)
		self.compile.clicked.connect(self.compileModel)
		self.run.clicked.connect(self.runModel)
		# Menu actions
		self.actionAbout.triggered.connect(self.helpAbout)
		self.actionModel_Creator.triggered.connect(self.helpCreator)
		self.actionModel_Connector.triggered.connect(self.helpConnector)
		self.actionTools.triggered.connect(self.helpTools)
		self.actionGraph.triggered.connect(self.graphModel)
		self.actionModel2Template.triggered.connect(self.model2Template)
		# General setup
		self.modelName.setFocus()
		self.editor = os.getenv('EDITOR', 'gedit')
		self.separator = '************************************************************************************************************************\n'
		self.SSTinstalled = None
		self.updateTabs()
		# Model Creator Tab
		self.templates.itemDoubleClicked.connect(self.templateHelp)
		self.templateSelect.clicked.connect(self.selectTemplate)
		self.templateBrowse.clicked.connect(self.browseTemplates)
		# Model Connector Tab
		self.tabWidget.currentChanged.connect(self.updateTabs)
		self.newComp.clicked.connect(self.addModel)
		self.addSub.clicked.connect(self.addSubcomponent)
		self.remove.clicked.connect(self.removeModel)
		self.available.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.available.itemDoubleClicked.connect(self.availableHelp)
		self.available.setExpandsOnDoubleClick(False)
		self.selected.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.selected.itemDoubleClicked.connect(self.selectedHelp)
		self.selected.setExpandsOnDoubleClick(False)
	############################################################################
	
	
	
	############################################################################
	### Main Buttons at the bottom of the GUI
	
	########################################################################
	### Generate/Open Files
	### Creates or opens model files for both Model Creator and Model Connector tabs
	def generateOpenFiles(self):
		if not self.getModel(): return
		# Check for template if in Creator Mode
		if self.tabWidget.currentIndex() == 0:
			if not self.getTemplate(): return
		# Check SST Registered Models and local folders
		self.updateModels()
		local = next(os.walk('.'))[1]
		makefiles = True
		if self.model in self.elements or self.model in local:
			# Model is already registered with SST or it is a local model
			lib = sstSHELL.runCommand('sst-config ' + self.model + ' ' + self.model + '_LIBDIR')
			if lib != '' or self.model in local:
				# local model, can overwrite
				if self.overwrite.isChecked():
					text = 'Do you really want to overwrite your local version of ' + self.model + '?'
					val = self.warningPopup(text, 'Overwrite Model?')
					if val == QMessageBox.No:
						makefiles = False
				else:
					makefiles = False
			else:
				# SST provided model
				self.writeInfo(self.separator)
				text = '*** THERE IS A SST MODEL WITH THAT NAME ALREADY!!! ***\n'
				text += '*** PLEASE CHOOSE ANOTHER NAME ***\n\n'
				self.writeInfo(text, 'red')
				self.writeInfo('SST provided models:\n')
				text = ''
				for item in self.elements:
					text += item + '\n'
				self.writeInfo(text, 'blue')
				self.writeInfo(self.separator + '\n')
				return
		f = ''
		if makefiles:
			# Check for selected components
			if self.tabWidget.currentIndex() == 1 and self.selected.invisibleRootItem().childCount() == 0:
				self.writeInfo('*** NO COMPONENTS SELECTED ***\n\n', 'red')
				return
			os.system(str('rm -rf ' + self.model))
		# Create/Open the files
		if self.tabWidget.currentIndex() == 0:
			# Create the model using the template
			if makefiles:
				sstSHELL.createModel(self.model, self.templatePath)
			self.templatesMessage(self.dest)
			for item in self.dest:
				f += './' + self.model + '/' + item + ' '
		elif self.tabWidget.currentIndex() == 1:
			# Connect the model using the components
			if makefiles:
				components = ''
				root = self.selected.invisibleRootItem()
				for i in range(root.childCount()):
					element = root.child(i)
					for j in range(element.childCount()):
						component = element.child(j)
						components += element.text(0) + '.' + component.text(0)
						if component.childCount() != 0:
							components += '.'
							for k in range(component.childCount()):
								components += component.child(k).text(0)
								if k == component.childCount() - 1:
									components += ';'
								else:
									components += ','
						else:
							components += ';'
				sstSHELL.connectModels(self.model, components)
			self.templatesMessage([self.model + '.py'])
			f += './' + self.model + '/' + self.model + '.py '
		# Open files
		os.system(str(self.editor + ' ' + f + '&'))
	########################################################################

	
	########################################################################
	### Compile Model
	### Compiles and registers the model with SST for the Model Creator tab
	def compileModel(self):
		if not self.isSSTinstalled(): return
		# Configure does nothing for connector mode
		if self.tabWidget.currentIndex() == 0:
			if not self.getModel(): return
			self.writeInfo(self.separator + '***** Building Model *****\n\n')
			# make clean
			if self.clean.isChecked():
				self.runCmdByLine(str('make clean -C ' + self.model))
			# runCmdByLine returns the make return value (0 success, others fail)
			failed = self.runCmdByLine(str('make all -C ' + self.model))
			if failed:
				text = '\n*** ERROR DURING MAKE!!! PLEASE FIX THE ERROR BEFORE CONTINUING ***\n'
				self.writeInfo(text, 'red')
				self.writeInfo(self.separator + '\n')
				return
			# make all passed
			text = '\nSST has been configured to run your model you may now proceed to the next\n'
			text += 'step Run Model\n'
			self.writeInfo(text + self.separator + '\n')
			# Run the model if autorun is checked
			if self.autoRun.isChecked():
				self.runModel()
		elif self.tabWidget.currentIndex() == 1:
			self.writeInfo('Nothing to compile when connecting models\n\n', 'cyan')
	########################################################################
	
	
	########################################################################
	### Run Model
	### Runs the tests in the model folder for Connector or in the model/tests/
	### for Creator mode
	def runModel(self):
		if not self.isSSTinstalled(): return
		if not self.getModel(): return
		# Run all tests
		if self.tabWidget.currentIndex() == 0:
			testfiles = os.listdir('./' + self.model + '/tests/')
		elif self.tabWidget.currentIndex() == 1:
			testfiles = os.listdir('./' + self.model)
		self.writeInfo(self.separator + '***** Running Model test(s) *****\n\n')
		# Tests are in the model/tests/ folder for Creator mode
		# Tests are in the model folder for Connector mode
		for testfile in testfiles:
			self.writeInfo('*** ' + testfile + ' ***\n')
			if self.tabWidget.currentIndex() == 0:
				self.runCmdByLine(str('sst ' + self.model + '/tests/' + testfile))
			elif self.tabWidget.currentIndex() == 1:
				self.runCmdByLine(str('sst ' + self.model + '/' + testfile))
			self.writeInfo('\n')
		self.writeInfo(self.separator + '\n')
	########################################################################
	
	### End Main Buttons at bottom of GUI
	############################################################################



	############################################################################
	### Model Creator Tab
	
	# Select template
	def selectTemplate(self):
		if self.templates.currentItem():
			self.templateType.setText(str(os.getcwd() + '/templates/' + self.templates.currentItem().text()))

	# Browse for templates
	def browseTemplates(self):
		templatePath = QFileDialog.getExistingDirectory(self, 'Select Template', './templates/', QFileDialog.ShowDirsOnly)
		self.templateType.setText(str(templatePath))

	# Update the Avaiable Templates
	def updateTemplates(self):
		self.templates.clear()
		self.templates.addItems(next(os.walk('./templates/'))[1])
	
	### End Model Creator Tab
	############################################################################



	############################################################################
	### Model Connector Tab
	
	# Update the Available Models
	def updateModels(self):
		self.available.clear()
		# Store an ElementTree with all the xml data from sst-info
		self.sstinfo = ET.fromstring(sstSHELL.runCommand('sst-info -qnxo /dev/stdout'))
		# Store a list of the elements SST knows about
		self.elements = []
		# Grab the subcomponents
		subs = self.sstinfo.findall('*/SubComponent')
		for element in self.sstinfo.findall('Element'):
			components = element.findall('Component')
			self.elements.append(element.get('Name'))
			# Make sure the Element has Components the user can use
			if components:
				# Create an element item in the TreeWidget
				e = QTreeWidgetItem(self.available)
				e.setText(0, element.get('Name'))
				for component in components:
					# Create component items in the element item
					c = QTreeWidgetItem(e)
					c.setText(0, component.get('Name'))
					subcomponents = component.findall('SubComponentSlot')
					if subcomponents:
						for subcomponent in subcomponents:
							# Create subcomponent items in the component item
							# that have the correct interface
							for sub in subs:
								if subcomponent.get('Interface') == sub.get('Interface'):
									s = QTreeWidgetItem(c)
									s.setText(0, sub.get('Name'))

	# Add Models
	def addModel(self):
		root = self.selected.invisibleRootItem()
		for item in self.available.selectedItems():
			# Make sure the item has a element (it is a component, not an element itself)
			if item.parent():
				# Subcomponent if it has 2 parents
				if item.parent().parent():
					c = item.parent()
					e = item.parent().parent()
				else:
					c = item
					e = item.parent()
				elementExists = False
				# Loop through the elements to see if we have a element that matches already
				for i in range(root.childCount()):
					element = root.child(i)
					if e.text(0) == element.text(0):
						elementExists = True
				# No element exists in the selected tree, create one
				if not elementExists:
					element = QTreeWidgetItem(self.selected)
					element.setText(0, e.text(0))
				# Connect the component to the proper element
				component = QTreeWidgetItem(element)
				component.setText(0, c.text(0))
				if item.parent().parent():
					# Connect the subcomponent to the component
					subcomponent = QTreeWidgetItem(component)
					subcomponent.setText(0, item.text(0))
			else:
				self.writeInfo('*** Need to select a COMPONENT or SUBCOMPONENT from the Available Components ***\n\n', 'red')
		self.selected.expandToDepth(1)
	
	# Add subcomponent to existing component
	def addSubcomponent(self):
		root = self.selected.invisibleRootItem()
		for item in self.available.selectedItems():
			if self.selected.currentItem():
				# Make sure the item is a subcomponent
				if item.parent():
					if item.parent().parent():
						# Selected item needs to be a component
						if self.selected.currentItem().parent():
							if not self.selected.currentItem().parent().parent():
								subcomponent = self.sstinfo.find("*/SubComponent[@Name='" + item.text(0) + "']")
								slots = self.sstinfo.find("*/Component[@Name='" + self.selected.currentItem().text(0) + "']").findall('SubComponentSlot')
								fits = False
								for slot in slots:
									if subcomponent.get('Interface') == slot.get('Interface'):
										# Connect the subcomponent to the component
										subcomponent = QTreeWidgetItem(self.selected.currentItem())
										subcomponent.setText(0, item.text(0))
										fits = True
								if not fits:
									self.writeInfo('*** Subcomponent does not fit in the selected component slot ***\n\n', 'red')
							else:
								self.writeInfo('*** Need to select a COMPONENT from the Selected Components ***\n\n', 'red')
						else:
							self.writeInfo('*** Need to select a COMPONENT from the Selected Components ***\n\n', 'red')
					else:
						self.writeInfo('*** Need to select a SUBCOMPONENT from the Available Components ***\n\n', 'red')
				else:
					self.writeInfo('*** Need to select a SUBCOMPONENT from the Available Components ***\n\n', 'red')
			else:
				self.writeInfo('*** Need to select a component from the Selected Components ***\n\n', 'red')
		self.selected.expandToDepth(1)
	
	# Remove Models
	def removeModel(self):
		root = self.selected.invisibleRootItem()
		for item in self.selected.selectedItems():
			if item.parent():
				# If removing the last component, remove the whole element
				if item.parent().childCount() == 1:
					root.removeChild(item.parent())
				else:
					item.parent().removeChild(item)
			else:
				root.removeChild(item)
	
	### End Model Connector Tab
	############################################################################
	
	
	
	############################################################################
	### Menu functions (not including Help)
	
	# Graph a model
	def graphModel(self):
		# Get the path to the python test file
		path = QFileDialog.getOpenFileName(self, 'Select Python Test File', '.', 'Python files (*.py)')[0]
		if not path:
			self.writeInfo('*** PLEASE SELECT A PYTHON TEST FILE ***\n\n', 'red')
			return
		self.writeInfo(self.separator + '***** Graphing Model *****\n')
		f = sstSHELL.graphModel(path)
		self.writeInfo('\nCreated ' + f + '\n' + self.separator + '\n')
		QDesktopServices.openUrl(QUrl(f.split()[1]))
	
	
	# Convert a model into a template
	def model2Template(self):
		# Prompt for a Model to convert
		model = QFileDialog.getExistingDirectory(self, 'Select Model', './', QFileDialog.ShowDirsOnly)
		if not model:
			self.writeInfo('*** PLEASE SELECT A MODEL TO CONVERT ***\n\n', 'red')
			return
		# Get the new template name
		text, ok = QInputDialog.getText(self, 'Enter Template Name', '', QLineEdit.Normal)
		if not ok or not text:
			self.writeInfo('*** PLEASE ENTER A TEMPLATE NAME ***\n\n', 'red')
			return
		# Check to see if the template exists already
		templates = os.listdir('./templates/')
		if text in templates:
			self.writeInfo('*** TEMPLATE ALREADY EXISTS ***\n\n', 'red')
			return
		self.writeInfo(self.separator + '***** Converting Model into Template *****\n\n')
		self.writeInfo('Converting ' + model + ' to ' + text + '\n\n')
		f = sstSHELL.model2Template(model, text)
		self.writeInfo('\nNew template created: ' + './templates/' + text + '\n' + self.separator + '\n')
		self.updateTemplates()
		# Open the new template in an editor
		os.system(str(self.editor + ' ' + f + '&'))
		
	### End Menu Functions
	############################################################################
	


	############################################################################
	### Application helper functions
	
	# Checks whether SST is installed
	def isSSTinstalled(self):
		if self.SSTinstalled is None:
			if subprocess.run(['bash', '-c', 'type sst'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8').startswith('sst is '):
				self.SSTinstalled = True
			else:
				self.SSTinstalled = False
		if self.SSTinstalled:
			return True
		else:
			self.writeInfo('*** SST IS NOT INSTALLED. YOU WILL NOT BE ABLE TO COMPILE OR RUN ANYTHING, BUT YOU CAN STILL CREATE OR CONNECT MODELS ***\n\n', 'red')
			return False
	
	
	# Gets the model name from the GUI
	def getModel(self):
		self.model = self.modelName.text()
		if self.model == '':
			self.writeInfo('*** PLEASE ENTER A MODEL NAME ***\n\n', 'red')
			return False
		return True


	# Gets the template information
	def getTemplate(self):
		# Get template path from GUI
		self.templatePath = str(self.templateType.text())
		self.template = os.path.basename(self.templatePath)
		# Check for empty string
		if self.template == '':
			self.writeInfo('*** PLEASE SELECT A TEMPLATE ***\n\n', 'red')
			return False
		# Check for a valid template
		if not os.path.isfile(self.templatePath + '/template'):
			self.writeInfo('*** TEMPLATE PATH IS INCORRECT OR TEMPLATE IS SETUP WRONG ***\n\n', 'red')
			return False
		# Read template sources and destinations
		with open(self.templatePath + '/template', 'r') as fp:
			structure = fp.read()
		self.source = structure.split()[0::2]
		destination = structure.split()[1::2]
		self.dest=[]
		# Replace <model> tag with the model name
		for item in destination:
			self.dest.append(item.replace('<model>', str(self.model)))
		return True


	# Write to information screen
	# Available Colors:
	# black(default), darkgray, gray, lightgray, white,
	# red, yellow, green, cyan, blue, magenta,
	# darkred, darkyellow, darkgreen, darkcyan, darkblue, darkmagenta
	def writeInfo(self, text, color='black', update=True):
		colorText = '<span style="white-space:pre-wrap; color:' + QColor(color).name() + ';">'
		colorText += cgi.escape(text, True) + '</span>'
		self.info.moveCursor(QTextCursor.End)
		self.info.insertHtml(colorText)
		self.info.moveCursor(QTextCursor.End)
		if update:
			app.processEvents() # force the GUI to display the text


	# Runs a command and prints the output line by line while the command is running
	# Returns the exit status of the command
	def runCmdByLine(self, command, color='black'):
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		output = process.stdout.readline()
		while output != b'' or process.poll() is None:
			output = process.stdout.readline()
			self.writeInfo(output.decode('utf-8'), color)
		return process.poll()


	# Update available models and templates
	def updateTabs(self):
		if self.isSSTinstalled():
			self.updateModels()
		self.updateTemplates()


	# Information for template generation
	def templatesMessage(self, files):
		self.writeInfo(self.separator + 'The following Templates should be displayed in the pop-up editor\n')
		text = ''
		for item in files:
			text += '\t- ' + item + '\n'
		self.writeInfo(text, 'green')
		text = 'Please review/edit your files to create your model. You can make changes in\n'
		text += 'the pop-up editor, save your file then close the editor or you can close the pop-up\n'
		text += 'editor and the GUI, then proceed to editing the files in the editor of your choice\n'
		text += 'they reside in your working directory under ' + self.model + '/. \n'
		text += 'After your are done you can proceed to the next step Compile Model.\n'
		text += self.separator + '\n'
		self.writeInfo(text)


	# Generates a warning pop-up when you try to overwrite existing files
	def warningPopup(self, text, title):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Warning)
		msg.setText(text)
		msg.setWindowTitle(title)
		msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		msg.setDefaultButton(QMessageBox.No)
		msg.buttonClicked.connect(self.warningButton)
		return msg.exec_()
	# Button to go along with the popup
	def warningButton(self, button):
		return button
	
	
	# Display model help
	def modelHelp(self, items, displayAll = False):
		for item in items:
			self.writeInfo(self.separator)
			if self.tabWidget.currentIndex() == 0:
				# Find doxygen comments from template
				f = os.getcwd() + '/templates/' + item.text() + '/' + item.text() + '.cc'
				if os.path.isfile(f):
					# Look for a doxygen style comment block at the beginning of the file
					with open(f, 'r') as help:
						incomment = False
						for line in help:
							if incomment:
								if line.strip().endswith('*/'):
									incomment = False
									break
								else:
									self.writeInfo(line, 'gray')
							else:
								if line.strip().startswith('/**'):
									incomment = True
			elif self.tabWidget.currentIndex() == 1:
				# Get sst-info description
				if item.parent():
					text = sstSHELL.runCommand('sst-info ' + item.parent().text(0) + '.' + item.text(0))
				else:
					text = sstSHELL.runCommand('sst-info ' + item.text(0))
				# If we want to display all of the sst-info output, write it
				if displayAll:
					self.writeInfo(text, 'gray')
				else:
					# otherwise just print out the component/subcomponent selected
					for line in text.split('\n'):
						l = line.strip()
						if item.parent():
							if l.startswith('COMPONENT') or l.startswith('SUBCOMPONENT'):
								self.writeInfo(l + '\n', 'gray')
						else:
							# If item is an element, print out the whole element with components and subcomponents
							if l.startswith('ELEMENT') or l.startswith('COMPONENT') or l.startswith('SUBCOMPONENT'):
								self.writeInfo(l + '\n', 'gray')
			self.writeInfo(self.separator + '\n\n')
	# Template Help
	def templateHelp(self):
		self.modelHelp(self.templates.selectedItems())
	# Available Models Help
	def availableHelp(self):
		self.modelHelp(self.available.selectedItems())
	# Selected Models Help
	def selectedHelp(self):
		self.modelHelp(self.selected.selectedItems(), True)
	
	### End Application Helper Functions
	############################################################################



	############################################################################
	### Help Menu
	
	# Help
	def help(self, f):
		self.writeInfo(self.separator)
		with open(f, 'r') as fp:
			for line in fp:
				if ' - ' in line:
					self.writeInfo(line.split(' - ')[0], 'darkcyan')
					self.writeInfo(' - ' + line.split(' - ')[1])
				else:
					self.writeInfo(line, 'black', False)
		self.writeInfo(self.separator + '\n')
	# About
	def helpAbout(self):
		self.help('resources/about')
	# Creator
	def helpCreator(self):
		self.help('resources/creator')
	# Connector
	def helpConnector(self):
		self.help('resources/connector')
	# Grapher
	def helpTools(self):
		self.help('resources/tools')
	### End Help Menu
	############################################################################
	

##### Main Application Class End
####################################################################################


##### Main Function
if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = MyApp()
	window.show()
	sys.exit(app.exec_())