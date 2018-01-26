#ifndef _<model>_H
#define _<model>_H

#include <sst/core/component.h>
#include <sst/core/link.h>
#include <sst/core/elementinfo.h>
#include <string>

class <model> : public SST::Component {

public:
	<model>( SST::ComponentId_t id, SST::Params& params );
	~<model>();

	void setup();
	void finish();

	bool clockTick( SST::Cycle_t currentCycle );

	void handleEventL(SST::Event *ev);

	void handleEventR(SST::Event *ev);

	SST_ELI_REGISTER_COMPONENT(
		<model>,
		"<model>",
		"<model>",
		SST_ELI_ELEMENT_VERSION( 1, 0, 0 ),
		"Logic Analyzer Element for SST",
		COMPONENT_CATEGORY_UNCATEGORIZED
	)

	// Document Parameters

	SST_ELI_DOCUMENT_PARAMS(
		{ "TriggerStartL", "What value to start Trace for left port.", "TriggerStart" },
		{ "TriggerStopL", "What value to stop Trace. left port", "TriggerStop" },
		{ "TriggerL", "Boolean value to control Triggering of left port", "false" },
		{ "TriggerStartR", "What value to start Trace for right port.", "TriggerStart" },
		{ "TriggerStopR", "What value to stop Trace for right port.", "TriggerStop" },
		{ "TriggerR", "Boolean value to control Triggering of right port", "false" },
	)

	// Document Ports

	SST_ELI_DOCUMENT_PORTS(
		{ "portL", "Left port on which to send/recv messages", {"sst.Interfaces.StringEvent"}},
		{ "portR", "Right port on which to send/recv messages", {"sst.Interfaces.StringEvent"}}
	)

private:
	SST::Output output;
	SST::Cycle_t repeats;
	bool TriggerL;
	std::string TriggerStartL;
	std::string TriggerStopL;
	bool TriggerR;
	std::string TriggerStartR;
	std::string TriggerStopR;

	SST::Link *portL;
	SST::Link *portR;
};

#endif
