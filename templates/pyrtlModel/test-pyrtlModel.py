import sst
import subprocess
subprocess.Popen('python counter.py'.split(' '))

obj0 = sst.Component("<model>0", "<model>.<model>")
obj0.addParams({
	"printFrequency" : "5",
	"repeats" : "15"
	})

