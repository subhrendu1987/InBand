############################################################
#sudo ifconfig lo:1 10.0.0.3/32;sleep 5; sudo mn --topo linear,3 --switch ovsk,inband=True --controller=remote,ip=10.0.0.3
############################################################
#!/usr/bin/python
level=3
from subprocess import call
import os, sys, argparse, random, re, netifaces

print('*** Add fake interface')
#os.system("ifconfig lo:1 10.0.0.3/32;sleep 5")
print( '*** Post configure switches and hosts\n')
for i in xrange(1,level):
	os.system("ifconfig s%d 10.5.20.%d up"%(i,(50+i)))
print('*** Stop Fake interface\n')
os.system("ifconfig lo:1 down")
print('*** Add routes\n')
for i in xrange(1,level):
	os.system("route add 10.5.20.%d dev s%d"%(i,i))
print("*** End of configuration")

####################################################
##  cd ~/ryu; PYTHONPATH=. ./bin/ryu run --observe-links ryu/app/simple_switch.py
####################################################
