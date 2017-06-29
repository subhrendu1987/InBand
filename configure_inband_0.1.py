############################################################
#sudo ifconfig lo:1 10.0.0.3/32;sleep 5; sudo mn --topo linear,3 --switch ovsk,inband=True --controller=remote,ip=10.0.0.3
############################################################
#!/usr/bin/python
############################################################
level=3
nw="10.0.0"
from subprocess import call
import os, sys, argparse, random, re, netifaces
############################################################
def CMD(cmd):
	print(cmd)
	os.system(cmd)
############################################################
print('*** Add fake interface')
#CMD("ifconfig lo:1 10.0.0.3/32;sleep 5")
print( '*** Post configure switches and hosts\n')
for i in xrange(1,level):
	CMD("ifconfig s%d %s.%d up"%(i,nw,(50+i)))
print('*** Stop Fake interface\n')
CMD("ifconfig lo:1 down")
print('*** Add routes\n')
for i in xrange(1,level):
	CMD("route add %s.%d dev s%d"%(nw,i,i))
print("*** End of configuration")
####################################################
##  cd ~/ryu; PYTHONPATH=. ./bin/ryu run --observe-links ryu/app/simple_switch.py
####################################################
##  sudo ovs-vsctl --columns=other_config list bridge | grep "disable-in-band"
##  ovs-vsctl set bridge br other-config:disable-in-band=true
####################################################
