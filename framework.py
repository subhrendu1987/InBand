#!/usr/bin/python
"""
RTT throughtput testing for mptcp
"""

import sys,os
from subprocess import Popen, PIPE, call
from time import sleep
import termcolor as T
import argparse
import networkx as nx
import matplotlib.pyplot as plt
import pickle
import random
import re,string
import netifaces

from itertools import chain
import networkx as nx
from mininet.net import Mininet
from mininet.log import lg
#from mininet.node import OVSKernelSwitch as Switch
from mininet.node import UserSwitch as Switch
from mininet.link import Link, TCLink
from mininet.util import makeNumeric, custom
from mininet.cli import CLI
from functools import partial
#from topo import TwoHostNInterfaceTopo
from mininet.node import Controller, RemoteController,OVSController
from mininet.topo import Topo
#import Switch6_part1 as sw_net
#import basic2switch as sw_net
#import Switch6_part2 as sw_net
#import Switch12_part3 as sw_net
#import test_4 as sw_net

#############################################################################
def get_hID(host):
    name=host.name
    hid=re.findall(r'\d+', name)
    return int(hid[0])
#############################################################################
def start_tcpdump_controllers(controllers):
    #sudo tcpdump -w h3-eth0.pcap -i h3-eth0 &
    for n in controllers:
        n.cmdPrint("tcpdump -n \"host %s and port %s\" -w results/%s.pcap &" %(n.IP(), n.port, n.name))
#############################################################################
def start_tcpdump_singlefile(nodes):
    #sudo tcpdump -w h3-eth0.pcap -i h3-eth0 &
    for n in nodes:
        intfs= intfs= { id:intf for (id,intf) in n.intfs.iteritems() if intf.name!='lo'}
        n.cmdPrint("tcpdump -w results/%s.pcap -i any &" %(n.name))
#############################################################################
def start_tcpdump(nodes):
    #sudo tcpdump -w h3-eth0.pcap -i h3-eth0 &
    for n in nodes:
        intfs= intfs= { id:intf for (id,intf) in n.intfs.iteritems() if intf.name!='lo'}
        #n.cmdPrint("tcpdump -w results/%s.pcap -i any &" %(n.name))
        for i in intfs.keys():
            dev = '%s-eth%i' % (n.name,i)
            n.cmdPrint("tcpdump -w results/%s.pcap -i %s &" %(dev,dev))
#############################################################################
def stop_tcpdump(nodes):
    for n in nodes:
        n.cmdPrint("killall -9 tcpdump")
#############################################################################
def start_tcpprobe(nodes):
    for n in nodes:
        n.cmdPrint("rmmod tcp_probe 1>/dev/null 2>&1; modprobe tcp_probe")
        n.cmdPrint("cat /proc/net/tcpprobe > results/%s_tcp_probe.txt" % (n.name))
#############################################################################
def stop_tcpprobe(nodes):
    for n in nodes:
        n.cmd("killall -9 cat; rmmod tcp_probe")
#############################################################################
def start_monitor(hosts):
    """Uses bwm-ng tool to collect iface tx rate stats.  Very reliable."""
    #bwm-ng -t 1000 -o csv -u bits -T rate -C 
    for n in hosts:
        n.cmdPrint("bwm-ng -t 1000 -o csv -u bits -T rate > results/%s_bwm.txt &"%(n.name))
#############################################################################
def stop_monitor(hosts):
    for n in hosts:
        n.cmdPrint("killall -9 bwm-ng")
        n.cmdPrint("killall -9 custom_server")
        n.cmdPrint("killall -9 custom_client")
        n.cmdPrint("killall -9 SimpleHTTPServer")
#############################################################################
def start_dataCollection(net,prefix):
    ''' prefix for pcap file names'''
    #start_tcpdump_controllers(net.controllers)
    print("---------------------------------")
    #start_tcpdump(net.hosts)
    start_tcpdump_singlefile(net.hosts)
    print("---------------------------------")
    #start_tcpprobe(net.hosts)
    print("---------------------------------")
    #start_monitor(net.hosts)
    print("---------------------------------")
#############################################################################
def stop_dataCollection(net):
    #stop_tcpdump(net.controllers)
    stop_tcpdump(net.hosts)
    #stop_tcpprobe(net.hosts)
    stop_monitor(net.hosts)
