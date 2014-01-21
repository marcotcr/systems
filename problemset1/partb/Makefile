CXX=g++
CPPFLAGS= -g -pthread
SRCS=main.cc server.cc threadpool.cc
OBJS=$(subst .cc,.o,$(SRCS))

550server: $(OBJS)
		g++ -pthread -o 550server $(OBJS)

run: 550server
		./550server
clean:
		rm -f $(OBJS) 550server
