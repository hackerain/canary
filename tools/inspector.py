import libvirt
from xml.etree import ElementTree
import operator
import time
import argparse


def statistics(number, data):
    raw_data = {}
    delta_data = {}
    datas = {"rd_req": 0,
             "rd_bytes": 1,
             "wr_req": 2,
             "wr_bytes": 3}
    sleep_time = 5

    conn=libvirt.open("qemu:///system")

    for id in conn.listDomainsID():
       domain = conn.lookupByID(id)
       tree = ElementTree.fromstring(domain.XMLDesc(0))
       devices = filter(bool, [target.get("dev") for target in
                               tree.findall('devices/disk/target')])
       for device in devices:
           block_stats = domain.blockStats(device)
           pre_data = int(block_stats[datas[data]])
           disk_info = str(domain.UUIDString()) + ' ' + str(device)
           raw_data.update({disk_info: [pre_data]})

    time.sleep(sleep_time)

    for id in conn.listDomainsID():
       domain = conn.lookupByID(id)
       tree = ElementTree.fromstring(domain.XMLDesc(0))
       devices = filter(bool, [target.get("dev") for target in
                               tree.findall('devices/disk/target')])
       for device in devices:
           block_stats = domain.blockStats(device)
           post_data = int(block_stats[datas[data]])
           disk_info = str(domain.UUIDString()) + ' ' + str(device)
           raw_data[disk_info].append(post_data)

    for key in raw_data:
        last_data = int(raw_data[key][1])-int(raw_data[key][0])
        delta_data.update({key: last_data})

    conn.close()

    sort_delta_data = sorted(delta_data.items(), key=operator.itemgetter(1), reverse=True)
    count = 0
    for key,value in sort_delta_data:
        count += 1
        print key,value
        if count >= number:
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--number', default=10,
                        type=int,
                        help='Number of Top N')
    parser.add_argument('-d', '--data', choices=['rd_req','wr_req','rd_bytes','wr_bytes'],
                        help='which data want to show')
    args = parser.parse_args()
    statistics(args.number, args.data)


if __name__ == '__main__':
    main()
