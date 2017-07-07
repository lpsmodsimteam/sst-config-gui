#!/usr/bin/python

# This is a model development script to help you develop,
# integrate and run a new model in SST. There should be
# a sstGUI.ui file, a logo.png file, and several help files
# in the resources directory. Templates can be found in
# the templates directory

import sys
import os
import subprocess
from PyQt4.QtGui import *
from PyQt4 import uic

# Load the UI
Ui_MainWindow, QtBaseClass = uic.loadUiType('resources/sstGUI.ui')


##### Main Application Class
class MyApp(QMainWindow, Ui_MainWindow):
	
	### Initialization Function
	def __init__(self):
		QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.setWindowIcon(QIcon('resources/logo.png'))
		self.logo.setPixmap(QPixmap('resources/logo.png'))
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
		# Model Creator Tab
		self.templateSelect.clicked.connect(self.selectTemplate)
		self.templateBrowse.clicked.connect(self.browseTemplates)
		self.updateTemplates()
		# Model Connector Tab
		self.tabWidget.currentChanged.connect(self.updateTabs)
		self.sstModels.stateChanged.connect(self.updateModels)
		self.localModels.stateChanged.connect(self.updateModels)
		self.modelBrowse.clicked.connect(self.browseModels)
		self.add.clicked.connect(self.addModel)
		self.remove.clicked.connect(self.removeModel)
		self.available.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.selected.setSelectionMode(QAbstractItemView.ExtendedSelection)
	
	
	### Generate/Open Files
	def generateOpenFiles(self):
		if not self.getModel(): return
		# Check for template if in Creator Mode
		if self.tabWidget.currentIndex() == 0:
			if not self.getTemplate(): return
		# Do some checking see if you already have a model in your working directory
		# with the same name or if there is one in the element directory
		workingModels = os.listdir('.')
		makefiles = 1
		# Check local models
		if (workingModels.count(self.model) != 0):
			if self.overwrite.isChecked():
				text = 'Do you really want to overwrite your local version of ' + self.model + '?'
				val = self.warningPopup(text, 'Overwrite Model?')
				if (val == QMessageBox.No):
					makefiles = 0
			else:
				makefiles = 0
		files = ''
		# Overwrite the model
		if (makefiles == 1):
			os.system(str('rm -rf ' + self.model))
		# Create/Open the files
		if self.tabWidget.currentIndex() == 0:
			if (makefiles == 1):
				self.createModel()
			self.templatesMessage(self.dest)
			for item in self.dest:
				files += './' + self.model + '/' + item + ' '
		elif self.tabWidget.currentIndex() == 1:
			if (makefiles == 1):
				self.connectModels()
			self.templatesMessage(['Makefile', '/tests/' + self.model + '.py'])
			files += './' + self.model + '/Makefile ./' + self.model + '/tests/' + self.model + '.py '
		# Open files
		os.system(str(self.editor + ' ' + files + '&'))


	### Configure Button main function
	def compileModel(self):
		if not self.getModel(): return
		self.writeInfo(self.separator + '***** Building Model *****\n\n')
		# make clean
		if self.clean.isChecked():
			self.runCommand(str('make clean -C ' + self.model))
		# runCommand returns the make return value (0 success, others fail)
		failed = self.runCommand(str('make all -C ' + self.model))
		if failed:
			text = '\n*** ERROR DURING MAKE!!! PLEASE FIX THE ERROR BEFORE CONTINUING ***\n'
			text += self.separator + '\n'
			self.writeInfo(text)
			return
		# make all passed
		text = '\nSST has been configured to run your model you may now proceed to the next\n'
		text += 'step Run Model\n'
		text += self.separator + '\n'
		self.writeInfo(text)
		# Run the model if autorun is checked
		if self.autoRun.isChecked():
			self.runModel()


	### Run SST Button main function
	def runModel(self):
		if not self.getModel(): return
		# Run all files under the tests directory
		testfiles = os.listdir('./' + self.model + '/tests/')
		self.writeInfo(self.separator + '***** Running Model test(s) *****\n\n')
		for testfile in testfiles:
			self.writeInfo('*** ' + testfile + ' ***\n')
			self.runCommand(str('sst ' + self.model + '/tests/' + testfile))
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
		self.templates.addItems(os.walk('./templates/').next()[1])
	
	
	
	### Model Connector Tab
	# Update the Available Models
	def updateModels(self):
		self.available.clear()
		# Display the local models on top
		if self.localModels.isChecked():
			items = os.walk('./').next()[1]
			for item in items:
				if item != 'templates' and item != 'resources' and item != '.git':
					self.available.addItem(str('./' + item))
		# Display SST models on bottom
		if self.sstModels.isChecked():
			[path, version] = str(os.getenv('SST_ELEMENTS_HOME')).split('/local/sstelements-')
			self.elements = path + '/scratch/src/sst-elements-library-' + version + '/src/sst/elements/'
			self.available.addItems(os.walk(self.elements).next()[1])
	
	# Browse for additional models
	def browseModels(self):
		modelDir = QFileDialog.getExistingDirectory(self, 'Select Model', './', QFileDialog.ShowDirsOnly)
		if modelDir:
			self.selected.addItem(modelDir)
	
	# Add Models
	def addModel(self):
		for item in self.available.selectedItems():
			self.selected.addItem(item.text())
	
	# Remove Models
	def removeModel(self):
		for item in self.selected.selectedItems():
			self.selected.takeItem(self.selected.row(item))
	
	
	
	### Application helper functions
	# Gets the model name from the GUI
	def getModel(self):
		self.model = self.modelName.text()
		if (self.model == ''):
			self.writeInfo('*** PLEASE ENTER A MODEL NAME ***\n\n')
			return False
		return True
	
	
	# Gets the template information
	def getTemplate(self):
		# Get template path from GUI
		self.templatePath = str(self.templateType.text())
		self.template = os.path.basename(self.templatePath)
		# Check for empty string
		if (self.template == ''):
			self.writeInfo('*** PLEASE SELECT A TEMPLATE ***\n\n')
			return False
		# Check for a valid template
		if not os.path.isfile(self.templatePath + '/template'):
			self.writeInfo('*** TEMPLATE PATH IS INCORRECT OR TEMPLATE IS SETUP WRONG ***\n\n')
			return False
		# Read template sources and destinations
		with open(self.templatePath + '/template', 'r') as fp:
			structure = fp.read()
		self.source = structure.split()[0::2]
		destination = structure.split()[1::2]
		self.dest=[]
		self.sourceFiles=[]
		# Replace <model> tag with the model name
		for item in destination:
			self.dest.append(item.replace('<model>', str(self.model)))
			if ('.cc' in item) | ('.h' in item):
				self.sourceFiles.append(item.replace('<model>', str(self.model)))
		return True
	
	
	# Move and update the template files to create a new model
	def createModel(self):
		os.system(str('mkdir -p ' + self.model + '/tests'))
		for s, d in zip(self.source, self.dest):
			os.system(str('cp ' + self.templatePath + '/' + s + ' ' + self.model + '/' + d))
			os.system(str('sed -i \'s/<model>/' + self.model + '/g\' ' + self.model + '/' + d))
			os.system(str('sed -i \'s/<sourceFiles>/' + ' '.join(self.sourceFiles) + '/g\' ' + self.model + '/' + d))
	
	
	# Connect various models together
	def connectModels(self):
		os.system(str('mkdir -p ' + self.model + '/tests'))
		make = '\t$(MAKE) -C '
		# Write the Makefile
		with open(str(self.model + '/Makefile'), 'w') as fp:
			# Make all command
			fp.write('all:\n')
			for i in xrange(self.selected.count()):
				item = str(self.selected.item(i).text())
				# Handle full paths, local paths, and no paths
				# Browsed models, local models, SST default models respectively
				if item.startswith('/'):
					fp.write(make + item + ' all\n')
				elif item.startswith('./'):
					fp.write(make + os.getcwd() + '/' + os.path.basename(item) + ' all\n')
				else:
					fp.write(make + self.elements + os.path.basename(item) + ' all\n')
			fp.write('\nclean:\n')
			for i in xrange(self.selected.count()):
				item = str(self.selected.item(i).text())
				if item.startswith('/'):
					fp.write(make + item + ' clean\n')
				elif item.startswith('./'):
					fp.write(make + os.getcwd() + '/' + os.path.basename(item) + ' clean\n')
				else:
					fp.write(make + self.elements + os.path.basename(item) + ' clean\n')
		# Write the test python file
		with open(str(self.model + '/tests/' + self.model + '.py'), 'w') as fp:
			fp.write('import sst\n\n')
			# Add in the component declarations
			for i in xrange(self.selected.count()):
				item = os.path.basename(str(self.selected.item(i).text()))
				fp.write('obj' + str(i) + ' = sst.Component("' + item + str(i) + '", "' + item + '.' + item + '")\n')
				fp.write('obj' + str(i) + '.addParams({\n\t"param1" : "val1",\n\t"param2" : "val2"\n\t})\n\n')
			# Add an example link at the end to show how to connect objects
			fp.write('sst.Link("MyLink").connect( (obj0, "port", "15ns"), (obj1, "port", "15ns") )')
	
	
	# Write to information screen
	def writeInfo(self, text):
		self.info.moveCursor(QTextCursor.End)
		self.info.insertPlainText(text)
		self.info.moveCursor(QTextCursor.End)
		app.processEvents() # force the GUI to display the text
	
	
	# Runs a command and prints the output line by line
	def runCommand(self, command):
		process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		while True:
			output = process.stdout.readline()
			if output == '' and process.poll() is not None:
				break
			if output:
			 	self.writeInfo(output.decode('utf-8'))
		return process.poll()
	
	
	# Update available models and templates
	def updateTabs(self):
		self.updateModels()
		self.updateTemplates()
	
	
	# Information for template generation
	def templatesMessage(self, files):
		text = self.separator
		text += 'The following Templates should be displayed in the pop-up editor\n'
		for item in files:
			text += '\t- ' + item + '\n'
		text += 'Please review/edit your files to create your model. You can make changes in\n'
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
			self.writeInfo('*** PLEASE SELECT A MODEL TO CONVERT ***\n\n')
			return
		# Get the new template name
		text, ok = QInputDialog.getText(self, 'Enter Template Name', '', QLineEdit.Normal)
		if not ok or not text:
			self.writeInfo('*** PLEASE ENTER A TEMPLATE NAME ***\n\n')
			return
		# Check to see if the template exists already
		templates = os.listdir('./templates/')
		if text in templates:
			self.writeInfo('*** TEMPLATE ALREADY EXISTS ***\n\n')
			return
		self.writeInfo(self.separator + '***** Converting Model into Template *****\n\n')
		self.writeInfo('Converting ' + model + ' to ' + text + '\n\n')
		path = './templates/' + text
		# Copy the model into the templates directory, clean the model
		os.system(str('cp -r ' + model + ' ' + path))
		self.runCommand(str('make clean -C ' + path))
		# Move any test files into the main directory with and add test- prefix
		for item in os.listdir(str(path + '/tests/')):
			os.system(str('mv ' + path + '/tests/' + item + ' ' + path + '/test-' + item))
		os.system(str('rmdir ' + path + '/tests'))
		modelName = os.path.basename(str(model))
		files = os.listdir(path)
		newFiles = []
		templateNames = []
		# For each file move the file to its new name
		for item in files:
			new = item.replace(modelName, str(text))
			newFiles.append(new)
			templateNames.append(item.replace(modelName, '<model>'))
			self.runCommand(str('mv ' + path + '/' + item + ' ' + path + '/' + new))
		# For all the new files replace the strings within
		for new in newFiles:
			os.system(str('sed -i \'s/' + modelName + '/<model>/Ig\' ' + path + '/' + new))
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
			
		
	
	### Help Menu
	# Help
	def help(self, f):
		with open(f, 'r') as fp:
			text = fp.read()
		self.writeInfo(text)
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

