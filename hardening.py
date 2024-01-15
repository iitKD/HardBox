#!/usr/bin/env python

import subprocess
import getpass
#to remove, disable or uninstall unused filesystems
def disable_filesystem_loading(l_mname):
    fsList = ["squashfs", "cramfs", "udf", "usb-storage"]
    for l_mname in fsList:
        install_line = f"install {l_mname} /bin/false\n"
        modprobe_conf_path = f"/etc/modprobe.d/{l_mname}.conf"

        try:
            with open(modprobe_conf_path, 'r') as f:
                if not any(install_line in line for line in f):
                    with open(modprobe_conf_path, 'a') as f:
                        print(f" - setting module: \"{l_mname}\" to be not loadable")
                        f.write(install_line)
        except FileNotFoundError:
            with open(modprobe_conf_path, 'w') as f:
                print(f" - setting module: \"{l_mname}\" to be not loadable")
                f.write(install_line)
        print(f" - unloading module \"{l_mname}\"")
        subprocess.run(["modprobe", "-r", l_mname])

        blacklist_line = f"blacklist {l_mname}\n"
        with open(modprobe_conf_path, 'r') as f:
            if not any(blacklist_line in line for line in f):
                with open(modprobe_conf_path, 'a') as f:
                    print(f" - deny listing \"{l_mname}\"")
                    f.write(blacklist_line)

#disabling automounting of file systems
def disable_autofs():
    depRes = subprocess.run(["apt-cache", "depends", "autofs"], capture_output=True, text=True)
    rdepRes = subprocess.run(["apt-cache", "depends", "autofs"], capture_output=True, text=True)

    if "Depnds" in depRes.stdout or "Reverse Depends" in rdepRes.stdout:
        subprocess.run(["system", "stop", "autofs"])
        subprocess.run(["system", "mask", "autofs"])
    else:
        print("No dependencies found, uninstalling  autofs")
        subprocess.run(["apt", "purge", "autofs"])
#Periodic checking of the filesystem integrity to detect changes to the filesystem.
def scheduling_side():
    #/etc/systemd/system/aidecheck.service
    servicePath = "aidecheck.service"
    timerPath = "aidecheck.timer"
    service_content = """[Unit]
Description=Aide Check

[Service]
Type=simple
ExecStart=/usr/bin/aide.wrapper --config /etc/aide/aide.conf --check

[Install]
WantedBy=multi-user.target
"""
    timer_content = """[Unit]
Description=Aide check every day at 5AM

[Timer]
OnCalendar=*-*-* 05:00:00
Unit=aidecheck.service

[Install]
WantedBy=multi-user.target
"""
    with open(servicePath, mode='w') as ServiceFile:
        ServiceFile.write(service_content)
    with open(timerPath, mode="w") as timerFile:
        timerFile.write(timer_content)
    subprocess.run(["chown", "root:root", "/etc/systemd/system/aidecheck.*"])
    subprocess.run(["chmod", "0644", "/etc/systemd/system/aidecheck.*"])
    subprocess.run(["systemctl", "daemon-reload"])
    subprocess.run(["systemctl","enable"," aidecheck.service"])
    subprocess.run(["systemctl","--now","enable","aidecheck.timer"])

def bootloaderPassword():
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Reenter password: ")
        if password != password_confirm:
            print("Passwords do not match. Please try again.")
            bootloaderPassword()
        else:
            command = ["grub-mkpasswd-pbkdf2"]
            result = subprocess.run(command, input=f"{password}\n{password_confirm}\n", capture_output=True, text=True)

            if result.returncode == 0:
                conf_content = f"""cat <<EOF 
                set superusers="<username>" 
                password_pbkdf2 <username> {result.stdout[68:]}
                EOF
                """
                with open("/etc/grub.d/CIS","w") as configFile:
                    configFile.write(conf_content)
            else:
                print("Error executing the command:")
                print(result.stderr)

def bootconfigPermission():
     cmd1 = ["chown","root:root","/boot/grub/grub.cfg"]
     cmd2 = ["chmod","u-wx,go-rwx","/boot/grub/grub.cfg"]
     subprocess.run(cmd1)
     subprocess.run(cmd2)

