#!/bin/sh
python start_nodes.py -l 10 -n 5
# Node 0:
# Broker: 8887
# Paxos: 8888
# Node 1:
# Broker: 8886
# Paxos: 8889
# Node 2:
# Broker: 8885
# Paxos: 8890
# Node 3:
# Broker: 8884
# Paxos: 8891
# Node 4:
# Broker: 8883
# Paxos: 8892
sleep 1
./Broker-remote -h localhost:8887 Lock 0 1
./Broker-remote -h localhost:8887 Unlock 0 1
./Broker-remote -h localhost:8887 Lock 1 1
./Broker-remote -h localhost:8887 Kill
# At this point, 1 becomes the new leader
./Broker-remote -h localhost:8885 Unlock 1 1
./Broker-remote -h localhost:8885 Lock 1 2
./Broker-remote -h localhost:8886 Kill
# At this point, 2 becomes the new leader
python ping_nodes.py -l 10 -n 5 > /dev/null 2>/dev/null
echo "Now lock 1 3 and then unlock 1 2 on 8883 and 8884"
echo "lock 1 3 should block"
echo "./Broker-remote -h localhost:8883 Lock 1 3"
echo "./Broker-remote -h localhost:8884 Unlock 1 2"
echo "python ping_nodes.py -l 10 -n 5 > /dev/null 2>/dev/null"
