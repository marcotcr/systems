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
  def __init__(self, n_locks):
  # TODO: init from log file
    # TODO: think about this
    self.commands = [None for x in xrange(10000)]
    self.last_run_command = -1
    self.lock_machine = lock_machine.LockMachine(n_locks)
    self.acceptor = Acceptor()
    pass
 
  def Ping(self):
    print 'pinged'
    return 1
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
    

 
handler = PaxosHandler(5)
processor = Paxos.Processor(handler)
transport = TSocket.TServerSocket(port=8888)
tfactory = TTransport.TBufferedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()

#server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
 
 
print "Starting python server..."
server.serve()
print "done!"
