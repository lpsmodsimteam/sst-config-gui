/**
This is a simple Logic Analyzer/Tap model. It should be placed in between
two elements that are communicating with one another. It will pass through
all communication without causing a delay. By setting the parameters 
correctly it will print out several different scenarios. There is an
Event Handler for each port. This default configuration has two ports
Left and Right, the user can add as many as he likes but make sure to 
also add event handlers for the ports, even if is simple as a pass through.
The Default Parameters are as follows:

TriggerStartL - Start printing for Left port (Default TriggerStart)
TriggerStopL - Stop printing for Left port (Default TriggerStop)
TriggerL - Boolean Trigger for Left port (Default False)
TriggerStartR - Start printing for Right port (Default TriggerStart)
TriggerStopR - Stop printing for Right port (Default TriggerStop)
TriggerR - Boolean Trigger for Right port (Default False)

*/

#include <sst/core/sst_config.h>
#include <sst/core/interfaces/stringEvent.h>
#include "<model>.h"


using SST::Interfaces::StringEvent;

<model>::<model>( SST::ComponentId_t id, SST::Params& params ) :
SST::Component(id), repeats(0) {

	output.init("<model>-" + getName() + "-> ", 1, 0, SST::Output::STDOUT);

	// Default Parameters for Logic Analyzer

	TriggerStartL  = params.find<std::string>("TriggerStartL", "TriggerStart");
	TriggerStopL  = params.find<std::string>("TriggerStopL", "TriggerStop");
	TriggerL  = params.find<bool>("TriggerL", false);
	TriggerStartR  = params.find<std::string>("TriggerStartR", "TriggerStart");
	TriggerStopR  = params.find<std::string>("TriggerStopR", "TriggerStop");
	TriggerR  = params.find<bool>("TriggerR", false);

	// Just register a plain clock for this simple example
	registerClock("100MHz", new SST::Clock::Handler<<model>>(this, &<model>::clockTick));

	// Configure ports 
	// You can add more ports if you want here but make sure to add event handlers

	// Configure our Left port
	portL = configureLink("portL", new SST::Event::Handler<<model>>(this, &<model>::handleEventL));
	if ( !portL ) {
		output.fatal(CALL_INFO, -1, "Failed to configure port 'portL'\n");
	}

	// Configure our Right port
	portR = configureLink("portR", new SST::Event::Handler<<model>>(this, &<model>::handleEventR));
	if ( !portR ) {
		output.fatal(CALL_INFO, -1, "Failed to configure port 'portR'\n");
	}

	

	// Tell SST to wait until we authorize it to exit
	
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
	return false;
}

// Below is the standard "Tap Configuration" for the Logic Analyzer
// In your Project Driver file you can update the parameters (Trigger, 
// TriggerStart, TriggerStop, (L and R are left and right) 
// as listed below to get the following results.This configuration assumes that
// it is placed between two components that are communicating with one
// another. As stated above the model is a pass through and will not 
// insert any delay. There is an event handler on each port both are
// designed the same way.
//
// Trigger Value	TriggerStart 	TriggerStop	Function
// True			Default		Stop Value	Will print out all communication
//							until Stop Value
// False		Start Value	Default		Will only start printing out
//							after it receives Start Value
// False		Start Value	Stop Value	Will only print out values between
//							Start Value and Stop Value
// True			Start Value	Stop Value	Will Print before the Start Value and
//							after the Stop Value
// True			Default		Default		Will print all
// False		Default		Default		Will print nothing (pass through only)
// Also included is the code to "oppisite ports" be used as triggers
// Simply uncomment the other Trigger code and comment the default and input to the Left
// will trigger printing from the right and vice-a-versa

void <model>::handleEventL(SST::Event *ev) {
	StringEvent *se = dynamic_cast<StringEvent*>(ev);
	if ( se != NULL ) {
		portR->send(new StringEvent(se));
		if (TriggerStartL.compare(se->getString()) == 0){
			TriggerL = !TriggerL; // Use this line if you want Left port to trigger Left
			//TriggerR = !TriggerR; // Use this line if you want Left port to trigger Right
		}
		if (TriggerStopL.compare(se->getString()) == 0){
			TriggerL = !TriggerL; // Use this line if you want Left port to trigger Left
			//TriggerR = !TriggerR; // Use this line if you want Left port to trigger Right
		}
		if (TriggerL){
			output.output("%s received an event: \"%s\"\n", getName().c_str(), se->getString().c_str());
		}
			
	}
	delete ev;
}

void <model>::handleEventR(SST::Event *ev) {
	StringEvent *se = dynamic_cast<StringEvent*>(ev);
	if ( se != NULL ) {
		portL->send(new StringEvent(se));
		if (TriggerStartR.compare(se->getString()) == 0){
			TriggerR = !TriggerR; // Use this line if you want Right port to trigger Right
			//TriggerL = !TriggerL; // Use this line if you want Right port to trigger Left
		}
		if (TriggerStopR.compare(se->getString()) == 0){
			TriggerR = !TriggerR; // Use this line if you want Right port to trigger Right
			//TriggerL = !TriggerL; // Use this line if you want Right port to trigger Left
		}
		if (TriggerR){
			output.output("%s received an event: \"%s\"\n", getName().c_str(), se->getString().c_str());
		}
			
	}
	delete ev;
}
