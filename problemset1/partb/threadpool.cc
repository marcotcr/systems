#include "threadpool.h"
#include <fcntl.h>
#include <pthread.h>
#include <algorithm>
using std::cout;
using std::endl;
using std::string;
using std::vector;
using std::unordered_map;

vector<pthread_t> ThreadPool::threads_;
vector<pthread_mutex_t> ThreadPool::mutex_;
vector<pthread_cond_t> ThreadPool::cond_;
vector<pthread_cond_t> ThreadPool::cond2_;
vector<bool> ThreadPool::working_;
vector<bool> ThreadPool::can_dispatch_;
vector<std::string> ThreadPool::file_to_read_;
vector<int> ThreadPool::socket_to_write_;
unordered_map<int, int> ThreadPool::file_content_;
ThreadPool* ThreadPool::instance_ = NULL;
int ThreadPool::pipe_descriptor_;

ThreadPool* ThreadPool::GetInstance(int num_threads, int file_pointer) {
  if (instance_ == NULL) {
    instance_ = new ThreadPool(num_threads, file_pointer);
  }
  return instance_;
}

void ThreadPool::Dispatch(std::string& filename, int socket_id) {
  pthread_mutex_lock(&dispatch_mutex_);
  int thread_id;
  for (int i = last_dispatched_;; ++i, i = i % num_threads_) {
    if (pthread_mutex_trylock(&mutex_[i]) == 0) {
      thread_id = i;
      last_dispatched_ = (i + 1) % num_threads_;
      break;
    }
  }
  while (!can_dispatch_[thread_id]) {
    pthread_cond_wait(&cond2_[thread_id], &mutex_[thread_id]);
  }
  file_to_read_[thread_id] = filename;
  socket_to_write_[thread_id] = socket_id;
  if (!working_[thread_id]) {
    pthread_cond_signal(&cond_[thread_id]);
  }
  working_[thread_id] = true;
  can_dispatch_[thread_id] = false;
  pthread_mutex_unlock(&mutex_[thread_id]);
  pthread_mutex_unlock(&dispatch_mutex_);
}

void ThreadPool::Stop(int thread_id) { 
  // I must wait for the thread to finish whatever work it's doing
  pthread_mutex_lock(&mutex_[thread_id]);
  while (!can_dispatch_[thread_id]) {
    pthread_cond_wait(&cond2_[thread_id], &mutex_[thread_id]);
  }
  pthread_cancel(threads_[thread_id]);
  pthread_mutex_unlock(&mutex_[thread_id]);
  pthread_mutex_destroy(&mutex_[thread_id]);
}

int ThreadPool::FileContent(int socket_id) {
  return file_content_[socket_id];
}
void ThreadPool::CloseSocket(int socket_id) {
  file_content_.erase(socket_id);
}
// Trims whitespace from end of string.
static inline std::string &trim(std::string &s) {
  s.erase(std::find_if(s.rbegin(), s.rend(), std::not1(std::ptr_fun<int, int>(std::isspace))).base(), s.end());
  return s;
}
void* ThreadPool::ThreadFunction(void* threadid) {
  long tid;
  tid = (long) threadid;
  while(true) {
    pthread_mutex_lock(&mutex_[tid]);
    while (!working_[tid]) {
      pthread_cond_wait(&cond_[tid], &mutex_[tid]);
    }
    long socket_id = socket_to_write_[tid];
    file_content_[socket_id] = open(trim(file_to_read_[tid]).c_str(), O_RDONLY);
    // printf("Hello, thread #%ld!\n", tid);
    // sleep(10);
    void* socket = (void*) socket_id;
    // Let self-pipe know I have the file descriptor.
    write(pipe_descriptor_, &socket, sizeof(long));
    working_[tid] = false;
    can_dispatch_[tid] = true;
    pthread_cond_signal(&cond2_[tid]);
    pthread_mutex_unlock(&mutex_[tid]);
    // printf("Bye\n");
  }
  pthread_exit(NULL);
}

ThreadPool::ThreadPool(int num_threads, int pipe_descriptor) {
  int return_code;
  last_dispatched_ = 0;
  num_threads_ = num_threads;
  threads_.resize(num_threads);
  mutex_.resize(num_threads);
  cond_.resize(num_threads);
  cond2_.resize(num_threads);
  working_.resize(num_threads);
  can_dispatch_.resize(num_threads);
  file_to_read_.resize(num_threads);
  socket_to_write_.resize(num_threads);
  pipe_descriptor_ = pipe_descriptor;
  pthread_attr_t attr;
  pthread_attr_init(&attr);
  pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);
  pthread_mutex_init(&dispatch_mutex_, NULL);
  for (long i = 0; i < num_threads; ++i) {
    pthread_mutex_init(&mutex_[i], NULL);
    pthread_cond_init (&cond_[i], NULL);
    pthread_cond_init (&cond2_[i], NULL);
    working_[i] = false;
    can_dispatch_[i] = true;
    return_code = pthread_create(&threads_[i], &attr, this->ThreadFunction, (void*)i);
    if (return_code){
      printf("ERROR; return code from pthread_create() is %d\n", return_code);
      exit(-1);
    }
  }
}
ThreadPool::~ThreadPool() {
}
