# This is a blocking server, except for flush_all and set_multi. If it becomes a bottleneck, we would have to do it
# in C++, or use threading (even though we have the interpreter lock), or
# something. For now, I'm planning on using this instead of the single memcached
# server and see how it performs.
import sys
sys.path.append('gen-py/test')
 
import ParameterServer
from ttypes import *
 
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import collections
import socket
import time
 
class ParameterServerHandler:
  def __init__(self):
    self.params = collections.defaultdict(lambda:0.0)
 
  def flush_all(self):
    self.params = collections.defaultdict(lambda:0.0)
 
  def set_multi(self, params):
    """Receives a dict (key, value), where value is the delta to be added to
    the key"""
    for param, value in params.iteritems():
      self.params[param] += value
    print 'set_multi'
 
  def get_multi(self, params):
    print "get_multi"
    return dict([(x, self.params[x]) for x in params])
 
handler = ParameterServerHandler()
processor = ParameterServer.Processor(handler)
transport = TSocket.TServerSocket(port=8888)
tfactory = TTransport.TBufferedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()
 
server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
 
print "Starting python server..."
server.serve()
print "done!"
