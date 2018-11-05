CXX=$(shell sst-config --CXX)
CXXFLAGS=$(shell sst-config --ELEMENT_CXXFLAGS)
LDFLAGS=$(shell sst-config --ELEMENT_LDFLAGS)

all: lib<model>.so install

lib<model>.so: <model>.cc <model>1.cc
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^

install:
	sst-register <model> <model>_LIBDIR=$(CURDIR)

clean:
	rm -rf tests/graphs lib<model>.so
	sst-register -u <model>
