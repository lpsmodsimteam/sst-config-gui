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
    info.moveCursor(QTextCursor.End)
    app.processEvents()

# Open template files in editor
def CallEditor(model):
    line = 'gedit ' + model + '/' + model + '.cc ' 
    line += model + '/' + model + '.h '
    line += model + '/tests/' + 'test_' + model + '.py '
    line += model + '/Makefile &'
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
    text += '\t\t- test_' + model + '.py\n'
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
                    LinuxCmd = 'rm -r ' + model
                    os.system(str(LinuxCmd))
            else:
                makefiles = 0
        
        # Create templates
        if (makefiles == 1):
            CreateFiles(model)

        # Print out message to the GUI and open editor
        templatesMessage(self.info, model)
        CallEditor(model)    


    ### Configure Button main function
    def ConfigureSST(self):
        model = self.modelName.text()
        if (model == ''):
            write_info(self.info, '***PLEASE ENTER A MODEL NAME***\n') 
            return
        
        # make clean and make all install
        if self.clean.isChecked():
            LinuxCmd = str('make clean -C ' + model).split()
            for line in run_command(LinuxCmd):
                write_info(self.info, line)

        LinuxCmd = str('make all -C' + model).split()
        for line in run_command(LinuxCmd):
            write_info(self.info, line)
        
        text = '****************************************************************************\n'
        text += 'If your compile completed successfully SST has been configured to run your\n'
        text += 'model you may now proceed to the next step Run SST\n'
        text += '****************************************************************************\n\n'
        write_info(self.info, text)
        
        # Run the model if autorun is checked
        if self.autoRun.isChecked():
            self.Run()


    ### Run SST Button main function
    def Run(self):
        
        model = self.modelName.text()
        if (model == ''):
            written = write_info(self.info, '***PLEASE ENTER A MODEL NAME***\n')  
            return
        LinuxCmd = str('sst ' + model + '/tests/test_' + model + '.py').split()
        text = '****************************************************************************\n'
        write_info(self.info, text)
        for line in run_command(LinuxCmd):
            write_info(self.info, line)
        text = '****************************************************************************\n\n'
        write_info(self.info, text)


    # Help Menu
    def help(self):
        with open('README', 'r') as fp:
            text = fp.read()
        write_info(self.info, text)

##### Main Application Class End 

### Template Creation SubFunctions
# Create the template files
def CreateFiles(model):
    line = 'mkdir -p ' + model + '/tests'
    os.system(str(line))
    testScript(model)
    line = 'mv test_' + model + '.py ' + model + '/tests/.'
    os.system(str(line))
    hFile(model)
    line = 'mv ' + model + '.h ' + model +'/.'
    os.system(str(line))
    ccFile(model)
    line = 'mv ' + model + '.cc ' + model +'/.'
    os.system(str(line))
    MakefileAM(model)
    line = 'mv Makefile ' + model +'/.'
    os.system(str(line))
    
# Writing information to test_<model>.py file
def testScript(model):
    filename = 'test_' + model + '.py'
    fp = open(filename, 'w+')
    fp.write('# Automatically generated SST Python input\n')
    fp.write('# Please edit for particular model specifics\n\n')
    fp.write('import sst\n\n')
    fp.write('# Define SST core options\n\n')
    fp.write('obj = sst.Component("' + model + '","' + model + '.' + model + '")\n')
    fp.write('obj.addParams({\n')
    fp.write('    "printFrequency" : "5",\n')
    fp.write('    "repeats" : "15"\n')
    fp.write('    })\n')
    fp.write('# End of generated output')
    fp.close()

# Writing information to <model>.h file
def hFile(model):
    filename = model + '.h'
    fp = open(filename, 'w+')
    fp.write('// This file is an automatic generated template of an sst model ".h" file\n')
    fp.write('// Please edit it to fit your specific model.\n\n')
    modelVar1 = str(model)
    modelVar = modelVar1.upper()
    line = '#ifndef _' + modelVar + '_H\n'
    fp.write(line)
    line = '#define _' + modelVar + '_H\n\n'
    fp.write(line)
    fp.write('#include <sst/core/component.h>\n')
    fp.write('#include <sst/core/elementinfo.h>\n\n')
    line = 'class ' + model + ' : public SST::Component {\n'
    fp.write(line)
    fp.write('public:\n')
    line = '\t' + model + '(SST::ComponentId_t id, SST::Params& params);\n'
    fp.write(line)
    fp.write('\t~' + model + '();\n\n')
    fp.write('\tvoid setup();\n')
    fp.write('\tvoid finish();\n\n')
    fp.write('\tbool clockTick( SST::Cycle_t currentCycle );\n\n')
    fp.write('\tSST_ELI_REGISTER_COMPONENT(\n')
    fp.write('\t\t' + model + ',\n')
    fp.write('\t\t"' + model + '",\n')
    fp.write('\t\t"' + model + '",\n')
    fp.write('\t\tSST_ELI_ELEMENT_VERSION( 1, 0, 0 ),\n')
    fp.write('\t\t"Demonstration of an External Element for SST",\n')
    fp.write('\t\tCOMPONENT_CATEGORY_PROCESSOR\n')
    fp.write('\t)\n\n')
    fp.write('\tSST_ELI_DOCUMENT_PARAMS(\n')
    fp.write('\t\t{ "printFrequency", "How frequently to print a message from the component", "5" },\n')
    fp.write('\t\t{ "repeats", "Number of repetitions to make", "10" }\n')
    fp.write('\t)\n\n')
    fp.write('private:\n')
    fp.write('\tSST::Output output;\n')
    fp.write('\tSST::Cycle_t printFreq;\n')
    fp.write('\tSST::Cycle_t maxRepeats;\n')
    fp.write('\tSST::Cycle_t repeats;\n')
    fp.write('};\n')    
    line = '#endif /* _' + modelVar + '_H */'
    fp.write(line)
    fp.close()

