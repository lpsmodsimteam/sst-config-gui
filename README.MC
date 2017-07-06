This is the SST Model Creation Tool is will assist in developing
simple models for the SST Simulation Framework. This tool assumes
that SST 7.1 or greater has been installed and is running on
your system. The tool will also read your EDITOR environment
variable and use your preferred editor if set. If the EDITOR
environment variable is not set gedit is used by default.

The tool is setup to step you through the model development
process. Information about each step will be displayed in the 
information screen. Additionally tool tips are available if
you mouse over each button. Below is a brief description of 
each button and box on the tool:

Enter Model Name --> text box - Simply enter the name of your
  model, this name will be used as the base name for all of
  your files and your model's directory. If you do not enter
  a name the GUI will not continue until a name is entered.

Browse Templates button & text box - You can manually type in
  the path to a template of your choosing or you can use the
  button to open a file browser where you can select the folder
  that contains the template you wish to use. A template must be
  selected in order to generate/open templates and to run sst.

Generate/Open Templates button - This button will first create a 
  directory in your working directory with your model name, 
  inside this directory you will find your <model>.cc, <model>.h,
  Makefile, and tests/<model>.py templates. The templates will also
  appear in an editor of your choice, so you can complete the
  development of your model. Create your model by editing the
  templates, save and close the editor. The templates do generate a
  very simple model that can be compiled and run by the tool without
  any editing if you just want to try the tool out to see how it 
  works before creating your own. If model already exists in your 
  working directory with the same name and the Overwrite Existing
  Model check box is unchecked, the popup editor will open the 
  existing model this will allow you use the GUI to complete your
  model if it is not complete or correct errors found during compilation.

Configure button - This button will run "make all" which builds the
  sst library for your model and then links it into sst.

Overwrite Existing Model check box - Generate Templates will check
  to see if a model is already present with the current name in your
  working directory. If this box is checked the old model will
  be overwritten with the new one you created.

Make Clean check box - If you select this check box Configure will
  run a "make clean" before running "make all"

Run SST button - This button will run the tests/<model>.py script
  (basically running your model in SST) the results will
  be displayed in the information window.

Run After Build check box - If you select this check box the tool
  will proceed directly to Run SST after Configure. It is suggested
  that this box remain unchecked until you at least get your model
  to compile.
