#include<stdio.h>
#include <unistd.h>
#include <sys/wait.h>

int main(){
    int p[2];
    pipe(p); //Creates a pipe with file descriptors Eg. input = 3 and output = 4 (Since, 0,1 and 2 are not available)

    if (fork() == 0) { //Child process
        close(0);//Release fd no - 0
        close(p[1]); 
        dup2(p[0],0); //Create duplicate of fd - 3 (pipe read end) with fd 0.
        close(p[0]);//Close pipe fds since useful one is duplicated
        execlp("wc", "wc", NULL, NULL);
    }
		else {//Parent process
				close(1);//Release fd no - 1
        close(p[0]); //Close pipe fds since useful one is duplicated
        dup2(p[1],1); //Create duplicate of fd - 4 (pipe write end) with fd 1.
        close(p[1]);
        execlp("ls", "ls" , NULL, NULL);
    }
	return 0;	
}
