#!/usr/bin/env python
import os
a = os.popen('ps aux | grep python | grep Cellar | grep -v kill | grep -v sh').readlines()
for line in a:
  os.system('kill -9 %s' % line.split()[1])
