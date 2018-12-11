# SST environment variables
CXX = $(shell sst-config --CXX)
CXXFLAGS = $(shell sst-config --ELEMENT_CXXFLAGS)
LDFLAGS  = $(shell sst-config --ELEMENT_LDFLAGS)

# Grab all the .cc files, put objs and depends in the .build folder
SRC = $(wildcard *.cc)
OBJ = $(SRC:%.cc=.build/%.o)
DEP = $(OBJ:%.o=%.d)

# Tell Make that all, install, uninstall, clean are NOT files, just targets
.PHONY: all install uninstall clean

# Simply typing "make" calls this by default, so everything gets build and installed
all: install

# Use the dependencies when compiling to check for header file changes
-include $(DEP)
.build/%.o: %.cc
	@mkdir -p $(@D)
	$(CXX) $(CXXFLAGS) -MMD -c $< -o $@

# Link all the objects to create the library
lib<model>.so: $(OBJ)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^

# Register the model with SST
install: lib<model>.so
	sst-register <model> <model>_LIBDIR=$(CURDIR)

# Unregister the model with SST
uninstall:
	sst-register -u <model>

# Remove the build files, output graphs and the library
clean: uninstall
	rm -rf .build tests/graphs lib<model>.so
