/**
Simple model that is basically a wrapper for PyRTL
This model will receive a string event from another
SST model then pass it through Linux Pipes to the 
PyRTL model that is running as a subprocess.
*/

#include <sst/core/sst_config.h>
#include <sst/core/interfaces/stringEvent.h>
#include "<model>.h"

using SST::Interfaces::StringEvent;

<model>::<model>( SST::ComponentId_t id, SST::Params& params ) :
SST::Component(id) {

	output.init("<model>-" + getName() + "-> ", 1, 0, SST::Output::STDOUT);

	// Just register a plain clock for this simple example

	registerClock("100MHz", new SST::Clock::Handler<<model>>(this, &<model>::clockTick));

	// Configure our Input Command port
/*
	portIN = configureLink("portIN", new SST::Event::Handler<<model>>(this, &<model>::handleEventIN));
	if ( !portIN ) {
		output.fatal(CALL_INFO, -1, "Failed to configure port 'portIN'\n");
	}

       // Configure our Output Data port

	portOUT = configureLink("portOUT", new SST::Event::Handler<<model>>(this, &<model>::handleEventOUT));
	if ( !portOUT ) {
		output.fatal(CALL_INFO, -1, "Failed to configure port 'portOUT'\n");
	}

	// Tell SST to wait until we authorize it to exit
*/
	registerAsPrimaryComponent();
}

<model>::~<model>() {

}

void <model>::setup() {

	 // Setup "fifos" in /tmp directory

        while(access("/tmp/output", R_OK) != 0){}
        inFifo = open("/tmp/output", O_RDONLY);
        while(access("/tmp/input", W_OK) != 0){}
        outFifo = open("/tmp/input", O_WRONLY);
	output.verbose(CALL_INFO, 1, 0, "Component is being setup.\n");
}

void <model>::finish() {

	close(inFifo);
        close(outFifo);
	output.verbose(CALL_INFO, 1, 0, "Component is being finished.\n");
}

bool <model>::clockTick( SST::Cycle_t currentCycle ) {

	// Command String to PyRTL model
        // Byte 1 "Load" 
        // Byte 2 and 3 data
        
        write(outFifo, s, 3);
	
        // Read "results from PyRTL Counter

        char r[5] = "\0\0\0\0";
	read(inFifo, r, 4);
        
        sprintf(s, "%s", "000");
	printf("%s\n",r);
	//portOUT->send(new StringEvent(r));
	return false;
}

void <model>::handleEventIN(SST::Event *ev) {

        // When a "command" and "input data are sent from 
        // Driver store in string to sent to PyRTL model

	StringEvent *se = dynamic_cast<StringEvent*>(ev);
	if ( se != NULL ) {
		sprintf(s, "%s", se->getString().c_str());
	}
	delete ev;
}

void <model>::handleEventOUT(SST::Event *ev) {

        // This Port is to return data to driver. If data is received on 
        // this port flag the error.

	StringEvent *se = dynamic_cast<StringEvent*>(ev);
	if ( se != NULL ) {
		output.output("%s received an event this port is for output only: \"%s\"\n", getName().c_str(), se->getString().c_str());
	}
	delete ev;
}
