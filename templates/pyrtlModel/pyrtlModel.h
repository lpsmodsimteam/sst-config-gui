#ifndef _<model>_H
#define _<model>_H

#include <stdio.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

#include <sst/core/component.h>
#include <sst/core/link.h>
#include <sst/core/elementinfo.h>

class <model> : public SST::Component {

public:
	<model>( SST::ComponentId_t id, SST::Params& params );
	~<model>();

	void setup();
	void finish();

	bool clockTick( SST::Cycle_t currentCycle );

// Setup two event handlers one for each port

	void handleEventIN(SST::Event *ev);

        void handleEventOUT(SST::Event *ev);

	SST_ELI_REGISTER_COMPONENT(
		<model>,
		"<model>",
		"<model>",
		SST_ELI_ELEMENT_VERSION( 1, 0, 0 ),
		"SST model to incorporate a PyRTL counter",
		COMPONENT_CATEGORY_UNCATEGORIZED
	)
// Document Ports

	SST_ELI_DOCUMENT_PORTS(
		{ "portIN", "Port to recieve commands and input data from driver", {"sst.Interfaces.StringEvent"}},
                { "portOUT", "Port to send result back to the driver", {"sst.Interfaces.StringEvent"}}
	)

	
private:
	SST::Output output;
	
// Initial Condition for input to PyRTL

	char s[4] = "000";

	SST::Link *portIN;
        SST::Link *portOUT;

        int inFifo;
        int outFifo;
};

#endif
