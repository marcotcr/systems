#!/bin/sh

# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s n -p 0.05 -u True -n 5 -l 1 -D 550
# mkdir ../Logs/Naive1.8.8/
# cp /tmp/* ../Logs/Naive1.8.8/
# sleep 2
# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s p -p 0.05 -u True -n 5 -l 1 -D 550
# mkdir ../Logs/Power1.8.8/
# cp /tmp/* ../Logs/Power1.8.8/
# sleep 2

# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s s -p 0.05 -u True -n 5 -l 1 -D 550
# mkdir ../Logs/Smart1.8.8/
# cp /tmp/* ../Logs/Smart1.8.8/
# sleep 2

# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s n -p 0.05 -u True -n 5 -l 2 -D 550
# mkdir ../Logs/Naive2.8.8/
# cp /tmp/* ../Logs/Naive2.8.8/
# sleep 2

# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s p -p 0.05 -u True -n 5 -l 2 -D 550
# mkdir ../Logs/Power2.8.8/
# cp /tmp/* ../Logs/Power2.8.8/
# sleep 2

# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s s -p 0.05 -u True -n 5 -l 2 -D 550
# mkdir ../Logs/Smart2.8.8/
# cp /tmp/* ../Logs/Smart2.8.8/
# sleep 2

# python run_experiment.py -a 0.97 -b 0.2 -t 0.1 -s s -p 0.05 -u True -n 5 -l 2 -D 550
# mkdir ../Logs/Smart2.97.2/
# cp /tmp/* ../Logs/Smart2.97.2/
# sleep 2

# python run_experiment.py -a 0.97 -b 0.2 -t 0.1 -s s -p 0.05 -u True -n 5 -l 1 -D 550
# mkdir ../Logs/Smart1.97.2/
# cp /tmp/* ../Logs/Smart1.97.2/
# sleep 2


# python run_experiment.py -a 0.8 -b 0.2 -t 0.1 -s n -p 0.05 -u True -n 5 -l 3 -D 1100
# mkdir ../Logs/Naive3.8.2/
# cp /tmp/* ../Logs/Naive3.8.2/
# sleep 2

# python run_experiment.py -a 0.8 -b 0.2 -t 0.1 -s p -p 0.05 -u True -n 5 -l 3 -D 1100
# mkdir ../Logs/Power3.8.2/
# cp /tmp/* ../Logs/Power3.8.2/
# sleep 2

# python run_experiment.py -a 0.8 -b 0.2 -t 0.1 -s s -p 0.05 -u True -n 5 -l 3 -D 1100
# mkdir ../Logs/Smart3.8.2/
# cp /tmp/* ../Logs/Smart3.8.2/
# sleep 2


# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s n -p 0.05 -u True -n 5 -l 3 -D 1100
# mkdir ../Logs/Naive3.8.8/
# cp /tmp/* ../Logs/Naive3.8.8/
# sleep 2

# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s p -p 0.05 -u True -n 5 -l 3 -D 1100
# mkdir ../Logs/Power3.8.8/
# cp /tmp/* ../Logs/Power3.8.8/
# sleep 2

# python run_experiment.py -a 0.8 -b 0.8 -t 0.1 -s s -p 0.05 -u True -n 5 -l 3 -D 1100
# mkdir ../Logs/Smart3.8.8/
# cp /tmp/* ../Logs/Smart3.8.8/
# sleep 2

python run_experiment.py -a 0.8 -b 0.2 -t 0.1 -s s -p 0.05 -u True -n 5 -l 1 -D 550 -k True
mkdir ../Logs/SmartKill1.8.2/
cp /tmp/* ../Logs/SmartKill1.8.2/
sleep 2

python run_experiment.py -a 0.97 -b 0.2 -t 0.1 -s s -p 0.05 -u True -n 5 -l 1 -D 550 -k True
mkdir ../Logs/SmartKill1.97.2/
cp /tmp/* ../Logs/SmartKill1.97.2/
sleep 2

python run_experiment.py -a 0.8 -b 0.2 -t 0.1 -s p -p 0.05 -u True -n 5 -l 1 -D 550 -k True
mkdir ../Logs/PowerKill1.8.2/
cp /tmp/* ../Logs/PowerKill1.8.2/
sleep 2

python run_experiment.py -a 0.8 -b 0.2 -t 0.1 -s n -p 0.05 -u True -n 5 -l 1 -D 550 -k True
mkdir ../Logs/NaiveKill1.8.2/
cp /tmp/* ../Logs/NaiveKill1.8.2/
sleep 2
