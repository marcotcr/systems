#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <vector>
#include <string.h>
#include <sys/wait.h>
using std::cout;
using std::endl;
using std::string;

int main(int argc, char** argv)
{
  string cmd;
  while(true) {
    usleep(100000);
    cout << "something" <<endl;
  }
}
