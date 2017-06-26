#!/usr/bin/python

# This is a model development script to help you develop,
# integrate and run a new model in SST. The code is setup
# in a menu option and each menu option corresponds to a
# button on the GUI. There should be a sstGUI.ui file, a README
# file and a sst-logo-small.png file in the same directory
# to run this script.

import sys
import os
import fileinput
import site
import getopt
import re
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4 import uic
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import subprocess
from subprocess import call

qtCreatorFile = "sstGUI.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

### Assistant functions for the application class
# Runs a command and returns the output line by line
def run_command(LinuxCmd):
	p = subprocess.Popen(LinuxCmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	return iter(p.stdout.readline, b'')

# Generates a warning pop-up when you try to overwrite existing files
def warningPopup(text):
	msg = QMessageBox()
	msg.setIcon(QMessageBox.Warning)
	msg.setText(text)
	msg.setWindowTitle("Overwrite Model")
	msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
	msg.setDefaultButton(QMessageBox.No)
	msg.buttonClicked.connect(warningButton)
	return msg.exec_()

def warningButton(button):
	return button


##### Main Application Class
class MyApp(QtGui.QMainWindow, Ui_MainWindow):
	# Initialization Function
	def __init__(self):
		QtGui.QMainWindow.__init__(self)
	   	Ui_MainWindow.__init__(self)
		self.setupUi(self)
		self.setWindowIcon(QtGui.QIcon('sst-logo-small.png'))
		self.browse.clicked.connect(self.browseTemplates)
		self.templates.clicked.connect(self.MakeTemplates)
		self.Configure.clicked.connect(self.ConfigureSST)
		self.RunSST.clicked.connect(self.Run)
		self.actionOpen_Help.triggered.connect(self.help)
	
	### Browse the templates folder
	def browseTemplates(self):
		templatePath = QFileDialog.getExistingDirectory(self, "Select Template", "./templates/", QFileDialog.ShowDirsOnly)
		self.templateType.setText(str(templatePath))
	
	### Generate Templates Button main function
	def MakeTemplates(self):
		if not self.getModel(): return
		if not self.getTemplate(): return
		
		# Do some checking see if you already have a model in your working directory
		# with the same name or if there is one in the element directory
		workingModels = os.listdir('.')
		makefiles = 1

		# Check local models
		if (workingModels.count(self.model) != 0):
			if self.overwrite.isChecked():
				text = "Do you really want to overwrite your local version of " + self.model + "?"
				val = warningPopup(text)
				if (val == QMessageBox.No):
					makefiles = 0
			else:
				makefiles = 0
		
		# Create templates
		if (makefiles == 1):
			self.createModel()

		# Print out message to the GUI and open editor
		self.templatesMessage()
		self.callEditor()


	### Configure Button main function
	def ConfigureSST(self):
		if not self.getModel(): return
		
		# make clean and make all install
		if self.clean.isChecked():
			LinuxCmd = str('make clean -C ' + self.model).split()
			for line in run_command(LinuxCmd):
				self.write_info(line)
		
		LinuxCmd = str('make all -C ' + self.model).split()
		for line in run_command(LinuxCmd):
			self.write_info(line)
		
		text = '****************************************************************************\n'
		text += 'SST has been configured to run your model you may now proceed to the next\n'
		text += 'step Run SST\n'
		text += '****************************************************************************\n\n'
		self.write_info(text)
		
		# Run the model if autorun is checked
		if self.autoRun.isChecked():
			self.Run()


	### Run SST Button main function
	def Run(self):
		if not self.getModel(): return
		if not self.getTemplate(): return
		
		regex=re.compile(".*(tests/).*")
		testfiles=[m.group(0) for item in self.dest for m in [regex.search(item)] if m]
		
		text = '****************************************************************************\n'
		self.write_info(text)
		LinuxCmd = str('sst ' + self.model + '/' + testfiles[0]).split()
		for line in run_command(LinuxCmd):
			self.write_info(line)
		text = '****************************************************************************\n\n'
		self.write_info(text)


	### Application helper functions
	# Gets the model name from the GUI
	def getModel(self):
		self.model = self.modelName.text()
		if (self.model == ''):
			self.write_info('***PLEASE ENTER A MODEL NAME***\n')
			return False
		return True
	
	# Gets the template information
	def getTemplate(self):
		self.templatePath = str(self.templateType.text())
		self.template = os.path.basename(self.templatePath)
		if (self.template == ''):
			self.write_info('***PLEASE SELECT A TEMPLATE***\n')
			return False
		if not os.path.isfile(self.templatePath + '/template'):
			self.write_info('***TEMPLATE PATH IS INCORRECT OR TEMPLATE IS SETUP WRONG***\n')
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
		os.system(str('mkdir ' + self.model))
		os.system(str('mkdir ' + self.model + '/tests'))
		for s, d in zip(self.source, self.dest):
			os.system(str('cp ' + self.templatePath + '/' + s + ' ' + self.model + '/' + d))
			os.system(str('sed -i \'s/<model>/' + self.model + '/g\' ' + self.model + '/' + d))
			os.system(str('sed -i \'s/<sourceFiles>/' + ' '.join(self.sourceFiles) + '/g\' ' + self.model + '/' + d))
	
	# Write to information screen
	def write_info(self, text):
		self.info.moveCursor(QTextCursor.End)
		self.info.insertPlainText(text)
		self.info.moveCursor(QTextCursor.End)
	
	# Open template files in editor
	def callEditor(self):
		line = 'gedit '
		for item in self.dest:
			line += self.model + '/' + item + ' '
		line += '&'
		os.system(str(line))
	
	# Information for template generation
	def templatesMessage(self):
		text = '****************************************************************************\n'
		text += 'The following Templates should be displayed in the pop-up editor\n'
		for item in self.dest:
			text += '\t\t- ' + item + '\n'
		text += 'Please review/edit your files to create your model. You can make changes in\n'
		text += 'the pop-up editor, save your file then close the editor or you can close the pop-up\n'
		text += 'editor and the GUI, then proceed to editing the files in the editor of your choice\n'
		text += 'they reside in your working directory under ' + self.model + '/. The test scipt is in the\n'
		text += 'tests directory. After your are done you can proceed to the next step "Configure".\n'
		text += '****************************************************************************\n\n'
		self.write_info(text)
	
	# Help Menu
	def help(self):
		with open('README', 'r') as fp:
			text = fp.read()
		self.write_info(text)

##### Main Application Class End 

###	Main Function
if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	window = MyApp()
	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('plastique'))
	window.show()
	sys.exit(app.exec_())

