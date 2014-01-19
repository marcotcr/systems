#include <unistd.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <vector>
#include <string.h>
#include <sys/wait.h>
#include <pthread.h>
#include <stdlib.h>
#define MAXBUF 1000000
using std::cout;
using std::endl;
using std::string;
using std::vector;

void ReadFile(char* path, char return_[MAXBUF]) {
  FILE *fp = fopen(path, "r");
  size_t len = fread(return_, sizeof(char), MAXBUF, fp);
  if (len == 0) {
    // maybe return 1 here
    printf("ERROR READING FILE\n");
  }
  else {
    return_[++len] = '\0';
  }
  // printf("%s\n", return_);
  fclose(fp); 
}
class ThreadPool {
 public:
  static ThreadPool* GetInstance(int num_threads);
  void Dispatch(int thread_id);
  void Stop(int thread_id);
  ~ThreadPool();
  static vector<char*> file_content_;
 private:
  ThreadPool(int num_threads);
  static ThreadPool* instance_;
  static void* Fun(void* threadid);
  static vector<pthread_t> threads_;
  static vector<pthread_mutex_t> mutex_;
  static vector<pthread_cond_t> cond_;
  static vector<pthread_cond_t> cond2_;
  static vector<bool> working_;
  static vector<bool> can_dispatch_;
};
vector<pthread_t> ThreadPool::threads_;
vector<pthread_mutex_t> ThreadPool::mutex_;
vector<pthread_cond_t> ThreadPool::cond_;
vector<pthread_cond_t> ThreadPool::cond2_;
vector<bool> ThreadPool::working_;
vector<bool> ThreadPool::can_dispatch_;
vector<char*> ThreadPool::file_content_;
ThreadPool* ThreadPool::instance_ = NULL;

ThreadPool* ThreadPool::GetInstance(int num_threads) {
  if (instance_ == NULL) {
    instance_ = new ThreadPool(num_threads);
  }
  return instance_;
}
void ThreadPool::Stop(int thread_id) { 
  // I must wait for the thread to finish whatever work it's doing
  pthread_mutex_lock(&mutex_[thread_id]);
  while (!can_dispatch_[thread_id]) {
    printf("Can't kill %d\n", thread_id);
    pthread_cond_wait(&cond2_[thread_id], &mutex_[thread_id]);
  }
  printf("Killing %d\n", thread_id);
  pthread_cancel(threads_[thread_id]);
  pthread_mutex_unlock(&mutex_[thread_id]);
  pthread_mutex_destroy(&mutex_[thread_id]);
}
void ThreadPool::Dispatch(int thread_id) {
  pthread_mutex_lock(&mutex_[thread_id]);
  while (!can_dispatch_[thread_id]) {
    //printf("Can't dispatch\n");
    pthread_cond_wait(&cond2_[thread_id], &mutex_[thread_id]);
  }
  //printf("Dispatching %d\n", thread_id);
  if (!working_[thread_id]) {
    pthread_cond_signal(&cond_[thread_id]);
  }
  working_[thread_id] = true;
  can_dispatch_[thread_id] = false;
  pthread_mutex_unlock(&mutex_[thread_id]);
}
void* ThreadPool::Fun(void* threadid) {
  long tid;
  tid = (long) threadid;
  //printf("Oi %ld\n" , tid);
  while(true) {
    pthread_mutex_lock(&mutex_[tid]);
    printf("Ola %ld\n", tid);
    while (!working_[tid]) {
      // printf("Not working %ld\n", tid);
      pthread_cond_wait(&cond_[tid], &mutex_[tid]);
    }
    // char file_contents[MAXBUF];
    ReadFile("Makefile", file_content_[tid]);
    printf("Hello, thread #%ld!\n", tid);
    working_[tid] = false;
    can_dispatch_[tid] = true;
    pthread_cond_signal(&cond2_[tid]);
    pthread_mutex_unlock(&mutex_[tid]);
  }
  pthread_exit(NULL);
}

ThreadPool::ThreadPool(int num_threads) {
  int return_code;
  threads_.resize(num_threads);
  mutex_.resize(num_threads);
  cond_.resize(num_threads);
  cond2_.resize(num_threads);
  working_.resize(num_threads);
  can_dispatch_.resize(num_threads);
  file_content_.resize(num_threads);
  pthread_attr_t attr;
  pthread_attr_init(&attr);
  pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);
  for (long i = 0; i < num_threads; ++i) {
    pthread_mutex_init(&mutex_[i], NULL);
    // pthread_mutex_lock(&mutex_[i]);
    pthread_cond_init (&cond_[i], NULL);
    pthread_cond_init (&cond2_[i], NULL);
    file_content_[i] = new char[MAXBUF];
    working_[i] = false;
    can_dispatch_[i] = true;
    return_code = pthread_create(&threads_[i], &attr, this->Fun, (void*)i);
    if (return_code){
      printf("ERROR; return code from pthread_create() is %d\n", return_code);
      exit(-1);
    }
  }
}
ThreadPool::~ThreadPool() {
  for (int i = 0; i < file_content_.size(); ++i) {
    delete file_content_[i];
  }
}


void *PrintHello(void *threadid) {
  long tid;
  tid = (long)threadid;
  printf("Hello World! It's me, thread #%ld!\n", tid);
  pthread_exit(NULL);
}

int main (int argc, char ** argv) {
  int num_threads = 3;
  // pthread_t threads[num_threads];
  // int rc;
  // long t;
  // for(t=0; t<num_threads; t++){
  //    printf("In main: creating thread %ld\n", t);
  //    rc = pthread_create(&threads[t], NULL, PrintHello, (void *)t);
  //    if (rc){
  //      printf("ERROR; return code from pthread_create() is %d\n", rc);
  //      exit(-1);
  //    }
  // }
  ThreadPool* tp = ThreadPool::GetInstance(num_threads);
  tp->Dispatch(0);
  //tp->Dispatch(0);
  //tp->Dispatch(0);
  // tp->Dispatch(1);
  // tp->Dispatch(2);
  tp->Stop(0);
  tp->Stop(1);
  tp->Stop(2);
  sleep(1);
  printf("%s\n", ThreadPool::file_content_[0]);
  // tp->Dispatch(3);
  // tp->Dispatch(4);

   /* Last thing that main() should do */
   pthread_exit(NULL);
}
