#ifndef SERVER_H
#define SERVER_H

#include <sys/socket.h>
#include <netinet/in.h>
#include <map>
#include <string>

using std::string;

//This is an abstraction over the basic server interface
class Server {
	public:
		// Starts the server, opens a socket at portno and starts to listen
		Server(string serverIPString, int portno, int queueLength);
		
		// Accepts a connection and returns acceptSockFD_ (accept socket FD)
		int Accept();
		string Read(int acceptSock);
		void Write(int acceptSock, string message);
		void CloseConnection(int acceptSock);
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
		void PrintError(std::string errorMsg);
};

#endif //SERVER_H