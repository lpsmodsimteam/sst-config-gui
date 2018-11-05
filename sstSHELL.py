#!/usr/bin/env python3

# This is a model development script to help you develop,
# integrate and run a new model in SST. There are functions
# to create, create subcomponents, connect, convert, and graph models

# WARNING: These functions have no error checking as they
# are meant to be called from other code which should
# already have done error checking

import os
import subprocess
import re
import fileinput
import xml.etree.ElementTree as ET
import argparse


# Move and update the template files to create a new model
def createModel(model, template, path):
	os.system('rm -rf ' + path + '/' + model)
	with open(template + '/template', 'r') as fp:
		structure = fp.read()
	source = structure.split()[0::2]
	destination = structure.split()[1::2]
	dest=[]
	for item in destination:
		dest.append(item.replace('<model>', str(model)))
	os.system('mkdir -p ' + path + '/' + model + '/tests')
	# Loop through sources and destinations at the same time
	for s, d in zip(source, dest):
		with open(template + '/' + s, 'r') as infile, open(path + '/' + model + '/' + d, 'w') as outfile:
			# Copy from source to destination while replacing <model> tags
			for line in infile:
				outfile.write(line.replace('<model>', str(model)))
	files = os.listdir(template)
	for file in files:
		if file != 'template' and file not in source:
			os.system('cp -r ' + template + '/' + file + ' ' + path + '/' + model + '/.')


# Connect various models together
def connectModels(model, componentList, path):
	components = componentList.rstrip(';').split(';')
	os.system('rm -rf ' + path + '/' + model)
	os.system('mkdir -p ' + path + '/' + model)
	elements = ET.fromstring(runCommand('sst-info -qnxo /dev/stdout'))
	with open(path + '/' + model + '/' + model + '.py', 'w') as fp:
		fp.write('import sst\n\n# TODO: Check the parameters for all components and connect the links at the bottom before running!!!\n\n')
		# Loop through all the components
		for i in range(len(components)):
			component = components[i]
			(element, comp, *sub) = component.split('.')
			if sub:
				sub = sub[0].split(',')
			# Write the Component Definition
			fp.write('obj' + str(i) + ' = sst.Component("' + comp + str(i) + '", "' + element + '.' + comp + '")\n')
			parameters = elements.find("*/Component[@Name='" + comp + "']").findall('Parameter')
			if parameters:
				fp.write('obj' + str(i) + '.addParams({\n')
				# Remove the DEPRECATED parameters
				params = []
				for param in parameters:
					if 'DEPRECATED' not in param.get('Description'):
						params.append(param)
				# Write out all of the available parameters with their defaults and description
				for k in range(len(params)):
					if k == len(params) - 1:
						fp.write('\t"' + params[k].get('Name') + '" : "' + params[k].get('Default') + '"}) # ' + params[k].get('Description') + '\n\n')
					else:
						fp.write('\t"' + params[k].get('Name') + '" : "' + params[k].get('Default') + '", # ' + params[k].get('Description') + '\n')
			else:
				fp.write('\n')
			# Create any subcomponents
			for j in range(len(sub)):
				s = sub[j]
				# Write the Subcomponent Definition
				slots = elements.find("*/Component[@Name='" + comp + "']").findall('SubComponentSlot')
				subcomp = elements.find("*/SubComponent[@Name='" + s + "']")
				for slot in slots:
					if slot.get('Interface') == subcomp.get('Interface'):
						fp.write('sub' + str(i) + str(j) + ' = obj' + str(i) + '.setSubComponent("' + slot.get('Name') + '", "' + element + '.' + s + '", ' + str(j) + ')\n')
				parameters = elements.find("*/SubComponent[@Name='" + s + "']").findall('Parameter')
				if parameters:
					fp.write('sub' + str(i) + str(j) + '.addParams({\n')
					# Remove the DEPRECATED parameters
					params = []
					for param in parameters:
						if 'DEPRECATED' not in param.get('Description'):
							params.append(param)
					# Write out all of the available parameters with their defaults and description
					for k in range(len(params)):
						if k == len(params) - 1:
							fp.write('\t"' + params[k].get('Name') + '" : "' + params[k].get('Default') + '"}) # ' + params[k].get('Description') + '\n\n')
						else:
							fp.write('\t"' + params[k].get('Name') + '" : "' + params[k].get('Default') + '", # ' + params[k].get('Description') + '\n')
				else:
					fp.write('\n')
			fp.write('\n')
		fp.write('\n###################################################################\n')
		fp.write('# TODO: Links have the first port connected but need to be manually\n')
		fp.write('# connected to a second port to work. Delays also should be edited\n\n')
		# After all components have been declared, write links
		for i in range(len(components)):
			component = components[i]
			(element, comp, *sub) = component.split('.')
			ports = elements.find("*/Component[@Name='" + comp + "']").findall('Port')
			if ports:
				fp.write('# ' + 'obj' + str(i) + ' Links\n')
			# Write out all of the available ports with their descriptions
			# These need to be modified by the user to actually connect components
			for k in range(len(ports)):
				fp.write('sst.Link("' + comp + str(i) + '_' + ports[k].get('Name') + '").connect( (obj' + str(i) + ', "' + ports[k].get('Name') + '", "1ps"), (OBJNAME, "PORTNAME", "DELAY") ) # ' + ports[k].get('Description') + '\n')
			if ports:
				fp.write('\n')
			# Write links for subcomponents
			if sub:
				sub = sub[0].split(',')
				for j in range(len(sub)):
					s = sub[j]
					ports = elements.find("*/SubComponent[@Name='" + s + "']").findall('Port')
					if ports:
						fp.write('# ' + 'sub' + str(i) + str(j) + ' Links\n')
					for k in range(len(ports)):
						fp.write('sst.Link("' + s + str(i) + str(j) + '_' + ports[k].get('Name') + '").connect( (sub' + str(i) + str(j) + ', "' + ports[k].get('Name') + '", "1ps"), (OBJNAME, "PORTNAME", "DELAY") ) # ' + ports[k].get('Description') + '\n')
					if ports:
						fp.write('\n')