#############################################################################
def repairPCAP():
    lsdir=os.listdir("results")
    pcapfiles=[f for f in lsdir if ".pcap" in f]
    for f in pcapfiles:
    	os.system("pcapfix results/%s"%(f))
    	if os.path.isfile("fixed_%s"%(f)):
    	    os.remove("results/%s"%(f))
    	    os.rename("fixed_%s"%(f),"results/%s"%(f))
    return
#############################################################################
def sysctl_set(key, value):
    """Issue systcl for given param to given value and check for error."""
    p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE,
              stderr=PIPE)
    # Output should be empty; otherwise, we have an issue.  
    stdout, stderr = p.communicate()
    stdout_expected = "%s = %s\n" % (key, value)
    if stdout != stdout_expected:
        raise Exception("Popen returned unexpected stdout: %s != %s" %
                        (stdout, stdout_expected))
    if stderr:
        raise Exception("Popen returned unexpected stderr: %s" % stderr)
#############################################################################
def set_mptcp_enabled(enabled):
    """Enable MPTCP if true, disable if false"""
    e = 1 if enabled else 0
    lg.info("setting MPTCP enabled to %s\n" % e)
    sysctl_set('net.mptcp.mptcp_enabled', e)
#############################################################################
def set_mptcp_ndiffports(ports):
    """Set ndiffports, the number of subflows to instantiate"""
    lg.info("setting MPTCP ndiffports to %s\n" % ports)
    if(ports !=1):
    	sysctl_set("net.mptcp.mptcp_path_manager", "ndiffports")
    	print("*****ndiff ports")
    else:
    	sysctl_set('net.mptcp.mptcp_path_manager','fullmesh')
    	print("*****FULL MESH")
    #sysctl_set("net.mptcp.mptcp_ndiffports", ports)
#############################################################################
def parse_args():
    parser = argparse.ArgumentParser(description="MPTCP 2-host 2-path 6-switch test")
    parser.add_argument('--bw', '-B',
                        action="store",
                        help="Bandwidth of links",
                        default=10)
#                        required=True)
    
    parser.add_argument('-n',
                        action="store",
                        help="Number of switches.  Must be >= 2",
                        default=2)
    
    parser.add_argument('-t',
                        action="store",
                        help="Seconds to run the experiment",
                        default=2)
    
    parser.add_argument('--mptcp',
                        action="store_true",
                        help="Enable MPTCP (net.mptcp.mptcp_enabled)",
                        default=True)
#                        default=False)
    parser.add_argument('--pause',
                        action="store_true",
                        help="Pause before test start & end (to use wireshark)",
                        default=False)
    parser.add_argument('--ndiffports',
                        action="store",
                        help="Set # subflows (net.mptcp.mptcp_ndiffports)",
                        default=1)
    parser.add_argument('--allTest','--test',
                        action="store",
                        help="Run all test",
                        default=None,
                        dest="test")

    parser.add_argument('--draw',
                        action="store_true",
                        help="Wheater visualization of topology is required (will be saved in topo.png/topo.dot)",
                        default=True)

    args = parser.parse_args()
    args.bw = float(args.bw)
    args.n = int(args.n)
    args.ndiffports = int(args.ndiffports)
    return args
#############################################################################
def setup(args):
    set_mptcp_enabled(args.mptcp)
    set_mptcp_ndiffports(args.ndiffports)
#############################################################################
def drawTopology(topo):
    G=topo.convertTo(nx.MultiGraph,data=True,keys=True)
    nx.write_dot(G,'topo.dot')
    #!neato -T png topo.dot > topo.png
#########################################################################
def get_hID(host):
    name=host.name
    hid=re.findall(r'\d+', name)
    return int(hid[0])
#############################################################################
def end(args):
    set_mptcp_enabled(False)
    set_mptcp_ndiffports(1)
#############################################################################
def checkAllSwitchConnected(net):
    for sw in net.switches:
       lg.info("Switch="+sw.name+" Connected="+str(sw.connected())+"\n")
#############################################################################
def getAllIP(net):
    host_ip_dict={}
    for h in net.hosts:
       no_of_intfs=len(h.intfs)
       output=str(h.cmd("ifconfig")).split()
       ip=[]
       regexp = re.compile(r'addr:\d+')
       ip=[j[5:] for i,j in enumerate(output) if(("addr:" in j)and(len(j)>5)and(j!="addr:127.0.0.1"))]
       host_ip_dict[h]=ip
    return(host_ip_dict)
