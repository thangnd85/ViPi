import psutil
import platform
from datetime import datetime
import os
try:
    import cpuinfo
except:
    os.system('pip install py-cpuinfo')
    import cpuinfo
import socket
import uuid
import re


def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def sysinfo():
    uname = platform.uname()
    sys = uname.system
    node = uname.node
    release = uname.release
    version= uname.version
    machine = uname.machine
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    boottime = bt.year, bt.month, bt.day, bt.hour, bt.minute, bt.second
    cpufreq = psutil.cpu_freq()
    maxfrequency = cpufreq.max
    minfrequency = cpufreq.min
    currentfrequency = cpufreq.current
    TotalCPUUsage = psutil.cpu_percent()
    svmem = psutil.virtual_memory()
    memTotal = get_size(svmem.total)
    memAvailable = get_size(svmem.available)
    memUsed = get_size(svmem.used)
    Percentage = svmem.percent
    swap = psutil.swap_memory()
    swTotal = get_size(swap.total)
    swFree = get_size(swap.free)
    swUsed = get_size(swap.used)
    swPercentage = swap.percent
    partitions = psutil.disk_partitions()
    Mountpoint,File_system_type,partition_usage,Total_Size,Part_Used,Part_Free,Part_Percentage=[],[],[],[],[],[],[]
    for partition in partitions:
        mp = partition.mountpoint
        Mountpoint.append(mp)
        fs = partition.fstype
        File_system_type.append(fs)
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            ts = get_size(partition_usage.total)
            Total_Size.append(ts)
            pu = get_size(partition_usage.used)
            Part_Used.append(pu)
            pf = get_size(partition_usage.free)
            Part_Free.append(pf)
            pp = partition_usage.percent
            Part_Percentage.append(pf)            
        except PermissionError:
            continue
    # get IO statistics since boot
    disk_io = psutil.disk_io_counters()
    Total_read = get_size(disk_io.read_bytes)
    Total_write = get_size(disk_io.write_bytes)
    return sys, node, release, version, machine, boottime, cpufreq, maxfrequency, minfrequency, currentfrequency, TotalCPUUsage, svmem, memTotal, memAvailable, memUsed, Percentage, swap, swTotal, swFree, swUsed, swPercentage, Mountpoint,File_system_type,partition_usage,Total_Size,Part_Used,Part_Free,Part_Percentage
if __name__ == "__main__":

    System_information()