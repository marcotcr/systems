#ifndef COMMAND_LIST_H
#define COMMAND_LIST_H

#include "pipe.h"
#include <vector>
#include <string>
// This class implements a list of commands of the form c1 | c2 | c3 ... cn.
// It doesn't handle command line arguments for any of the commands, and it
// assumes that there is a pipe in between every command
class CommandList {
 public:
  // Creates the command list. Parses command line (setting number of commands
  // to 0 if there is any errors) and  sets up the appropriate pipes. This
  // function must be called before forking other processes.
  CommandList(const std::string& command);
  // Fixes stdins and stdouts accordingly, and closes all pipes. See the
  // comments below on pipes_ for details on what accordingly means.
  void HandlePipes(int command_id);
  // Destructor: does nothing.
  ~CommandList();
  // Runs a command (execlp). If the command fails, write out to stdout an error
  // message.
  void ExecCmd(int command_id);
  // Returns the number of commands.
  int num_commands();
 private:
  void CloseAllPipes();
  int num_commands_;
  std::vector<std::string> commands_;
  // There are num_commands - 1 pipes. So, command 1 interacts with pipes 0 and
  // 1, while commands 2 interacts with pipes 1 and 2, and so on.
  // Command 0 and the last command are the exceptions: command 0 interacts only
  // with pipe 0 and the last command interacts only with pipe num_commands - 1.
  std::vector<Pipe> pipes_;
};

#endif  // COMMAND_LIST_H
