# InBand
## Requirements
Ryu controller
If you do not have ryu, use default ovs controller
## How to run
* Use the following command for running the test case
** sudo python testbed.py
* In mininet cli use 
** "xterm h3" (if it throws an error, use "xterm cltr")
* Run ryu inside xterm by useing the following command in h3/cltr xterm window
** "cd ~/ryu; PYTHONPATH=. ./bin/ryu run --observe-links ryu/app/simple_switch.py"
** if you don't have ryu, you can use "controller ptcp:6633"
* Use pingall in mininet cli to check the connectivity
