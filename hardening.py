#!/usr/bin/env python

import subprocess
import sys
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
vim 

    
    

