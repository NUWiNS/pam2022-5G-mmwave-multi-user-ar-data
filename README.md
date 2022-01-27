# Can 5G mmWave support Multi-User AR?
Data from our PAM 2022 publication where we conducted multi-user AR measurements over 5G mmWave and LTE networks.

If you use this dataset in your publication, please cite us as follows:
```
@InProceedings{ghoshal:pam2022,
author={Ghoshal, Moinak and Dash, Pranab and Kong, Zhaoning and Xu, Qiang and Hu, Y. Charlie and Koutsonikolas, Dimitrios and Li, Yuanjie},
title={Can 5G mmWave support Multi-User AR?},
booktitle={Passive and Active Measurement (PAM)},
year={2022}
}
```
## Multi-user AR Application Workflow

Below is an image of the workflow of multi-user AR applications. The image also shows the different components of the end-to-end latency (1a-1c, 2x and 2a-2d).

<img src="app.png" width="80%"/>

## Dataset Description

The data directory contains different directories pertaining to various experiments done in this work:

1. Baseline experiment (Section 4.1-4.5) 
2. Varying MSS experiment (Section 4.6)
3. ICMP background traffic experiment (Section 4.6)
4. Energy drain and power draw experiment (Section 5.2)

Each such directory has sub directories based on the type of experiments. There are two parts to each data collected: Host and the Resolver data.

The Host and Resolver directories contain 2 files: 
* **capture.pcap**: Packet capture file recorded while doing the measurements. We use this file to extract the latency components discussed in Section 4 of the paper.
* **static_log.logcat**: This file contains application logged timestamps of events like tapping the screen to place an object or when an object resolution has finished.

For energy drain and power draw experiment, the following files are located in Host and Resolver subdirectories in `data/power_data/`:
* **Timeline traces** : These are the timeline traces for CPU and GPU
* **screen.trace** : Screen power trace
* **intial.log** : The initial state of the CPU and GPU frequencies
* **current.txt** : It contain the timeline, current and voltage
* **interval.txt** : A given time interval [T1, T2]

## Scripts

We use a python script `scripts/get_delay_from_capture_files.py` to extract the latency from the capture.pcap and static_log.logcat files. 

The script needs an external package `pyshark`. Use the following command to install `pyshark`.

```
python3 -m pip install pyshark
```

We run the script as follows:

```
python3 get_delay_from_capture_files.py <path_to_host_resolver_subdirectory>
```

Note: To run the script, the directory structure has to be the following:
```
Example: 
/home/user/data/experiment_name/subdirectory/host/run_number

/home/user/data/experiment_name/subdirectory/resolver/run_number

There can be multiple directories (signifying multiple runs) in the host and resolver directories. 

The script can extract latencies for multiple measurement runs provided the name of the run directory is exactly the same in host and resolver directory.
```

The script generates a file called `latency.csv` denoting the latency components for a particular run. 


___
For energy drain and power draw experiments, the processing scripts and programs are located in the `honeycomb_s` module located in `scripts/`.
To get the module please run the following
```
git submodule update --init --recursive
```
 
Please see the following example to use the `honeycomb_s`.
<br>The scripts can be found in the `honeycomb_s/scripts`.
<br>To compute for `data/power_data/subdirectory/host/run_number/`.
```
python3 scripts/generate_raw_timeline.py <path to interval.txt> <path to current.txt> timeline.snippet
python3 scripts/generate_config.py <path to timeline traces> timeline.snippet config
bin/run config > utilization
 
python3 scripts/cpu_gpu_power_timeline.py utilization <path to cpu model> <path to gpu model> cpu_gpu_timeline.csv
python3 scripts/camera_timeline.py <path to current.txt> <path to interval.txt> <path to camera model> camera_timeline.csv
python3 scripts/screen_timeline.py <path to screen.trace> <path to current.txt> <path to interval.txt> screen_timeline.csv
```
The power models are located in `scripts/models`
1. cpu.model : CPU power model
1. gpu.model : GPU power model
1. camera.model : Camera power model
 
The cpu_gpu_timeline.csv, camera_timeline.csv and screen_timeline.csv contain the cpu & gpu; camera and; screen power timeline respectively.
 
For further information please refer to README of `honeycomb_s`.
