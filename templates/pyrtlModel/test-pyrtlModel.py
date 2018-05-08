import sst
import subprocess
subprocess.Popen('python Counter.py'.split(' '))

obj0 = sst.Component("<model>0", "<model>.<model>")




###################################################################
# TODO: Links have the first port connected but need to be manually
# connected to a second port to work. Delays also should be edited

# obj0 Links
#sst.Link("<model>0_portIN").connect( (obj0, "portIN", "1ns"), (obj1, "cmdport", "1ns") ) # Port to recieve commands and input data from driver
#sst.Link("<model>0_portOUT").connect( (obj0, "portOUT", "1ns"), (obj1, "resport", "1ns") ) # Port to send result back to the driver


