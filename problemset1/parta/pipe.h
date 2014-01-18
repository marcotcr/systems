#ifndef SHELL_PIPE_H
#define SHELL_PIPE_H

// Just a container for a pipe
class Pipe {
 public:
  // fd is an int vector that is the result of a pipe() call
  Pipe(int fd[2]);
  // returns the write handler
  int write();
  // returns the read handler
  int read();
 private:
  int write_;
  int read_;
};

#endif  // SHELL_PIPE_H
