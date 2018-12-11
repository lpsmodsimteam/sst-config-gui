/**
Simple Model with one clock that functions as a wrapper for a Chisel simulation

Uses named pipes to send and receive data between SST and Chisel
*/

#include <sst/core/sst_config.h>
#include <sst/core/interfaces/stringEvent.h>
#include "<model>.h"

using SST::Interfaces::StringEvent;

<model>::<model>( SST::ComponentId_t id, SST::Params& params ) :
SST::Component(id), repeats(0) {

	output.init("<model>-" + getName() + "-> ", 1, 0, SST::Output::STDOUT);

	printFreq  = params.find<SST::Cycle_t>("printFrequency", 5);
	maxRepeats = params.find<SST::Cycle_t>("repeats", 10);

	if( ! (printFreq > 0) ) {
		output.fatal(CALL_INFO, -1, "Error: printFrequency must be greater than zero.\n");
	}

	output.verbose(CALL_INFO, 1, 0, "Config: maxRepeats=%" PRIu64 ", printFreq=%" PRIu64 "\n",
	static_cast<uint64_t>(maxRepeats), static_cast<uint64_t>(printFreq));

	// Just register a plain clock for this simple example
	registerClock("100MHz", new SST::Clock::Handler<<model>>(this, &<model>::clockTick));
	// Configure our port
	/*port = configureLink("port", new SST::Event::Handler<<model>>(this, &<model>::handleEvent));
	if ( !port ) {
		output.fatal(CALL_INFO, -1, "Failed to configure port 'port'\n");
	}*/

	// Tell SST to wait until we authorize it to exit
	registerAsPrimaryComponent();
	primaryComponentDoNotEndSim();
}

<model>::~<model>() {

}

void <model>::setup() {
	system("mkfifo /tmp/input /tmp/output");
	inFifo = open("/tmp/output", O_RDONLY);
	outFifo = open("/tmp/input", O_WRONLY);
	srand(time(NULL));
	output.verbose(CALL_INFO, 1, 0, "Component is being setup.\n");
}

void <model>::finish() {
	write(outFifo, "q", 1);
	close(inFifo);
	close(outFifo);
	system("rm /tmp/input /tmp/output");
	output.verbose(CALL_INFO, 1, 0, "Component is being finished.\n");
}

bool <model>::clockTick( SST::Cycle_t currentCycle ) {
	
	char s[4] = "100";
	for(int i = 1; i < 3; i++) {
		sprintf(s + i, "%x", rand() % 16);
	}
	char r[3] = "\0\0";
	
	printf("Clock %02lu: ", currentCycle);
	if( currentCycle % printFreq == 0 ) {
		printf("Send %s  ", s);
		//Chisel FIFO reads NEED to see a newline otherwise they will hang
		s[3] = '\n';
		write(outFifo, s, 4);
	}else{
		printf("Send 000  ");
		write(outFifo, "000\n", 4);
	}
	repeats++;
	
	read(inFifo, r, 2);
	printf("Read 0x%s\n",r);

	if( repeats == maxRepeats ) {
		primaryComponentOKToEndSim();
		return true;
	} else {
		return false;
	}
}

/*void <model>::handleEvent(SST::Event *ev) {
	StringEvent *se = dynamic_cast<StringEvent*>(ev);
	if ( se != NULL ) {
		output.output("%s received an event: \"%s\"\n", getName().c_str(), se->getString().c_str());
	}
	delete ev;
}*/
