#ifndef _<model>_H
#define _<model>_H

#include <sst/core/component.h>
#include <sst/core/elementinfo.h>

class <model> : public SST::Component {

public:
	<model>( SST::ComponentId_t id, SST::Params& params );
	~<model>();

	void setup();
	void finish();

	bool clockTick( SST::Cycle_t currentCycle );

	SST_ELI_REGISTER_COMPONENT(
		<model>,
		"<model>",
		"<model>",
		SST_ELI_ELEMENT_VERSION( 1, 0, 0 ),
		"<model> Description",
		COMPONENT_CATEGORY_PROCESSOR
	)

	SST_ELI_DOCUMENT_PARAMS(
		{ "printFrequency", "How frequently to print a message from the component", "5" },
		{ "repeats", "Number of repetitions to make", "10" }
	)

private:
	SST::Output output;
	SST::Cycle_t printFreq;
	SST::Cycle_t maxRepeats;
	SST::Cycle_t repeats;

};


#endif
