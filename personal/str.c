#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>

char* trim(char* str)
{
        int     i, j;
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

int main()
{
	char cmd[256];
	scanf("%s", cmd);
	printf("%s\n", cmd);

	
	char* cmd1 = trim(cmd);
	printf("%s\n", cmd1);
	printf("%d\n", (int)strlen(cmd1));

	
}
