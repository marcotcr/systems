#!/usr/bin/env python

import sys
sys.path.append('gen-py')
sys.path.append('gen-py/autoscale')
import time

import pprint
import argparse
from thrift.transport import TTransport
from thrift.transport import TSocket
from thrift.transport import THttpClient
from thrift.protocol import TBinaryProtocol

from autoscale import LoadBalancer
from autoscale import Worker
from autoscale.ttypes import *

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-l', '--loadbalancer', required=True, help="Load LoadBalancer host in the format host::port")
  parser.add_argument('-t', '--times', type=int, required=True, help="number of times you want this run")
  args = parser.parse_args()
  
  lb_port = 9090

  parts = args.loadbalancer.split(':')
  lb_host = parts[0]
  if len(parts) > 1:
    lb_port = int(parts[1])

  for i in range(args.times):
    lb_socket = TSocket.TSocket(lb_host, lb_port)
    lb_transport = TTransport.TBufferedTransport(lb_socket)
    lb_protocol = TBinaryProtocol.TBinaryProtocol(lb_transport)
    lb_client = LoadBalancer.Client(lb_protocol)
    lb_transport.open()
    
    node_port = 9090
    node = lb_client.GetNode()

    node_parts = node.split(':')
    node_host = node_parts[0]
    if len(node_parts) > 1:
      node_port = int(node_parts[1])

    node_socket = TSocket.TSocket(node_host, node_port)
    node_transport = TTransport.TBufferedTransport(node_socket)
    node_protocol = TBinaryProtocol.TBinaryProtocol(node_transport)
    node_client = Worker.Client(node_protocol)
    node_transport.open()

    print 'Calling learn'
    start = time.time()
    node_client.Test()
    end = time.time()
    print 'Learn took: ', end-start
    
    # print 'Calling predict'
    # start = time.time()
    # node_client.Predict(1, 'something')
    # end = time.time()
    # print 'Predict took: ', end-start
    
    node_transport.close()
    lb_transport.close()
