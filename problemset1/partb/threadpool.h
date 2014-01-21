#ifndef THREADPOOL_H
#define THREADPOOL_H
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
#define MAXBUF 1000000

class ThreadPool {
 public:
  static ThreadPool* GetInstance(int num_threads, int file_pointer);
  void Dispatch(std::string& filename, int socket_id);
  void Stop(int thread_id);
  // Returns the file descriptor.
  int FileContent(int thread_id);

  ~ThreadPool();
 private:
  // TODO: Why does this stuff need to be static?
  ThreadPool(int num_threads, int file_pointer);
  static void* Fun(void* threadid);
  static int file_pointer_;
  static std::vector<pthread_t> threads_;
  static std::vector<pthread_mutex_t> mutex_;
  static std::vector<pthread_cond_t> cond_;
  static std::vector<pthread_cond_t> cond2_;
  static std::vector<bool> working_;
  static std::vector<bool> can_dispatch_;
  static ThreadPool* instance_;
  static std::map<int, int> file_content_;
  static std::vector<std::string> file_to_read_;
  static std::vector<int> socket_to_write_;
  pthread_mutex_t dispatch_mutex_;
  int last_dispatched_;
  int num_threads_;
};


#endif  // THREADPOOL_H
