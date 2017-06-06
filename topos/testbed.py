#!/usr/bin/python
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
class InbandController( RemoteController ):
    ######################################
    def checkListening( self ):
        "Overridden to do nothing."
        return
####################################################
def myNetwork():
    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.5.20.0/24')
    ######################################
    info('*** Add fake interface')
    os.system("ifconfig lo:1 10.5.20.113/32;sleep 5")
    ######################################
    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='10.5.20.113',
                      protocol='tcp',
                      port=6633)
    ######################################
    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch)
    s1.inband=True
    s2.inband=True
    s3.inband=True
    s4.inband=True
    s5.inband=True
    ######################################
    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.5.20.15', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.5.20.16', defaultRoute=None)
    h3 = net.addHost('h3', cls=Host, ip='10.5.20.113', defaultRoute=None)
    h4 = net.addHost('h4', cls=Host, ip='10.5.20.17', defaultRoute=None)
    h5 = net.addHost('h5', cls=Host, ip='10.5.20.18', defaultRoute=None)
    ######################################
    info( '*** Add links (H -> S)\n')
    net.addLink(s1, h1)
    net.addLink(s2, h2)
    net.addLink(s3, h3)
    net.addLink(s4, h4)
    net.addLink(s5, h5)
    info( '*** Add links (S -> S)\n')
    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s3, s4)
    net.addLink(s4, s5)
    ######################################
    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()
    ######################################
    info( '*** Starting switches\n')
    net.get('s1').start([])
    net.get('s2').start([])
    net.get('s3').start([])
    net.get('s4').start([])
    net.get('s5').start([])
    ######################################
    info( '*** Post configure switches and hosts\n')
    os.system("ifconfig s1 10.5.20.19 up")
    os.system("ifconfig s2 10.5.20.20 up")
    os.system("ifconfig s3 10.5.20.21 up")
    os.system("ifconfig s4 10.5.20.22 up")
    os.system("ifconfig s5 10.5.20.23 up;sleep 5")
    info('*** Stop Fake interface\n')
    os.system("ifconfig lo:1 down")
    info('*** Add routes\n')
    os.system("route add 10.5.20.15 dev s1")#address of h1
    os.system("route add 10.5.20.16 dev s2")#address of h2
    os.system("route add 10.5.20.113 dev s3")#address of h3
    os.system("route add 10.5.20.17 dev s4")#address of h4
    os.system("route add 10.5.20.18 dev s5")#address of h5
    ######################################
    print("USE FOLLOWING IN ctlr/h3\n")
    print("cd ~/ryu; PYTHONPATH=. ./bin/ryu run --observe-links ryu/app/simple_switch.py")
    CLI(net)
    net.stop()
    #return(net)
####################################################
if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()
####################################################
