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
  def __init__(self, address, timeout=None):
    self.name = address
    host, port = address.split(':')
    socket = TSocket.TSocket(host, int(port))
    if timeout:
      socket.setTimeout(timeout)
    self.transport = TTransport.TBufferedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
    self.client = Worker.Client(protocol)
    self.avg_prediction_time = 0
    self.is_down = False
    try:
      self.transport.open()
    except:
      self.is_down = True
  def AvgPredictionTime(self):
    return self.avg_prediction_time
  def PingAvgPredictionTime(self):
    try:
      self.avg_prediction_time = self.client.AvgPredictionTime()
      self.is_down = False
      return self.avg_prediction_time
    except:
      try:
        self.transport.open()
      except:
        self.is_down = True
      return False
  def PingPrediction(self):
    a = time.time()
    try:
      self.client.Predict(1, 'a')
      self.is_down = False
      b = time.time()
      return b - a
    except:
      try:
        self.transport.open()
      except:
        self.is_down = True
      return False
  def IsDown(self):
    return self.is_down

class NaiveStrategy:
  def __init__(self):
    self.state_lock = threading.Lock()
    pass
  def Start(self, autoscaler):
    self.autoscaler = autoscaler
    self.nodes_to_include = []
    self.nodes_to_remove = []
    t = threading.Thread(target=self.CheckSLALoop)
    t.start()
    pass
  def StartNewNode(self):
    print 'Starting a new node'
    #TODO: I'm assuming a node starts instantly
    #time.sleep(30)
    self.state_lock.acquire()
    possible_nodes = [x for x in self.autoscaler.possible_nodes if x not in self.autoscaler.nodes]
    if not possible_nodes:
      print 'ERROR! Not enough available nodes'
      quit()
    print 'Possible nodes:', possible_nodes
    self.nodes_to_include.append(possible_nodes[0])
    self.state_lock.release()
    self.autoscaler.SetStuff()

  def StopNode(self):
    print 'Stopping node'
    if len(self.autoscaler.nodes) == 1:
      return
    self.state_lock.acquire()
    self.nodes_to_remove.append(self.autoscaler.nodes[-1])
    self.state_lock.release()
    self.autoscaler.SetStuff()

  def CheckSLALoop(self):
    while True:
      time.sleep(60)
      mean_time = np.mean(self.autoscaler.prediction_times)
      print 'CHECK mean time:', mean_time, 'SLA:', self.autoscaler.SLA
      if mean_time > self.autoscaler.SLA:
        self.StartNewNode()
      if mean_time and mean_time < self.autoscaler.SLA / 2: 
        self.StopNode()
  def NewState(self):
    self.state_lock.acquire()
    nodes = [x for x in self.autoscaler.nodes if not x.IsDown()]
    for node in self.nodes_to_include:
      nodes.append(node)
    if len(nodes) > 1:
      for node in self.nodes_to_remove:
        nodes.remove(node)
        if len(nodes) == 1:
          break
    self.nodes_to_include = []
    self.nodes_to_remove = []
    # print 'Nodes', nodes
    nodes = [x for x in nodes if not x.IsDown()]
    state = {x.name:str(x.AvgPredictionTime()) for x in nodes}
    self.state_lock.release()
    self.autoscaler.nodes = nodes
    return state

class AutoScaler:
  def __init__(self, load_balancer_client, load_balancer_address, possible_nodes, SLA, strategy):
    self.possible_nodes = [Node(x) for x in possible_nodes]
    for node in self.possible_nodes:
      for i in range(10):
        node.PingPrediction()
      node.PingAvgPredictionTime()
    for node in self.possible_nodes:
      if node.IsDown():
        print 'NODE ', node.name, ' IS DOWN! ERROR!'
        quit()
    print 'Starting...'
    self.nodes = []
    self.nodes.append(self.possible_nodes[0])
    # this load balancer is always open, to check for the number of requests and
    # change state
    self.load_balancer = load_balancer_client
    # start a new load balancer that we will open and close before checking
    # latency
    host, port = load_balancer_address.split(':')
    socket = TSocket.TSocket(host, int(port))
    socket.setTimeout(1000)
    self.transport = TTransport.TBufferedTransport(socket)
    protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
    self.load_balancer2 = LoadBalancer.Client(protocol)

    self.prediction_times = np.zeros(10) + SLA
    self.p_cycle = cycle(range(10))

    self.start_time = time.time()
    self.nodes_log = open('/tmp/nodes', 'w', 0)
    self.num_requests = [0] * 15
    self.previous_num_requests = 0
    self.SLA = SLA
    self.strategy = strategy
    self.strategy.Start(self)
    self.SetStuff()
    # t = threading.Thread(target=self.LoadBalancerLoop)
    # t.start()
    t2 = threading.Thread(target=self.AvgPredictionLoop)
    t2.start()
    t3 = threading.Thread(target=self.PredictionTimeLoop)
    t3.start()
    t4 = threading.Thread(target=self.NumRequestsLoop)
    t4.start()

  def AvgPredictionLoop(self):
    while True:
      for node in self.nodes:
        node.PingAvgPredictionTime()
        print 'Stats', node.name, node.avg_prediction_time
      time.sleep(30)
  def PredictionTimeLoop(self):
    file_ = open('/tmp/pred_time', 'w', 0)
    while True:
      start = time.time()
      self.transport.open()
      node_address = None
      try:
        node_address = self.load_balancer2.GetNode()
        self.transport.close()
      except:
        print 'Could not talk to load balancer!'
        # TODO: THink about timeout time
        self.prediction_times[self.p_cycle.next()] = 10
      if node_address:
        try:
          # TODO: Maybe this here should be SLA
          node = Node(node_address, timeout=1000)
          print 'Got node ', node.name, 
          if node.PingPrediction():
            prediction_time = time.time() - start
          else:
            prediction_time = 10
          self.prediction_times[self.p_cycle.next()] = prediction_time
          print 'Prediction_time', prediction_time
        except:
          print 'Timeout!'
          self.prediction_times[self.p_cycle.next()] = 10
      file_.write('%s %s %s\n' % (time.time() - self.start_time, np.mean(self.prediction_times), ','.join(map(str, self.prediction_times))))
      time.sleep(5)
  def SetStuff(self):
    # self.load_balancer.SetNodes({'localhost:6666': '1', 'localhost:5555':'5'})
    state = self.strategy.NewState()
    print 'New state:', state
    self.nodes_log.write('%s %s\n' % (time.time() - self.start_time, len(state)))
    self.load_balancer.SetNodes(state)
  def LoadBalancerLoop(self):
    while True:
      self.SetStuff()
      time.sleep(60)
  def NumRequestsLoop(self):
    out = open('/tmp/requests', 'w', 0)
    start_time = time.time()
    while(True):
      num_requests = self.load_balancer.NumRequests()
      temp = num_requests - self.previous_num_requests
      self.previous_num_requests = num_requests
      self.num_requests.append(temp)
      self.num_requests.pop(0)
      out.write('%s %s\n' % (time.time() - start_time, self.previous_num_requests))
      # print 'Requests:', self.num_requests
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
  
  SLA = 1
  strategy = NaiveStrategy()
  a = AutoScaler(client, args.load_balancer, args.nodes, SLA, strategy)

  print "done!"
if __name__ == '__main__':
  main()
