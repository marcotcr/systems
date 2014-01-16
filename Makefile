CXX=g++
CPPFLAGS= -g -pthread
SRCS=main.cc command_list.cc pipe.cc
OBJS=$(subst .cc,.o,$(SRCS))

shell: $(OBJS)
		g++ -o shell $(OBJS)

run: shell
		./shell
clean:
		rm -f $(OBJS)

