CXX=g++
CPPFLAGS= -g -pthread
SRCS=main.cc command_list.cc pipe.cc
OBJS=$(subst .cc,.o,$(SRCS))

550shell: $(OBJS)
		g++ -o 550shell $(OBJS)

run: 550shell
		./550shell
clean:
		rm -f $(OBJS) 550shell