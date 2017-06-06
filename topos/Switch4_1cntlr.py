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

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=Controller,
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
    h2 = net.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
    h3 = net.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)

    info( '*** Add links\n')
    s1h1 = {'bw':10,'delay':'20ms','loss':0,'max_queue_size':200}# Path A
    net.addLink(s1, h1, cls=TCLink , **s1h1)
    s2h2 = {'bw':10,'delay':'1ms','loss':0,'max_queue_size':200}
    net.addLink(s2, h2, cls=TCLink , **s2h2)
    s1s2 = {'bw':10,'delay':'1ms','loss':0,'max_queue_size':200}
    net.addLink(s1, s2, cls=TCLink , **s1s2)
    s3h2 = {'bw':10,'delay':'1ms','loss':0,'max_queue_size':200}
    net.addLink(s3, h2, cls=TCLink , **s3h2)
    s4s3 = {'bw':10,'delay':'1ms','loss':0,'max_queue_size':200}
    net.addLink(s4, s3, cls=TCLink , **s4s3)
    h1s4 = {'bw':10,'delay':'20ms','loss':0,'max_queue_size':200}# Path B
    net.addLink(h1, s4, cls=TCLink , **h1s4)
    s2h3 = {'bw':10,'delay':'1ms','loss':0,'max_queue_size':200}
    net.addLink(s2, h3, cls=TCLink , **s2h3)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])
    net.get('s1').start([c0])

    info( '*** Post configure switches and hosts\n')
    return(net)

    #CLI(net)
    #net.stop()
    
if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()
topos = { 'myNetwork': ( lambda: myNetwork() ) }
