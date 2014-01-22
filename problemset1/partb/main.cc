#include "server.h"
#include <fcntl.h>
#include "threadpool.h"
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
#include <tr1/unordered_map>

using std::cout;
using std::endl;
using std::string;
using std::tr1::unordered_map;

#define MAX_NUM_REQ 1000
#define NUM_THREADS 50
#define TIMEOUT (5*60*1000)  //timeout of 5 mins for the poll()

int main(int argc, char** argv) {
  string usage = "Usage: ./550server <server_adderess> <port_no>";
  int i, pollReturn, newFd;
  bool unexpected = false;
  struct pollfd fds[MAX_NUM_REQ];
  int nfds = 0, old_nfds = 0;
	unordered_map<int, std::string> filenames;
  std::map<int, int> socketid_to_pollfd;
  int threadFD[2];
  // This is a self pipe.
  pipe(threadFD);
  // Setting the pipe to non-blocking IO.
  fcntl(threadFD[0], F_SETFL, fcntl(threadFD[0], F_GETFL) | O_NONBLOCK);
  ThreadPool *tp = ThreadPool::GetInstance(NUM_THREADS, threadFD[1]);

  if (argc < 3)
  {
    std::cerr << usage;
    exit(1);
  }
  string server_ip = argv[1];
  int portno = atoi(argv[2]);
  
  // Starting the server...
  Server amtedServer(server_ip, portno, 32);

  bzero((char *)&fds, sizeof(fds));

  // Setting up the initially poll to listen socket file descriptor.
  fds[0].fd = amtedServer.SocketFD();
  fds[0].events = POLLIN;
  fds[1].fd = threadFD[0];
  fds[1].events = POLLIN;
  // nfds = number of file descriptors we are polling for.
  nfds = 2;

  do {
    cout << "Starting to poll nfds: " << nfds << endl;
    cout << "Sockets are: ";
    for (int loop_var = 0; loop_var < nfds; ++loop_var) {
    	cout << fds[loop_var].fd << " ";
    }
    cout << endl;

    // This is the poll call.
    pollReturn = poll(fds, nfds, TIMEOUT);
    if(pollReturn < 0) {
      cout << "Poll failed.";
      break;
    } else if (pollReturn == 0) {
      cout << "Poll Timed out.";
      break;
    }

    old_nfds = nfds;
    for (i = 0; i < old_nfds; i++) {
      // This means that there is no event for this file descriptor;
    	if (fds[i].revents == 0) {
        continue;
      }

      // This means that there is an event on this file descriptor
      // So lets figure out what socket this is.
      if (fds[i].revents & POLLIN) {
        // This happens when the file descriptor is the socket that accepts
        // connections.
        if (fds[i].fd == amtedServer.SocketFD()) {
          // We accept all of the connections in the queue.
          do {
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
            socketid_to_pollfd[newFd] = nfds;
            fds[nfds++].events = POLLIN; 
          } while (newFd > 0);
        } // This corresponds to the accept socket.
        // This is if the file descriptor is the self-pipe. If we have an event
        // here, it means that a thread has finished reading.
        else if (fds[i].fd == threadFD[0]) {
          printf("A thread has finished. I'll send the file here."); 
          long socket_id;
          int fileFd;
          bool should_exit = false;
          do {
            // The working thread writes which socket it has done work for.
            read(threadFD[0], (void *) &socket_id, sizeof(long));
            if (errno == (EWOULDBLOCK | EAGAIN)) {
              cout << "No more threads ready.." << endl;
              errno = 0;
              should_exit = true;
            }
            fileFd = tp->FileContent(socket_id);
            // Send file contents or error message.
            if (fileFd == -1) {
              amtedServer.Write(socket_id, "File doesnt exist or is unavailable for reading.\n");
            } else {
              amtedServer.SendFile(socket_id, fileFd);
            }
            // Close the connection
            amtedServer.CloseConnection(socket_id);
            tp->CloseSocket(socket_id);

            printf("Removing fds for socket %ld\n" , socket_id);
            
            //fds[socketid_to_pollfd[socket_id]].fd = -1;
            for (int k = 0; k < old_nfds; ++k)
            {
            	if (fds[k].fd == (int)socket_id)
            	{
            		printf("Removing fds for socket %ld, k = %d\n" , socket_id,k);
            		fds[k].fd = -1;
            		break;
            	}
            }
          } while (!should_exit);
          printf("------------Leaving threadFD\n");
        } // This corresponds to the self pipe.
        // This else corresponds to some client writing to a socket (requesting
        // a file).
        else {
          cout << "Received event for fd: " << fds[i].fd <<endl;
          filenames[fds[i].fd] = amtedServer.Read(fds[i].fd);
          cout << "Received filename from :" << fds[i].fd << " filename: " << filenames[fds[i].fd] <<endl;
          // Dispatch a thread to read the file to memory.
          tp->Dispatch(filenames[fds[i].fd], fds[i].fd);
          // socketForThreadId[threadId] = fds[i].fd;
          // pollFdIndexForThreadId[threadId] = i;
        }
      } // This corresponds to the POLLIN if.
      else {
        // This means that some other unexpected event has happened
        // printf("%d, %d %d %d\n", nfds, fds[i].revents, fds[i].fd, i);
        unexpected = true;
        break;
      }
    } // Corresponds to for that goes through file descriptors.
    
    if (unexpected)
      break;

    // Removing closed connections.
    for (i = 0; i < nfds; i++)
    {
      if (fds[i].fd == -1)
      {
      	cout << "Removing someone: " << i << endl;
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
  for(i = 0; i < nfds; i++) {
    if(fds[i].fd >=0)
      close(fds[i].fd);
  }
  close(threadFD[0]);
  close(threadFD[1]);
  return 0; 
}
