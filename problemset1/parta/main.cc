#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <vector>
#include <string.h>
#include <sys/wait.h>
#include "command_list.h"
using std::cout;
using std::endl;
using std::string;

bool IsParent(pid_t pid) {
  return pid > 0;
}


void ExecuteCommand(std::string& cmd) {
  int status;
  pid_t pid = 1;
  int cur = -1;
  CommandList cl(cmd);
  int n = cl.num_commands();
  // This happens if there is a malformed command.
  if (!n) {
    return;
  }
  // This code spawns one process for each command.
  while (cur < n - 1) {
    if (IsParent(pid)) {
      cur++;
      pid = fork();
    }
    else {
      break;
    }
  }

  if (IsParent(pid)) {
    // this just closes all pipes
    cl.HandlePipes(-1);
    // TODO: maybe have some error checking here?
    // waiting for all my children.
    while(wait(NULL) > 0);
  }
  else {
    cl.HandlePipes(cur);
    cl.ExecCmd(cur);
  }
}

int main(int argc, char** argv)
{
  string cmd;
  while(true) {
    cout << ">";
    std::getline(std::cin, cmd);
    if (cmd == "exit") {
      break;
    }
    ExecuteCommand(cmd);
  }
}
