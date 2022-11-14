<img width="407" alt="Logo" src="https://user-images.githubusercontent.com/31121102/198831561-6cb6b1ed-c229-4f3c-bcb3-c0dbd43b9e42.png">

# TODO for all
- Read paper of sandpiper


# Notes
## CPU Monitoring (Ramneek + Tushar + Sahil)
### Host
- CPU usage for each VM (just check cpu usage for vm process)
- In CPU monitoring of different VMs, we will not be able to directly monitor the work done during copying from memory to buffers (work done during IO)
    - This work is done by HOST
    - We will assume that no other work is done on host
    - Then we will calculate total IO (Input/Output + Network packets) used in each VM and calculate the total amount of CPU usage in VM as percentage of HOST CPU usage
    - Ignoring Input ourput right now

## Memory Monitoring (Vishal + Saurav)
### Memory Monitoring of VMs
- Total memory for this VM. Done
- Also check total memory usage inside VM

### Memory Monitoring of Host
- Done
- Total swapped memory (Try to keep this as less as possible) -> Try to do it

## Network Monitoring (Amar + Rishi)
- Monitor the tap device (Virtual NIC) in VMM Reference


## Basic frontend
- Make a simple frontend to display histogram & timeseries for each vm and each host.  

## Load Balancing
- Provision VM (choose where to launch a new VM)
- Detect hotspot
- Choose the suitable VM to migrate and to which host, in case of hotspot. 

## Redis Data Sturcture
- **host_id_to_ip** hash
  - Host ID (str (key is always int in redis)) to IP (str)
- **mon_proxy_addr:{host_id}** string
- **host_config:{host_id}** hash
  - 'mem': Integer
    - Physical Memory of Server
  - 'cpu': Integer
    - CPU Cores
  - 'net': Integer
    - Bandwidth
- **vms_in_host:{host_id}** set
  - All the vm ids
- **vmm_proxy_addr:{host_id}** string
- **vm_configs:{vm_id}** hash
  - 'mem': Integer
  - 'cpu': Integer
  - 'disk': String (Network Disk Info)
  - 'image_path': Integer
  - 'host_id': Integer
    - In which host does this VM exists
  - 'pid': Integer
    - Process ID
  - 'tap_device': String
  - 'rpc_port': Integer
- **host_ids** set

## Running Monitoring/server.py
PYTHONPATH=./ python ./Monitoring/server.py


