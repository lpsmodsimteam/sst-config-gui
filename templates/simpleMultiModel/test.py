import sst

obj0 = sst.Component("<model>0", "<model>.<model>")
obj0.addParams({
    "printFrequency" : "5",
    "repeats" : "15"
    })

obj1 = sst.Component("<model>1", "<model>.<model>")
obj1.addParams({
    "printFrequency" : "5",
    "repeats" : "10"
    })

sst.Link("MyLink").connect( (obj0, "port", "15ns"), (obj1, "port", "15ns") )
