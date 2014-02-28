GEN_SRC := MLEngine_server.cpp gen-cpp/ml_constants.cpp gen-cpp/ml_types.cpp gen-cpp/MLEngine.cpp
GEN_OBJ := $(patsubst %.cpp,%.o, $(GEN_SRC))

THRIFT_DIR := /usr/local/include/thrift
BOOST_DIR := /usr/local/include
CPPFLAGS=-std=c++11 -stdlib=libc++
CXX=g++

INC := -I$(THRIFT_DIR) -I$(BOOST_DIR)


.PHONY: all clean

all: mlserver

%.o: %.cpp
	$(CXX) $(CPPFLAGS) -Wall -DHAVE_INTTYPES_H -DHAVE_NETINET_IN_H $(INC) -c $< -o $@

mlserver: MLEngine_server.o $(GEN_OBJ)
	$(CXX) $(CPPFLAGS) $^ -o $@ -L/usr/local/lib -lthrift 

something_client: Something_client.o $(GEN_OBJ)
	$(CXX) $^ -o $@ -L/usr/local/lib -lthrift 

clean:
		$(RM) *.o mlserver something_client gen-cpp/*.o