# Writing information to <model>.cc file
def ccFile(model):
    filename = model + '.cc'
    fp = open(filename, 'w+')
    fp.write('// This file is an automatic generated template of an sst model ".cc" file\n')
    fp.write('// Please edit it to fit your specific model.\n\n')
    fp.write('#include <sst/core/sst_config.h>\n')
    line = '#include "' + model + '.h"\n\n'
    fp.write(line)
    line = model + '::' + model + '( SST::ComponentId_t id, SST::Params& params) :\n'
    fp.write(line)
    fp.write('\tSST::Component(id), repeats(0) {\n\n')
    fp.write('\toutput.init("' + model + '-" + getName() + "-> ", 1, 0, SST::Output::STDOUT);\n\n')
    fp.write('\tprintFreq = params.find<SST::Cycle_t>("printFrequency", 5);\n')
    fp.write('\tmaxRepeats = params.find<SST::Cycle_t>("repeats", 10);\n\n')
    fp.write('\tif( ! (printFreq > 0) ) {\n')
    fp.write('\toutput.fatal(CALL_INFO,  -1, "Error: printFrequency must be greater than zero.\\n");\n')
    fp.write('\t}\n')
    fp.write('\toutput.verbose(CALL_INFO, 1, 0, "Config: maxRepeats=%" PRIu64 ",printFreq=%" PRIu64 "\\n",\n')
    fp.write('\t\tstatic_cast<uint64_t>(maxRepeats), static_cast<uint64_t>(printFreq));\n\n')
    fp.write('\t// Just register a plain clock for this simple example\n\n')
    fp.write('\tregisterClock("100MHz", new SST::Clock::Handler<' + model + '>(this, &' + model + '::clockTick));\n\n')
    fp.write('\t// Tell SST to wait until we authorize it to exit\n')
    fp.write('\tregisterAsPrimaryComponent();\n')
    fp.write('\tprimaryComponentDoNotEndSim();\n')
    fp.write('}\n\n')
    fp.write(model + '::~' + model + '() {\n')
    fp.write('}\n\n')
    fp.write('void ' + model + '::setup() {\n')
    fp.write('\toutput.verbose(CALL_INFO, 1, 0, "Component is being setup.\\n");\n')
    fp.write('}\n\n')
    fp.write('void ' + model + '::finish() {\n')
    fp.write('\toutput.verbose(CALL_INFO, 1, 0, "Component is being finished.\\n");\n')
    fp.write('}\n\n')
    fp.write('bool ' + model + '::clockTick( SST::Cycle_t currentCycle ) {\n')
    fp.write('\tif( currentCycle % printFreq == 0 ) {\n')
    fp.write('\t\toutput.verbose(CALL_INFO, 1, 0, "Hello World!\\n");\n')
    fp.write('\t}\n\n')
    fp.write('\trepeats++;\n\n')
    fp.write('\tif( repeats == maxRepeats ) {\n')
    fp.write('\t\tprimaryComponentOKToEndSim();\n')
    fp.write('\t\treturn true;\n')
    fp.write('\t} else {\n')
    fp.write('\t\treturn false;\n')
    fp.write('\t}\n')
    fp.write('}')    
    fp.close()

# Writing information to Makefile.am file
def MakefileAM(model):
    filename = 'Makefile'
    fp = open(filename, 'w+')
    fp.write('# -*- Makefile -*-\n\n')
    fp.write('CXX=$(shell sst-config --CXX)\n')
    fp.write('CXXFLAGS=$(shell sst-config --ELEMENT_CXXFLAGS)\n')
    fp.write('LDFLAGS=$(shell sst-config --ELEMENT_LDFLAGS)\n\n')
    fp.write('all: lib' + model + '.so install\n\n')
    fp.write('lib' + model + '.so: ' + model + '.cc\n')
    fp.write('\t$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $<\n\n')
    fp.write('install:\n')
    fp.write('\tsst-register ' + model + ' ' + model + 'LIBDIR=$(CURDIR)\n\n')
    fp.write('clean:\n')
    fp.write('\trm -f *.o lib' + model + '.so\n')
    fp.close()

###	Main Function
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('plastique'))
    window.show()
    sys.exit(app.exec_())

