import sst

obj0 = sst.Component("<model>0", "<model>.<model>")
obj0.addParams({
	"TriggerStartL" : "TriggerStart",
	"TriggerStopL" : "TriggerStop",
	"TriggerL" : "false"
	"TriggerStartR" : "TriggerStart",
	"TriggerStopR" : "TriggerStop",
	"TriggerR" : "false"
	})

obj1 = sst.Component("<model>1", "<model>.<model>")
obj1.addParams({
	"TriggerStarLt" : "TriggerStart",
	"TriggerStopL" : "TriggerStop",
	"TriggerL" : "false"
	"TriggerStartR" : "TriggerStart",
	"TriggerStopR" : "TriggerStop",
	"TriggerR" : "false"
	})

sst.Link("MyLink").connect( (obj0, "port", "15ns"), (obj1, "port", "15ns") )
