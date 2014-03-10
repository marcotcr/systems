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
    self.n = 0
    pass

  def GetNode(self):
    # print 'GetNode'
    while True:
      try:
        node = np.random.choice(self.nodelist, p=self.probs)
        self.n += 1
        break
      except:
        pass
    return node
  def SetNodes(self, state):
    print 'SetNodes', state
    self.node_times = {}
    self.previous_state = state
    self.nodelist = []
    self.probs = []
    for node, quota in state.iteritems():
      self.nodelist.append(node)
      self.probs.append(float(quota))
    self.probs = np.array(self.probs)
    self.probs = (1 / self.probs) / sum(1 / self.probs)
    print 'Probs', self.probs
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
  
  # server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
  # server.setNumThreads(10)
  server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
   
   
  print "Starting python server..."
  server.serve()
  print "done!"
if __name__ == '__main__':
  main()