# Create a subcomponent
def createSubcomponent(name, subcomp, header):
	found = False
	with open(str(header), 'r') as infile, open(os.path.dirname(header) + '/' + name + '.cc', 'w') as cFile, open(os.path.dirname(header) + '/' + name + '.h', 'w') as hFile:
		# create the beginning of the header file
		htxt = '#ifndef _' + name + '_H\n#define _' + name + '_H\n\n'
		htxt += '#include <sst/core/sst_config.h>\n#include <sst/core/elementinfo.h>\n'
		htxt += '#include <sst/core/component.h>\n#include <sst/core/subcomponent.h>\n'
		htxt += '#include <sst/core/link.h>\n#include "' + os.path.basename(header) + '"\n\n'
		htxt += '// TODO: Fill in the element library name where it says PUT ELEMENT LIBRARY HERE\n\n'
		htxt += 'class ' + name + ' : public ' + subcomp + ' {\n\npublic:\n'
		htxt += '\t' + name + '( SST::Component *owningComponent, SST::Params& params );\n'
		htxt += '\t~' + name + '();\n\n'
		# create the beginning of the cpp file
		ctxt = '#include "' + name + '.h"\n\n'
		ctxt += name + '::' + name + '(SST::Component *owningComponent, SST::Params &params) : '
		ctxt += subcomp + '(owningComponent) {\n'
		ctxt += '\toutput.init("' + name + '-" + getName() + "-> ", 1, 0, SST::Output::STDOUT);\n'
		ctxt += '\t// Get parameters\n\t//parameter = params.find<type>("param name", default);\n\n'
		ctxt += '\t// Setup statistics\n\t//statistic = registerStatistic<type>("stat name");\n\n'
		ctxt += '\t// Setup ports\n'
		ctxt += '\t/*port = configureLink("port name", new SST::Event::Handler<type>(this, &' + name + '::handleEvent));\n'
		ctxt += '\tif ( !port ) {\n\t\toutput.fatal(CALL_INFO, -1, "Failed to configure port \'port\'");\n\t}*/\n\n'
		ctxt += '}\n\n' + name + '::~' + name + '() {}\n\n'
		ctxt += '/*void ' + name + '::handleEvent(SST::Event *ev) {\n\t\n}*/\n\n'
		# grab the functions from the prototype in the header
		for line in infile:
			if found:
				if line.strip().startswith('}'):
					found = False
				elif line.strip().startswith('virtual'):
					while (not '=' in line) and (not '{' in line):
						htxt += line.replace('virtual ', '')
						ctxt += line.replace('virtual ', '').lstrip()
						line = next(infile)
					tmp = line.replace('virtual ', '')
					if '=' in line:
						htxt += str(tmp.split('=')[0].rstrip() + ';\n')
						ctxt += str(tmp.lstrip().split('=')[0].rstrip() + '{\n\t\n}\n\n')
					elif '{' in line:
						htxt += str(tmp.split('{')[0].rstrip() + ';\n')
						ctxt += str(tmp.lstrip().split('{')[0].rstrip() + '{\n\t\n}\n\n')
			elif 'SST::SubComponent' in line:
				if line.lstrip().split(':')[0].split(' ')[1] == subcomp:
					found = True
		# finish the header file
		htxt += '\n\t// Register the subcomponent\n\tSST_ELI_REGISTER_SUBCOMPONENT(\n'
		htxt += '\t\t' + name + ', // class\n'
		htxt += '\t\t"PUT ELEMENT LIBRARY HERE", // element library\n'
		htxt += '\t\t"' + name + '", // subcomponent\n'
		htxt += '\t\tSST_ELI_ELEMENT_VERSION( 1, 0, 0 ),\n'
		htxt += '\t\t"' + name + ' subcomponent description",\n'
		htxt += '\t\t"SST::PUT ELEMENT LIBRARY HERE::' + subcomp + '" // subcomponent slot\n\t)\n\n'
		htxt += '\t// Parameter name, description, default value\n'
		htxt += '\t/*SST_ELI_DOCUMENT_PARAMS(\n\t\t{ "", "", "" },\n\t)*/\n\n'
		htxt += '\t// Statistic name, description, unit, enable level\n'
		htxt += '\t/*SST_ELI_DOCUMENT_STATISTICS(\n\t\t{ "", "", "", 1 },\n\t)*/\n\n'
		htxt += '\t// Port name, description, event type\n'
		htxt += '\t/*SST_ELI_DOCUMENT_PORTS(\n\t\t{ "", "", {""} }\n\t)*/\n\n'
		htxt += 'private:\n\tSST::Output output;\n};\n\n#endif'
		# write both files
		hFile.write(str(htxt))
		cFile.write(str(ctxt))
		

