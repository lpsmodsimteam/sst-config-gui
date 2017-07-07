#!/usr/bin/python

# This is a model development script to help you develop,
# integrate and run a new model in SST. The code is setup
# in a menu option and each menu option corresponds to a
# button on the GUI. There should be a sstGUI.ui file,
# a README file and a logo.png file
# in the same directory to run this script.

import sys
import os
import subprocess
import re
import fileinput
from PyQt4.QtGui import *
from PyQt4 import uic

# Load the UI
Ui_MainWindow, QtBaseClass = uic.loadUiType("sstGUI.ui")


##### Main Application Class
class MyApp(QMainWindow, Ui_MainWindow):
	
	### Initialization Function
	def __init__(self):
		QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.setWindowIcon(QIcon('logo.png'))
		self.generate.clicked.connect(self.generateOpenFiles)
		self.compile.clicked.connect(self.compileModel)
		self.run.clicked.connect(self.runModel)
		self.actionOpen_Help.triggered.connect(self.help)
		self.actionModel2Template.triggered.connect(self.model2Template)
		self.modelName.setFocus()
		self.editor = os.getenv('EDITOR', 'gedit')
		self.separator = '********************************************************************************\n'
		# Model Creator Tab
		self.templateBrowse.clicked.connect(self.browseTemplates)
		# Model Connector Tab
		self.tabWidget.currentChanged.connect(self.updateModels)
		self.sstModels.stateChanged.connect(self.updateModels)
		self.localModels.stateChanged.connect(self.updateModels)
		self.modelBrowse.clicked.connect(self.browseModels)
		self.add.clicked.connect(self.addModel)
		self.remove.clicked.connect(self.removeModel)
		self.available.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.selected.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.updateModels()
	
	
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
				text = "Do you really want to overwrite your local version of " + self.model + "?"
				val = self.warningPopup(text, "Overwrite Model?")
				if (val == QMessageBox.No):
					makefiles = 0
			else:
				makefiles = 0
		files = ''
		if (makefiles == 1):
			os.system(str('rm -rf ' + self.model))
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
		testfiles = os.listdir('./' + self.model + '/tests/')
		self.writeInfo(self.separator + '***** Running Model test(s) *****\n\n')
		for testfile in testfiles:
			self.writeInfo('*** ' + testfile + ' ***\n')
			self.runCommand(str('sst ' + self.model + '/tests/' + testfile))
			self.writeInfo('\n')
		self.writeInfo(self.separator + '\n')



	### Model Creator Tab
	# Browse the templates folder
	def browseTemplates(self):
		templates = os.walk('./templates/').next()[1]
		item, ok = QInputDialog.getItem(self, "Select Template", "Select Cancel if you don't see your template listed", templates, 0, False)
		if ok and item:
			self.templateType.setText(str(os.getcwd() + '/templates/' + item))
		else:
			templatePath = QFileDialog.getExistingDirectory(self, "Select Template", "./templates/", QFileDialog.ShowDirsOnly)
			self.templateType.setText(str(templatePath))
	
	
	
	### Model Connector Tab
	# Update the Available Models
	def updateModels(self):
		self.available.clear()
		if self.localModels.isChecked():
			items = os.walk('./').next()[1]
			for item in items:
				if item != 'templates' and item != '.git':
					self.available.addItem(str('./' + item))
		if self.sstModels.isChecked():
			[path, version] = str(os.getenv('SST_ELEMENTS_HOME')).split('/local/sstelements-')
			self.elements = path + '/scratch/src/sst-elements-library-' + version + '/src/sst/elements/'
			self.available.addItems(os.walk(self.elements).next()[1])
	
	
	# Browse for additional models
	def browseModels(self):
		modelDir = QFileDialog.getExistingDirectory(self, "Select Model", "./", QFileDialog.ShowDirsOnly)
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
		self.templatePath = str(self.templateType.text())
		self.template = os.path.basename(self.templatePath)
		if (self.template == ''):
			self.writeInfo('*** PLEASE SELECT A TEMPLATE ***\n\n')
			return False
		if not os.path.isfile(self.templatePath + '/template'):
			self.writeInfo('*** TEMPLATE PATH IS INCORRECT OR TEMPLATE IS SETUP WRONG ***\n\n')
			return False
		with open(self.templatePath + '/template', 'r') as fp:
			structure = fp.read()
		self.source = structure.split()[0::2]
		destination = structure.split()[1::2]
		self.dest=[]
		self.sourceFiles=[]
		for item in destination:
			self.dest.append(item.replace('<model>', str(self.model)))
			if (".cc" in item) | (".h" in item):
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
			fp.write('all:\n')
			for i in xrange(self.selected.count()):
				item = str(self.selected.item(i).text())
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
			for i in xrange(self.selected.count()):
				item = os.path.basename(str(self.selected.item(i).text()))
				fp.write('obj' + str(i) + ' = sst.Component("' + item + str(i) + '", "' + item + '.' + item + '")\n')
				fp.write('obj' + str(i) + '.addParams({\n\t"param1" : "val1",\n\t"param2" : "val2"\n\t})\n\n')
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
			 	self.writeInfo(output.decode("utf-8"))
		return process.poll()
	
	
	
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
		text += 'After your are done you can proceed to the next step "Compile Model".\n'
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
		model = QFileDialog.getExistingDirectory(self, "Select Model", "./", QFileDialog.ShowDirsOnly)
		templates = os.listdir('./templates/')
		if not model:
			self.writeInfo('*** PLEASE SELECT A MODEL TO CONVERT ***\n\n')
			return
		self.writeInfo('Model to convert: ' + model + '\n\n')
		text, ok = QInputDialog.getText(self, "Enter Template Name", "", QLineEdit.Normal)
		if not ok or not text:
			self.writeInfo('*** PLEASE ENTER A TEMPLATE NAME ***\n\n')
			return
		if text in templates:
			self.writeInfo('*** TEMPLATE ALREADY EXISTS ***\n\n')
			return
		path = './templates/' + text
		os.system(str('cp -r ' + model + ' ' + path))
		os.system(str('make clean -C ' + path))
		os.system(str('mv ' + path + '/tests/* ' + path + '/.'))
		os.system(str('rmdir ' + path + '/tests'))
		modelName = os.path.basename(str(model))
		pattern = re.compile(modelName, re.IGNORECASE)
		files = os.listdir(path)
		newFiles = []
		templateNames = []
		for item in files:
			new = pattern.sub(str(text), item)
			newFiles.append(new)
			templateNames.append(pattern.sub('<model>', item))
			os.system(str('mv ' + path + '/' + item + ' ' + path + '/' + new))
		for new in newFiles:
			for line in fileinput.input(str(path + '/' + new), inplace=True):
				print pattern.sub('<model>', line),
		with open(str(path + '/template'), 'w') as fp:
			for new, tmp in zip(newFiles, templateNames):
				if new.endswith('.py'):
					fp.write(str(new + ' tests/' + tmp + '\n'))
				else:
					fp.write(str(new + ' ' + tmp + '\n'))
		self.writeInfo('New template created: ' + path + '\n\n')
		
	
	# Help Menu
	def help(self):
		with open('README', 'r') as fp:
			text = fp.read()
		self.writeInfo(text)

##### Main Application Class End 


##### Main Function
if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MyApp()
	window.show()
	sys.exit(app.exec_())

