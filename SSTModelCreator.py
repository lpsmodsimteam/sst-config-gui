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

# Creates elements library directory from SST_ELEMENTS_HOME enviroment variable
def get_libDir():
    element_home = os.environ['SST_ELEMENTS_HOME']
    array = element_home.split('local/sstelements-')
    prefix = array[0]
    version = array[1]
    return prefix + 'scratch/src/sst-elements-library-' + version

# Open template files in editor
def CallEditor(model):
    line = 'gedit ' + model + '/' + model + '.cc ' 
    line += model + '/' + model + '.h '
    line += model + '/tests/' + 'test_' + model + '.py '
    line += model + '/Makefile.am '
    line += model + '/' + model + 'Wrapper.cc &'
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
    text += '\t\t- Makefile.am\n'
    text += '\t\t- ' + model + 'Wrapper.cc\n'
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
        FulllibDir = get_libDir() + '/src/sst/elements/'

        # Do some checking see if you already have a model in your working directory
        # with the same name or if there is one in the element directory
        currentModels = os.listdir(FulllibDir)
        workingModels = os.listdir('.')
        makefiles = 1
        
        # Check SST Models
        if (self.checkSSTModels( model, currentModels) == 0):
            return
        
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
        origDir = os.getcwd()
        libDir = get_libDir()
        FulllibDir = libDir + '/src/sst/elements/'
        FullcoreDir = os.environ['SST_CORE_HOME']
        element_home = os.environ['SST_ELEMENTS_HOME']

        # Do some error checking see if there is already a model by the same name in the 
        # elements directory.
        currentModels = os.listdir(FulllibDir)
        if (self.checkSSTModels(model, currentModels) == 0):
            return
        
        # Copy new model directory to the SST elements directory
        LinuxCmd = 'cp -r ' + model + '/ ' + FulllibDir + '.'
        os.system(str(LinuxCmd))
        
        # Run autogen.sh and configure
        os.chdir(libDir)
        os.system('./autogen.sh')
        config = './configure --prefix=' + element_home + ' --with-sst-core=' + FullcoreDir
        os.system(config)

        # make clean and make all install
        if self.clean.isChecked():
            os.system('make clean')
        os.system('make all install')
        text = '****************************************************************************\n'
        text += 'SST has been configured to run your model you may now proceed to the next\n'
        text += 'step Run SST\n'
        text += '****************************************************************************\n\n'
        write_info(self.info, text)
        
        # Go back to original directory
        os.chdir(origDir)
        # Run the model if autorun is checked
        if self.autoRun.isChecked():
            self.Run()


    ### Run SST Button main function
    def Run(self):
        
        model = self.modelName.text()
        if (model == ''):
            written = write_info(self.info, '***PLEASE ENTER A MODEL NAME***\n')  
            return
        origDir = os.getcwd()
        TestsDir = get_libDir() + '/src/sst/elements/' + model + '/tests/'
        LinuxCmd = str('sst test_' + model + '.py').split()
        os.chdir(TestsDir)
        text = '****************************************************************************\n'
        write_info(self.info, text)
        for line in run_command(LinuxCmd):
            write_info(self.info, line)
        text = '****************************************************************************\n\n'
        write_info(self.info, text)
        os.chdir(origDir)


    # Help Menu
    def help(self):
        with open('README', 'r') as fp:
            text = fp.read()
        write_info(self.info, text)

    # Check SST Models to see if the model already exists
    def checkSSTModels(self, model, currentModels):
        if (currentModels.count(model) != 0):
            if self.overwrite.isChecked():
                text = 'THERE IS ALREADY AN SST MODEL NAMED '
                text += model + '.\n'
                text += 'IF THIS IS YOUR MODEL YOU MAY OVERWRITE IT, OTHERWISE SELECT NO\n'
                text += 'Do you really want to overwrite the SST model?'
                val = warningPopup(text)
                if (val == QMessageBox.No):
                    return 0
            else:
                write_info(self.info, '***THERE IS ALREADY AN SST MODEL NAMED ' + model + '***\n\n')
                return 0
        return 1

##### Main Application Class End 

### Template Creation SubFunctions
# Create the template files
def CreateFiles(model):
    line = 'mkdir ' + model
    os.system(str(line))
    line = 'mkdir ' + model + '/tests'
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
    line = 'mv Makefile.am ' + model +'/.'
    os.system(str(line))
    Wrapper(model)
    line = 'mv ' + model + 'Wrapper.cc ' + model +'/.'
    os.system(str(line))

# Writing information to test_<model>.py file
def testScript(model):
    filename = 'test_' + model + '.py'
    fp = open(filename, 'w+')
    fp.write('# Automatically generated SST Python input\n')
    fp.write('# Please edit for particular model specifics\n\n')
    fp.write('import sst\n\n')
    fp.write('# Define SST core options\n\n')
    fp.write('sst.setProgramOption("timebase", "1 ps")\n')
    fp.write('sst.setProgramOption("stopAtCycle", "10000s")\n\n')
    fp.write('# Define the simulation components\n\n')
    line = 'comp_clocker0 = sst.Component("clocker0","' + model + '.' + model + '")'
    fp.write(line)
    fp.write('\n')
    fp.write('comp_clocker0.addParams({\n')
    fp.write('    "clockcount" : """100000000""",\n')
    fp.write('    "clock" : """1MHz""",\n\n')
    fp.write('# Add in any specific clock parameters here\n\n')
    fp.write('})\n\n')
    fp.write('# Define the simulation links\n')
    fp.write('# End of generated output')
    fp.close()