#############################################################################
def pingAllIP(host_ip_dict,times):
    #print times
    for h in host_ip_dict.keys():
    	print("--------------------------------------------")
    	temp={k:host_ip_dict[k] for k in host_ip_dict if k!=h}
    	IPs=list(chain.from_iterable(temp.values()))
    	for ip in IPs:
    	    output=h.pexec("ping "+ip+" -c %d"%times)[0].split()
    	    if len(output)>0:#to remove unreachable network IPs
	    	    if("time" in output[13]):
	    	    	n=len(output)
	    	    	out_str=h.name+" --> "+output[1]+" rtt "+output[n-4]+" "+output[n-2]+" ms"
	    	    else:
	    	    	out_str=h.name+" --> "+output[1]+" X "
	    	    print(out_str)
    	    #print (h.name+" ping "+ip+" -c 3")
#############################################################################
def getAllIntfMac(net):
    hosts=net.hosts
#############################################################################
def run_configure_single_nw(args, net):
	seconds = int(args.t)
	hosts=net.hosts
	counter=0
	for h in hosts:
		hid=get_hID(h)
		name=h.name
		intfs= { id:intf for (id,intf) in h.intfs.iteritems() if intf.name!='lo'}
		for i in intfs.keys():
		# Setup IPs:
			dev = '%s-eth%i' % (name,i)
			counter=counter+1
			subnetmask= "255.255.255.0"
			h.cmdPrint('ifconfig %s 10.0.0.%i netmask %s' % (dev, counter,subnetmask))
'''
			#h.cmdPrint('ifconfig %s 10.0.%i.%i netmask 255.255.255.0' % (dev, i,hid))
			if (len(net.controllers) >1):
				if args.mptcp:
				    lg.info("configuring source-specific routing tables for MPTCP\n")
				    # This creates two different routing tables, that we use based on the
				    # source-address.
				    table = '%s' % (i + 1)
				    ####################### CHANGE THE GRAPH First
				    #######################START TEST
				    h.cmdPrint('ip rule add from 10.0.%i.%i table %s' % (i,hid, table))
				    mask= 24
				    h.cmdPrint('ip route add 10.0.%i.0/%d dev %s scope link table %s' % (i,mask, dev, table))
				    h.cmdPrint('ip route add default via 10.0.%i.1 dev %s table %s' % (i, dev, table))
			else:
				if args.mptcp:
				    lg.info("configuring source-specific routing tables for MPTCP\n")
				    # This creates two different routing tables, that we use based on the
				    # source-address.
				    table = '%s' % (i + 1)
				    ####################### CHANGE THE GRAPH First
				    #######################START TEST
				    h.cmdPrint('ip rule add from 10.0.%i.%i table %s' % (i,hid, table))
				    mask= 24
				    h.cmdPrint('ip route add 10.0.%i.0/%d dev %s scope link table %s' % (i,mask, dev, table))
				    h.cmdPrint('ip route add default via 10.0.%i.1 dev %s table %s' % (i, dev, table))
'''
#############################################################################
def run_configure(args, net):
	seconds = int(args.t)
	hosts=net.hosts
	for h in hosts:
		hid=get_hID(h)
		name=h.name
		intfs= { id:intf for (id,intf) in h.intfs.iteritems() if intf.name!='lo'}
		for i in intfs.keys():
		# Setup IPs:
			print("--------------------------------------------")
			dev = '%s-eth%i' % (name,i)
			subnetmask= "255.255.255.0" if (len(net.controllers) >1)  else "255.255.0.0"
			h.cmdPrint('ifconfig %s 10.0.%i.%i netmask %s' % (dev, i,hid,subnetmask))
			#h.cmdPrint('ifconfig %s 10.0.%i.%i netmask 255.255.255.0' % (dev, i,hid))
			if (len(net.controllers) >1):
				if args.mptcp:
				    lg.info("configuring source-specific routing tables for MPTCP\n")
				    # This creates two different routing tables, that we use based on the
				    # source-address.
				    table = '%s' % (i + 1)
				    ####################### CHANGE THE GRAPH First
				    #######################START TEST
				    h.cmdPrint('ip rule add from 10.0.%i.%i table %s' % (i,hid, table))
				    mask= 24
				    h.cmdPrint('ip route add 10.0.%i.0/%d dev %s scope link table %s' % (i,mask, dev, table))
				    h.cmdPrint('ip route add default via 10.0.%i.1 dev %s table %s' % (i, dev, table))
			else:
				if args.mptcp:
				    lg.info("configuring source-specific routing tables for MPTCP\n")
				    # This creates two different routing tables, that we use based on the
				    # source-address.
				    table = '%s' % (i + 1)
				    ####################### CHANGE THE GRAPH First
				    #######################START TEST
				    h.cmdPrint('ip rule add from 10.0.%i.%i table %s' % (i,hid, table))
				    mask= 24
				    h.cmdPrint('ip route add 10.0.%i.0/%d dev %s scope link table %s' % (i,mask, dev, table))
				    h.cmdPrint('ip route add default via 10.0.%i.1 dev %s table %s' % (i, dev, table))
