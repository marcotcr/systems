#!/bin/sh
python start_nodes.py -l 10 -n 3
sleep 1
./Broker-remote -h localhost:8887 Lock 0 1
./Broker-remote -h localhost:8887 Unlock 0 1
./Broker-remote -h localhost:8887 Lock 1 1
# This is simulating a message fail between 1 and 0, so 1 elects a new leader
./Paxos-remote -h localhost:8889 ElectNewLeader 1
./Paxos-remote -h localhost:8890 ElectNewLeader 1
python ping_nodes.py -l 10 -n 3
echo "Now lock 1 2 on 8887 and then unlock 1 1 on 8885:"
echo "./Broker-remote -h localhost:8887 Lock 1 2"
echo "./Broker-remote -h localhost:8885 Unlock 1 1"
echo "python ping_nodes.py -l 10 -n 3"
