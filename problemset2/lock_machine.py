#!/usr/bin/python
import sys
import getopt
import collections
import os
import re

class LockMachine:
  def __init__(self, n):
    """Inits n mutexes"""
    self.mutexes = [None for x in xrange(n)]
    self.waiting = [[] for x in xrange(n)]
  def Lock(self, mutex, worker):
    """Returns True if lock was acquired, False otherwise"""
    if self.mutexes[mutex]:
      self.waiting[mutex].append(worker)
      return False
    else:
      self.mutexes[mutex] = worker
      return True
  def Unlock(self, mutex, worker):
    """Returns 0 if successful and no one has the lock, x if x now has the lock
    or -1 if failure"""
    if self.mutexes[mutex] != worker:
      return -1
    if self.waiting[mutex]:
      x = self.waiting[mutex].pop(0)
      self.mutexes[mutex] = x
      return x
    else:
      self.mutexes[mutex] = None
      return 0

def main():
  a = LockMachine(3)
  a.Lock(1, 2)
  print a.Unlock(1, 2)
  a.Lock(1, 3)
  a.Lock(1, 2)
  a.Lock(1, 1)

  print a.mutexes
  print a.waiting
  print a.Unlock(1,3)
  print a.mutexes
  print a.waiting
  
  pass
if __name__ == '__main__':
  main()
