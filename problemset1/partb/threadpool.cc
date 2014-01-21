#include "threadpool.h"
 #include <fcntl.h>
using std::cout;
using std::endl;
using std::string;
using std::vector;

void ReadFile(std::string& path, char return_[MAXBUF]) {
  FILE *fp = fopen(path.c_str(), "r");
  size_t len = 0;
  if (fp) {
    len = fread(return_, sizeof(char), MAXBUF, fp);
  }
  else { 
    strcpy(return_, "Error opening file. It might not exist\n");
  }
  if (len != 0) {
    return_[++len] = '\0';
  }
  // printf("%s\n", return_);
  fclose(fp); 
}
vector<pthread_t> ThreadPool::threads_;
vector<pthread_mutex_t> ThreadPool::mutex_;
vector<pthread_cond_t> ThreadPool::cond_;
vector<pthread_cond_t> ThreadPool::cond2_;
vector<bool> ThreadPool::working_;
vector<bool> ThreadPool::can_dispatch_;
vector<std::string> ThreadPool::file_to_read_;
vector<int> ThreadPool::file_content_;
ThreadPool* ThreadPool::instance_ = NULL;
int ThreadPool::file_pointer_;

ThreadPool* ThreadPool::GetInstance(int num_threads, int file_pointer) {
  if (instance_ == NULL) {
    instance_ = new ThreadPool(num_threads, file_pointer);
  }
  return instance_;
}

long ThreadPool::Dispatch(std::string& filename) {
  // TODO: I have to give the file name here somehow.

  pthread_mutex_lock(&dispatch_mutex_);
  int thread_id;
  for (int i = last_dispatched_;; ++i, i = i % num_threads_) {
    
    if (pthread_mutex_trylock(&mutex_[i]) == 0) {
      thread_id = i;
      last_dispatched_ = (i + 1) % num_threads_;
      break;
    }
  }
  // int thread_id = 5;
  // pthread_mutex_lock(&mutex_[thread_id]);
  while (!can_dispatch_[thread_id]) {
    //printf("Can't dispatch\n");
    pthread_cond_wait(&cond2_[thread_id], &mutex_[thread_id]);
  }
  //printf("Dispatching %d\n", thread_id);
  file_to_read_[thread_id] = filename;
  if (!working_[thread_id]) {
    pthread_cond_signal(&cond_[thread_id]);
  }
  working_[thread_id] = true;
  can_dispatch_[thread_id] = false;
  pthread_mutex_unlock(&mutex_[thread_id]);
  pthread_mutex_unlock(&dispatch_mutex_);
  return thread_id;
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

int ThreadPool::FileContent(int thread_id) {
  return file_content_[thread_id];
}
void* ThreadPool::Fun(void* threadid) {
  long tid;
  tid = (long) threadid;
  //printf("Oi %ld\n" , tid);
  while(true) {
    pthread_mutex_lock(&mutex_[tid]);
    // printf("Ola %ld\n", tid);
    while (!working_[tid]) {
      // printf("Not working %ld\n", tid);
      pthread_cond_wait(&cond_[tid], &mutex_[tid]);
    }
    // char file_contents[MAXBUF];
    //ReadFile(file_to_read_[tid], file_content_[tid]);
    file_content_[tid] = open(file_to_read_[tid].c_str(), O_RDONLY);
    printf("Hello, thread #%ld!\n", tid);
    write(file_pointer_, threadid, sizeof(long));
    sleep(3);
    working_[tid] = false;
    can_dispatch_[tid] = true;
    pthread_cond_signal(&cond2_[tid]);
    pthread_mutex_unlock(&mutex_[tid]);
  }
  pthread_exit(NULL);
}

ThreadPool::ThreadPool(int num_threads, int file_pointer) {
  int return_code;
  last_dispatched_ = 0;
  num_threads_ = num_threads;
  threads_.resize(num_threads);
  mutex_.resize(num_threads);
  cond_.resize(num_threads);
  cond2_.resize(num_threads);
  working_.resize(num_threads);
  can_dispatch_.resize(num_threads);
  file_content_.resize(num_threads);
  file_to_read_.resize(num_threads);
  file_pointer_ = file_pointer;
  pthread_attr_t attr;
  pthread_attr_init(&attr);
  pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);
  pthread_mutex_init(&dispatch_mutex_, NULL);
  for (long i = 0; i < num_threads; ++i) {
    pthread_mutex_init(&mutex_[i], NULL);
    // pthread_mutex_lock(&mutex_[i]);
    pthread_cond_init (&cond_[i], NULL);
    pthread_cond_init (&cond2_[i], NULL);
    //file_content_[i] = new char[MAXBUF];
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
    // delete file_content_[i];
  }
}


void *PrintHello(void *threadid) {
  long tid;
  tid = (long)threadid;
  printf("Hello World! It's me, thread #%ld!\n", tid);
  pthread_exit(NULL);
}

// int main (int argc, char ** argv) {
//   int num_threads = 2;
//   char buf[50];
//   // pthread_t threads[num_threads];
//   // int rc;
//   // long t;
//   // for(t=0; t<num_threads; t++){
//   //    printf("In main: creating thread %ld\n", t);
//   //    rc = pthread_create(&threads[t], NULL, PrintHello, (void *)t);
//   //    if (rc){
//   //      printf("ERROR; return code from pthread_create() is %d\n", rc);
//   //      exit(-1);
//   //    }
//   // }
//   ThreadPool* tp = ThreadPool::GetInstance(num_threads, 1);
//   string a = "Makefile";
//   string b = "df  erver.h";
//   printf("Dispatched %ld\n", tp->Dispatch(a));
//   printf("Dispatched %ld\n", tp->Dispatch(b));
//   // tp->Dispatch();
//   // tp->Dispatch();
//   // tp->Dispatch();
//   // tp->Dispatch();
//   // tp->Stop(0);
//   // tp->Stop(1);
//   // tp->Stop(2);
//   sleep(1);
//   printf("%d\n", tp->FileContent(0));
//   printf("%d\n", tp->FileContent(1));
//   // tp->Dispatch(3);
//   // tp->Dispatch(4);
// 
//    /* Last thing that main() should do */
//   pthread_exit(NULL);
// }
