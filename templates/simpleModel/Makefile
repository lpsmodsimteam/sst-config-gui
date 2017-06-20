CXX=$(shell sst-config --CXX)
CXXFLAGS=$(shell sst-config --ELEMENT_CXXFLAGS)
LDFLAGS=$(shell sst-config --ELEMENT_LDFLAGS)

all: lib<model#1>.so install

lib<model#1>.so: <sourceFiles>
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $<

install:
	sst-register <model#1> <model#1>_LIBDIR=$(CURDIR)

clean:
	rm -f *.o lib<model#1>.so

