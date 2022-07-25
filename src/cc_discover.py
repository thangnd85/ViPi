import pychromecast
services, browser = pychromecast.discovery.discover_chromecasts()
def getinfo():
    cclist = []
    for cc in services:
        cclist.append(cc)
    hostinf = []
    ip = []
    hostname = []
    for i in range (len(cclist)):
        for host in cclist[i]:
            hostinf.append(host)
            ip.append(hostinf[4])
            hostname.append(hostinf[3])
    return ip,hostname
