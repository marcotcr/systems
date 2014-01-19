#include "server.h"
#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <vector>
#include <string.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/poll.h>
#include <errno.h>
#include <vector>

using std::cout;
using std::endl;
using std::string;

#define MAX_NUM_REQ 1000
#define TIMEOUT (5*60*1000)  //timeout of 5 mins for the poll()

int main(int argc, char** argv)
{
	string usage = "Usage: ./550server <server_adderess> <port_no>";
	int i, pollReturn, newFd;
	bool unexpected = false;
	struct pollfd fds[MAX_NUM_REQ];
	int nfds = 0, old_nfds = 0;
	std::map<int, std::string> filenames;

	if (argc < 3)
	{
		std::cerr << usage;
		exit(1);
	}
	string serverName = argv[1];
	int portno = atoi(argv[2]);
	
	// Starting the server...
	Server amtedServer(serverName, portno, 32);

	bzero((char *)&fds, sizeof(fds));

	// Setting up the initially poll to listen socket file descriptor.
	fds[0].fd = amtedServer.SocketFD();
	fds[0].events = POLLIN;
	nfds++;

	do
	{
		cout << "Starting to poll nfds: " << nfds << endl;
		pollReturn = poll(fds, nfds, TIMEOUT);
		if (pollReturn == 0)
		{
			cout << "Poll Timed out.";
			break;
		}
		
		if(pollReturn < 0)
		{
			cout << "Poll failed.";
			break;
		}

		old_nfds = nfds;
		for (i = 0; i < old_nfds; i++)
		{
			if (fds[i].revents == 0)
			{
				// This means that there is no event for this file descriptor;
				continue;
			}

			if (fds[i].revents == POLLIN)
			{
				// This means that there is an event on this file descriptor
				// So lets figure out what socket this is.
				if (fds[i].fd == amtedServer.SocketFD())
				{
					// Listen for connections socket has an event
					// So lets accept all the queued up connections
					do
					{
						cout << "Accepting connections..."<<endl;
						newFd = amtedServer.Accept();
						if (errno == EWOULDBLOCK)
						{
							cout << "No more connections right now.." <<endl;
							errno = 0;
							break; // This means no more incoming connections
						}

						cout << "Accepted connection: " << newFd << endl;
						// Add new connection to poll fd list
						fds[nfds].fd = newFd;
						fds[nfds++].events = POLLIN; 

					} while (newFd > 0);
				}
				else
				{
					// This means that there is an event on some other socket
					// i.e. there is some data on accept socket available.
					// so lets read this data, i.e. filename;
					cout << "Received event for fd: " << fds[i].fd <<endl;
 					filenames[fds[i].fd] = amtedServer.Read(fds[i].fd);
					cout << "Received filename from :" << fds[i].fd << " filename: " << filenames[fds[i].fd] <<endl;

					// Send back data, I am just returning back the filename for now.
					amtedServer.Write(fds[i].fd, filenames[fds[i].fd]);

					// Close the connection
					amtedServer.CloseConnection(fds[i].fd);

					fds[i].fd = -1;
				}
			}
			else
			{
				// This means that some other unexpected event has happened
				unexpected = true;
				break;
			}
		}
		
		if (unexpected)
			break;

		// Removing closed connections.
		for (i = 0; i < nfds; i++)
		{
			if (fds[i].fd == -1)
			{
				for(int j = i; j < nfds; j++)
				{
					fds[j].fd = fds[j+1].fd;
				}
				nfds--;
			}
		}
	} while(true);

	// Close the connection.
	amtedServer.CloseServer();
	
	// Close all open sockets.
	for(i = 0; i < nfds; i++)
	{
		if(fds[i].fd >=0)
			close(fds[i].fd);
	}

	return 0; 
}