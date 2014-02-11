# This is a blocking server, except for flush_all and set_multi. If it becomes a bottleneck, we would have to do it
# in C++, or use threading (even though we have the interpreter lock), or
# something. For now, I'm planning on using this instead of the single memcached
# server and see how it performs.
import sys
sys.path.append('gen-py')
sys.path.append('gen-py/paxos')
 
import Paxos
from broker import Broker
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
    self.highest_accepted = -1
    self.future_promise = (10001, -1)
  def Propose(self, instance, proposal_number, value):
    if instance >= self.future_promise[0] and proposal_number < self.future_promise[1]:
      return self.future_promise[1]
    if proposal_number >= self.promised[instance]:
      self.accepted[instance] = value
      self.highest_accepted = max(self.highest_accepted, instance)
      return 0
    else:
      return self.promised[instance]

  def Prepare(self, instance, proposal_number):
    response = PrepareResponse()
    if self.accepted[instance]:
      response.highest_accepted_value = self.accepted[instance]
    if instance >= self.future_promise[0]:
      if proposal_number > max(self.future_promise[1],self.promised[instance]):
        response.promised = True
        self.promised[instance] = proposal_number
      else:
        response.promised = False
        response.highest_prepared = max(self.future_promise[1], self.promised[instance])
    else:
      response.highest_prepared = self.promised[instance]
      if proposal_number > self.promised[instance]:
        response.promised = True
        self.promised[instance] = proposal_number
      else:
        response.promised = False
    response.value_is_chosen = False
    return response
  def PrepareFuture(self, instance, proposal_number):
    print 'Prepare Future', instance, proposal_number
    return_ = PrepareFutureResponse(accepted=[], values=[])
    if proposal_number < self.future_promise[1]:
      return_.promised = False
      return_.highest_prepared = self.future_promise[1]
      return return_
    return_.promised = True
    for i in range(self.future_promise[0], instance):
      self.promised[i] = self.future_promise[1]
    self.future_promise = (instance, proposal_number)
    for i in range(instance, self.highest_accepted + 1):
      if self.accepted[i]:
        return_.accepted.append(i)
        return_.values.append(self.accepted[i])
    print return_
    return return_

      
class PaxosHandler:
  def __init__(self, n_locks, my_id, nodes, leader, broker):
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
    self.broker = broker
 
  def Ping(self):
    print 'pinged'
    return 1

  def Learn(self, instance, cmd):
    print 'Learn', instance, cmd
    self.commands[instance] = cmd
    if instance == self.last_run_command + 1:
      self.last_run_command += 1
      cmd_id, node_id, cmd = cmd.split('_')
      node_id = int(node_id)
      cmd_id = int(cmd_id)
      command, mutex, worker = cmd.split(' ')
      if command == 'noop':
        pass
      elif command == 'Lock':
        locked = self.lock_machine.Lock(int(mutex), int(worker))
        print locked, mutex, worker
        if locked:
          self.broker.GotLock(int(mutex), int(worker))
      elif command == 'Unlock':
        response = self.lock_machine.Unlock(int(mutex), int(worker))
        #TODO: Upcall: unlock
        if response > 0:
          self.broker.GotLock(int(mutex), response)
  def RunPhase2(self, instance, cmd):
    """Returns 0 if successful, or the number of the highest proposal number
    prepared by any acceptor."""
    print 'RunPhase2'
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

          
  def RunCommand(self, cmd_id, node_id, command):
    # Command here is in the form:
    # Lock 1 2
    # Unlock 2 3
    print 'Run Command', cmd_id, node_id, command
    full_command = str(cmd_id) + '_' + str(node_id) + '_' + command
    if self.my_id == self.leader:
      #TODO: call runPhase2 with correct instance and cmd id
      #chosen = self.RunPhase2(self.last_run_command + 1, full_command)
      chosen = 0
      # This value was chosen
      if chosen == 0:
        self.Learn(self.last_run_command + 1, full_command)
        for i in range(self.num_nodes):
          if i != self.my_id:
            try:
              self.nodes.transports[i].open()
              self.nodes.clients[i].Learn(self.last_run_command, full_command)
            except:
              print sys.exc_info()[0]
              print 'Exception learning'
              pass
      else:
        #TODO: I am not the leader anymore, must learn new leader and etc.
        pass
    else:
      try:
        self.nodes.transports[self.leader].open()
        self.nodes.clients[self.leader].RunCommand(cmd_id, node_id, command)
      except:
        self.ElectNewLeader()
        #TODO: must still run this command!
    pass
    
  def ElectNewLeader(self):
    print 'ElectNewLeader'
    pass

  # This is all other people calling my acceptor.
  def Propose(self, instance, proposal_number, value):
    print 'Propose'
    return self.acceptor.Propose(instance, proposal_number, value)
  def Prepare(self, instance, proposal_number):
    print 'Prepare'
    # If this instance already has a chosen value
    if self.commands[instance]:
      response = PrepareResponse()
      response.value_is_chosen = True
      response.highest_accepted_value = self.commands[instance]
    else:
      response = self.acceptor.Prepare(instance, proposal_number)
    return response
  def PrepareFuture(self, instance, proposal_number):
    return self.acceptor.PrepareFuture(instance, proposal_number)
    
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

class BrokerClient:
  """Encapsulates paxos client"""
  def __init__(self, host, port):
    socket = TSocket.TSocket(host, port)
    self.transport = TTransport.TBufferedTransport(socket)
    try:
      self.transport.open()
    except:
      pass
    protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
    self.client = Broker.Client(protocol)
  def GotLock(self, mutex, worker):
    while True:
      print 'Trying broker'
      try:
        self.client.GotLock(mutex, worker)
        break
      except:
        self.transport.open()

def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-l', '--num_locks', dest='n_locks', required=True, help="Number of mutexes available", type=int)
  parser.add_argument('-i', '--my_id', type=int, required=True, help="This machine's ID (must be integer)")
  parser.add_argument('-n', '--nodes', required=True, dest='nodes', nargs = '+', help="all nodes in the form ip:port")
  parser.add_argument('-b', '--broker', required=True, help="broker handler's ip:port")
  # parser.add_argument('-e', '--error', default=0, type=float, dest='error', help="desired error rate")
  # parser.add_argument('-o', '--output', default='/dev/null', dest='output', help="output file, saving progress")
  args = parser.parse_args()
  nodes = Nodes(args.nodes, args.my_id) 
  port = int(args.nodes[args.my_id].split(':')[1])

  broker_host, broker_port = args.broker.split(':')
  broker = BrokerClient(broker_host, int(broker_port))

  handler = PaxosHandler(args.n_locks, args.my_id, nodes, 0, broker)
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
