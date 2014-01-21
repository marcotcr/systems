#ifndef THREADPOOL_H
#define THREADPOOL_H
#include <unordered_map>
#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <vector>
#include <string.h>
#include <sys/wait.h>
#include <pthread.h>
#include <stdlib.h>
#include <map>

class ThreadPool {
 public:
  static ThreadPool* GetInstance(int num_threads, int file_pointer);
  void Dispatch(std::string& filename, int socket_id);
  void Stop(int thread_id);
  // Returns the file descriptor.
  int FileContent(int socket_id);
  // Removes the file descriptor for socket_id from the map.
  void CloseSocket(int socket_id);

  ~ThreadPool();
 private:
  ThreadPool(int num_threads, int pipe_descriptor);
  static void* ThreadFunction(void* threadid);
  // File descriptor to the self-pipe
  static int pipe_descriptor_;
  static std::vector<pthread_t> threads_;
  static std::vector<pthread_mutex_t> mutex_;
  // Condition variable for thread to see if it can start working.
  static std::vector<pthread_cond_t> cond_;
  // Condition variable for threadpool to know if it can dispatch a thread.
  static std::vector<pthread_cond_t> cond2_;
  static std::vector<bool> working_;
  static std::vector<bool> can_dispatch_;
  static ThreadPool* instance_;
  // Pointer from socket id to file descriptor.
  static std::unordered_map<int, int> file_content_;
  // File name 
  static std::vector<std::string> file_to_read_;
  static std::vector<int> socket_to_write_;
  pthread_mutex_t dispatch_mutex_;
  int last_dispatched_;
  int num_threads_;
};


#endif  // THREADPOOL_H
