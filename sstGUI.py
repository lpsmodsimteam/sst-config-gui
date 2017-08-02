#!/usr/bin/env python3

# This is a model development script to help you develop,
# integrate and run a new model in SST. There should be
# a sstGUI.ui file, a logo.png file, and several help files
# in the resources directory. Templates can be found in
# the templates directory

import sys
import os
import subprocess
import re
import fileinput
import cgi
import xml.etree.ElementTree as ET
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

# Load the UI
Ui_MainWindow, QtBaseClass = uic.loadUiType('resources/sstGUI.ui')

##### Main Application Class
class MyApp(QMainWindow, Ui_MainWindow):

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
		self.actionModel_to_Template_Converter.triggered.connect(self.helpConverter)
		self.actionRun.triggered.connect(self.model2Template)
		# General setup
		self.modelName.setFocus()
		self.editor = os.getenv('EDITOR', 'gedit')
		self.separator = '********************************************************************************\n'
		self.updateTabs()
		# Model Creator Tab
		self.templates.itemDoubleClicked.connect(self.templateHelp)
		self.templateSelect.clicked.connect(self.selectTemplate)
		self.templateBrowse.clicked.connect(self.browseTemplates)
		# Model Connector Tab
		self.tabWidget.currentChanged.connect(self.updateTabs)
		self.add.clicked.connect(self.addModel)
		self.remove.clicked.connect(self.removeModel)
		self.available.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.available.itemDoubleClicked.connect(self.availableHelp)
		self.selected.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.selected.itemDoubleClicked.connect(self.selectedHelp)


	### Generate/Open Files
	def generateOpenFiles(self):
		if not self.getModel(): return
		# Check for template if in Creator Mode
		if self.tabWidget.currentIndex() == 0:
			if not self.getTemplate(): return
		# Check SST Registered Models and local folders
		self.updateModels()
		local = next(os.walk('.'))[1]
		makefiles = True
		if self.model in self.components or self.model in local:
			lib = self.runCommand('sst-config ' + self.model + ' ' + self.model + '_LIBDIR')
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
				self.writeInfo(self.separator)
				text = '*** THERE IS A SST MODEL WITH THAT NAME ALREADY!!! ***\n'
				text += '*** PLEASE CHOOSE ANOTHER NAME ***\n\n'
				self.writeInfo(text, 'red')
				self.writeInfo('SST provided models:\n')
				text = ''
				for item in self.components:
					text += item + '\n'
				self.writeInfo(text, 'blue')
				self.writeInfo(self.separator + '\n')
				return
		files = ''
		# Overwrite the model
		if makefiles:
			os.system(str('rm -rf ' + self.model))
		# Create/Open the files
		if self.tabWidget.currentIndex() == 0:
			if makefiles:
				self.createModel()
			self.templatesMessage(self.dest)
			for item in self.dest:
				files += './' + self.model + '/' + item + ' '
		elif self.tabWidget.currentIndex() == 1:
			if makefiles:
				self.connectModels()
			self.templatesMessage([self.model + '.py'])
			files += './' + self.model + '/' + self.model + '.py '
		# Open files
		os.system(str(self.editor + ' ' + files + '&'))


	### Configure Button main function
	def compileModel(self):
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


	### Run SST Button main function
	def runModel(self):
		if not self.getModel(): return
		# Run all tests
		if self.tabWidget.currentIndex() == 0:
			testfiles = os.listdir('./' + self.model + '/tests/')
		elif self.tabWidget.currentIndex() == 1:
			testfiles = os.listdir('./' + self.model)
		self.writeInfo(self.separator + '***** Running Model test(s) *****\n\n')
		for testfile in testfiles:
			self.writeInfo('*** ' + testfile + ' ***\n')
			if self.tabWidget.currentIndex() == 0:
				self.runCmdByLine(str('sst ' + self.model + '/tests/' + testfile))
			elif self.tabWidget.currentIndex() == 1:
				self.runCmdByLine(str('sst ' + self.model + '/' + testfile))
			self.writeInfo('\n')
		self.writeInfo(self.separator + '\n')



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



	### Model Connector Tab
	# Update the Available Models
	def updateModels(self):
		self.available.clear()
		# Store an ElementTree with all the xml data from sst-info
		self.elements = ET.fromstring(self.runCommand('sst-info -qnxo /dev/stdout'))
		# Store a list of the components SST knows about
		self.components = []
		for element in self.elements.findall('Element'):
			components = element.findall('Component')
			self.components.append(element.get('Name'))
			# Make sure the Element has Components the user can use
			if components:
				# Create an element item in the TreeWidget
				e = QTreeWidgetItem(self.available)
				e.setText(0, element.get('Name'))
				for component in components:
					# Create component items in the element item
					c = QTreeWidgetItem(e)
					c.setText(0, component.get('Name'))
					self.components.append(component.get('Name'))

	# Add Models
	def addModel(self):
		root = self.selected.invisibleRootItem()
		for item in self.available.selectedItems():
			# Make sure the item has a element (it is a component, not an element itself)
			if item.parent():
				elementExists = False
				# Loop through the elements to see if we have a element that matches already
				for i in range(root.childCount()):
					element = root.child(i)
					if item.parent().text(0) == element.text(0):
						elementExists = True
				# No element exists in the selected tree, create one
				if not elementExists:
					element = QTreeWidgetItem(self.selected)
					element.setText(0, item.parent().text(0))
				# Connect the component to the proper element
				component = QTreeWidgetItem(element)
				component.setText(0, item.text(0))
		self.selected.expandToDepth(0)

	# Remove Models
	def removeModel(self):
		root = self.selected.invisibleRootItem()
		for item in self.selected.selectedItems():
			(item.parent() or root).removeChild(item)



	### Application helper functions
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


	# Move and update the template files to create a new model
	def createModel(self):
		os.system(str('mkdir -p ' + self.model + '/tests'))
		# Loop through sources and destinations at the same time
		for s, d in zip(self.source, self.dest):
			with open(str(self.templatePath + '/' + s), 'r') as infile, open(str(self.model + '/' + d), 'w') as outfile:
				# Copy from source to destination while replacing <model> tags
				for line in infile:
					outfile.write(line.replace('<model>', str(self.model)))


	# Connect various models together
	def connectModels(self):
		root = self.selected.invisibleRootItem()
		os.system(str('mkdir -p ' + self.model))
		self.elements = ET.fromstring(self.runCommand('sst-info -qnxo /dev/stdout'))
		# Write the test python file
		with open(str(self.model + '/' + self.model + '.py'), 'w') as fp:
			fp.write('import sst\n\n# TODO: Check the parameters for all components and connect the links at the bottom before running!!!\n\n')
			# Loop through all the elements
			for i in range(root.childCount()):
				element = root.child(i)
				# Loop through all the components
				for j in range(element.childCount()):
					comp = element.child(j).text(0)
					# Write the Component Definition
					fp.write('obj' + str(i) + str(j) + ' = sst.Component("' + comp + str(i) + str(j) + '", "' + element.text(0) + '.' + comp + '")\n')
					fp.write('obj' + str(i) + str(j) + '.addParams({\n')
					parameters = self.elements.find("*/Component[@Name='" + comp + "']").findall('Parameter')
					# Remove the DEPRECATED parameters
					params = []
					for param in parameters:
						if not param.get('Description').strip().startswith('DEPRECATED'):
							params.append(param)
					# Write out all of the available parameters with their defaults and description
					for k in range(len(params)):
						if k == len(params) - 1:
							fp.write('\t"' + params[k].get('Name') + '" : "' + params[k].get('Default') + '"}) # ' + params[k].get('Description') + '\n\n')
						else:
							fp.write('\t"' + params[k].get('Name') + '" : "' + params[k].get('Default') + '", # ' + params[k].get('Description') + '\n')
			fp.write('\n###################################################################\n')
			fp.write('# TODO: Links have the first port connected but need to be manually\n')
			fp.write('# connected to a second port to work. Delays also should be edited\n\n')
			# After all components have been declared, write links
			for i in range(root.childCount()):
				element = root.child(i)
				# Loop through all the components
				for j in range(element.childCount()):
					comp = element.child(j).text(0)
					ports = self.elements.find("*/Component[@Name='" + comp + "']").findall('Port')
					fp.write('# ' + comp + ' Links\n')
					# Write out all of the available ports with their descriptions
					# These need to be modified by the user to actually connect components
					for k in range(len(ports)):
						
						fp.write('sst.Link("' + comp + '_' + ports[k].get('Name') + '").connect( (obj' + str(i) + str(j) + ', "' + ports[k].get('Name') + '", "1ps"), (OBJNAME, "PORTNAME", "DELAY") ) # ' + ports[k].get('Description') + '\n')
					fp.write('\n')


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
			self.writeInfo(output.decode("utf-8"), color)
		return process.poll()

	# Runs a command and returns the output when the command has completed
	def runCommand(self, command):
		return subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode("utf-8")


	# Update available models and templates
	def updateTabs(self):
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
		path = './templates/' + text
		# Copy the model into the templates directory, clean the model
		os.system(str('cp -r ' + model + ' ' + path))
		self.runCmdByLine(str('make clean -C ' + path))
		# Move any test files into the main directory with and add test- prefix
		for item in os.listdir(str(path + '/tests/')):
			os.system(str('mv ' + path + '/tests/' + item + ' ' + path + '/test-' + item))
		os.system(str('rmdir ' + path + '/tests'))
		modelName = os.path.basename(str(model))
		files = os.listdir(path)
		newFiles = []
		templateNames = []
		# For each file move the file to its new name and replace model with <model> tag
		for item in files:
			new = item.replace(modelName, str(text))
			newFiles.append(new)
			templateNames.append(item.replace(modelName, '<model>'))
			os.system(str('mv ' + path + '/' + item + ' ' + path + '/' + new))
		# Case insensitive replacing modelName with <model> tag
		pattern = re.compile(modelName, re.IGNORECASE)
		for new in newFiles:
			for line in fileinput.input(str(path + '/' + new), inplace=True):
				print(pattern.sub('<model>', line), end='')
		# Create the template file
		with open(str(path + '/template'), 'w') as fp:
			for new, tmp in zip(newFiles, templateNames):
				if new.endswith('.py'):
					fp.write(str(new + ' tests/' + tmp + '\n'))
				else:
					fp.write(str(new + ' ' + tmp + '\n'))
		self.writeInfo('\nNew template created: ' + path + '\n' + self.separator + '\n')
		self.updateTemplates()
		# Open the new template in an editor
		f = path + '/template '
		for new in newFiles:
			f += path + '/' + new + ' '
		os.system(str(self.editor + ' ' + f + '&'))


	# Display model help
	def modelHelp(self, items, elementInfo = False):
		for item in items:
			self.writeInfo(self.separator)
			# Write the sst-info output of the item
			if elementInfo:
				if item.parent():
					self.writeInfo(self.runCommand('sst-info ' + item.parent().text(0) + '.' + item.text(0)), 'gray')
				else:
					self.writeInfo(self.runCommand('sst-info ' + item.text(0)), 'gray')
			# Find doxygen comments from template
			else:
				f = os.getcwd() + '/templates/' + item.text() + '/' + item.text() + '.cc'
				if os.path.isfile(f):
					# Look for doxygen style comments
					with open(f, 'r') as help:
						incomment = False
						for line in help:
							if incomment:
								if line.strip().endswith('*/'):
									incomment = False
									self.writeInfo('\n')
								else:
									self.writeInfo(line)
							else:
								if line.strip().startswith('/**'):
									incomment = True
			self.writeInfo(self.separator + '\n')
	# Template Help
	def templateHelp(self):
		self.modelHelp(self.templates.selectedItems())
	# Available Models Help
	def availableHelp(self):
		self.modelHelp(self.available.selectedItems(), True)
	# Selected Models Help
	def selectedHelp(self):
		self.modelHelp(self.selected.selectedItems(), True)


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
	# Model2Template
	def helpConverter(self):
		self.help('resources/model2template')

##### Main Application Class End


##### Main Function
if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = MyApp()
	window.show()
	sys.exit(app.exec_())
