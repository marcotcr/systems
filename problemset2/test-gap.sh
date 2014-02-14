#!/bin/sh
# The scenario here is as follows:
# Instance 0 is chosen with Lock 1 1 
# Instance 1 is accepted in node 1 as Unlock 1 1, but not learned
# Instance 2 has no accepts
# Instance 3 is chosen as Lock 2 2
# node 0 (leader) dies
# node 1 (new leader) should get instance 1 accepted with unlock 1 1, and
# instance 2 as noop.
# Client comes up and executes Lock 1 2 (should not block)
# Client comes up and executes Lock 2 3 (should block)
# Client comes up and executes Unlock 2 2 (should unblock previous client)
python start_nodes.py -l 10 -n 3
# Node 0:
# Broker: 8887
# Paxos: 8888
# Node 1:
# Broker: 8886
# Paxos: 8889
# Node 2:
# Broker: 8885
# Paxos: 8890
sleep 1
./Broker-remote -h localhost:8887 Lock 1 1
./Paxos-remote -h localhost:8889 Propose 1 0 "0_0_Unlock 1 1"
./Paxos-remote -h localhost:8889 Learn 3 "0_3_Lock 2 2"
./Paxos-remote -h localhost:8890 Learn 3 "0_3_Lock 2 2"
./Broker-remote -h localhost:8887 Kill
python ping_nodes.py -l 10 -n 3 > /dev/null 2>/dev/null
echo "Now do the following:"
echo "./Broker-remote -h localhost:8886 Lock 1 2"
echo "(this should not block)"
echo "./Broker-remote -h localhost:8885 Lock 2 3"
echo "(this should block)"
echo "./Broker-remote -h localhost:8886 Unlock 2 2"
echo "(this should unblock the previous one)"
echo "python ping_nodes.py -l 10 -n 3 >/dev/null 2>/dev/null"
