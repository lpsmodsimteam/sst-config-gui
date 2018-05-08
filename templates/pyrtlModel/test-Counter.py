# This is a simple PyRTL file that produces an eight bit loadable Counter
# Replace the RTL generation code with your specific code and modify the
# Simultation similar to the code in the simulation section to allow your
# PyRTL code to run with rest of the SST template. 

# It should be noted that the SST GUI can be used to generate and Compile
# your code you can not use the GUI to run your code you will need to
# use the standard sst <model> where model is your SST/PyRTL combined model
# model. This is because inorder for the PyRTL simulator to run at the same
# time as SST it must use subprocesses and the GUI can not handle subprocesses.


import pyrtl
from pyrtl.rtllib import muxes
import os

# Setup and open Fifos

os.mkfifo('/tmp/output')
os.mkfifo('/tmp/input')

# Open Linux "Pipes"

outFifo = os.open('/tmp/output', os.O_WRONLY)
inFifo = os.open('/tmp/input', os.O_RDONLY)

# Setup Inputs Outputs and internal "wires"

load = pyrtl.Input(bitwidth=1, name='load')
data = pyrtl.Input(bitwidth=8, name='data')
counterval = pyrtl.WireVector(bitwidth=8, name='counterval')
counterinc = pyrtl.WireVector(bitwidth=8, name='counterinc')

# Define Logic

counter = pyrtl.Register(bitwidth=8, name='counter')
counterinc <<= counter + 1
with muxes.MultiSelector(load,counterval) as mux:
    mux.option(1,data)
    mux.option(0,counterinc) 
   
counter.next <<= counterval

# Uncomment next 3 lines to generate Verilog of circuit

#vfile = open("counter.v","w")
#pyrtl.OutputToVerilog(vfile)
#vfile.close

# Uncomment next 3 lines to generate GraphViz dot file of circuit

#dotfile = open("counter.dot","w")
#pyrtl.output_to_graphviz(dotfile)
#dotfile.close

# Uncomment next line to print out PyRTL view of circuit

#print(pyrtl.working_block())

# Start Simulation

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)

while True:
    cmd = os.read(inFifo,3)
    if cmd != '':
        if cmd[0] == 'q':
            break
        l = int(cmd[0], 2)
        d = int(cmd[1:3],16)
        sim.step({'load': l, 'data': d})
        os.write(outFifo, hex(sim.inspect(counter)))

# Comment next line to remove "timing waveforms" for PyRTL simulation

sim_trace.render_trace()

# Close Fifos and remove Linux "Pipes"
os.close(inFifo)
os.close(outFifo)
os.system('rm /tmp/input /tmp/output')
 
