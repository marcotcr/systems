# This is a blocking server, except for flush_all and set_multi. If it becomes a bottleneck, we would have to do it
# in C++, or use threading (even though we have the interpreter lock), or
# something. For now, I'm planning on using this instead of the single memcached
# server and see how it performs.
import sys
sys.path.append('gen-py/paxos')
 
import Paxos
from ttypes import *
 
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import collections
import socket
import time
import lock_machine
import argparse
import numpy as np
 

class Acceptor:
  def __init__(self):
    self.promised = [None for x in xrange(10000)]
    self.accepted = [None for x in xrange(10000)]
  def Propose(self, instance, proposal_number, value):
    if proposal_number >= self.promised[instance]:
      self.accepted[instance] = value
      return 0
    else:
      return self.promised[instance]

  def Prepare(self, instance, proposal_number):
    response = PrepareResponse()
    response.highest_prepared = self.promised[instance]
    if self.accepted[instance]:
      response.highest_accepted_value = self.accepted[instance]
    if proposal_number > self.promised[instance]:
      response.promised = True
      self.promised[instance] = proposal_number
    else:
      response.promised = False
    response.value_is_chosen = False
    return response
      
class PaxosHandler:
  def __init__(self, n_locks, my_id, nodes, leader):
  # TODO: init from log file
    # TODO: think about this
    self.commands = [None for x in xrange(10000)]
    self.last_run_command = -1
    self.lock_machine = lock_machine.LockMachine(n_locks)
    self.acceptor = Acceptor()
    self.leader = leader
    self.my_id = my_id
    self.nodes = nodes
    self.num_nodes = len(self.nodes.clients)
    self.majority = int(np.floor(self.num_nodes / 2)) + 1
    self.current_proposal_number = 0
    self.last_command = 0
    pass
 
  def Ping(self):
    print 'pinged'
    return 1

  def RunPhase2(self, instance, cmd):
    """Returns 0 if successful, or the number of the highest proposal number
    prepared by any acceptor."""
    nodes = range(self.num_nodes).remove(self.my_id)
    # asking my own acceptor
    responses = [self.acceptor.Propose(self.last_command + 1, self.current_proposal_number * 1000 + self.my_id, cmd)]
    while len(responses) < self.majority:
      node = np.random.choice(nodes)
      try:
        # This doesnt work with more than 1000 nodes
        responses.append(self.nodes.clients[node].Propose(self.last_command + 1, self.current_proposal_number * 1000 + self.my_id, cmd))
        # Whenever a node responds, I can remove it from the list of nodes
        # to be queried.
        nodes.remove(node)
      except:
        try:
          self.nodes.transports[node].open()
        except:
          pass
    responses = np.array(responses)    
    accepts = sum(responses == 0)
    if accepts >= self.majority:
      return 0
    else:
      return np.max(responses[responses != 0])

          
  def RunCommand(self, cmd_id, command):
    print 'Run Command', cmd_id, command
    if self.my_id == self.leader:
      #TODO: call runPhase2 with correct instance and cmd id
      pass
      # TODO:
      # 1. accepted: learn it, propagate to everyone else
      # 2. not accepted: learn new leader. forward this cmd to new leader.
    else:
      try:
        self.nodes.transports[self.leader].open()
        self.nodes.clients[self.leader].RunCommand(cmd_id, command)
      except:
        self.ElectNewLeader()
        #TODO: must still run this command!
    pass
    
  def ElectNewLeader(self):
    print 'ElectNewLeader'
    pass

  # This is all other people calling my acceptor.
  def Propose(self, instance, proposal_number, value):
    return self.acceptor.Propose(instance, proposal_number, value)
  def Prepare(self, instance, proposal_number):
    # If this instance already has a chosen value
    if self.commands[instance]:
      response = PrepareResponse()
      response.value_is_chosen = True
      response.highest_accepted_value = self.commands[instance]
    else:
      response = self.acceptor.Prepare(instance, proposal_number)
    return response
    
class Nodes:
  def __init__(self, node_list, my_id):
    """Node list has each node in the form ip:port"""
    self.transports = []
    self.clients = []
    self.sockets = []
    for i, node in enumerate(node_list):
      if i == my_id:
        self.transports.append(None)
        self.clients.append(None)
        continue
      host, port = node.split(':')
      socket = TSocket.TSocket(host, port)
      transport = TTransport.TBufferedTransport(socket)
      try:
        transport.open()
      except:
        pass
      protocol = TBinaryProtocol.TBinaryProtocol(transport)
      client = Paxos.Client(protocol)
      self.transports.append(transport)
      self.clients.append(client)
      self.sockets.append(socket)

def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-l', '--num_locks', dest='n_locks', required=True, help="Number of mutexes available", type=int)
  parser.add_argument('-i', '--my_id', type=int, required=True, help="This machine's ID (must be integer)")
  parser.add_argument('-n', '--nodes', required=True, dest='nodes', nargs = '+', help="all nodes in the form ip:port")
  # parser.add_argument('-e', '--error', default=0, type=float, dest='error', help="desired error rate")
  # parser.add_argument('-o', '--output', default='/dev/null', dest='output', help="output file, saving progress")
  args = parser.parse_args()
  nodes = Nodes(args.nodes, args.my_id) 
  port = int(args.nodes[args.my_id].split(':')[1])
  handler = PaxosHandler(args.n_locks, args.my_id, nodes, 0)
  processor = Paxos.Processor(handler)
  transport = TSocket.TServerSocket(port=port)
  tfactory = TTransport.TBufferedTransportFactory()
  pfactory = TBinaryProtocol.TBinaryProtocolFactory()
  
  #server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
  server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
   
   
  print "Starting python server..."
  server.serve()
  print "done!"
if __name__ == '__main__':
  main()
