service Broker {
  void Lock(1:i32 mutex, 2:i32 worker),
  void Unlock(1:i32 mutex, 2:i32 worker),
  void GotLock(1:i32 mutex, 2:i32 worker),
  void Kill()
}
