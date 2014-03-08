from __future__ import division
import sys
sys.path.append('gen-py/autoscale')
sys.path.append('gen-py/')
 
import AutoScaler
import Worker
from autoscale.ttypes import *
from autoscale import AutoScaler
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
import threading

class Node:
  def __init__(self, address):
    self.name = address
    host, port = address.split(':')
    socket = TSocket.TSocket(host, int(port))
    self.transport = TTransport.TBufferedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
    self.client = Worker.Client(protocol)
    try:
      self.transport.open()
    except:
      pass
  def AvgPredictionTime(self):
    try:
      self.transport.open()
      return self.client.AvgPredictionTime()
    except:
      return -1

class AutoScaler:
  def __init__(self, load_balancer, possible_nodes):
    self.possible_nodes = possible_nodes
    self.nodes = []
    self.nodes.append(Node(self.possible_nodes[0]))
    self.load_balancer = load_balancer
    self.possible_nodes = possible_nodes
    self.stats = {}
    t = threading.Thread(target=self.LoadBalancerLoop)
    t.start()
    t2 = threading.Thread(target=self.NodesLoop)
    t2.start()

  def NodesLoop(self):
    while True:
      for node in self.nodes:
        self.stats[node.name] = node.AvgPredictionTime()
        # Failed node
        if self.stats[node.name] == -1:
          pass
        print 'Stats', node.name, self.stats[node.name]
      time.sleep(30)
  def SetStuff(self):
    self.load_balancer.SetNodes({node.name: '500' for node in self.nodes})
  def LoadBalancerLoop(self):
    while True:
      self.SetStuff()
      time.sleep(60)
    
def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-l', '--load_balancer', required=True, help="load balancer ip:port")
  parser.add_argument('-n', '--nodes', nargs='+', required=True,  help="list of nodes in the format ip:port")
  args = parser.parse_args()


  host, port = args.load_balancer.split(':')
  socket = TSocket.TSocket(host, int(port))
  transport = TTransport.TBufferedTransport(socket)
  protocol = TBinaryProtocol.TBinaryProtocol(transport)
  client = LoadBalancer.Client(protocol)
  transport.open()
  
  a = AutoScaler(client, args.nodes)

  print "done!"
if __name__ == '__main__':
  main()
