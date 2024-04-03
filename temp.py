#!/usr/bin/env python3

import os
import subprocess
import shutil
import re
def disableNetworkinterfaces():
    wirelessResult = subprocess.run(["nmcli", "radio", "all"],text=True,capture_output=True)
    wirePattern = r'\s+\S+\s+disabled\s+\S+\s+disabled\s+'
    match  = re.search(wirePattern,wirelessResult.stdout)
    if not match:
        print("Wireless interfaces are not disabled, disabling them...")
        wirelessresult = subprocess.run(["nmcli","radio","all","off"],capture_output=True,text=True)
        if wirelessresult.returncode==0:
            print("disabled!")
        else:
            print("Wireless interfaces could not be disabled, do it manually!")
    else:
        print("Wireless interfaces are disabled!")





def ufwConfiguration():
    print("Checking 'ufw' configuration")
    cmd = f"dpkg-query -W -f='${{binary:Package}}\t${{Status}}\t${{db:Status-Status}}\n' ufw"
    isinstalled = subprocess.run(cmd,shell=True,text=True,capture_output=True)
    install_status =[]
    for line in isinstalled.stdout.splitlines():
        install_status.append(line.split("\t")[1].split()[2].lower())
    if "installed" in install_status:
        print("\t-ufw is installed in the system!")
    else:
        print("\t-ufw is not installed, installing...")
        subprocess.run(["sudo","apt","install","ufw","-y"],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
        print("Done!")
    ifiptblpersist = subprocess.run(["dpkg-query","-s","iptables-persistent"],capture_output=True,text=True)
    if ifiptblpersist.returncode==0:
        print("\t-iptables-persistent is installed in the system , removing it!")
        removed =subprocess.run(["apt","purge","iptables-persistent"],capture_output=True,text=True)
        if removed.returncode==0:
            print("\t-iptables-persistent have been removed!")
        else:
            print("\t-iptables-persistent not removed, need to be done manually!")
    else:
        print("\t-iptables-persistent not found, so not removed!")
    ufwenable = subprocess.run(["systemctl","is-enabled","ufw.service"],capture_output=True,text=True)
    ufwactive = subprocess.run(["systemctl","is-active","ufw"],capture_output=True,text=True)
    ufwstatus = subprocess.run(["ufw","status"],capture_output=True,text=True)
    ufwstatus = ufwstatus.stdout.split(":")
    if ufwenable.stdout=="enable" and ufwactive.stdout=="active" and ufwstatus[1].strip()=="active":
        print("\t-ufw is enabled and active in the system!" )
    else:
        print("\t-ufw is not enabled, enabling it for the system...")
        subprocess.run(["systemctl","unmask","ufw.service"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl","--now","enable","ufw.service"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw" ,"allow" ,"proto" ,"tcp" ,"from" ,"any" ,"to" ,"any","port" ,"22"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ufw","--force","enable"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print("\tDone!")

            
    ufwstatus = subprocess.run(["ufw","status","verbose"],capture_output=True,text=True)
    loopPattern = [r'\s+Anywhere\s+on\s+lo\s+ALLOW\sIN\s+Anywhere\s+',r'\s+Anywhere\s+DENY\sIN\s+127.0.0.0/8\s+', r'\s+Anywhere\s+\(v6\)\s+on\s+lo\s+ALLOW\sIN\s+Anywhere\s+\(v6\)'
        ,r'\s+Anywhere\s+DENY\sIN\s+::1\s+',r'\s+Anywhere\s+ALLOW\sOUT\s+Anywhere\s+on\slo\s+',r'\s+Anywhere\s\(v6\)\s+ALLOW\sOUT\s+Anywhere\s\(v6\)\son\slo\s+']
    outPattern = [r'\s+Anywhere\s+ALLOW\sOUT\s+Anywhere\s+on\sall\s+',r'\s+Anywhere\s\(v6\)\s+ALLOW\sOUT\s+Anywhere\s\(v6\)\son\sall\s+']
    ufwstatus = ufwstatus.stdout
    ufwloopflag = True
    ufwoutflag = True
    for pattern in loopPattern:
        match = re.search(pattern,ufwstatus)
        if not match:
            ufwloopflag = False
    if ufwloopflag:
        print("\t-ufw loopback traffic is configured")
    else:
        print("\t-configuring ufw loopback traffic...")
        subprocess.run(["ufw","allow","in","on","lo"],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
        subprocess.run(["ufw","allow","out","on","lo"],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
        subprocess.run(["ufw","deny","in","from","127.0.0.0/8"],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
        subprocess.run(["ufw","deny","in","from","::1"],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
        print("\tDone!")
    for pattern in outPattern:
        match = re.search(pattern,ufwstatus)
        if not match:
            ufwoutflag = False
    if ufwoutflag:
        print("\t-ufw outbound traffic is configured")
    else:
        print("\t-configuring ufw outbound traffic...")
        subprocess.run(["ufw","allow","out","on","all"],stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
        
        print("\tDone!")
    

    ufwOut = subprocess.run(["ufw","status","verbose"],capture_output=True,text=True)
    portOut = subprocess.run(["ss","-tuln"],capture_output=True,text=True)
    portOut = portOut.stdout.strip().split("\n")
    ports = set()
    for line in portOut:
        if not any(pat in line for pat in ["%lo:", "127.0.0.0:", "::1"]):
            if ":]" in line:
                ports.add(line.split("]:")[1].strip().split()[0])
            else:
                ports.add(line.split(":")[1].strip().split()[0])
    for port in ports.copy():
        if port == "Port":
            continue
        portpat = r'\s+'+re.escape(port)+r'/(tcp|udp)'
        match = re.search(portpat,ufwOut.stdout)
        if not match:
            print(f"\t-Port:{port} is missing a firewall rule")
        else:
            ports.remove(port)
    if "631" in ports:
        subprocess.run(["ufw","allow","631/tcp"])
        print("\t-rule added for Port:631, for other ports the rules and configured as per requirements.")
    
    defPat = r'\s+Default:\s+deny\s+\(incoming\),\s+deny\s+\(outgoing\),\s+disabled\s+\(routed\)\s+'
    match = re.search(defPat,ufwOut)
    if match:
        print("\t-Default settings is set for ufw")
    else:
        print("\t-setting Default deny ufw for all connections")
        subprocess.run(["ufw", "allow", "git"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "allow","in", "http"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "allow","out", "http"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "allow","in", "https"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "allow","out", "https"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "allow", "out","53"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "logging", "on"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "Default", "deny","incoming"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "Default", "deny","incoming"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(["ufw", "Default", "deny","routed"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print("\tDone!")







