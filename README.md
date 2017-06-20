# InBand

## Requirements

- Ryu controller
- If you do not have Ryu, use default ovs controller

## How to run

1. Use the following command for running the test case

    `sudo python testbed.py`
2. In mininet cli use

    `xterm h3` 
    
    **Note : if it throws an error, use `xterm cltr`**
    
3. Run ryu inside xterm by using the following command in h3/cltr xterm window

    `cd ~/ryu; PYTHONPATH=. ./bin/ryu run --observe-links ryu/app/simple_switch.py`

4. if you don't have Ryu, you can use `controller -v ptcp:6633`

5. Use `pingall` in Mininet cli to check the connectivity

## Additional

1. `configure_inband_0.1.py` is for debugging purpose. It should be used with the following command

    `sudo ifconfig lo:1 10.0.0.3/32;sleep 5; sudo mn --topo linear,3 --switch ovsk,inband=True --controller=remote,ip=10.0.0.3`

