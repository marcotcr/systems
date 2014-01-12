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
// Note that the command needs to be a complete path, such as /bin/ls instead of
// just ls.
void launch_simple(std::string cmd) {
  pid_t pid = fork();
  int status;
  if (pid < 0) {
    // fork failed
    exit(1);
  }
  if (pid == 0) { // child process
    // I think this is needless
    char arg[40];
    // trimming the command
    size_t startpos = cmd.find_first_not_of(" \t");
    if( string::npos != startpos )
    {
        cmd = cmd.substr( startpos );
    }

    size_t endpos = cmd.find_last_not_of(" \t");
    if( string::npos != endpos )
    {
        cmd = cmd.substr( 0, endpos+1 );
    }
    strcpy(arg, cmd.c_str());
   
    // commenting out as we dont need this anymore. 
    // char *args[] = {arg, 0};
    // char *env[] = {NULL};
    status = execlp(cmd.c_str(), arg, NULL, NULL); // I am changing this to execlp as it doesnt require full path of the command
    cout << 1 << status << endl;
    exit(status);
  }
  else { // parent process
    wait(&status);
    if (WEXITSTATUS(status) != 0) {
      cout << "Error " << WEXITSTATUS(status) << endl;
    }
  }
}

char* trim(char* str)
{
	if(str == NULL)
		return NULL;
	int	i, j;
	for(i=0;i<strlen(str);i++)
        {
                if(str[i] == ' ' || str[i] == '\t' || str[i] == '\n')
                        continue;
                break;
        }
        for(j = strlen(str) -1; j>=0; j--)
        {
                if(str[j] == ' ' || str[j] == '\t' || str[j] == '\n')
                        continue;
                break;
        }

        return strndup(str, j-i+1);
}

void launch_piped(std::string input_cmd)
{
	int	fd[2], i, fd2[2];
	pid_t	childpid;	
	int status;
	
	// we will need two pipelines, one for communication with the previous command, second for communication with the next.
	pipe(fd);
	pipe(fd2);	
	char	*cmd = strdup(input_cmd.c_str());
	char	*tok = trim(strtok(cmd, "|"));
	char	*tok_next = tok;
	// save the stdout to use for the output of final command.
	int	saved_stdout = dup(1);
		
	// setting the output to flow only through the pipe, we will change this for the last command.
	int	cmdCount = 0;
	do
	{
		if(tok!=NULL)
		{
			// do readahead to figure out if we are at the last command
			tok_next = trim(strtok(NULL,"|"));
			if(tok_next == NULL)
			{
				// This means that only the last command is left to execute
				// set output to standard output.
				// set input to fd[0]
				if((childpid = fork()) == 0)
				{
					if(cmdCount%2 !=0)
					{
						dup2(fd2[0],0);
					}
					else
					{
						dup2(fd[0],0);
					}
					
					close(fd[0]);	
					close(fd[1]);	
					close(fd2[0]);	
					close(fd2[1]);	
					// since we are at the final command, restore the stdout
					dup2(saved_stdout, 1);
					close(saved_stdout); 
					status = execlp(tok, tok, NULL, NULL);
				}
				else if(childpid < 0)
				{
					//fork failed
					printf("fork failed;");
				}
			}
			else
			{
				if((childpid = fork()) == 0)
				{
					if(cmdCount%2 != 0)
					{
						dup2(fd2[0], 0);
						dup2(fd[1], 1);
					}
					else
					{
						dup2(fd2[1],1);
						dup2(fd[0], 0);
					}
					
					close(fd[0]);	
					close(fd[1]);	
					close(fd2[0]);	
					close(fd2[1]);	
					status = execlp(tok, tok, NULL, NULL);
				}
				else if (childpid > 0)
				{
					cmdCount++;
    					//wait(&status);
    					//if (WEXITSTATUS(status) != 0)
					//{
						// cout << "Error " << WEXITSTATUS(status) << endl;
					//}
				}
				else
				{
					//fork failed
                                        printf("fork failed;");
				}
			}
		}
	       	tok = tok_next;
	}while(tok!=NULL);
	
	for(i=0;i<cmdCount;i++)
		wait(&status);
	
	// Closing all pipes from the main thread.				
	close(fd[0]);	
	close(fd[1]);	
	close(fd2[0]);	
	close(fd2[1]);	
}

int main(int argc, char** argv)
{
	string cmd;
	
	while(true)
	{
		cout << ">";
		std::getline(std::cin, cmd);
		if (cmd == "exit")
		{
			break;
		}
		launch_piped(cmd);	
	}
}