# Writing information to <model>.h file
def hFile(model):
    filename = model + '.h'
    fp = open(filename, 'w+')
    fp.write('// This file is an automatic generated template of an sst model ".h" file\n')
    fp.write('// This cannot be used in its present form.\n')
    fp.write('// Please edit it to fit your specific model.\n\n')
    modelVar1 = str(model)
    modelVar = modelVar1.upper()
    line = '#ifndef _' + modelVar + '_H\n'
    fp.write(line)
    line = '#define _' + modelVar + '_H\n\n'
    fp.write(line)
    fp.write('#include <sst/core/component.h>\n')
    fp.write('#include <sst/core/rng/marsaglia.h>\n\n')
    fp.write('namespace SST {\n')
    line = 'namespace ' + model + '_Class {'
    fp.write(line)
    line = 'class ' + model + ' : public SST::Component\n'
    fp.write(line)
    fp.write('{\n')
    fp.write('public:\n')
    line = '\t' + model + '(SST::ComponentId_t id, SST::Params& params);\n'
    fp.write(line)
    fp.write('\t// Constructor\n\n')
    fp.write('\tvoid setup() {}\n')
    fp.write('\tvoid finish() {}\n\n')
    fp.write('private:\n')
    fp.write('\tvirtual bool tick(SST::Cycle_t);\n\n')
    fp.write('// Add in any specific functions you need for your model\n\n')
    fp.write('// Simulation Variables\n\n')
    fp.write('\tSST::RNG::MarsagliaRNG* m_rng;\n')
    fp.write('\tint64_t m_SimulationTimeLength;\n\n')
    fp.write('\tstd::string clock_frequency_str;\n')
    fp.write('\tint clock_count;\n\n')
    fp.write('// Add in any specif variables you need for your model\n')
    fp.write('\tint m_tick;')
    fp.write('};\n\n')
    line = '} // namespace ' + model + '\n'
    fp.write(line)
    fp.write('} // namespace SST\n\n')
    line = '#endif /* _' + modelVar + '_H */'
    fp.write(line)
    fp.close()

# Writing information to <model>.cc file
def ccFile(model):
    filename = model + '.cc'
    fp = open(filename, 'w+')
    fp.write('// This file is an automatic generated template of an sst model ".cc" file\n')
    fp.write('// This cannot be used in its present form.\n')
    fp.write('// Please edit it to fit your specific model.\n\n')
    fp.write('#include "sst_config.h"\n')
    line = '#include "' + model + '.h"\n\n'
    fp.write(line)
    fp.write('namespace SST {\n')
    line = 'namespace ' + model + '_Class {'
    fp.write(line)
    fp.write('// Constructor \n\n')
    line = model + '::' + model + '(ComponentId_t id, Params& params) :\n'
    fp.write(line)
    fp.write('Component(id)\n')
    fp.write('{\n\n')
    fp.write('// See if any optional simulation parameters were set in the\n')
    fp.write('// executing Python script\n\n')
    fp.write('\tclock_frequency_str = params.find<std::string>("clock", "1MHz");\n')
    fp.write('\tclock_count = params.find<int64_t>("clockcount", 1000);\n')
    fp.write('\tm_SimulationTimeLength = params.find<int64_t>("simulationtime", 5);\n')
    fp.write('\tm_tick = 0;\n\n')
    fp.write('// If you added other parameters in the Python script list here\n\n')
    fp.write('\tstd::cout << std::endl << std::endl;\n\n')
    fp.write('// You can put any introductory greating here\n\n')
    fp.write('// Tell the simulator not to end without us\n\n')
    fp.write('// Register as Primary Component\n\n')
    fp.write('\tregisterAsPrimaryComponent();\n\n')
    fp.write('// Put this model in charge of the simulation execution\n\n')
    fp.write('\tprimaryComponentDoNotEndSim();\n\n')
    fp.write('// Initialize variables for simulation model\n\n')
    fp.write('// Register Main Clock\n\n')
    fp.write('// This will automatically be called by the SST framework\n\n')
    line = '\tregisterClock(clock_frequency_str, new Clock::Handler<' + model + '>(this, &' + model + '::tick));\n\n'
    fp.write(line)
    fp.write('// Set up any other clocks and build any one-shots if you are using them\n\n')
    fp.write('} // Construction - End\n\n')
    fp.write('// Create the main part of the model below \n\n')
    line = 'bool ' + model + '::tick( Cycle_t )\n'
    fp.write(line)
    fp.write('{\n\n')
    fp.write('// The body of your model\n')
    fp.write('\tif(m_tick >= m_SimulationTimeLength) {\n')
    fp.write('\t\treturn(true);\n')
    fp.write('\t}else{\n')
    fp.write('\t\tprintf("Hello\\n");\n')
    fp.write('\t\tm_tick++;\n')
    fp.write('\t\treturn(false);\n\t}\n')
    fp.write('} \n\n')
    fp.write('// Add in any other functions, one-shots or clock control specific to your model ..\n\n')
    line = '} // namespace ' + model + '\n'
    fp.write(line)
    fp.write('} // namespace SST')
    fp.close()

