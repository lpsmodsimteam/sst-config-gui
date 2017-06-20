#ifndef _<model#1>_H
#define _<model#1>_H

#include <sst/core/component.h>
#include <sst/core/elementinfo.h>

class <model#1> : public SST::Component {

public:
	<model#1>( SST::ComponentId_t id, SST::Params& params );
	~<model#1>();

	void setup();
	void finish();

	bool clockTick( SST::Cycle_t currentCycle );

	SST_ELI_REGISTER_COMPONENT(
		<model#1>,
		"<model#1>",
		"<model#1>",
		SST_ELI_ELEMENT_VERSION( 1, 0, 0 ),
		"<model#1> Description",
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
