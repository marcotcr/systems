#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#define INT_MAX 32767

int main(int argc, char** argv)
{
	char 	cmd[INT_MAX]; 
	int	fd[2], i, fd2[2];
	pid_t	childpid;	
	pid_t	globalPid;
	int status;

	pipe(fd);
	pipe(fd2);	
	scanf("%s", cmd);
	printf("%s\n", cmd);
	
	char	*tok = strtok(cmd, "|");
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
			tok_next = strtok(NULL,"|");
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
}
