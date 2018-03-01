#!/usr/bin/env python3

# This is a model development script to help you develop,
# integrate and run a new model in SST. There should be
# a sstGUI.ui file, a logo.png file, several other .png files
# and several help files in the resources directory.
# Templates can be found in the templates directory

import sys
import os
import subprocess
import glob
import html
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
		self.browseDir.clicked.connect(self.browseDirectories)
		# Dropdown Menus
		self.helpMenu.currentIndexChanged.connect(self.helpSelect)
		self.toolsMenu.currentIndexChanged.connect(self.toolsSelect)
		# General setup
		self.modelDir.setText(str(os.getcwd()))
		self.modelName.setFocus()
		self.editor = os.getenv('EDITOR', 'gedit')
		self.SSTinstalled = None
		self.firstSeparator = True
		self.updateTabs()
		self.tabWidget.currentChanged.connect(self.updateTabs)
		# Model Creator Tab
		self.templates.itemDoubleClicked.connect(self.templateHelp)
		self.templates.currentItemChanged.connect(self.selectTemplate)
		self.templateBrowse.clicked.connect(self.browseTemplates)
		self.generate.clicked.connect(self.generateOpenFiles)
		self.compile.clicked.connect(self.compileModel)
		self.run.clicked.connect(self.runModel)
		# Subcomponent Creator Tab
		self.headerBrowse.clicked.connect(self.browseHeaders)
		self.generate_sub.clicked.connect(self.generateSub)
		# Model Connector Tab
		self.newComp.clicked.connect(self.addModel)
		self.addSub.clicked.connect(self.addSubcomponent)
		self.remove.clicked.connect(self.removeModel)
		self.available.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.available.itemDoubleClicked.connect(self.availableHelp)
		self.available.setExpandsOnDoubleClick(False)
		self.selected.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.selected.itemDoubleClicked.connect(self.selectedHelp)
		self.selected.setExpandsOnDoubleClick(False)
		self.generate_con.clicked.connect(self.generateCon)
		self.run_con.clicked.connect(self.runCon)
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
	
	
	# Creates or opens model files
	def generateOpenFiles(self):
		if not self.getModel(): return
		if not self.getTemplate(): return
		# Check SST Registered Models and local folders
		makefiles = self.checkModels()
		if makefiles == None:
			return
		# Create the model using the template
		if makefiles:
			os.system(str('rm -rf ' + self.model))
			sstSHELL.createModel(self.model, self.templatePath, self.modelPath)
		f = ''
		for item in self.dest:
			f += self.modelPath + '/' + self.model + '/' + item + ' '
		# Open files
		self.createdFilesMessage(f.rstrip().split(' '))
		os.system(str(self.editor + ' ' + f + '&'))
	
	
	# Compiles and registers the model with SST
	def compileModel(self):
		if not self.isSSTinstalled(): return
		if not self.getModel(): return
		self.writeSeparator()
		self.writeInfo('***** Building Model *****\n\n')
		if self.clean.isChecked():
			self.runCmdByLine(str('make clean -C ' + self.modelPath + '/' + self.model))
		# runCmdByLine returns the make return value (0 success, others fail)
		failed = self.runCmdByLine(str('make all -C ' + self.modelPath + '/' + self.model))
		if failed:
			self.writeInfo('\n*** ERROR DURING MAKE!!! PLEASE FIX THE ERROR BEFORE CONTINUING ***', 'red')
			return
		# make all passed
		self.writeInfo('\nModel has compiled successfully\n')
		# Run the model if autorun is checked
		if self.autoRun.isChecked():
			self.runModel()
	
	
	# Runs the tests in the model/tests/ folder
	def runModel(self):
		if not self.isSSTinstalled(): return
		if not self.getModel(): return
		self.writeSeparator()
		self.writeInfo('***** Running Model test(s) *****\n\n')
		self.runTests(sorted(glob.glob(self.modelPath + '/' + self.model + '/tests/*.py')))
	
	### End Model Creator Tab
	############################################################################
	
	
	
	############################################################################
	### Subcomponent Creator Tab
	
	# Browse for a header file containing a subcomponent prototype
	def browseHeaders(self):
		# Get the path to the header file
		path = QFileDialog.getOpenFileName(self, 'Select Header File', '.', 'Header files (*.h)')[0]
		if not path:
			self.writeInfo('*** PLEASE SELECT A HEADER FILE ***\n\n', 'red')
			return
		self.header.setText(path)
		self.available_sub.clear()
		self.modelDir.setText(os.path.dirname(path))
		with open(path, 'r') as fp:
			for line in fp:
				if 'SST::SubComponent' in line:
					self.available_sub.addItem(line.lstrip().split(':')[0].split(' ')[1])
	
	
	# Generate a subcomponent using the prototype selected from the header file
	def generateSub(self):
		if not self.getModel(): return
		if self.available_sub.currentItem() == None:
			self.writeInfo('*** PLEASE SELECT A SUBCOMPONENT TYPE ***\n\n', 'red')
			return
		# make sure the files don't already exist
		files = os.listdir(self.modelPath)
		if str(self.model + '.cc') in files or str(self.model + '.h') in files:
			if self.overwrite.isChecked():
				text = 'Files already exist(' + self.model + '.cc, ' + self.model + '.h), are you sure you want to overwrite?'
				val = self.warningPopup(text, 'Overwrite Files?')
				if val == QMessageBox.No:
					return
			else:
				self.writeInfo('*** FILES ALREADY EXIST WITH THIS NAME ***\n\n', 'red')
				return
		sstSHELL.createSubcomponent(self.model, self.available_sub.currentItem().text(), self.header.text())
		f = self.modelPath + '/' + self.model + '.cc ' + self.modelPath + '/' + self.model + '.h'
		self.createdFilesMessage(f.split(' '))
		self.writeInfo('Make sure to add the subcomponent into the Element\'s Makefile so that it gets built\n', 'green')
		os.system(str(self.editor + ' ' + f + ' &'))
		
	### End Subcomponent Creator Tab
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
	
	
	# Creates or opens python file
	def generateCon(self):
		if not self.isSSTinstalled(): return
		if not self.getModel(): return
		# Check SST Registered Models and local folders
		makefiles = self.checkModels()
		if makefiles == None:
			return
		if makefiles:
			# Check for selected components
			if self.selected.invisibleRootItem().childCount() == 0:
				self.writeInfo('*** NO COMPONENTS SELECTED ***\n\n', 'red')
				return
			os.system(str('rm -rf ' + self.model))
			components = ''
			root = self.selected.invisibleRootItem()
			# build up the list with format element.component.subcomponent,subcomponent;
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
			sstSHELL.connectModels(self.model, components, self.modelPath)
		f = self.modelPath + '/' + self.model + '/' + self.model + '.py'
		# Open files
		self.createdFilesMessage([f])
		os.system(str(self.editor + ' ' + f + ' &'))
	
	
	# Runs the tests in the model folder
	def runCon(self):
		if not self.isSSTinstalled(): return
		if not self.getModel(): return
		self.writeSeparator()
		self.writeInfo('***** Running Model test(s) *****\n\n')
		self.runTests(sorted(glob.glob(self.modelPath + '/' + self.model + '/*.py')))
	
	### End Model Connector Tab
	############################################################################
	
	
	
	############################################################################
	### Menu functions (not including Help)
	
	# Tools Dropdown has changed
	def toolsSelect(self):
		t = self.toolsMenu.currentIndex()
		self.toolsMenu.setCurrentIndex(0)
		if t == 1:
			self.graphModel()
		elif t == 2:
			self.paramSweep()
		elif t == 3:
			self.model2Template()
	
	
	# Graph a model
	def graphModel(self):
		if not self.isSSTinstalled(): return
		# Get the path to the python test file
		path = QFileDialog.getOpenFileName(self, 'Select Python Test File', '.', 'Python files (*.py)')[0]
		if not path:
			self.writeInfo('*** PLEASE SELECT A PYTHON TEST FILE ***\n\n', 'red')
			return
		files = sstSHELL.graphModel(path)
		self.createdFilesMessage(files.split(' '))
		for f in files.split(' '):
			if not f.endswith('.2.jpg') and not f.endswith('.dot'):
				QDesktopServices.openUrl(QUrl(f))
	
	
	# Parameter sweep expansion
	def paramSweep(self):
		# Get the path to the python test file
		path = QFileDialog.getOpenFileName(self, 'Select Python Test File', '.', 'Python files (*.py)')[0]
		if not path:
			self.writeInfo('*** PLEASE SELECT A PYTHON TEST FILE ***\n\n', 'red')
			return
		self.writeSeparator()
		self.writeInfo('Expanding Parameters\n')
		subdir = sstSHELL.paramSweep(path)
		if subdir.startswith('ERROR'):
			self.writeInfo(subdir, 'red')
		else:
			self.writeInfo('Parameters expanded successfully into ' + subdir + '\n')
	
	
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
		self.writeSeparator()
		self.writeInfo('***** Converting Model into Template *****\n\n')
		self.writeInfo('Converting ' + model + ' to ' + text + '\n\n')
		f = sstSHELL.model2Template(model, text)
		self.writeInfo('\nNew template created: ' + './templates/' + text + '\n')
		self.updateTemplates()
		# Open the new template in an editor
		os.system(str(self.editor + ' ' + f + '&'))
	
	### End Menu Functions
	############################################################################
	
	
	
	############################################################################
	### Application helper functions
	
	# Browse for a directory to put the model in
	def browseDirectories(self):
		# Prompt for a directory
		directory = QFileDialog.getExistingDirectory(self, 'Select Directory', './', QFileDialog.ShowDirsOnly)
		if not directory:
			self.writeInfo('*** PLEASE SELECT A DIRECTORY ***\n\n', 'red')
		else:
			self.modelDir.setText(str(directory))
	
	
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
			self.writeInfo('*** SST IS NOT INSTALLED. YOU WILL NOT BE ABLE TO COMPILE OR RUN ANYTHING, BUT YOU CAN STILL CREATE MODELS FROM TEMPLATES ***\n\n', 'red')
			return False
	
	
	# Gets the model name from the GUI
	def getModel(self):
		self.model = self.modelName.text()
		self.modelPath = self.modelDir.text()
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
	
	
	# checks the model name to see if a SST model already exists
	def checkModels(self):
		self.updateModels()
		local = next(os.walk(self.modelPath))[1]
		makefiles = True
		if self.model in self.elements or self.model in local:
			# Model is already registered with SST or it is a local model
			if self.model in local:
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
				self.writeSeparator()
				text = '*** THERE IS A SST MODEL WITH THAT NAME ALREADY!!! ***\n'
				text += '*** PLEASE CHOOSE ANOTHER NAME ***\n\n'
				self.writeInfo(text, 'red')
				self.writeInfo('SST provided models:\n')
				text = ''
				for item in self.elements:
					text += item + '\n'
				self.writeInfo(text, 'blue')
				return None
		return makefiles
	
	
	# loops through all the tests and runs them
	def runTests(self, testfiles):
		for testfile in testfiles:
			self.writeInfo('*** ' + os.path.basename(testfile) + ' ***\n')
			sweep = False
			with open(testfile, 'r') as infile:
				found = False
				for line in infile:
					if not line.lstrip().startswith('#'): # Skip comments
						if '.addParams' in line:
							found = True
						if found:
							newline = line.strip().split(':')
							if len(newline) >= 2:
								value = newline[1].split('"')[1]
								if ';' in value or ',' in value:
									sweep = True
			if sweep:
				subdir = sstSHELL.paramSweep(testfile)
				if subdir.startswith('ERROR'):
					self.writeInfo(subdir, 'red')
				else:
					sweepfiles = sorted(glob.glob(subdir + '/*.py'))
					for sweep in sweepfiles:
						self.writeInfo('\n** ' + os.path.basename(sweep) + ' **\n')
						self.runCmdByLine(str('sst ' + sweep))
			else:
				self.runCmdByLine(str('sst ' + testfile))
	
	
	# Write a horizontal separator to information screen
	def writeSeparator(self):
		if self.firstSeparator:
			self.firstSeparator = False
		else:
			self.info.moveCursor(QTextCursor.End)
			self.info.insertHtml('<hr><br>')
			self.info.moveCursor(QTextCursor.End)
	
	
	# Write to information screen
	# Available Colors:
	# black(default), darkgray, gray, lightgray, white,
	# red, yellow, green, cyan, blue, magenta,
	# darkred, darkyellow, darkgreen, darkcyan, darkblue, darkmagenta
	def writeInfo(self, text, color='black', update=True):
		colorText = '<span style="white-space:pre-wrap; color:' + QColor(color).name() + ';">'
		colorText += html.escape(text) + '</span>'
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
		self.modelDir.setText(str(os.getcwd()))
		if self.tabWidget.currentIndex() == 1 and self.header.text():
			self.modelDir.setText(os.path.dirname(self.header.text()))
	
	
	# File Creation message
	def createdFilesMessage(self, files):
		self.writeSeparator()
		self.writeInfo('The following files have been created/opened:\n')
		text = ''
		for item in files:
			text += '\t- ' + item + '\n'
		self.writeInfo(text, 'green')
	
	
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
	
	
	# Display template help
	def templateHelp(self):
		for item in self.templates.selectedItems():
			self.writeSeparator()
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
	
	
	# Display model information from sst-info
	def sstInfoHelp(self, items, displayAll = False):
		for item in items:
			self.writeSeparator()
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
	# Available Models Help
	def availableHelp(self):
		self.sstInfoHelp(self.available.selectedItems())
	# Selected Models Help
	def selectedHelp(self):
		self.sstInfoHelp(self.selected.selectedItems(), True)
	
	### End Application Helper Functions
	############################################################################
	
	
	
	############################################################################
	### Help Menu
	
	# Help Dropdown has changed
	def helpSelect(self):
		h = self.helpMenu.currentIndex()
		self.helpMenu.setCurrentIndex(0)
		if h == 1:
			self.help('resources/about.txt')
		elif h == 2:
			self.help('resources/global.txt')
		elif h == 3:
			self.help('resources/creator.txt')
		elif h == 4:
			self.help('resources/subcomponent.txt')
		elif h == 5:
			self.help('resources/connector.txt')
		elif h == 6:
			self.help('resources/tools.txt')
	
	# Help
	def help(self, f):
		self.writeSeparator()
		with open(f, 'r') as fp:
			for line in fp:
				if ' - ' in line:
					self.writeInfo(line.split(' - ')[0], 'darkcyan')
					self.writeInfo(' - ' + line.split(' - ')[1])
				else:
					self.writeInfo(line, 'black', False)
	
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

