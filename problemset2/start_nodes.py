#!/usr/bin/env python
import argparse
import os
def main():
  parser = argparse.ArgumentParser(description='TODO')
  parser.add_argument('-l', '--num_locks', required=True, help="Number of mutexes available", type=int)
  parser.add_argument('-n', '--num_nodes', type=int, required=True, help="number of nodes to run")
  args = parser.parse_args()
  all_paxos = range(8888, 8888+ args.num_nodes)
  all_broker = range(8887, 8887- args.num_nodes, -1)
  for i in xrange(args.num_nodes):
    cmd = 'python paxo.py -l %d -i %d -n %s -b localhost:%d > /tmp/paxos%d &'  % (args.num_locks, i,
        ' '.join(['localhost:%d' % x for x in all_paxos]), all_broker[i], i)
    os.system(cmd)
    cmd = 'python broker.py -l %d -p localhost:%d -m %d -i %d > /tmp/broker%d &' % (args.num_locks,
    all_paxos[i], all_broker[i], i, i)
    print 'Node %d:' % i
    print 'Broker: %d' % all_broker[i]
    print 'Paxos: %d' % all_paxos[i]
    os.system(cmd)
  quit()
    
  # paxos
  paxos_host, paxos_port = args.paxos.split(':')
  paxos = PaxosClient(paxos_host, int(paxos_port))

  port = args.myport
  handler = BrokerHandler(args.n_locks, args.my_id, paxos)
  processor = Broker.Processor(handler)
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
