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
import argparse


# Move and update the template files to create a new model
def createModel(model, template):
	os.system(str('rm -rf ' + model))
	# Check for a valid template
	if os.path.isfile(template + '/template'):
		# Read template sources and destinations
		with open(template + '/template', 'r') as fp:
			structure = fp.read()
		source = structure.split()[0::2]
		destination = structure.split()[1::2]
		dest=[]
		# Replace <model> tag with the model name
		for item in destination:
			dest.append(item.replace('<model>', str(model)))
	os.system(str('mkdir -p ' + model + '/tests'))
	# Loop through sources and destinations at the same time
	for s, d in zip(source, dest):
		with open(str(template + '/' + s), 'r') as infile, open(str(model + '/' + d), 'w') as outfile:
			# Copy from source to destination while replacing <model> tags
			for line in infile:
				outfile.write(line.replace('<model>', str(model)))


# Connect various models together
def connectModels(model, componentList):
	components = componentList.split(',')
	os.system(str('rm -rf ' + model))
	os.system(str('mkdir -p ' + model))
	elements = ET.fromstring(runCommand('sst-info -qnxo /dev/stdout'))
	# Write the test python file
	with open(str(model + '/' + model + '.py'), 'w') as fp:
		fp.write('import sst\n\n# TODO: Check the parameters for all components and connect the links at the bottom before running!!!\n\n')
		# Loop through all the components
		for i in range(len(components)):
			component = components[i]
			(element, comp) = component.split('.')
			# Write the Component Definition
			fp.write('obj' + str(i) + ' = sst.Component("' + comp + str(i) + '", "' + component + '")\n')
			fp.write('obj' + str(i) + '.addParams({\n')
			parameters = elements.find("*/Component[@Name='" + comp + "']").findall('Parameter')
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
		for i in range(len(components)):
			component = components[i]
			(element, comp) = component.split('.')
			ports = elements.find("*/Component[@Name='" + comp + "']").findall('Port')
			fp.write('# ' + comp + ' Links\n')
			# Write out all of the available ports with their descriptions
			# These need to be modified by the user to actually connect components
			for k in range(len(ports)):
				
				fp.write('sst.Link("' + comp + '_' + ports[k].get('Name') + '").connect( (obj' + str(i) + ', "' + ports[k].get('Name') + '", "1ps"), (OBJNAME, "PORTNAME", "DELAY") ) # ' + ports[k].get('Description') + '\n')
			fp.write('\n')


# Convert a model into a template
def model2Template(model, template):
	# Check to see if the template exists already
	templates = os.listdir('./templates/')
	if template in templates:
		print('*** TEMPLATE ALREADY EXISTS ***\n\n')
		return
	path = './templates/' + template
	# Copy the model into the templates directory, clean the model
	os.system(str('cp -r ' + model + ' ' + path))
	os.system(str('make clean -C ' + path))
	# Move any test files into the main directory with and add test- prefix
	for item in os.listdir(str(path + '/tests/')):
		os.system(str('mv ' + path + '/tests/' + item + ' ' + path + '/test-' + item))
	os.system(str('rmdir ' + path + '/tests'))
	modelName = os.path.basename(str(model.rstrip('/')))
	files = os.listdir(path)
	newFiles = []
	templateNames = []
	# For each file move the file to its new name and replace model with <model> tag
	for item in files:
		new = item.replace(modelName, str(template))
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
	print('\nNew template created: ' + path + '\n')


def graphModel(model):
	path = model + '/tests/'
	tests = os.listdir(path)
	comp = [{}]
	sub = [{}]
	link = [{}]
	with open(str(path + tests[0]), 'r') as infile:
		for line in infile:
			tmp = {}
			if 'sst.Component' in line:
				tmp['Name'] = re.split('\'|"', line)[1].strip()
				tmp['Obj'] = line.split('=')[0].strip()
				comp.append(tmp)
			if '.setSubComponent' in line:
				tmp['Name'] = re.split('\'|"', line)[1].strip()
				tmp['Obj'] = line.split('=')[0].strip()
				tmp['Comp'] = line.split('.setSubComponent')[0].split('=')[1].strip()
				sub.append(tmp)
			if 'sst.Link' in line:
				tmp['Name'] = re.split('\'|"', line)[1].strip()
				tmp['A'] = line.split(',')[0].strip().split('(')[-1]
				tmp['B'] = line.split(',')[3].strip().split('(')[-1]
				link.append(tmp)
	# remove empty item from the beginning of the lists
	comp = list(filter(None,comp))
	sub = list(filter(None,sub))
	link = list(filter(None,link))
	with open(str(model + '/' + model + '.dot'),'w') as outfile:
		outfile.write(str('graph ' + model + ' {\n\n'))
		for item in comp:
			outfile.write(str('\t' + item['Obj'] + ' [label="' + item['Name'] + '" shape=box];\n\n'))
		for item in sub:
			outfile.write(str('\t' + item['Obj'] + ' [label="' + item['Name'] + '"];\n'))
			outfile.write(str('\t' + item['Comp'] + ' -- ' + item['Obj'] + ' [style=dotted];\n\n'))
		for item in link:
			outfile.write(str('\t' + item['A'] + ' -- ' + item['B'] + '[label="' + item['Name'] + '"];\n\n'))
		outfile.write('}')
	os.system(str('dot -Tps ' + model + '/' + model + '.dot -o ' + model + '/' + model + '.ps'))


# Runs a command and returns the output when the command has completed
def runCommand(command):
	return subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode("utf-8")


##### Main Function
if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("function", help="The function you wish to run", choices=['create','connect','convert','graph'])
	parser.add_argument("model", help="The name of the model")
	parser.add_argument("-t", "--template", help="The path to the template")
	parser.add_argument("-c", "--components", help="The components you want to connect. Format is <element>.<component> with commas separating, NO spaces")
	args = parser.parse_args()
	if args.function == 'create':
		createModel(args.model, args.template)
	elif args.function == 'connect':
		connectModels(args.model, args.components)
	elif args.function == 'convert':
		model2Template(args.model, args.template)
	elif args.function == 'graph':
		graphModel(args.model)

