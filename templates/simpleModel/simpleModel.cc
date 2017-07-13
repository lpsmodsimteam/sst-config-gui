/**
Simple Model with one clock that prints "Hello World!"
*/

#include <sst/core/sst_config.h>
#include "<model>.h"

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

	// Tell SST to wait until we authorize it to exit
	registerAsPrimaryComponent();
	primaryComponentDoNotEndSim();
}

<model>::~<model>() {

}

void <model>::setup() {
	output.verbose(CALL_INFO, 1, 0, "Component is being setup.\n");
}

void <model>::finish() {
	output.verbose(CALL_INFO, 1, 0, "Component is being finished.\n");
}

bool <model>::clockTick( SST::Cycle_t currentCycle ) {

	if( currentCycle % printFreq == 0 ) {
		output.verbose(CALL_INFO, 1, 0, "Hello World!\n");
	}

	repeats++;

	if( repeats == maxRepeats ) {
		primaryComponentOKToEndSim();
		return true;
	} else {
		return false;
	}
}
