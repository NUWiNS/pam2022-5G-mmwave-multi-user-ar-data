# Can 5G mmWave support Multi-User AR?
Data from our PAM 2022 publication where we conducted multi-user AR measurements over 5G mmWave and LTE networks

If you use this dataset in your publication, please cite us as follows:
```
@InProceedings{ghoshal:pam2022,
author={Ghoshal, Moinak and Das, Pranab and Kong, Zhaoning and Xu, Qiang and Hu, Y. Charlie and Koutsonikolas, Dimitrios and Li, Yuanjie},
title={Can 5G mmWave support Multi-User AR?},
booktitle={Passive and Active Measurement (PAM)},
year={2022}
}
```
## Multi-user AR Application Workflow

Below is an image of the workflow of multi-user AR applications.
<img src="application-workflow/app.pdf" width="30%"/>

## Dataset Description

The data directory contains different folders pertaining to various experiments done in this work:

1. Baseline experiment (Section 4.1-4.5) 
2. Varying MSS experiment (Section 4.6)
3. ICMP background traffic experiment (Section 4.6)
4. Power data (Section 5)
Each such folder has sub folders based on the type of experiments. There are two parts to each data collected: Host and the Resolver data.

The Host and Resolver directories contain 2 files: 
* **capture.pcap**: Packet capture file recorded while doing the measurements. We use this file to extract the delays discussed in Section 4 of the paper.
* **static_log.logcat**: This file contains application logged timestamps of events like tapping the screen to place an object or when an object resolution is finished.

