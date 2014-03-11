import os
import sys
import argparse
import time
parser = argparse.ArgumentParser(description='TODO')
parser.add_argument('-a', '--alpha',type=float, required=False, help="Alpha")
parser.add_argument('-b', '--beta', type=float, required=False, help="beta")
parser.add_argument('-t', '--prediction_time', type=float, required=True, help="Amount of time the prediction step should take")
parser.add_argument('-s', '--strategy', required=True, help="n for naive, p for power, s for smart")
parser.add_argument('-p', '--p_fail', type=float, required=False, help="probability of node failing")
parser.add_argument('-u', '--use_predictions', required=False, type=bool, default=True, help="Using predictions. Default=false")
parser.add_argument('-n', '--num_nodes', required=True, type=int, default=True, help="number of nodes")
args = parser.parse_args()
if args.strategy == 's' and (not args.alpha or not args.beta):
  print 'Alpha and beta required for smart strategy' 
  quit()

all_workers = range(8888, 8888 + args.num_nodes)
for i in xrange(args.num_nodes):
  cmd = 'python worker-server.py -p %s -t %s >/dev/null &' % (all_workers[i], args.prediction_time)
  print cmd
  os.system(cmd)
cmd = 'python loadbalancer2-server.py -p 7777 >/tmp/loadbalancer &'
print cmd
os.system(cmd)
time.sleep(1)
nodes = ['localhost:%s' % w for w in all_workers]
nodes = ' '.join(nodes)
cmd = 'python autoscaler.py -l localhost:7777 -n %s -s %s' % (nodes, args.strategy)
if args.use_predictions:
  cmd += ' -u True'
if args.strategy == 's':
  cmd += ' -a %s -b %s -p %s' % (args.alpha, args.beta, args.p_fail)
cmd += ' > /tmp/autoscaler &'
print cmd
os.system(cmd)
time.sleep(60)
cmd = 'python client.py -l localhost:7777 >/tmp/clientz &'
print cmd
os.system(cmd)
