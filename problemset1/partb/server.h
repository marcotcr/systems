#ifndef SERVER_H
#define SERVER_H

#include <sys/socket.h>
#include <netinet/in.h>
#include <map>
#include <string>

//This is an abstraction over the basic server interface
class Server {
 public:
  // Starts the server, opens a socket at portno and starts to listen
  Server(const std::string& serverIPString, int portno, int queueLength);
  
  // Accepts a connection and returns acceptSockFD_ (accept socket FD)
  int Accept();
  std::string Read(int acceptSock);
  // Sends a string of data to the client.
  void Write(int acceptSock, const std::string& message);
  // Close Client connection.
  void CloseConnection(int acceptSock);
  // Sends a file to the client using the sendfile system call.
  void SendFile(int acceptSock, int fileDescriptor);
  // Shuts down the server
  void CloseServer();
  // Returns the socket handle
  int SocketFD();
 private:
  bool isSocketOpen_;
  int sockFD_, acceptSockFD_, port_;
  socklen_t clientLen_;
  char buffer_[256];
  struct sockaddr_in server_addr_;
  struct sockaddr_in client_addr_;
  // This is private method to handle error and bail out.
  void PrintError(const std::string& errorMsg);
};

#endif //SERVER_H