def setTerminalvalue():
    path = "/etc/sysctl.conf"
    with open(path,"a") as file:
          file.write("#kernel.randomize_va_space = 2")
    subprocess.run(["sysctl","-w","kernel.randomize_va_space=2"])

def prelinkRmBinaryrestore():
     subprocess.run(["prelink","-ua"])
     subprocess.run(["apt", "purge","prelink"])

def disableAutomaticErrorReporting():
    apportPath = "/etc/default/apport"
    with open(apportPath,"r") as apportFile :
          line = apportFile.readlines()
    for i in range(len(line)):
         if line[i].startswith("enable="):
              line[i] = "enable=0\n"
              break
    with open(apportPath,"w") as apportFile:
         apportFile.writelines(line)
    subprocess.run(["systemctl","stop","apport.service"])
    subprocess.run(["systemctl","--now","disable","apport.service"])

def coreDumpRestriction():
    pathLimits = "/etc/security/limits.conf"
    pathsysctl = "/etc/sysctl.conf"
    with open(pathLimits, "r") as limitsFile:
        lines = limitsFile.readlines()
    for i in range(len(lines)):
        if lines[i].startswith("# End of File"):
             lines[i] = """#*               hard    core            0
# End of File
"""
    with open(pathLimits, "w") as limitsFile:
         limitsFile.writelines(lines)
    with open(pathsysctl, "a") as sysctlFile:
         sysctlFile.write("fs.suid_dumpable = 0")
    subprocess.run(["sysctl","-w","fs.suid_dumpable=0"])

    result = subprocess.run(["systemctl" "is-enabled" "coredump.service"], text = True, capture_output=True)
    lst = ["enabled", "masked", "disbaled"]
    
    if result.stdout in lst:
        coreDumpPath = "/etc/systemd/coredump.conf"
        with open(coreDumpPath , "r") as coreDumpFile:
            coreDumpLines = coreDumpFile.readlines()
        flag=0
        for i in range(len(coreDumpLines)):
            if coreDumpLines[i].startswith("Storage="):
                coreDumpLines[i] = "Storage = none\n"
                flag+=1
            if coreDumpLines[i].startswith("ProcessSizeMax="):
                coreDumpFile[i] = "ProcessSizeMax = 0\n"
                flag+=1
            if flag==2:
                break
        with open(coreDumpPath,"w") as coreDumpFile:
             coreDumpFile.writelines(coreDumpLines)
    subprocess.run(["systemctl","daemon-reload"])
    
def configureApparmor():
     subprocess.run(["apt", "install","apparmor"])
     apparmorPath = "/etc/default/grub"
     with open(apparmorPath,"r") as apparmorFile:
          apparmorLines = apparmorFile.readline()
     for i in range(len(apparmorLines)):
          if apparmorLines[i].startswith("GRUB_CMDLINE_LINUX="):
               apparmorLines[i] = """GRUB_CMDLINE_LINUX="apparmor=1 security=apparmor" """

     subprocess.run(["update-grub"])
     subprocess.run(["aa-enforece","/etc/apparmor.d/*"])


def cmdLineBanners():
     cmdMsg = "Authorized uses only. All activity may be monitored and reported."
     with open("/etc/issue","a") as cmdFile:
         cmdFile.write(cmdMsg)
     with open("/etc/issue.net","a") as cmdFile:
         cmdFile.write(cmdMsg)
     subprocess.run(["chown ","root:root" ,"$(readlink -e /etc/issue)"])
     subprocess.run(["chmod","u-x,go-wx","$(readlink -e /etc/issue)"])
     subprocess.run(["chown ","root:root" ,"$(readlink -e /etc/issue.net)"])
     subprocess.run(["chmod","u-x,go-wx","$(readlink -e /etc/issue.net)"])

#<-------------------WARNING!!!!!!------------->
#--------RUN below funtion only when GUI is not required-------
def removeGDM():
     subprocess.run(["apt", "purge","gdm3"])


    
    

