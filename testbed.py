#!/usr/bin/python
"""
Test Inband Control using Mininet
"""
import termcolor as T
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
import os, sys, argparse, random, re, netifaces
####################################################
#	s1-----s2-----s3
#	|       |     |
#	h1      h2    ctlr
####################################################
##  cd ~/ryu; PYTHONPATH=. ./bin/ryu run --observe-links ryu/app/simple_switch.py
####################################################
def CMD(cmd):
	print(cmd)
	os.system(cmd)
####################################################
class InbandController( RemoteController ):
    ######################################
    def checkListening( self ):
        "Overridden to do nothing."
        return
####################################################
def myNetwork():
    net = Mininet( topo=None,
                   build=False)
    ######################################
    info('*** Add fake interface\n')
    CMD("ifconfig lo:1 10.0.0.3/32;sleep 5")
    ######################################
    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='10.0.0.3',
                      protocol='tcp',
                      port=6633)
    ######################################
    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    #s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s1.inband=True
    s2.inband=True
    #s3.inband=True
    ######################################
    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
    h3 = net.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)
    ######################################
    info( '*** Add links (H -> S)\n')
    net.addLink(s1, h1)
    net.addLink(s2, h2)
    net.addLink(s2, h3)
    ######################################
    info( '*** Add links (S -> S)\n')
    net.addLink(s1, s2)
    #net.addLink(s2, s3)
    ######################################
    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()
    ######################################
    info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    #net.get('s3').start([c0])
    ######################################
    info( '*** Post configure switches and hosts\n')
    CMD("ifconfig s1 10.0.0.11 up")
    CMD("ifconfig s2 10.0.0.12 up;sleep 5")
    #CMD("ifconfig s3 10.0.0.13 up")
    ###################
    info('*** Stop Fake interface\n')
    CMD("ifconfig lo:1 down")
    ###################
    info('*** Add routes\n')
    CMD("route add 10.0.0.1 dev s1")#address of h1
    CMD("route add 10.0.0.2 dev s2")#address of h2
    CMD("route add 10.0.0.3 dev s2")#address of h3
    ######################################
    T.cprint("USE FOLLOWING IN ctlr/h3","red")
    T.cprint("cd ~/ryu; PYTHONPATH=. ./bin/ryu run --observe-links ryu/app/simple_switch.py","red")
    T.cprint("or","green")
    T.cprint("controller -v pctp:6633","red")
    CLI(net)
    net.stop()
    #return(net)
####################################################
if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()
####################################################