# Writing information to Makefile.am file
def MakefileAM(model):
    filename = 'Makefile.am'
    fp = open(filename, 'w+')
    text = '# -*- Makefile -*-\n'
    text += '# \n'
    text += '# \n'
    text += '\n'
    text += 'AM_CPPFLAGS = \\\n'
    text += '\t$(BOOST_CPPFLAGS)\\\n'
    text += '\t$(MPI_CPPFLAGS)\n\n'
    text += 'compdir = $(pkglibdir)\n'
    text += 'comp_LTLIBRARIES = lib' + model + '.la\n'
    text += 'lib' + model + '_la_SOURCES =  \\\n'
    text += '\t' + model + 'Wrapper.cc \\\n'
    text += '\t' + model + '.h \\\n'
    text += '\t' + model + '.cc\n\n\n'
    text += 'EXTRA_DIST =\\\n'
    text += '\tREADME \\\n'
    text += '\ttests/test_' + model + '.py\n\n'
    text += 'lib' + model + '_la_LDFLAGS = -module -avoid-version\n\n'
    text += '########################################################################## \n'
    text += '########################################################################## \n'
    text += '########################################################################## \n'
    fp.write(text)
    fp.close()

# Writing information to <model>Wrapper.cc file
def Wrapper(model):
    filename = model + 'Wrapper.cc'
    fp = open(filename, 'w+')
    text = '// This is the ' + model + 'Wrapper.cc file for Model ' + model + '.\n'
    text +=  '// Update according for your particulare simulation model.\n\n\n'
    text +=  '// Make sure any modifications to parameters are also reflected in\n'
    text +=  '// the Python script\n\n\n'
    text +=  '#include "sst_config.h"\n'
    text +=  '#include "sst/core/element.h"\n'
    text +=  '#include "' + model + '.h"\n\n'
    text +=  'using namespace SST;\n'
    text +=  'using namespace SST::' + model + '_Class;\n\n'
    text +=  'static Component* create_' + model + '(SST::ComponentId_t id, SST::Params& params)\n'
    text +=  '{\n'
    text +=  '\treturn new ' + model + '(id, params);\n'
    text +=  '}\n\n'
    text +=  'static const ElementInfoParam ' + model + '_params[] = {\n'
    text +=  '\t{ "clock", "Clock frequency", "1GHz" },\n'
    text +=  '\t{ "clockcount", "Number of clock ticks to execute", "100000"},\n'
    text +=  '\t{ NULL, NULL, NULL }\n'
    text +=  '};\n\n'
    text +=  'static const ElementInfoComponent ' + model + 'Components[] = {\n'
    text +=  '\t{ "' + model + '",\t\t\t\t// Name\n'
    text +=  '\t "' + model + ' Simulator",\t\t\t\t// Description\n'	
    text +=  '\t NULL,\t\t\t\t\t// PrintHelp\n'
    text +=  '\t create_' + model + ',\t\t\t\t// Allocator\n'
    text +=  '\t ' + model +'_params,\t\t\t\t// Parameters\n'
    text +=  '\t NULL,\t\t\t\t\t// Ports\n'
    text +=  '\t COMPONENT_CATEGORY_UNCATEGORIZED,\t\t\t// Category\n'
    text +=  '\t NULL\t\t\t\t\t// Statistics\n'
    text +=  '\t},\n'
    text +=  '\t{ NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL}\n'
    text +=  '};\n\n'
    text +=  'extern \"C\" {\n'
    text +=  '\tElementLibraryInfo ' + model + '_eli = {\n'
    text +=  '\t\t\"' + model + '\",\t\t\t\t\t// Name\n'
    text +=  '\t\t\"A Simple Example Element With Demo Components\",\t// Description\n'
    text +=  '\t\t' + model + 'Components,\t\t\t\t// Components\n'
    text +=  '\t\tNULL,\t\t\t\t\t\t// Events\n'
    text +=  '\t\tNULL,\t\t\t\t\t\t// Introspectors\n'
    text +=  '\t\tNULL,\t\t\t\t\t\t// Modules\n'
    text +=  '\t\tNULL,\t\t\t\t\t\t// Subcomponents\n'
    text +=  '\t\tNULL,\t\t\t\t\t\t// Partitioners\n'
    text +=  '\t\tNULL,\t\t\t\t\t\t// Python Module Generator\n'
    text +=  '\t\tNULL\t\t\t\t\t\t// Generators\n'
    text +=  '\t};\n'
    text +=  '}'
    fp.write(text)
    fp.close()


###	Main Function
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('plastique'))
    window.show()
    sys.exit(app.exec_())

