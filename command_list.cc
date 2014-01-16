#include "command_list.h"
#include <iostream>
#include <sstream>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
using std::cout;
using std::endl;
using std::string;
using std::vector;

void replace_all(std::string& str, const std::string& from, const std::string& to) {
  size_t start_pos = str.find(from);
  while (start_pos != std::string::npos) {
    str.replace(start_pos, from.length(), to);
    start_pos = str.find(from, start_pos + to.length()); 
  }
}

std::vector<std::string> split(const std::string &s) {
  string s2 = s;
  // making sure all |s have spaces in between them.
  replace_all(s2, "|", " | ");
  bool malformed = false;
  char* buffer = (char*) malloc(sizeof(char) * (s2.length() + 1));
  strcpy(buffer, s2.c_str());
  vector<string> return_;
  char *pch = strtok (buffer," ");
  bool even = 1;
  while (pch != NULL) {
    if (even) {
      return_.push_back(string(pch));
    }
    else {
      if (string(pch) != "|") {
        cout << "Malformed command. You must only have commands and pipes, no command line arguments allowed" << endl;
        malformed = true;
        break;
      }
    }
    even = 1 - even;
    pch = strtok (NULL, " ");
  }
  free(buffer);
  if (malformed) {
    return_.clear();
  }
  return return_;
}


CommandList::CommandList(const std::string& command) {
  commands_ = split(command); 
  num_commands_ = commands_.size();
  // cout << "-------------" << endl;
  // cout << "size " << commands_.size() << endl;
  // cout << "commands" << endl;
  // for (int i = 0; i < commands_.size(); ++i) {
  //   cout << commands_[i] << endl;
  // }
  // cout << "-------------" << endl;
  for (int i = 0; i < num_commands_ - 1; ++i) {
    int fd[2];
    pipe(fd);
    pipes_.push_back(Pipe(fd));
  }
}
CommandList::~CommandList() {

}

void CommandList::ExecCmd(int command_id) {
  int status = execlp(commands_[command_id].c_str(),
                      commands_[command_id].c_str(), NULL, NULL);
  cout << "Command \"" << commands_[command_id] << "\" failed" << endl;
  // cout << 1 << status << endl;
  exit(status);
}

int CommandList::num_commands() {
  return num_commands_;
}
void CommandList::HandlePipes(int command_id) {
  // If there is only one command, no piping is happening.
  if (num_commands_ == 1) {
    return;
  }
  string cmd;
  int status;
  // First command must duplicate pipe to its STDOUT.
  if (command_id == 0) {
    dup2(pipes_[0].write(), 1);
  }
  // Intermediate command must handle both STDIN and STDOUT.
  else if (command_id > 0 and command_id < num_commands_ - 1) {
    dup2(pipes_[command_id - 1].read(), 0);
    dup2(pipes_[command_id].write(), 1);
  }
  // Last command must duplicate pipe to its STDIN.
  else if (command_id == num_commands_ - 1) {
    dup2(pipes_[command_id - 1].read(), 0);
  }
  CloseAllPipes();
}

void CommandList::CloseAllPipes() {
  std::vector<Pipe>::iterator it;
  for (it = pipes_.begin() ; it != pipes_.end(); ++it) {
    close(it->write());
    close(it->read());
  }
}
