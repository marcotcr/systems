from __future__ import division
import sys
sys.path.append('gen-py/autoscale')
sys.path.append('gen-py/')
 
import LoadBalancer
from autoscale.ttypes import *
from autoscale import LoadBalancer
 
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
import random
import threading
from itertools import cycle
class LoadBalancerHandler:
  def __init__(self):
    self.node_times = {}
    self.nodelist = []
    self.n_cycle = cycle(range(0))
    self.n = 0
    self.n_threads = 10
    pass

  def Finish(self, node):
    time.sleep(self.node_times[node])
    self.n_running[node] -= 1
  def GetNode(self):
    # print 'GetNode'
    node = self.nodelist[self.n_cycle.next()]
    while self.n_running[node] >= self.n_threads:
      node = self.nodelist[self.n_cycle.next()]
    self.n_running[node] += 1
    self.n += 1
    t = threading.Thread(target=self.Finish, args=(node,))
    t.start()
    return node
  def SetNodes(self, state):
    print 'SetNodes', state
    self.node_times = {}
    self.previous_state = state
    for node, quota in state.iteritems():
      self.node_times[node] = float(quota)
    self.nodelist = self.node_times.keys()
    self.n_running = collections.defaultdict(lambda: 0)
    self.n_cycle = cycle(range(len(self.nodelist)))
  def NumRequests(self):
    return self.n
    
def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-p', '--port', type=int, required=True, help="My port")
  args = parser.parse_args()

  port = args.port
  handler = LoadBalancerHandler()
  processor = LoadBalancer.Processor(handler)
  transport = TSocket.TServerSocket(port=port)
  tfactory = TTransport.TBufferedTransportFactory()
  pfactory = TBinaryProtocol.TBinaryProtocolFactory()
  
  server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
  server.setNumThreads(10)
  # server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
   
   
  print "Starting python server..."
  server.serve()
  print "done!"
if __name__ == '__main__':
  main()
