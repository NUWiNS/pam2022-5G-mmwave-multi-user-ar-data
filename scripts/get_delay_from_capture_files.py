import glob
import pyshark
import sys
import time 

from datetime import datetime

# each run consists of a host and resolver part of data
# base path is the directory path where the host and resolver data is present
# example : /home/user/data/host/run1 /home/user/data/resolver/run1
base_path = sys.argv[1]
host_dirs = glob.glob(base_path + '/host/*')
# dump the delays in a csv file called latency.csv
csv_file_path = base_path + '/latency.csv'
csv_fh = open(csv_file_path, 'w+')
csv_fh.write("run_name,delay_1a,delay_1b,delay_1c,delay_2x,delay_2a,delay_2b,delay_2c,delay_2d,pkt_host_delay,pkt_resolve_delay,pkt_e2e,diff_host,diff_resolve,diff_e2e\n")

#iterate through all the runs in a current folder
for host_path in host_dirs:
    #set resolver path
    resolve_path = base_path + '/resolver/' + host_path.split('/')[-1]
    run_name = host_path.split('/')[-1]
    #parse host side data first
    host_fh = open(host_path + '/static_log.logcat', 'r')
    host_data = host_fh.readlines()
    screen_tap_flag  = 0
    #get data from the app logs 
    for data in host_data:
        data =data.strip()
        if 'Screen tap recorded' in data and screen_tap_flag == 0:
            screen_tap_sys_time = data.split()[-1]
            screen_tap_sys_time = datetime.strptime(screen_tap_sys_time, "%H:%M:%S.%f")
            screen_tap_flag = 1
        elif 'Anchor has been placed' in data:
            anchor_placed_utc_time = float(data.split()[-1])
        elif 'The anchor id was successfully shared' in data:
            anchor_shared_utc_time = float(data.split()[-1])
            
    # get delay from packet captures
    host_pcap = host_path + '/capture.pcap'
    #get phone and google cloud server IPs automatically
    cap_host_syn = pyshark.FileCapture(host_pcap,only_summaries=False,display_filter="tcp.flags.syn ==1 && tcp.flags.ack ==1")
    syn_counter = 0
    for pkt in cap_host_syn:
        if syn_counter == 0:
            try:
                gcloud_one_ip = pkt.ipv6.src
                phone_ip = pkt.ipv6.dst
            except:
                gcloud_one_ip = pkt.ip.src
                phone_ip = pkt.ip.dst
            
        elif syn_counter == 1:
            try:
                gcloud_two_ip = pkt.ipv6.src
                if pkt.ipv6.dst != phone_ip:
                    print("How can phone ips be different?!")
                    sys.exit(1)
            except:
                gcloud_two_ip = pkt.ip.src
                if pkt.ip.dst != phone_ip:
                    print("How can phone ips be different?!")
                    sys.exit(1)

            
        elif syn_counter == 2:
            print("More syn packets?")
            exclude_list = []
            sys.exit(1)
        syn_counter+=1
    
    cap_host_syn.close()
    time.sleep(2)

    if ':' in phone_ip:
        filter = 'ipv6.src == %s || ipv6.dst == %s' %(phone_ip, phone_ip)
    else:
        filter = 'ip.src == %s || ip.dst == %s' %(phone_ip, phone_ip)
    cap = pyshark.FileCapture(host_pcap,only_summaries=True,display_filter=filter,keep_packets=False)
    first_data_pkt_found=0
    last_ack_list = []
    #get the timestamps of various packets
    for pkt in cap:
        if 'TCP' in pkt.protocol or 'TLS' in pkt.protocol:
            if pkt.source == phone_ip and pkt.destination == gcloud_one_ip and 'Client' not in pkt.summary_line and ('Application Data' in pkt.summary_line or (pkt.protocol == 'TLSv1.2' and int(pkt.length) > 100)) and first_data_pkt_found == 0:
                first_data_pkt_found=1
                first_data_pkt_relative_time = float(pkt.time)
                first_data_pkt_sys_time = pkt.systemtime
                first_data_pkt_sys_time = datetime.strptime(first_data_pkt_sys_time, "%H:%M:%S.%f")
            elif pkt.source == gcloud_two_ip and pkt.destination == phone_ip and int(pkt.length) < 100 and '[ACK]' in pkt.summary_line:
                #last ack found
                if gcloud_one_ip != gcloud_two_ip:
                    last_ack_relative_time = float(pkt.time)
                    last_ack_system_time = pkt.systemtime 
                    last_ack_system_time = datetime.strptime(last_ack_system_time, "%H:%M:%S.%f")
                else:
                    last_ack_relative_time = float(pkt.time)
                    last_ack_list.append(last_ack_relative_time)
            elif pkt.source == gcloud_one_ip and pkt.destination == phone_ip and ('Application Data' in pkt.summary_line or (pkt.protocol == 'TLSv1.2' and int(pkt.length) > 100)) and int(pkt.length) > 100:
                last_data_pkt_relative_time_host = float(pkt.time)
                last_data_pkt_system_time_host = pkt.systemtime
                last_data_pkt_system_time_host = datetime.strptime(last_data_pkt_system_time_host, "%H:%M:%S.%f")

    # calculate the delays on the host side
    delay_1a = first_data_pkt_sys_time - screen_tap_sys_time 
    delay_1a = (delay_1a.seconds) + (delay_1a.microseconds)/1000000.0
    if gcloud_two_ip != gcloud_one_ip:
        delay_1b = last_ack_relative_time - first_data_pkt_relative_time
        delay_1c = last_data_pkt_relative_time_host - last_ack_relative_time
    else:
        delay_1b = last_ack_list[-3] - first_data_pkt_relative_time
        delay_1c = last_data_pkt_relative_time_host - last_ack_list[-3]


    #parse resolver side data
    resolve_fh = open(resolve_path + '/static_log.logcat', 'r')
    resolve_data = resolve_fh.readlines()
    #get data from the app logs 
    for data in resolve_data:
        data = data.strip()
        if 'Anchor seen on screen at time' in data:
            object_seen_sys_time = data.split()[-1]
            object_seen_sys_time = datetime.strptime(object_seen_sys_time, "%H:%M:%S.%f")
        elif 'anchor has been successfully resolved' in data:
            anchor_resolved_utc_time = float(data.split()[-1])
    cap.close()
    resolve_pcap = resolve_path + '/capture.pcap'
    #get phone and google cloud server IPs automatically
    cap = pyshark.FileCapture(resolve_pcap,only_summaries=False,display_filter="tcp.flags.syn ==1 && tcp.flags.ack ==1")
    syn_counter = 0
    for pkt in cap:
        try:
            gcloud_one_ip = pkt.ipv6.src
            phone_ip = pkt.ipv6.dst
        except:
            gcloud_one_ip = pkt.ip.src
            phone_ip = pkt.ip.dst
        
    cap.close()
    time.sleep(2)
    
    # the firebase database server has a fixed ip
    # ipv4 address = 35.201.97.85
    # ipv6 address = 2600:1901:0:94b6::
    if ':' in phone_ip:
        filter = 'ipv6.src == %s || ipv6.dst == %s' %(phone_ip, phone_ip)
        firebase_ip = '2600:1901:0:94b6::'
    else:
        filter = 'ip.src == %s || ip.dst == %s' %(phone_ip, phone_ip)
        firebase_ip = '35.201.97.85'
    
    last_ack_relative_list = []
    last_ack_system_list = []
    cap = pyshark.FileCapture(resolve_pcap,only_summaries=True,display_filter=filter,keep_packets=False)
    first_data_pkt_found = 0
    last_data_pkt_found = 0

    for pkt in cap:
        if 'TCP' in pkt.protocol or 'TLS' in pkt.protocol:
            if pkt.source == firebase_ip and pkt.destination == phone_ip and ('Application Data' in pkt.summary_line or 'TCP Retransmission' in pkt.summary_line or (pkt.protocol == 'TLSv1.2' and int(pkt.length) > 100)) and first_data_pkt_found == 0:
                notification_data_pkt_relative_time = float(pkt.time)
                notification_data_pkt_system_time = pkt.systemtime
                notification_data_pkt_system_time = datetime.strptime(notification_data_pkt_system_time, "%H:%M:%S.%f")
            elif pkt.source == phone_ip and pkt.destination == gcloud_one_ip and 'Client' not in pkt.summary_line and ('Application Data' in pkt.summary_line or (pkt.protocol == 'TLSv1.2' and int(pkt.length) > 100)) and first_data_pkt_found == 0:
                first_data_pkt_found=1
                first_data_pkt_relative_time = float(pkt.time)
                first_data_pkt_sys_time = pkt.systemtime
                first_data_pkt_sys_time = datetime.strptime(first_data_pkt_sys_time, "%H:%M:%S.%f")

            elif pkt.source == gcloud_one_ip and pkt.destination == phone_ip and int(pkt.length) < 100 and '[ACK]' in pkt.summary_line:
                #last ack found/ second last ack
                last_ack_relative_time = float(pkt.time)
                last_ack_system_time = pkt.systemtime 
                last_ack_system_time = datetime.strptime(last_ack_system_time, "%H:%M:%S.%f")
                last_ack_relative_list.append(last_ack_relative_time)
                last_ack_system_list.append(last_ack_system_time)
            elif pkt.source == gcloud_one_ip and pkt.destination == phone_ip and ('Application Data' in pkt.summary_line or (pkt.protocol == 'TLSv1.2' and int(pkt.length) > 100)):
                last_data_pkt_relative_time_resolve = float(pkt.time)
                last_data_pkt_system_time_resolve = pkt.systemtime
                last_data_pkt_system_time_resolve = datetime.strptime(last_data_pkt_system_time_resolve, "%H:%M:%S.%f")
                last_data_pkt_found = 1
    
    #recalculate delay 2b with the first burst only 
    # if the experiment is with mss 400 or 650 Bytes, the ips are IPv4 else it is IPv6
    # we change the filters accordingly
    if 'mss_400' in resolve_pcap:
        data_filter = 'ip.src == %s && frame.len == 468' %(phone_ip)
    elif 'mss_650' in resolve_pcap:
        data_filter = 'ip.src == %s && frame.len == 718' %(phone_ip)
    else:
        data_filter = 'ipv6.src == %s && frame.len > 1000' %(phone_ip)
    res_cap_temp = pyshark.FileCapture(resolve_pcap, only_summaries=True,display_filter=data_filter)
    start_flag = 0
    pkt_time_rel = []
    for temp_pkt in res_cap_temp:
        if start_flag == 0:
            prev_time = float(temp_pkt.time)
            start_flag = 1
        else:
            if (float(temp_pkt.time) - prev_time) >= 0.3:
                delay_2b_end_time = pkt_time_rel[-1]
                break
            else:
                pkt_time_rel.append(float(temp_pkt.time))
                prev_time = float(temp_pkt.time)
    res_cap_temp.close()
    try:
        delay_2b_end_time = pkt_time_rel[-1]
    except:
        print("Old 2b value retained")
        delay_2b_end_time = last_ack_relative_list[-3]
    delay_2x = notification_data_pkt_system_time - last_data_pkt_system_time_host
    if delay_2x.days < 0:
        # negative 2x would mean that either the phones are not synchronised properly
        # or the difference is negligible so that we can ignore them
        print("***** Negative 2X ******")
        delay_2x = 0
    else:
        delay_2x = delay_2x.seconds + (delay_2x.microseconds)/1000000.0
    delay_2a = first_data_pkt_relative_time - notification_data_pkt_relative_time
    delay_2b = last_ack_relative_list[-3] -  first_data_pkt_relative_time
    delay_2c = last_data_pkt_relative_time_resolve - last_ack_relative_list[-3]
    delay_2d = object_seen_sys_time - last_data_pkt_system_time_resolve
    delay_2d = (delay_2d.microseconds)/1000000.0

    print("######### Packet Capture Delays #########")
    print("######### Delay 1a == %s" %delay_1a)
    print("######### Delay 1b == %s" %delay_1b)
    print("######### Delay 1c == %s" %delay_1c)
    print("######### Delay 2x == %s" %delay_2x)
    print("######### Delay 2a == %s" %delay_2a)
    print("######### Delay 2b == %s" %delay_2b)
    print("######### Delay 2c == %s" %delay_2c)
    print("######### Delay 2d == %s" %delay_2d)
    pkt_host_delay = delay_1a + delay_1b + delay_1c
    print("######### Host delay == %s" %(delay_1a + delay_1b + delay_1c))
    pkt_resolve_delay = delay_2x + delay_2a + delay_2b + delay_2c + delay_2d
    print("######### Resolver delay == %s" %(delay_2x + delay_2a + delay_2b + delay_2c + delay_2d))
    pkt_e2e = delay_1a + delay_1b + delay_1c + delay_2x + delay_2a + delay_2b + delay_2c + delay_2d
    print("######### Total E2E delay == %s" %(delay_1a + delay_1b + delay_1c + delay_2x + delay_2a + delay_2b + delay_2c + delay_2d))
    print()
    print("######### Application Delays #########")
    placed_utc_seconds = int(str(int(anchor_placed_utc_time))[-2:])
    shared_utc_seconds = int(str(int(anchor_shared_utc_time))[-2:])
    resolve_utc_seconds = int(str(int(anchor_resolved_utc_time))[-2:])
    if placed_utc_seconds < shared_utc_seconds:
        diff_host = anchor_shared_utc_time - anchor_placed_utc_time
        print("######### Host delay == %s" %(diff_host))
    else:
        diff_host = (shared_utc_seconds + 60) - placed_utc_seconds
        print("######### Host delay == %s" %(diff_host))
    if shared_utc_seconds < resolve_utc_seconds:
        diff_resolve = anchor_resolved_utc_time - anchor_shared_utc_time
        print("######### Resolver delay == %s" %(anchor_resolved_utc_time - anchor_shared_utc_time))
    else:
        diff_resolve = (resolve_utc_seconds + 60) - shared_utc_seconds
        print("######### Resolver delay == %s" %(diff_resolve))
    if placed_utc_seconds < resolve_utc_seconds:
        diff_e2e = anchor_resolved_utc_time - anchor_placed_utc_time
        print("######### Total E2E delay == %s" %(diff_e2e))
    else:
        diff_e2e = (resolve_utc_seconds + 60) - placed_utc_seconds
        print("######### Total E2E delay == %s" %diff_e2e)
    print("%s,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f" %(run_name,delay_1a,delay_1b,delay_1c,delay_2x,delay_2a,delay_2b,delay_2c,delay_2d,pkt_host_delay,pkt_resolve_delay,pkt_e2e,diff_host,diff_resolve,diff_e2e))
    csv_fh.write("%s,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f\n" %(run_name,delay_1a,delay_1b,delay_1c,delay_2x,delay_2a,delay_2b,delay_2c,delay_2d,pkt_host_delay,pkt_resolve_delay,pkt_e2e,diff_host,diff_resolve,diff_e2e))
    cap.close()
    print()
csv_fh.close()
print()