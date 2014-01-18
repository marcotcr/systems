#include "pipe.h"
Pipe::Pipe(int fd[2]) {
  read_ = fd[0];
  write_ = fd[1];
}

int Pipe::write() {
  return write_;
}
int Pipe::read() {
  return read_;
}