# Parameter sweep expansion
def paramSweep(filename):
	List1 = []
	List2 = []
	List3 = []
	List4 = []
	List5 = []
	found = False
	full = False
	# Scan through the file first to find parameters that need swept
	with open(filename,'r') as infile:
		for line in infile:
			if not line.lstrip().startswith('#'): # Skip comments
				if '.addParams' in line:
					found = True
				if found:
					newline = line.strip().split(':')
					if len(newline) >= 2:
						value = newline[1].split('"')[1]
						# fill up lists starting with List1
						if not List1:
							current = List1
						elif not List2:
							current = List2
						elif not List3:
							current = List3
						elif not List4:
							current = List4
						elif not List5:
							current = List5
						else:
							full = True
						# pull out the start, end, and increment
						if ';' in value and not full:
							tmp = value.split(';')
							start = int(tmp[0].split('-')[0], 0)
							end = int(tmp[0].split('-')[1], 0)
							index = int(tmp[1].split(' ')[0], 0)
							for i in range(start, end+index, index):
								units = tmp[1].split(' ')
								if len(units) >= 2:
									current.append(str(i) + ' ' + units[1])
								else:
									current.append(str(i))
						elif ',' in value and not full:
							current.extend(value.split(','))
						elif full and (';' in value or ',' in value):
							return 'ERROR: Only five (5) parameters may be expanded at a time'
				if found and '})' in line:
					found = False
	found = False
	path = filename.split('.py')[0] + '_expanded'
	os.system('mkdir -p ' + path)
	# python doesn't support do while, so these loops are simply doing that
	i = 0
	while(1):
		j = 0
		while(1):
			k = 0
			while(1):
				l = 0
				while(1):
					m = 0
					while(1):
						count = 1
						# create the filename
						testfile = path + '/' + os.path.basename(filename).split('.')[0]
						testfile += '_' + str(i) if List1 else ''
						testfile += '_' + str(j) if List2 else ''
						testfile += '_' + str(k) if List3 else ''
						testfile += '_' + str(l) if List4 else ''
						testfile += '_' + str(m) if List5 else ''
						testfile += '.py'
						with open(filename,'r') as infile, open(testfile,'w') as fptest:		   
							for line in infile:
								if not line.lstrip().startswith('#'): # Skip comments
									if '.addParams' in line:
										found = True
									if found:
										newline = line.split(':')
										if len(newline) >= 2:
											tmp = newline[1].split('"')
											# for each file, put in the correct parameters
											if ';' in tmp[1] or ',' in tmp[1]:
												line = newline[0] + ': "'
												line += List1[i] if count == 1 else ''
												line += List2[j] if count == 2 else ''
												line += List3[k] if count == 3 else ''
												line += List4[l] if count == 4 else ''
												line += List5[m] if count == 5 else ''
												line += '"' + tmp[2]
												count = count + 1
									if found and '})' in line:
										found = False
								fptest.write(line)
						m = m + 1
						if m >= len(List5): break
					l = l + 1
					if l >= len(List4): break
				k = k + 1
				if k >= len(List3): break
			j = j + 1
			if j >= len(List2): break
		i = i + 1
		if i >= len(List1): break
	return path