#############################################################################
def add_gateway_internet(net,i,h):
    net.stop()
    h0 = net.addHost('h0', ip='0.0.0.0')
    s0=net.addSwitch('s0')
    Intf(i,node=s0)
    net.addLink(h0, s0)
#############################################################################
def param_mismatch(n1_params,n2_params):
    if(n1_params<>n2_params):print "Parameter mismatch"
    return(n1_params)
#############################################################################
def get_path_stats(node_graph,src,dest):
    paths=list(nx.all_simple_paths(node_graph,src,dest))
    bw={}
    delay={}
    loss={}
    for P in paths:
	P_id="-".join(P)
	bw[P_id]=[]
	delay[P_id]=[]
	loss[P_id]=[]
	for i in xrange(1,len(P)):
	    params=node_graph[P[i-1]][P[i]][0]
	    try:
	    	bw[P_id].append(params['bw'])
	    except KeyError:
	        bw[P_id].append(float('inf'))
	    try:
	        delay[P_id].append(params['delay'])
	    except KeyError:
	        delay[P_id].append(0)
	    try:
	        loss[P_id].append(params['loss'])
	    except KeyError:
	        loss[P_id].append(0)
	bw[P_id]=min(bw[P_id])
	delay[P_id]=sum([float(re.sub("\D", "", i)) for i in delay[P_id]])
	loss[P_id]=sum(loss[P_id])
    state={}
    for k in bw.keys():
    	state[k]=[bw[k],delay[k],loss[k]]
    return(state)
#############################################################################
def mininet_to_networkx(net):
    ret_node=nx.MultiGraph()
    ret_intfs=nx.MultiGraph()
    hosts=[ h.name for h in net.hosts]
    sw=[ s.name for s in net.switches]
    h_intfs=[[intf.name for intf in h.intfs.values()] for h in net.hosts]
    sw_intfs=[[intf.name for intf in s.intfs.values()] for s in net.switches]
    ret_intfs.add_nodes_from(sum(h_intfs,[])+sum(sw_intfs,[]))
    ret_node.add_nodes_from(hosts+sw)
    for l in net.links:
    	n1=l.intf1
    	n2=l.intf2
    	n1_params=n1.params
    	n2_params=n2.params
	edge_params=param_mismatch(n1_params,n2_params)
    	ret_node.add_edge(n1.node.name,n2.node.name,**edge_params)
    	ret_intfs.add_edge(n1.name,n2.name,**edge_params)
    ret=(ret_node,ret_intfs)
    return(ret)
#############################################################################
def preconfigure():
    call(["mn","-c"])
    call(["sysctl", "-w", "net.mptcp.mptcp_debug=1"])
    call(["sysctl", "-w", "net.mptcp.mptcp_enabled=1"])
    call(["sysctl", "-w", "net.ipv4.tcp_no_metrics_save=1"])
    call(["sysctl", "-w", "net.ipv4.tcp_slow_start_after_idle=1"])
    call(["sysctl", "-w", "net.mptcp.mptcp_path_manager","fullmesh"])
    call(["sysctl", "-w", "net.ipv4.tcp_congestion_control=balia"])
#############################################################################
def monitor_controller(net):
    cnt_process_name_list=[ "mininet:"+c.name for c in net.controllers]
    for pname in cnt_process_name_list:
    	Popen(["sh","watch_controller_usage.sh",pname,"&"])
    return
#############################################################################
#############################################################################
#############################################################################
#############################################################################

