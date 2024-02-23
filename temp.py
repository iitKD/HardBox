import subprocess
import os
def uninstallservices( toUninstall,Sname):
    print(f"Checking {Sname}...")
    cmd = f"dpkg-query -W -f='${{binary:Package}}\t${{Status}}\t${{db:Status-Status}}\n' {toUninstall}"
    isinstalled = subprocess.run(cmd,shell=True,text=True,capture_output=True)
    install_status =[]
    for line in isinstalled.stdout.splitlines():
        install_status.append(line.split("\t")[1].split()[2].lower())
    if "installed" in install_status:
        print(f"{Sname} is installed, removing {Sname}...")
        uninstalled= subprocess.run(["apt","purge",f"{toUninstall}","-y"],stdout=subprocess.DEVNULL)
        if uninstalled.returncode==0:
            print(f"{Sname} is removed form system")
            print("-"*64)
            return
        else:
            print(f"{Sname} was not removed ")
            print("-"*64)
            return
    else:
        print(f"{Sname} is not installed")
        print("-"*64)
        return


def removeXserver():
    cmdX = "dpkg-query -W -f='${binary:Package}\\t${Status}\\t${db:Status-Status}\\n' xserver-xorg*"
    Xinstalled = subprocess.run(cmdX, shell=True, text=True, capture_output=True)
    install_status = []
    for line in Xinstalled.stdout.splitlines():
        install_status.append(line.split("\t")[1].split()[2])
    if "installed" in install_status:
        print(" Removing xserver-xorg packages" )
        Xuninstall = subprocess.run(["apt", "purge", "xserver-xorg*", "-y"],stdout=subprocess.DEVNULL)
        if Xuninstall.returncode==0:
            print("Xserver-xorg packages are removed")
            print("-"*64)
        else:
            print("Xserver-xorg packages are removed")
            print("-"*64)


    else:
        print("xserver-xorg packages are not installed")
        print("-"*64)

def removeAvahi():
    cmdavahi = "dpkg-query -W -f='${binary:Package}\t${Status}\t${db:Status-Status}\n' avahi-daemon"
    avahiinstalled = subprocess.run(cmdavahi,shell=True, text=True, capture_output=True)
    install_status = []
    for line in avahiinstalled.stdout.splitlines():
        install_status.append(line.split("\t")[1].split()[2])
    if "installed" in install_status:
        print("avahi-daemon is installed, removing it...")
        
        subprocess.run(["systemctl","stop","avahi-daaemon.service", "-y"],stdout=subprocess.DEVNULL)
        subprocess.run(["systemctl","stop","avahi-daemon.socket","-y"],stdout=subprocess.DEVNULL)
        subprocess.run(["apt","purge","avahi-daemon","-y"],stdout=subprocess.DEVNULL)
    else:
        print("Avahi package is not installed")


removeXserver()
removeAvahi()
uninstallservices("cups","CUPS")

uninstallservices("isc-dhcp-server","DHCP")

uninstallservices("sldap","LDAP")

uninstallservices("nfs-kernel-server","NFS")
uninstallservices("bind9","DNS")
uninstallservices("vsftpd","FTP")
uninstallservices("apache2", "HTTP server")
uninstallservices("dovecot-imapd", "IMAP")
uninstallservices("dovecot-pop3d", "POP3")
uninstallservices("samba","Server Message Block(SMB) daemon")
uninstallservices("squid","HTTP Proxy Server")
uninstallservices("snmp", "Simple Network Management Protocol (SNMP)")
uninstallservices("nis", "Network Information System (NIS)")
uninstallservices("rsync","rsync")
uninstallservices("rsh-client","RSH packages")
uninstallservices("talk","Talk")
uninstallservices("telnet","Telnet")
uninstallservices("ldap-utils","LDAP clients")
uninstallservices("rpcbind","Remote Procedure Call (RPC)")


def localonlyMTA():
    if os.path.isfile("/etc/postfix/main.conf"):
        with open("/etc/postfix.main.conf","r") as postfixFile:
                lines = postfixFile.readlines()
        for i in range(len(lines)):
            if "inet_interfaces = " in lines[i]:
                if "inet_interfaces = loopback-only" in lines[i]:
                    print("postfix MTA is not listining on any non-loopback addresses")
                    break
                else:
                    lines[i] = f"inet_interfaces = loopback-only\n"
                    break
        with open("/etc/postfix.main.conf", "w") as file:
            file.writelines(lines)

    else:
        print("Postfix MTA is not enabled")