# Graph a Model using the python test script
def graphModel(test):
	path = os.path.dirname(test) + '/graphs'
	name = os.path.basename(test).replace('.py','')
	os.makedirs(path, exist_ok=True)
	filename = path + '/' + name
	os.system('PYTHONPATH=$PYTHONPATH:' + path + ' sst --output-dot=' + filename + '.dot --run-mode=init ' + test)
	# Convert .dot file to a .svg file using multiple graphing tools
	convert = ['neato', 'twopi', 'circo', 'fdp', 'dot']
	files = ''
	for tool in convert:
		os.system(tool + ' -Tsvg ' + filename + '.dot -O')
		if not tool == 'dot':
			os.system('mv ' + filename + '.dot.svg ' + filename + '.' + tool + '.svg')
			os.system('mv ' + filename + '.dot.2.svg ' + filename + '.' + tool + '.2.svg')
		files += filename + '.' + tool + '.svg ' + filename + '.' + tool + '.2.svg '
	return str(filename + '.dot ' + files.rstrip())


# Convert a model into a template
def model2Template(model, template):
	path = './templates/' + template
	# Copy the model into the templates directory, clean the model
	os.system('rm -rf ' + path)
	os.system('cp -r ' + model + ' ' + path)
	os.system('make clean -C ' + path)
	# Move any test files into the main directory with and add test- prefix
	for item in os.listdir(path + '/tests/'):
		os.system('mv ' + path + '/tests/' + item + ' ' + path + '/test-' + item)
	os.system('rmdir ' + path + '/tests')
	modelName = os.path.basename(str(model.rstrip('/')))
	files = next(os.walk(path))[2]
	newFiles = []
	templateNames = []
	# For each file move the file to its new name and replace model with <model> tag
	for item in files:
		new = item.replace(modelName, str(template))
		newFiles.append(new)
		templateNames.append(item.replace(modelName, '<model>'))
		os.system('mv ' + path + '/' + item + ' ' + path + '/' + new)
	# Case insensitive replacing modelName with <model> tag
	pattern = re.compile(modelName, re.IGNORECASE)
	for new in newFiles:
		for line in fileinput.input(path + '/' + new, inplace=True):
			print(pattern.sub('<model>', line), end='')
	# Create the template file
	with open(path + '/template', 'w') as fp:
		for new, tmp in zip(newFiles, templateNames):
			if new.startswith('test-'):
				fp.write(new + ' tests/' + tmp[5:] + '\n')
			else:
				fp.write(new + ' ' + tmp + '\n')
	f = path + '/template '
	for new in newFiles:
		f += path + '/' + new + ' '
	return f
	

# Runs a command and returns the output when the command has completed
def runCommand(command):
	return subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8')


##### Main Function
if __name__ == '__main__':
	parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
	parser.add_argument('function', help='The function you wish to run\n\n', choices=['create','connect','subcomponent','convert','graph', 'sweep'])
	parser.add_argument('param',
			help=str('Function       | Help\n' + 
					 '---------------+--------------------------------------------------\n' + 
					 'Create/Connect | Name of the model to create\n' + 
					 'Subcomponent   | Name of the subcomponent to create\n' + 
					 'Param Sweep    | The path to the python test file\n' + 
					 'Graph          | The path to the python test file\n' +
					 'Convert        | The path to the model\n'))
	parser.add_argument('-a', '--args',
			help=str('Function       | Help\n' + 
					 '---------------+--------------------------------------------------\n' + 
					 'Create         | The path to the template\n' + 
					 'Connect        | The components you want to connect\n' + 
					 '               | Format is <element>.<component>.<subcomponent>,<subcomponent>;\n' + 
					 'Subcomponent   | The name of the subcomponent class\n' + 
					 'Convert        | The destination template name\n'))
	parser.add_argument('-p', '--path',
			help=str('Function       | Help\n' + 
					 '---------------+--------------------------------------------------\n' + 
					 'Create/Connect | The path where the model will be created\n' + 
					 'Subcomponent   | The path to the header file with the subcomponent definition\n'))
	args = parser.parse_args()
	if args.function == 'create':
		createModel(args.param, args.args, args.path)
	elif args.function == 'connect':
		connectModels(args.param, args.args, args.path)
	elif args.function == 'subcomponent':
		createSubcomponent(args.param, args.args, args.path)
	elif args.function == 'convert':
		model2Template(args.param, args.args)
	elif args.function == 'graph':
		graphModel(args.param)
	elif args.function == 'sweep':
		paramSweep(args.param)

