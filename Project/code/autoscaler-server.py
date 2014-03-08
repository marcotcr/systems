from __future__ import division
import sys
sys.path.append('gen-py/autoscale')
sys.path.append('gen-py/')
 
import AutoScaler
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
class AutoScalerHandler:
  def __init__(self, load_balancer):
    self.load_balancer = load_balancer
    t = threading.Thread(target=self.Loop)
    t.start()


  def HeartBeat(self, state):
    print 'Heartbeat'
    pass
  def SetStuff(self):
    self.load_balancer.SetNodes({'5:1' : '2', 'dum': '5'})
  def Loop(self):
    while True:
      self.SetStuff()
      time.sleep(20)
    
def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-p', '--port', type=int, required=True, help="My port")
  parser.add_argument('-l', '--load_balancer', required=True, help="load balancer ip:port")
  args = parser.parse_args()


  host, port = args.load_balancer.split(':')
  socket = TSocket.TSocket(host, int(port))
  transport = TTransport.TBufferedTransport(socket)
  protocol = TBinaryProtocol.TBinaryProtocol(transport)
  client = LoadBalancer.Client(protocol)
  transport.open()


  port = args.port
  handler = AutoScalerHandler(client)
  processor = AutoScaler.Processor(handler)
  transport = TSocket.TServerSocket(port=port)
  tfactory = TTransport.TBufferedTransportFactory()
  pfactory = TBinaryProtocol.TBinaryProtocolFactory()
  
  # server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
  # server.setNumThreads(2)
  server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
   
   
  print "Starting python server..."
  server.serve()
  print "done!"
if __name__ == '__main__':
  main()
