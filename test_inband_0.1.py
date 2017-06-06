#!/usr/bin/python
"""
RTT throughtput testing for mptcp
"""
import os, sys, argparse, random, re, netifaces
from subprocess import Popen, PIPE, call
from time import sleep
import termcolor as T
from itertools import chain
import json

from mininet.net import Mininet
from mininet.log import lg
#from mininet.node import OVSKernelSwitch as Switch
from mininet.node import UserSwitch as Switch
from mininet.link import Link, TCLink, Intf
from mininet.util import makeNumeric, custom
from mininet.cli import CLI
from functools import partial
#from topo import TwoHostNInterfaceTopo
from mininet.node import Controller, RemoteController,OVSController
from mininet.topo import Topo

sys.path.append('topos')

#import Switch15 as sw_net
#import star3 as sw_net
import testbed as sw_net
import framework
#from framework import *
#import Switch12_part3 as sw_net
#import test_4 as sw_net

#PYTHONPATH=. ./bin/ryu run --observe-links ryu/app/gui_topology/gui_topology.py
#############################################################################
def main():
    framework.preconfigure()
    args = framework.parse_args()
    lg.setLogLevel('info')
    net = sw_net.myNetwork()
    A=framework.mininet_to_networkx(net)
    node_graph=A[0]
    if (args.test == None): 
        ans=raw_input("Press [y] to Start ping test:")
        print("Your choice:%s"%ans)
    else:
        ans="y"
    if(ans=="y"):
        print "-----Start PING test"
        hIpDict=framework.getAllIP(net)
        lg.info("Before configuring routing table")
        framework.pingAllIP(hIpDict,1)
        if(len(net.controllers)>1):
	    framework.run_configure(args,net)
        else:
    	    framework.run_configure_single_nw(args,net)
        hIpDict=framework.getAllIP(net)
        lg.info("After configuring routing table")
        framework.pingAllIP(hIpDict,3)
        pathA=None
        pathA=False
        #call(["sysctl", "-w", "net.ipv4.tcp_congestion_control=balia"])
        os.system("sh clean.sh")
        os.system("/etc/init.d/networking restart")
        os.system("cat /dev/null > /var/log/kern.log")
        ans=raw_input("Press [1] to Select 10.0.0.1:")
        if ans=="1":
            path='10.0.0.1'
            print "Option:%s\tChosen path=%s" %(ans,path)
        else:
            path='10.0.1.1'
            print "Option:%s\tChosen path=%s" %(ans,path)
        src="h2"
        dest="h1"
        path_stat=framework.get_path_stats(node_graph,src,dest)
        with open('results/notes.json', 'w') as fp:
    	    json.dump(path_stat, fp)
        if (args.test == None): 
            ans=raw_input("Press [y] to Start BW test:")
            print("Your choice:%s"%ans)
        else:
            ans="y"
        ###########################################
        if(ans=="y"):
            print "-----Start BW test"
            #stopinterface
            #ans=raw_input("Press [y] Drop interface:")
            #if(ans=="y"):
                #for x in xrange(0,1):
                    #net.getNodeByName(src).cmdPrint("ifconfig %s-eth%i down"%(src,x))
            framework.start_dataCollection(net,"")
            #net.getNodeByName(src).cmdPrint("python -m SimpleHTTPServer 80 &")
            net.getNodeByName(dest).cmdPrint("iperf -s&")#h1
            #res=net.getNodeByName(dest).cmdPrint("sleep 5; iperf -c 10.0.0.1 -i 2 -t 100 -m  > results/h2_iperf.txt")
            net.getNodeByName(src).cmdPrint("sleep 5; iperf -c %s -i 2 -t 100 -m  | tee results/h2_iperf.txt"%(path))#h2
            #res=net.getNodeByName(dest).cmdPrint("sleep 3 && time wget -O /dev/null  http://%s/input/transfer_100.dataaa"%(path))
            #time_req=res[res.find("\nreal"):].split()[1:2]
            #f = file('results/%s.time'%(time_req[0]), 'w')
            #print >>f, time_req
            #f.close()
            os.system("cat /var/log/kern.log |grep 'mptcp_balia_recalc_ai 183' > results/kernel.txt")
            os.system("wc -l results/kernel.txt")
            os.system("cat /var/log/kern.log |grep 'mptcp' > results/kernel_mptcp.txt")
            framework.stop_dataCollection(net)
            framework.repairPCAP()
    ans=raw_input("Press [y] to finish test and DESTROY:")
    if(ans!="y"):
    	CLI(net)
    net.stop()
    os.system("cat /dev/null > /var/log/kern.log")
    #print "Plotting started"
    #os.system("python util/plot_pcap_bw_singlefile.py --eps True --files results/h1.pcap --out results/results_h1_pcap_analysis.png")
    #print "Plotting ended"
    framework.end(args)

#############################################################################
if __name__ == '__main__':
    main()
#############################################################################
#### Garbage################################
    #####CLI(net)## for debugging
    '''
    h1 ping 10.0.0.2 -c 3
    h1 ping 10.0.1.2 -c 3
    h1 ping 10.0.2.2 -c 3
    h1 ping 10.0.3.2 -c 3
    h2 ping 10.0.0.1 -c 3
    h2 ping 10.0.1.1 -c 3
    h2 ping 10.0.2.1 -c 3
    h2 ping 10.0.3.1 -c 3
    exit
    '''
    #%system sysctl -w net.mptcp.mptcp_enabled=0
    #%system sysctl -a|grep mptcp
    #%system sysctl -w net.mptcp.mptcp_path_manager=ndiffports
    #call(["sysctl", "-w", "net.ipv4.tcp_congestion_control=lia"])


    #net.getNodeByName("h1").cmdPrint("iperf3 -s&")
    #net.getNodeByName("h1").cmdPrint("iperf -s -F data.txt &")
    #net.getNodeByName("h1").cmdPrint("./custom_server &")

    #net.getNodeByName("h2").cmdPrint("sleep 10 && echo 'dropped' && ifconfig h2-eth0 down && sleep 10 && echo 'up' && ifconfig h2-eth0 down &")
    #CLI(net)
    '''
    h2 ./custom_client 10.0.0.1
    h2 ./custom_client 10.0.1.1
    #h1 ./custom_client 10.0.0.3
    #h1 ./custom_client 10.0.0.4
    exit
    '''

#############################################################################
