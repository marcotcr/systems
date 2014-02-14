import sys
sys.path.append('gen-py/broker')
sys.path.append('gen-py/')
 
import Broker
from paxos.ttypes import *
from paxos import Paxos
 
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import collections
import socket
import time
import argparse
import numpy as np
import os
from threading import Condition
import threading
class BrokerHandler:
  def __init__(self, n_locks, my_id, paxos):
    self.my_id = my_id
    self.n_locks = n_locks
    self.paxos = paxos
    self.counter_lock = threading.Lock()
    self.locks = [None for x in xrange(n_locks)]
    self.conds = [threading.Condition() for x in xrange(n_locks)]
    self.queue = [0 for x in xrange(n_locks)]
    self.command_id = 0

  def Lock(self, mutex, worker):
    cmd = 'Lock %d %d' % (mutex, worker)
    print self.command_id, self.my_id, cmd
    sys.stdout.flush()
    self.counter_lock.acquire()
    self.paxos.RunCommand(self.command_id, self.my_id, cmd)
    self.command_id += 1
    self.counter_lock.release()
    self.conds[mutex].acquire()
    self.queue[mutex] += 1
    while self.locks[mutex] != worker:
      self.conds[mutex].wait()
    self.queue[mutex] -= 1
    self.locks[mutex] = None
    self.conds[mutex].release()

  def Unlock(self, mutex, worker):
    cmd = 'Unlock %d %d' % (mutex, worker)
    print self.command_id, self.my_id, cmd
    sys.stdout.flush()
    self.counter_lock.acquire()
    self.paxos.RunCommand(self.command_id, self.my_id, cmd)
    self.command_id += 1
    self.counter_lock.release()

  def GotLock(self, mutex, worker):
    print 'GotLock', mutex, worker
    sys.stdout.flush()
    self.conds[mutex].acquire()
    if self.queue[mutex] > 0:
      self.locks[mutex] = worker
      self.conds[mutex].notify()
    self.conds[mutex].release()
  def Kill(self):
    self.paxos.Kill()
    sys.stdout.flush()
    os._exit(0)
    
class PaxosClient:
  """Encapsulates paxos client"""
  def __init__(self, host, port):
    socket = TSocket.TSocket(host, port)
    self.transport = TTransport.TBufferedTransport(socket)
    try:
      self.transport.open()
    except:
      pass
    protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
    self.client = Paxos.Client(protocol)
  def RunCommand(self, command_id, my_id, cmd):
    while True:
      try:
        self.client.RunCommand(command_id, my_id, cmd)
        break
      except:
        self.transport.open()

  def Kill(self):
    try:
      self.client.Kill()
    except:
      pass
    
    

def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-l', '--num_locks', dest='n_locks', required=True, help="Number of mutexes available", type=int)
  parser.add_argument('-p', '--paxos', required=True, help="paxos handler's ip:port")
  parser.add_argument('-m', '--myport', type=int, required=True, help="My port")
  parser.add_argument('-i', '--my_id', type=int, required=True, help="My id")
  # parser.add_argument('-o', '--output', default='/dev/null', dest='output', help="output file, saving progress")
  args = parser.parse_args()
  # paxos
  paxos_host, paxos_port = args.paxos.split(':')
  paxos = PaxosClient(paxos_host, int(paxos_port))

  port = args.myport
  handler = BrokerHandler(args.n_locks, args.my_id, paxos)
  processor = Broker.Processor(handler)
  transport = TSocket.TServerSocket(port=port)
  tfactory = TTransport.TBufferedTransportFactory()
  pfactory = TBinaryProtocol.TBinaryProtocolFactory()
  
  #server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
  server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
   
   
  print "Starting python server..."
  server.serve()
  print "done!"
if __name__ == '__main__':
  main()
