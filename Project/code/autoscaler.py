from __future__ import division
import sys
sys.path.append('gen-py/autoscale')
sys.path.append('gen-py/')
from itertools import cycle
 
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
    self.prediction_times = np.zeros(10)
    self.p_cycle = cycle(range(10))
    self.avg_prediction_time = 0
    self.is_down = False
    try:
      self.transport.open()
    except:
      self.is_down = True
  def AvgPredictionTime(self):
    try:
      self.transport.open()
      self.avg_prediction_time = self.client.AvgPredictionTime()
      self.is_down = False
      return self.avg_prediction_time
    except:
      self.is_down = True
      return -1
  def PingPrediction(self):
    a = time.time()
    try:
      self.transport.open()
      self.client.Predict(1, 'a')
      self.is_down = False
      b = time.time()
      self.prediction_times[self.p_cycle.next()] = b - a
    except:
      self.is_down = True
  def AvgPredictionLatency(self):
    return np.mean(self.prediction_times)
  def IsDown(self):
    return self.is_down

class NaiveStrategy:
  def __init__(self):
    pass
  def Start(self, autoscaler):
    # Start CHECK SLA loop
    t = threading.Thread(target=self.CheckSLALoop)
    pass
  def CheckSLALoop(self):
    while True:
      sleep(1)
  def NewState(self):
    # Maybe do a lock here. Think.
    return {}

class AutoScaler:
  def __init__(self, load_balancer, possible_nodes, SLA, strategy):
    self.possible_nodes = possible_nodes
    self.nodes = []
    self.nodes.append(Node(self.possible_nodes[0]))
    self.load_balancer = load_balancer
    self.possible_nodes = possible_nodes
    self.num_requests = [0] * 15
    self.previous_num_requests = 0
    self.SLA = SLA
    self.strategy = strategy
    self.strategy.Start(self)
    t = threading.Thread(target=self.LoadBalancerLoop)
    t.start()
    t2 = threading.Thread(target=self.AvgPredictionLoop)
    t2.start()
    t3 = threading.Thread(target=self.PredictionTimeLoop)
    t3.start()
    t4 = threading.Thread(target=self.NumRequestsLoop)
    t4.start()

  def AvgPredictionLoop(self):
    while True:
      for node in self.nodes:
        node.AvgPredictionTime()
        print 'Stats', node.name, node.avg_prediction_time
      time.sleep(30)
  def PredictionTimeLoop(self):
    while True:
      for node in self.nodes:
        node.PingPrediction()
        print 'Latency', node.AvgPredictionLatency()
      time.sleep(5)
  def SetStuff(self):
    self.load_balancer.SetNodes({'localhost:6666': '1', 'localhost:5555':'5'})
    self.load_balancer.SetNodes(self.strategy.NewState())
  def LoadBalancerLoop(self):
    while True:
      self.SetStuff()
      time.sleep(60)
  def NumRequestsLoop(self):
    while(True):
      num_requests = self.load_balancer.NumRequests()
      temp = num_requests - self.previous_num_requests
      self.previous_num_requests = num_requests
      self.num_requests.append(temp)
      self.num_requests.pop(0)
      print 'Requests:', self.num_requests
      time.sleep(5)

    
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
  
  SLA = .5
  a = AutoScaler(client, args.nodes, SLA)

  print "done!"
if __name__ == '__main__':
  main()
