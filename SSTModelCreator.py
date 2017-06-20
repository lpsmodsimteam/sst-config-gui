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

# Write to information screen
def write_info(info, text):
    info.moveCursor(QTextCursor.End)
    info.insertPlainText(text)

# Open template files in editor
def callEditor(model):
    line = 'gedit ' + model + '/' + model + '.cc ' 
    line += model + '/' + model + '.h '
    line += model + '/tests/' + model + '.py '
    line += model + '/Makefile '
    os.system(str(line))

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

# Information for template generation
def templatesMessage(info, model):
    text = '****************************************************************************\n'
    text += 'The following Templates should be displayed in the pop-up editor\n'
    text += '\t\t- ' + model + '.cc\n'
    text += '\t\t- ' + model + '.h\n'
    text += '\t\t- ' + model + '.py\n'
    text += '\t\t- Makefile\n'
    text += 'Please review/edit your files to create your model. You can make changes in\n'
    text += 'the pop-up editor, save your file then close the editor or you can close the pop-up\n'
    text += 'editor and the GUI, then proceed to editing the files in the editor of your choice\n'
    text += 'they reside in your working directory under ' + model + '/. The test scipt is in the\n'
    text += 'tests directory. After your are done you can proceed to the next step "Configure".\n'
    text += '****************************************************************************\n\n'
    write_info(info, text)

##### Main Application Class
class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    # Initialization Function
    def __init__(self):
    	QtGui.QMainWindow.__init__(self)
       	Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('sst-logo-small.png'))
        self.templates.clicked.connect(self.MakeTemplates)
        self.Configure.clicked.connect(self.ConfigureSST)
        self.RunSST.clicked.connect(self.Run)
        self.actionOpen_Help.triggered.connect(self.help)
       
    
    ### Generate Templates Button main function
    def MakeTemplates(self):
        model = self.modelName.text()
        if (model == ''):
            write_info(self.info, '***PLEASE ENTER A MODEL NAME***\n')  
            return

        # Do some checking see if you already have a model in your working directory
        # with the same name or if there is one in the element directory
        workingModels = os.listdir('.')
        makefiles = 1

        # Check local models
        if (workingModels.count(model) != 0):
            if self.overwrite.isChecked():
                text = "Do you really want to overwrite your local version of " + model + "?"
                val = warningPopup(text)
                if (val == QMessageBox.No):
                    makefiles = 0
            else:
                makefiles = 0
        
        # Create templates
        if (makefiles == 1):
            createSimpleModel(model)

        # Print out message to the GUI and open editor
        templatesMessage(self.info, model)
        callEditor(model)    


    ### Configure Button main function
    def ConfigureSST(self):
        model = self.modelName.text()
        if (model == ''):
            write_info(self.info, '***PLEASE ENTER A MODEL NAME***\n') 
            return
        
        os.chdir(model)
        # make clean and make all install
        if self.clean.isChecked():
            LinuxCmd = str('make clean').split()
            for line in run_command(LinuxCmd):
                write_info(self.info, line)
        
        LinuxCmd = str('make all').split()
        for line in run_command(LinuxCmd):
            write_info(self.info, line)
        
        text = '****************************************************************************\n'
        text += 'SST has been configured to run your model you may now proceed to the next\n'
        text += 'step Run SST\n'
        text += '****************************************************************************\n\n'
        write_info(self.info, text)
        
        os.chdir('..')
        # Run the model if autorun is checked
        if self.autoRun.isChecked():
            self.Run()


    ### Run SST Button main function
    def Run(self):
        
        model = self.modelName.text()
        if (model == ''):
            written = write_info(self.info, '***PLEASE ENTER A MODEL NAME***\n')  
            return
        
        os.chdir(model + '/tests')
        text = '****************************************************************************\n'
        write_info(self.info, text)
        LinuxCmd = str('sst ' + model + '.py').split()
        for line in run_command(LinuxCmd):
            write_info(self.info, line)
        text = '****************************************************************************\n\n'
        write_info(self.info, text)
        os.chdir('../..')


    # Help Menu
    def help(self):
        with open('README', 'r') as fp:
            text = fp.read()
        write_info(self.info, text)

##### Main Application Class End 

### Move and update the template files to create a new model
def createSimpleModel(model):
    os.system(str('mkdir ' + model))
    os.system(str('mkdir ' + model + '/tests'))
    
    os.system(str('cp templates/Makefile ' + model + '/.'))
    os.system(str('cp templates/simpleModel.cc ' + model + '/' + model + '.cc'))
    os.system(str('cp templates/simpleModel.h '  + model + '/' + model + '.h'))
    os.system(str('cp templates/simpleModel.py ' + model + '/tests/' + model + '.py'))
    
    os.system(str('sed -i \'s/<model#1>/' + model + '/g\' ' + model + '/Makefile'))
    os.system(str('sed -i \'s/<model#1>/' + model + '/g\' ' + model + '/' + model + '.cc'))
    os.system(str('sed -i \'s/<model#1>/' + model + '/g\' ' + model + '/' + model + '.h'))
    os.system(str('sed -i \'s/<model#1>/' + model + '/g\' ' + model + '/tests/' + model + '.py'))

###	Main Function
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('plastique'))
    window.show()
    sys.exit(app.exec_())

