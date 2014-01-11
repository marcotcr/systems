#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <string.h>
#include <sys/wait.h>
using std::cout;
using std::endl;
using std::string;

// Launches a simple command, without pipe support. Doesn't support command line
// arguments. If an error occurs, prints error status.
void launch_simple(std::string cmd) {
  pid_t pid = fork();
  int status;
  if (pid < 0) {
    // fork failed
    exit(1);
  }
  if (pid == 0) { // child process
    // I think this is useless
    char arg[40];
    strcpy(arg, cmd.c_str());
    char *args[] = {arg, 0};
    char *env[] = {NULL};
    status = execve(cmd.c_str(), args, env);
    exit(status);
  }
  else { // parent process
    wait(&status);
    if (WEXITSTATUS(status) != 0) {
      cout << "Error " << WEXITSTATUS(status) << endl;
    }
  }
}

int main(int argc, char** argv) {
  string cmd;
  while(true) {
    cout << ">";
    std::getline(std::cin, cmd);
    if (cmd == "exit") {
      break;
    }
    launch_simple(cmd);
  }
}
