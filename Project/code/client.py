#!/usr/bin/env python

import sys
sys.path.append('gen-py')
sys.path.append('gen-py/autoscale')
import time
import numpy as np
import pprint
import argparse
from thrift.transport import TTransport
from thrift.transport import TSocket
from thrift.transport import THttpClient
from thrift.protocol import TBinaryProtocol

from autoscale import LoadBalancer
from autoscale import Worker
from autoscale.ttypes import *
import threading

def request(lb_host, lb_port):
  try:
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

    lb_transport.close()
  except:
    print 'Request to LB dropped...'
    return

  try:
    node_socket = TSocket.TSocket(node_host, node_port)
    node_transport = TTransport.TBufferedTransport(node_socket)
    node_protocol = TBinaryProtocol.TBinaryProtocol(node_transport)
    node_client = Worker.Client(node_protocol)
    node_transport.open()

    #print 'Calling learn'
    #start = time.time()
    node_client.Test()
    #end = time.time()
    #print 'Learn took: ', end-start
    
    # print 'Calling predict'
    # start = time.time()
    # node_client.Predict(1, 'something')
    # end = time.time()
    # print 'Predict took: ', end-start
    
    node_transport.close()
  except:
    print 'Request to Node dropped..'


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-l', '--loadbalancer', required=True, help="Load LoadBalancer host in the format host::port")
  parser.add_argument('-p', '--load_pattern', required=True, type= int, help="1 for bell, 2 for step.")
  args = parser.parse_args()
  
  lb_port = 9090

  parts = args.loadbalancer.split(':')
  lb_host = parts[0]
  if len(parts) > 1:
    lb_port = int(parts[1])

  if args.load_pattern == 1:
    num_requests = [50]*10
    sigma = 340
    mu = 40
    bins = np.linspace(-420, 500, 520) 
    num_ranges = (1/(sigma * np.sqrt(2 * np.pi)) * np.exp( - (bins - mu)**2 / (2 * sigma**2)))*125000
    num_requests.extend(num_ranges)
    num_requests.extend([50]*10)
    #num_requests.extend(num_requests[:])
    #num_requests.extend(num_requests[:])
  elif args.load_pattern == 2:
    num_requests = [50]*20
    num_requests.extend([160]*80)
    num_requests.extend([50]*20)
    num_requests.extend(num_requests[:])
    num_requests.extend(num_requests[:])
  else:
    num_requests = [50]*10
    sigma = 340
    mu = 40
    bins = np.linspace(-420, 500, 520) 
    num_ranges = (1/(sigma * np.sqrt(2 * np.pi)) * np.exp( - (bins - mu)**2 / (2 * sigma**2)))*125000
    num_requests.extend(num_ranges)
    num_requests.extend([50]*10)
    num_requests.extend(num_requests[:])
    #num_requests.extend(num_requests[:])

  for times in num_requests:
    print int(times)
    start = time.time()
    for i in range(int(times)):
      t = threading.Thread(target=request, args=(lb_host,lb_port))
      t.start()
    end = time.time()
    time.sleep(1-(end-start))

