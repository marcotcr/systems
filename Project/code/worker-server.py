from __future__ import division
import sys
sys.path.append('gen-py/autoscale')
sys.path.append('gen-py/')
 
import Worker
import AutoScaler
from autoscale.ttypes import *
from autoscale import Worker
 
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
class WorkerHandler:
  def __init__(self, prediction_time, learn_time, hist_instances):
    self.p_wait = prediction_time
    self.l_wait = learn_time
    self.prediction_time = 0
    self.counter = 0
    self.prediction_times_count = hist_instances
    self.prediction_times = np.zeros(self.prediction_times_count) + prediction_time
    self.a = 0
    pass

  def Predict(self, id_, x):
    print 'Predict'
    a = time.time()
    time.sleep(self.p_wait)
    b = time.time()
    self.prediction_times[self.counter] = b - a
    self.counter = (self.counter + 1) % self.prediction_times_count
    return 1
    pass
  def Learn(self, x, y):
    print 'Learn'
    pass
  def AvgPredictionTime(self):
    print 'AvgPredictionTime'
    return sum(self.prediction_times) / self.prediction_times_count
  def Test(self):
    # print 'Test'
    self.a += 1
    time.sleep(self.p_wait)
    if self.a % 1000 == 0:
      print self.a
    pass
    
def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-p', '--port', type=int, required=True, help="My port")
  args = parser.parse_args()

  port = args.port
  handler = WorkerHandler(.1, .2, 15)
  processor = Worker.Processor(handler)
  transport = TSocket.TServerSocket(port=port)
  tfactory = TTransport.TBufferedTransportFactory()
  pfactory = TBinaryProtocol.TBinaryProtocolFactory()
  
  server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
  server.setNumThreads(10)
  #server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
   
   
  print "Starting python server..."
  server.serve()
  print "done!"
if __name__ == '__main__':
  main()
