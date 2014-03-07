from __future__ import division
import sys
sys.path.append('gen-py/ml')
sys.path.append('gen-py/')
 
import MLEngine
from ml.ttypes import *
from ml import MLEngine
 
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
class MLEngineHandler:
  def __init__(self, prediction_time, learn_time):
    self.p_wait = prediction_time
    self.l_wait = learn_time
    self.prediction_time = 0
    self.counter = 0
    self.prediction_times = np.zeros(15)
    pass

  def Predict(self, id_, x):
    print 'Predict'
    a = time.time()
    time.sleep(self.p_wait)
    b = time.time()
    self.prediction_times[self.counter] = b - a
    self.counter = (self.counter + 1) % 15
    return 1
    pass
  def Learn(self, x, y):
    print 'Learn'
    pass
  def AvgPredictionTime(self):
    print 'AvgPredictionTime'
    return sum(self.prediction_times) / 15
  def Test(self):
    print 'Test'
    pass
    
def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-p', '--port', type=int, required=True, help="My port")
  args = parser.parse_args()

  port = args.port
  handler = MLEngineHandler(.5, .2)
  processor = MLEngine.Processor(handler)
  transport = TSocket.TServerSocket(port=port)
  tfactory = TTransport.TBufferedTransportFactory()
  pfactory = TBinaryProtocol.TBinaryProtocolFactory()
  
  server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
  #server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
   
   
  print "Starting python server..."
  server.serve()
  print "done!"
if __name__ == '__main__':
  main()
