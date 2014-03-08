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
class LoadBalancerHandler:
  def __init__(self):
    self.node_quotas = {}
    self.nodelist = []
    self.current_node = 0
    self.n = 0
    pass

  def GetNode(self):
    print 'GetNode'
    if not self.nodelist:
      self.SetNodes(self.previous_state)
    return_ = self.nodelist[self.current_node]
    self.node_quotas[return_] -= 1
    if self.node_quotas[return_] == 0:
      self.nodelist.remove(return_)
      if self.nodelist:
        self.current_node = self.current_node % len(self.nodelist)
    else:
      self.current_node = (self.current_node + 1) % len(self.nodelist)
    self.n += 1
    return return_
  def SetNodes(self, state):
    print 'SetNodes', state
    self.node_quotas = {}
    self.previous_state = state
    for node, quota in state.iteritems():
      self.node_quotas[node] = int(quota)
    self.nodelist = self.node_quotas.keys()
    self.current_node = 0
  def NumRequests(self):
    return self.n
    print 'SetNodes', state
    
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
