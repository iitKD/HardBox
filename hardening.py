#!/usr/bin/env python
import os
import subprocess
import getpass
import re
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


def installingAIDE():
    aideCMD = ["sudo","DEBIAN_FRONTEND=noninteractive","-yp","apt","install","aide"]
    subprocess.run(aideCMD)
#Periodic checking of the filesystem integrity to detect changes to the filesystem.
        
def schedulingAideChecks():
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
     with open(apparmorPath,"w") as apparmorFile:
         apparmorFile.writelines(apparmorLines)
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
#<------------------------------------------------------------->
def loginBannerMsg():
    l_pkgoutput = ""
    if os.system("command -v dpkg-query > /dev/null 2>&1") == 0:
        l_pq = "dpkg-query -W"
    elif os.system("command -v rpm > /dev/null 2>&1") == 0:
        l_pq = "rpm -q"
    else:
        return

    l_pcl = ["gdm", "gdm3"]
    for l_pn in l_pcl:
        if os.system(f"{l_pq} {l_pn} > /dev/null 2>&1") == 0:
            l_pkgoutput += f"\n - Package: \"{l_pn}\" exists on the system\n - checking configuration"

    if l_pkgoutput:
        l_gdmprofile = "gdm"  
        l_bmessage = "'Authorized uses only. All activity may be monitored and reported'"

        if not os.path.isfile(f"/etc/dconf/profile/{l_gdmprofile}"):
            print(f"Creating profile \"{l_gdmprofile}\"")
            with open(f"/etc/dconf/profile/{l_gdmprofile}", 'w') as profile_file:
                profile_file.write(f"user-db:user\nsystem-db:{l_gdmprofile}\nfile-db:/usr/share/{l_gdmprofile}/greeter-dconf-defaults")

        if not os.path.isdir(f"/etc/dconf/db/{l_gdmprofile}.d/"):
            print(f"Creating dconf database directory \"/etc/dconf/db/{l_gdmprofile}.d/\"")
            os.makedirs(f"/etc/dconf/db/{l_gdmprofile}.d/")
        

        l_kfile = f"/etc/dconf/db/{l_gdmprofile}.d/01-banner-message"
        dbPath = "/etc/dconf/db/{l_gdmprofile}.d/"
        flag=False
        file = False
        for filee in os.listdir(dbPath):
            filePath = os.path.join(dbPath,file)
            if os.path.isfile(filePath):
                for line in open(filePath,"r").readlines():
                    if "banner-message-enable" in line:
                        l_kfile = filePath
                        file = True
                    if "banner-message-enable=true"in line:
                        l_kfile = filePath
                        flag=True
                        break
        if flag ==True:
            if not any("banner-message-text=" in line for line in open(l_kfile)):
                with open(l_kfile, 'a') as keyfile:
                    keyfile.write(f"\nbanner-message-text={l_bmessage}")
            else:
                print("Login banner message already set")
        else:
            if file==True:
                with open(l_kfile,"r") as bannerFile:
                    bannerLines = bannerFile.readlines()
                if not any("banner-message-text" in line for line in open(l_kfile)):
                    for i in range(len(bannerLines)):
                        if "banner-message-enable" in bannerLines[i]:
                            bannerFile[i] = f"\n[org/gnome/login-screen]\nbanner-message-enable=true\nbanner-message-text={l_bmessage}"
                with open(l_kfile,"w") as bannerFile:
                    bannerFile.writelines(bannerLines)
            else:
                with open(l_kfile,"w") as bannerFile:
                    bannerFile.write(f"\n[org/gnome/login-screen]\nbanner-message-enable=true\nbanner-message-text={l_bmessage}")
        os.system("dconf update")
    else:
        print("\n\n - GNOME Desktop Manager isn't installed\n - Recommendation is Not Applicable\n - No remediation required\n")

def disableLoginUserList():
    gdmProfile = "gdm"
    gdmProfilePath = f"/etc/dconf/profile/{gdmProfile}"
    gdmDbPath = f"/etc/dconf/db/{gdmProfile}.d/"

    if not os.path(gdmProfilePath):
        print(f"creating {gdmProfile} profile ")
        with open(gdmProfilePath,"w") as gdmProfileFile:
            gdmProfileFile.write(f"user-db:user\nsystem-db:{gdmProfile}\nfile-db:/usr/share/{gdmProfile}/greeter-dconf-defaults")
    if not os.path(gdmDbPath):
        print("creating database directory fot gdm profile")
        subprocess.run(["mkdir", "f/etc/dconf/db/{gdmProfile}.d/"])

    gdmKeyfileContent = f"\n[org/gnome/login-screen]\n# Do not show the user list\ndisable-user-list=true"
    gdmKeyFilePath = f"{gdmDbPath}00-login-screen"
    flag = False
    fileExist = False       
    for file in os.listdir(gdmDbPath):
        filePath = os.path.join(gdmDbPath,file)
        if os.path.isfile(filePath):
            for line in open(filePath,"r").readlines():
                if "[org/gnome/login-screen/]" in line:
                    gdmKeyFile = filePath
                    fileExist = True
                if "disable-user-list=true" in line:
                    flag = True
    if flag == True:
        print("User list already disabled on Login Screen")
    else:
        if fileExist == True:
            with open(gdmKeyFilePath,"a") as gdmKeyFile:
                gdmKeyFile.write("\n# Do not show the user list\ndisable-user-list=true")
        else:
            with open( gdmKeyFilePath,"w") as gdmKeyFile:
                gdmKeyFile.write(gdmKeyfileContent)