#!/bin/sh
python start_nodes.py -l 10 -n 3
sleep 1
./Broker-remote -h localhost:8887 Lock 0 1
./Broker-remote -h localhost:8887 Unlock 0 1
./Broker-remote -h localhost:8887 Lock 1 1
./Broker-remote -h localhost:8888 Kill
python ping_nodes.py -l 10 -n 3
echo "Now lock 1 2 and then unlock 1 1 on 8886 and 8885"
echo "./Broker-remote -h localhost:8886 Lock 1 2"
echo "./Broker-remote -h localhost:8885 Unlock 1 1"
echo "python ping_nodes.py -l 10 -n 3"
