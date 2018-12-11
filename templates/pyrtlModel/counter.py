import pyrtl
import os

# Create and connect to named pipes
os.mkfifo('/tmp/output')
os.mkfifo('/tmp/input')

outFifo = os.open('/tmp/output', os.O_WRONLY)
inFifo = os.open('/tmp/input', os.O_RDONLY)


# PyRTL functions to create an adder
def one_bit_add(a, b, carry_in):
	assert len(a) == len(b) == 1  # len returns the bitwidth
	sum = a ^ b ^ carry_in
	carry_out = a & b | a & carry_in | b & carry_in
	return sum, carry_out


def ripple_add(a, b, carry_in=0):
	a, b = pyrtl.match_bitwidth(a, b)
	# this function is a function that allows us to match the bitwidth of multiple
	# different wires. By default, it zero extends the shorter bits
	if len(a) == 1:
		sumbits, carry_out = one_bit_add(a, b, carry_in)
	else:
		lsbit, ripplecarry = one_bit_add(a[0], b[0], carry_in)
		msbits, carry_out = ripple_add(a[1:], b[1:], ripplecarry)
		sumbits = pyrtl.concat(msbits, lsbit)
	return sumbits, carry_out

# Inputs and outputs of the module
load = pyrtl.Input(1, 'load')
data = pyrtl.Input(8, 'data')
out  = pyrtl.Output(8, 'out')

# Simple logic to allow loading of the counter
counter = pyrtl.Register(8, 'counter')
sum, carry_out = ripple_add(counter, pyrtl.Const("1'b1"))
counter.next <<= pyrtl.mux(load, sum, data)
out <<= counter


# Setup the simulation
sim_trace = pyrtl.SimulationTrace([load, data, out])
sim = pyrtl.Simulation(tracer=sim_trace)
# Run until receive a 'q' from the named pipe
while True:
	cmd = os.read(inFifo,3)
	if cmd != '':
		if cmd == 'q':
			break
		l = int(cmd[0],2)
		d = int(cmd[1:3],16)
		sim.step({'load': l, 'data': d})
		os.write(outFifo, hex(sim.inspect(counter)))

# Clean up fifos and print out waveform
os.close(inFifo)
os.close(outFifo)
os.system('rm /tmp/input /tmp/output')
sim_trace.render_trace()

# Extra features to print out dot graph, and output verilog
# Dot graph
#with open('test.dot', 'w') as fp:
#	pyrtl.output_to_graphviz(fp)
# Verilog
#with open('test.v', 'w') as fp:
#	pyrtl.OutputToVerilog(fp)
# Optimized verilog
#with open('testO.v', 'w') as fp:
#	pyrtl.synthesize()
#	pyrtl.optimize()
#	pyrtl.OutputToVerilog(fp)

exit(0)
