import sst
import subprocess
subprocess.Popen(['sbt', 'testOnly counter.CounterTester'], cwd='../chisel')

obj0 = sst.Component("<model>0", "<model>.<model>")
obj0.addParams({
	"printFrequency" : "5",
	"repeats" : "15"
	})

