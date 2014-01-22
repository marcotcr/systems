#include "server.h"
#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <stdlib.h>
#include <sys/stat.h>
#include <string>
#include <vector>
#include <string.h>
#include <sys/wait.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/ioctl.h>
#include <sys/poll.h>
#include <signal.h>
#include <errno.h>
#ifndef __APPLE__
#include <sys/sendfile.h>
#endif

using std::string;

Server::Server(const std::string& serverIPString, int portno, int queueLength) {
	int on = 1;
	isSocketOpen_ = false;
	port_ = portno;
	sockFD_ = socket(AF_INET, SOCK_STREAM, 0);
	if (sockFD_ < 0) 
		PrintError("Failed to open socket.");
	isSocketOpen_ = true;
	in_addr_t serverIP = inet_addr(serverIPString.c_str());
	
	// Checking for invalid serverIP
	if (serverIP == INADDR_NONE) {
		PrintError("Server IP string is invalid.");
	}

	// Set the socket descriptor as reuseable, this is needed for non blocking calls.
	// Also helps with the "Address already in use" error messages after server restarts.
	if (setsockopt(sockFD_, SOL_SOCKET, SO_REUSEADDR, (char *)&on, sizeof(on)) < 0) {
		PrintError("Failed to allow socket descriptor to be reuseable");
	}

	// Set socket as non blocking.
	if (ioctl(sockFD_, FIONBIO, (char *)&on) < 0) {
		PrintError("Failed to set socket as non-blocking.");
	}

	// Setting server parameters
	bzero((char *) &server_addr_, sizeof(server_addr_));
	server_addr_.sin_family = AF_INET;
	server_addr_.sin_addr.s_addr = serverIP;
	server_addr_.sin_port = htons(port_);
	
	// Binding the server address to the socket file descriptor
	if (bind(sockFD_, (struct sockaddr *) &server_addr_, sizeof(server_addr_)) < 0)
		PrintError("Failed to bind socket file descriptor to server address");
	std::cout << "Server Started, listening for incoming connections at socket file descriptor: " << sockFD_ << std::endl;

	listen(sockFD_, queueLength);

	// Finally ignoring the SIGPIPE
	struct sigaction sa;
	sa.sa_handler = SIG_IGN;
	sa.sa_flags = 0;
	if (sigaction(SIGPIPE, &sa, 0) == -1)
		PrintError("Setting SIGPIPE to SIG_IGN failed.");
}

int Server::SocketFD() {
	return sockFD_;
}

int Server::Accept() {
	struct sockaddr_in client_addr;
	socklen_t clientLen = sizeof(client_addr);
	acceptSockFD_ = accept(sockFD_, (struct sockaddr *) &client_addr, &clientLen);
	if (acceptSockFD_ < 0)
		// EWOULDBLOCK would mean that there are no more connections on the socket
		// if that is the case, we dont want to error out.
		if (errno != EWOULDBLOCK) {
			PrintError("Failed to accept connection.");
		}
	return acceptSockFD_;
}

std::string Server::Read(int acceptSock) {
	bzero(buffer_,256);
	int n = read(acceptSock,buffer_,255);
	if (n < 0) {
		std::cerr<< "Failed to read from client."<< acceptSock << std::endl;
		CloseConnection(acceptSock);
	}
	return buffer_;
}

void Server::Write(int acceptSock, const std::string& message) {
	int n = write(acceptSock,message.c_str(),message.length());
	if (n < 0) {
		std::cerr<< "Failed to write to client."<< acceptSock << std::endl;
		CloseConnection(acceptSock);
	}
}

void Server::SendFile(int acceptSock, int fileDescriptor) {
	off_t offset = 0;
	struct stat fileStats;
	fstat(fileDescriptor, &fileStats);
	// the #ifdef is just to make sure that the code compiles properly
	// on my mac. The code would work properly on linux.
	#ifdef __APPLE__
	std::string message = "Mac architecture has issues with sendfile(). \n";
	write(acceptSock,message.c_str(),message.length());
	#else
	sendfile(acceptSock, fileDescriptor, &offset, fileStats.st_size);
	#endif
	close(fileDescriptor);
}

void Server::CloseConnection(int acceptSock) {
	close(acceptSock);
}

void Server::CloseServer() {
	close(sockFD_);	
}

void Server::PrintError(const std::string& errorMsg) {
	std::cerr << errorMsg <<std::endl;
	// If the accept connection socket is open, we need to close it in case of error.
	if (isSocketOpen_) {
		CloseServer();
	}
	exit(1);
}
