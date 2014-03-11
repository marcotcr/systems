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
from scipy import stats
from scipy.stats import binom
from scipy.stats.distributions import  t
START_TIME = 0

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
    try:
      self.transport.open()
      self.is_down = False
    except:
      self.is_down = True
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

class PowerStrategy:
  def __init__(self, use_predictions=False):
    self.state_lock = threading.Lock()
    self.use_predictions = use_predictions
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
      # how many requests I can handle every minute
      power = self.autoscaler.PowerRequestsPerSecond() * 60
      # how many requests I got in the last minute
      last_requests = sum(self.autoscaler.num_requests)
      if self.use_predictions:
        x = range(1,13)
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, self.autoscaler.num_requests)
        prediction = sum([max(0, intercept + slope * x) for x in range(13,25)])
        last_requests = prediction
      print 'CHECK power:', power, 'prediction', prediction
      added_nodes = False
      while last_requests > power :
        self.StartNewNode()
        power = self.autoscaler.PowerRequestsPerSecond() * 60
        print 'new power:', power, 'last_requests', last_requests
        added_nodes = True
      if not added_nodes:
        power_last = ((1 / self.autoscaler.nodes[-1].AvgPredictionTime()) * 10) * 60
        print 'Last requests:', last_requests, 'Power without one node:', power - power_last
        while last_requests < power - power_last and len(self.autoscaler.nodes) > 1:
          self.StopNode()
          power = power - power_last
          power_last = (1 / self.autoscaler.nodes[-1].AvgPredictionTime()) * 10
        
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



class SmartStrategy:
  def __init__(self, alpha, beta, p_failure, use_predictions=False):
    self.use_predictions = use_predictions
    self.alpha = alpha
    self.beta = beta
    self.p_failure = p_failure
  def Start(self, autoscaler):
    self.autoscaler = autoscaler
    t = threading.Thread(target=self.CheckSLALoop)
    t.start()
    pass

  def ProbSLAViolation(self, n_nodes, power, requests):
    """Assumes that every node has power equal to the third parameter"""
    min_nodes = np.ceil(requests / power)
    return binom.cdf(min_nodes - 1, n_nodes, self.p_failure)

  def ExpectedCost(self, n_nodes, power, requests):
    return self.alpha * self.ProbSLAViolation(n_nodes, power, requests) + self.beta * n_nodes

  def CheckSLALoop(self):
    while True:
      time.sleep(60)
      self.autoscaler.SetStuff()
        
  def NewState(self):
    power = self.autoscaler.PowerRequestsPerSecond() * 60
    power_per_node = (power / len(self.autoscaler.nodes))
    # how many requests I got in the last minute
    last_requests = sum(self.autoscaler.num_requests)
    if self.use_predictions:
      x = range(1,13)
      slope, intercept, r_value, p_value, std_err = stats.linregress(x, self.autoscaler.num_requests)
      
      x = np.arange(1,13)
      y = np.array(self.autoscaler.num_requests)
      y_err = y - (intercept + slope * x)
      p_x = np.arange(13, 25)
      mean_x = np.mean(x) 
      alpha = 0.05
      n = len(x)
      t_ = t.ppf(1 - alpha / 2, n - 2)
      s_err = np.sum(np.power(y_err,2))
      confs = t_ * np.sqrt((s_err/(n-2))*(1.0/n + (np.power((p_x-mean_x),2)/
                    ((np.sum(np.power(x,2)))-n*(np.power(mean_x,2))))))
      p_y = slope*p_x+intercept
      lower = p_y - abs(confs)
      upper = p_y + abs(confs)

      prediction = sum([max(0, intercept + slope * x) for x in range(13,25)])
      print 'Last requests:', last_requests
      print 'Prediction: ', prediction, 'Upper:', sum(upper), 'Lower: ', sum(lower)
      # I'm being conservative here, and not decreasing the number of nodes
      # before the load goes down. I'm also using the upper bound of 95%
      # confidence interval.
      last_requests = max(upper, last_requests)
      # last_requests = max(prediction, last_requests)



    print 'Current power:', power, 'requests to handle:', prediction
    min_cost = sys.maxint
    n_nodes = 1
    nodes = [x for x in self.autoscaler.possible_nodes if not x.IsDown()]
    for i in range(1, len(nodes) + 1):
      cost = self.ExpectedCost(i, power_per_node, last_requests)
      print i, 'nodes, P(SLA): ', self.ProbSLAViolation(i, power_per_node, last_requests), 
      print 'cost:', cost
      if cost < min_cost:
        min_cost, n_nodes = cost, i
    nodes = nodes[:n_nodes]
    state = {x.name:str(x.AvgPredictionTime()) for x in nodes}
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
    self.num_requests = [0] * 12
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

  def PowerRequestsPerSecond(self):
    """Return how many requests I could handle per second if none of my nodes
    fail"""
    power = 0
    for node in self.nodes:
      power += (1 / node.AvgPredictionTime()) * 10 # assuming 10 worker threads
    return power

  def AvgPredictionLoop(self):
    while True:
      for node in self.nodes:
        node.PingAvgPredictionTime()
        print 'Stats', node.name, node.avg_prediction_time
      time.sleep(30)
  def PredictionTimeLoop(self):
    file_ = open('/tmp/pred_time', 'w', 0)
    global START_TIME
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
      file_.write('%s %s %s\n' % (time.time() - START_TIME, np.mean(self.prediction_times), ','.join(map(str, self.prediction_times))))
      time.sleep(5)
  def SetStuff(self):
    global START_TIME
    # self.load_balancer.SetNodes({'localhost:6666': '1', 'localhost:5555':'5'})
    state = self.strategy.NewState()
    print 'New state:', state
    self.nodes_log.write('%s %s\n' % (time.time() - START_TIME, len(state)))
    self.load_balancer.SetNodes(state)
  def LoadBalancerLoop(self):
    while True:
      self.SetStuff()
      time.sleep(60)
  def NumRequestsLoop(self):
    global START_TIME
    out = open('/tmp/requests', 'w', 0)
    out2 = open('/tmp/regression', 'w', 0)
    while(True):
      num_requests = self.load_balancer.NumRequests()
      temp = num_requests - self.previous_num_requests
      x = range(1,13)
      slope, intercept, r_value, p_value, std_err = stats.linregress(x, self.num_requests)
      print self.num_requests, slope, intercept

      self.previous_num_requests = num_requests
      self.num_requests.append(temp)
      self.num_requests.pop(0)
      out.write('%s %s\n' % (time.time() - START_TIME, self.previous_num_requests))
      out2.write('True: %s Predicted: %s r: %s p: %s stderr:%s\n' % (temp, intercept + slope * 11, r_value, p_value, std_err))

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
  global START_TIME
  strategy = SmartStrategy(2, .5, .9, use_predictions= True)
  START_TIME = time.time()
  a = AutoScaler(client, args.load_balancer, args.nodes, SLA, strategy)

  print "done!"
if __name__ == '__main__':
  main()
