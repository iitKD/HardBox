#!/usr/bin/env python
import os
import subprocess
import getpass
import re
#to remove, disable or uninstall unused filesystems
def disable_filesystem_loading():
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
                else:
                    print(f"{l_mname} is set to be not loadable")
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
            else:
                print(f"{l_mname} is blacklisted ")

#disabling automounting of file systems
def disable_autofs():
    depRes = subprocess.run(["apt-cache", "depends", "autofs"], capture_output=True, text=True)
    rdepRes = subprocess.run(["apt-cache", "depends", "autofs"], capture_output=True, text=True)

    if "Depnds" in depRes.stdout or "Reverse Depends" in rdepRes.stdout:
        print("Dependencies found for autofs, so masking and stopping the module..")
        subprocess.run(["system", "stop", "autofs"])
        subprocess.run(["system", "mask", "autofs"])
    else:
        print("No dependencies found, uninstalling  autofs")
        subprocess.run(["apt", "purge", "autofs"])


def installingAIDE():
    is_installed = subprocess.run(["dpkg", "-s", "aide"], stdout=subprocess.DEVNULL)
    if is_installed.returncode == 0:
        print("AIDE is already installed.")
    else:
        print("Installing AIDE")
        aideCMD = ["sudo","DEBIAN_FRONTEND=noninteractive","apt","install","aide", "aide-common","-y"]
        aideinstalled = subprocess.run(aideCMD, stdout=subprocess.DEVNULL)
        if aideinstalled.returncode==0:
            print("AIDE installed successfully!")
        else:
            print(aideinstalled.std)
            print("Error in installing AIDE, cheack manually!")
#Periodic checking of the filesystem integrity to detect changes to the filesystem.
        
def schedulingAideChecks():
    #/etc/systemd/system/aidecheck.service
    servicePath = "/etc/systemd/system/aidecheck.service"
    timerPath = "/etc/systemd/system/aidecheck.timer"
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
    if not os.path.exists(servicePath) or service_content != open(servicePath).read():
        print("Creating serviceFile for aide checks!")
        with open(servicePath, mode='w') as ServiceFile:
            ServiceFile.write(service_content)
    else:
        print("ServiceFile for AIDE checks exist!")
    if not os.path.exists(timerPath) or timer_content != open(timerPath).read():
        print("Creating timerFile for AIDE checks!")
        with open(timerPath, mode="w") as timerFile:
            timerFile.write(timer_content)
    else:
        print("Timer file for AIDE checks already exists!")
    subprocess.run("chown root:root /etc/systemd/system/aidecheck.*", shell=True)
    subprocess.run("chmod 0644 /etc/systemd/system/aidecheck.*", shell=True)
    subprocess.run("systemctl daemon-reload", shell=True)
    subprocess.run("systemctl enable aidecheck.service", shell=True)
    subprocess.run("systemctl --now enable aidecheck.timer", shell=True)

def bootloaderPassword():
    print("Setting bootloader password...")
    password = getpass.getpass("Enter password for your bootloader: ")
    password_confirm = getpass.getpass("Re-enter password: ")
    if password != password_confirm:
        print("Passwords do not match. Please try again.")
        bootloaderPassword()
    else:
        command = ["grub-mkpasswd-pbkdf2"]
        result = subprocess.run(command, input=f"{password}\n{password_confirm}\n", capture_output=True, text=True)

        if result.returncode == 0:
            conf_content = f"""cat <<EOF 
            set superusers="bootloader" 
            password_pbkdf2 bootloader {result.stdout[68:]}
            EOF
            """
            with open("/etc/grub.d/CIS","w") as configFile:
                configFile.write(conf_content)
            print("Bootloader password is set")
        else:
            print("Error , password could not be set, try manually!")
            print(result.stderr)

def bootconfigPermission():
     print("Restricting permissions on bootloader config files")
     subprocess.run(["chown","root:root","/boot/grub/grub.cfg"])
     subprocess.run(["chmod","u-wx,go-rwx","/boot/grub/grub.cfg"])

def setTerminalvalue():
    path = "/etc/sysctl.conf"
    flag=False
    with open(path,"r") as confFile:
        confLines = confFile.readlines()
    for line in confLines:
        if line == "kernel.randomize_va_space = 2\n":
            flag=True
            break
    if flag == True:
        print("ASLR randomization is set")
    else:
        print("Setting up ASLR randomization...")
        with open(path,"a") as file:
            file.write("kernel.randomize_va_space = 2\n")
        subprocess.run(["sysctl","-w","kernel.randomize_va_space=2"])
        print("Done...")

def prelinkRmBinaryrestore():
     subprocess.run("prelink -ua", shell=True)
     subprocess.run(["apt", "purge","prelink"])

def disableAutomaticErrorReporting():
    
    print("Checking for automatic error reporting system...")
    apportPath = "/etc/default/apport"
    with open(apportPath, "r") as apportFile:
        lines = apportFile.readlines()
    enable_found = False
    for i in range(len(lines)):
        if lines[i].startswith("enabled=0"):
            enable_found = True
            break
    if not enable_found:
        print("Disabling apport service..")
        for i in range(len(lines)):
            if lines[i].startswith("enabled="):
                lines[i] = "enabled=0\n"
                break
        with open(apportPath, "w") as apportFile:
            apportFile.writelines(lines)
        subprocess.run(["systemctl", "stop", "apport.service"])
        subprocess.run(["systemctl", "--now", "disable", "apport.service"])
    else:
        print("Automatic error reporting system is disabled!")


def coreDumpRestriction():
    pathLimits = "/etc/security/limits.conf"
    pathsysctl = "/etc/sysctl.conf"
    with open(pathLimits, "r") as limitsFile:
        lines = limitsFile.readlines()
    hard_flag = False
    for line in lines:
        if line == "*\thard\tcore\t0\n":
            hard_flag = True
            break
    if hard_flag:
        print("Core dumps for all user is Disabled!")
    else:
        print("Disabling core dump for all users...")
        for i in range(len(lines)):
            if lines[i].startswith("# End of file\n"):
                lines[i] = "*\thard\tcore\t0\n# End of file\n"
        with open(pathLimits, "w") as limitsFile:
            limitsFile.writelines(lines)

    suid_flag = False
    with open(pathsysctl,"r") as sysctlFile:
        sysLines= sysctlFile.readlines()
    for line in sysLines:
        if line == "fs.suid_dumpable = 0\n":
            suid_flag=True
            break
    if suid_flag:
        print("Core dumps from suid binaries been disabled!")
    else:
        print("Disabling core dumps from suid bnaries...")
        with open(pathsysctl, "a") as sysctlFile:
            sysctlFile.write("fs.suid_dumpable = 0\n")
        subprocess.run(["sysctl","-w","fs.suid_dumpable=0"])


    coreDumpPath = "/etc/systemd/coredump.conf"
    storage_modified = False
    process_size_max_modified = False
    try:
        with open(coreDumpPath, "r") as coreDumpFile:
            coreDumpLines = coreDumpFile.readlines()        
        for line in coreDumpLines:
            if "Storage=none" in line:
                storage_modified = True
            if "ProcessSizeMax=0" in line:
                process_size_max_modified = True
    except:
        print("config file for core dump don't exist")
    if not (storage_modified and process_size_max_modified):
        print("Modifying/creating config file to limit the core dump sixe to 0 Byte...")
        with open(coreDumpPath, "r") as coreDumpFile:
            coreDumpLines = coreDumpFile.readlines()
        with open(coreDumpPath, "w") as coreDumpFile:
            for i in range(len(coreDumpLines)):
                if coreDumpLines[i].startswith("#Storage="):
                    coreDumpLines[i] = "Storage=none\n"
                if coreDumpLines[i].startswith("#ProcessSizeMax="):
                    coreDumpLines[i] = "ProcessSizeMax=0\n"
            coreDumpFile.writelines(coreDumpLines)
        subprocess.run(["systemctl", "daemon-reload"])
    else:
        print("Core dump size is restricted to 0 Byte!")

    
def configureApparmor():
    result = subprocess.run(["dpkg","-s", "apparmor"],stdout=subprocess.DEVNULL)
    if result.returncode==0:
        print("apparmor is already installed!")
        if os.path.exists("/usr/sbin/aa-enforce"):
            print("apparmor utils are avilable")
        else:
            subprocess.run(["apt","install", "apparmor-utils"],stdout=subprocess.DEVNULL)
    else:
        print("installing Apparmor...")
        subprocess.run(["apt", "install","apparmor"],stdout=subprocess.DEVNULL)
        subprocess.run(["apt", "install","apparmor-utils"],stdout=subprocess.DEVNULL)

    apparmorPath = "/etc/default/grub"
    with open(apparmorPath,"r") as apparmorFile:
        apparmorLines = apparmorFile.readline()
    apparmor_flag = False
    for line in apparmorLines:
        if line ==  """GRUB_CMDLINE_LINUX="apparmor=1 security=apparmor"\n""":
            apparmor_flag=True
            break

    if apparmor_flag:
        print("Apparmor security profile already enabled and enforced!")
    else:
        print("enabling and enforcing Apparmor security profile...")
        for i in range(len(apparmorLines)):
            if apparmorLines[i].startswith("GRUB_CMDLINE_LINUX="):
                apparmorLines[i] = """GRUB_CMDLINE_LINUX="apparmor=1 security=apparmor"\n"""
        with open(apparmorPath,"w") as apparmorFile:
            apparmorFile.writelines(apparmorLines)
        subprocess.run(["update-grub"])
        subprocess.run("aa-enforce /etc/apparmor.d/*",shell=True)


def cmdLineBanners():
    cmdMsg = "Authorized uses only. All activity may be monitored and reported."
    with open("/etc/issue", "r") as cmdFile:
        if cmdMsg not in cmdFile.read():
            print("Setting Command line banner..")
            with open("/etc/issue", "a") as cmdFile:
                cmdFile.write(cmdMsg)
        else:
            print("Command Line banner is already set!")
    with open("/etc/issue.net", "r") as cmdFile:
        if cmdMsg not in cmdFile.read():
            with open("/etc/issue.net", "a") as cmdFile:
                cmdFile.write(cmdMsg)
    if os.path.exists("/etc/issue"):
        subprocess.run("chown root:root $(readlink -e /etc/issue)", shell=True)
        subprocess.run("chmod u-x,go-wx $(readlink -e /etc/issue)", shell=True)
    if os.path.exists("/etc/issue.net"):
        subprocess.run("chown root:root $(readlink -e /etc/issue.net)", shell = True)
        subprocess.run("chmod u-x,go-wx $(readlink -e /etc/issue.net)", shell = True)


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
        dbPath = f"/etc/dconf/db/{l_gdmprofile}.d/"
        flag=False
        file = False
        for file in os.listdir(dbPath):
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
                print("Setting login banner message...")
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

    if not os.path.isfile(gdmProfilePath):
        print(f"creating {gdmProfile} profile ")
        with open(gdmProfilePath,"w") as gdmProfileFile:
            gdmProfileFile.write(f"user-db:user\nsystem-db:{gdmProfile}\nfile-db:/usr/share/{gdmProfile}/greeter-dconf-defaults")
    if not os.path.isdir(gdmDbPath):
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

def screenLockIdle():
    keyfilepath = "/etc/dconf/db/gdm.d/00-screensaver"
    idleTime = "900"
    lockTime = "5"
    keyfileContent = f"""# Specify the dconf path\n[org/gnome/desktop/session]\n\n# Number of seconds of inactivity before the screen goes blank\n# Set to 0 seconds if you want to deactivate the screensaver.\nidle-delay = uint32 {idleTime}\n\n# Specify the dconf path\n[org/gnome/desktop/screensaver]\n\n# Number of seconds after the screen is blank before locking the screen\nlock-delay = unit32 {lockTime}\n"""
    
    if not os.path.exists(keyfilepath) or keyfileContent != open(keyfilepath).read():
        print("Creating/updating config file for Idle screen time and Lock time")
        with open(keyfilepath,"w") as Screenfile:
            Screenfile.write(keyfileContent)
        os.system("dconf update")
    else:
        print("Idle-delay and Lock_delay are already set!")
def patternCheckScreen(directory,pattern,something):
    if not directory:
            print(f" {something}-delay is not set, so it cannot be locked\n - Please follow Recommendation \"Ensure GDM screen locks when the user is idle\" and follow this Recommendation again")
    else:
        for root,dirs, files in os.walk(directory):
            for file in files:
                path = os.path.join(root,file)
                try:
                    for line in open(path,"r").readlines():
                        if pattern in line:
                                print(f" {something}-delay is locked in {path} ")
                                return
                except:
                    continue
        print(f"Creating entry to lock {something}-delay")
        path = os.path.join(directory, 'locks', '00-screensaver')
        if os.path.isfile(path):
            with open(path, 'a') as lockFile:
                lockFile.write(f"\n# Lock desktop screensaver {something}-delay setting\n{pattern}")
        os.makedirs(os.path.join(directory, 'locks'), exist_ok=True)
        with open(path, 'w') as lockFile:
            lockFile.write(f"\n# Lock desktop screensaver {something}-delay setting\n{pattern}")

def screenLockFile():
    packageInstalled = ""
    if os.system("command -v dpkg-query > /dev/null 2>&1") == 0:
        packageManager = "dpkg-query -W"
    elif os.system("command -v rpm > /dev/null 2>&1") == 0:
        packageManager = "rpm -q"
    else:
        return

    packageList = ["gdm", "gdm3"]
    for package in packageList:
        if os.system(f"{packageManager} {package} > /dev/null 2>&1") == 0:
            packageInstalled += f"\n - Package: \"{package}\" exists on the system\n - Remediating configuration if needed"
    if packageInstalled:
        print(packageInstalled)

        # Look for idle-delay to determine profile in use, needed for remaining tests
        directoryPath = "/etc/dconf/db/"

        keyfileDirectoryidle = None
        keyfileDirectorylock = None
        settingIdle = "idle-delay = uint32"
        settingLock = "lock-delay = uint32"
        idledelayPattern = '/org/gnome/desktop/session/idle-delay'
        lockdelayPattern = "/org/gnome/desktop/screensaver/lock-delay"
        for root, dirs, files in os.walk(directoryPath):
            for file in files:
                    filepath = os.path.join(root,file)
                    try:
                        for line in open(filepath,"r").readlines():
                            if settingIdle in line:
                                keyfileDirectoryidle = root
                                break
                    except:
                        continue
        for root, dirs, files in os.walk(directoryPath):
            for file in files:
                    filepath = os.path.join(root,file)
                    try:
                        for line in open(filepath,"r").readlines():
                            if settingLock in line:
                                keyfileDirectorylock = root
                                break
                    except:
                        continue
        patternCheckScreen(keyfileDirectoryidle,idledelayPattern,"idle")
        patternCheckScreen(keyfileDirectorylock,lockdelayPattern,"lock")
    else:
        print(" - GNOME Desktop Manager package is not installed on the system\n - Recommendation is not applicable")


def findFilepath(directoryPath, tofind):
    for roots, dirs, files in os.walk(directoryPath):
            for file in files:
                for line in open(file,"r").readlines():
                    if tofind in line:
                        return os.path.join(roots,file)
    return "else"
def createupdateEntry(filePath, entryFor, entryValue):
    flag=False
    writeFlag =False
    if os.path.isfile(filePath):
        with open(filePath,"r") as mountFile:
            mountLines = mountFile.readlines()
        for i in range(len(mountLines)):
            if entryValue in mountLines[i]:
                flag = True
            if "[org/gnome/desktop/media-handling]" in mountLines[i]:
                writeFlag = True
                writeline = i
        if flag ==True:
            print(f" {entryFor} is set to false in {filePath}")
        else:
            if writeFlag==True:
                print(f"Creating or updating {entryFor} entry in {filePath}")
                mountLines[writeline] = f"\n[org/gnome/desktop/media-handling]\n{entryValue}\n"
                with open(filePath,"w") as mountFile:
                    mountFile.writelines(mountLines)
    else:
        print(f"Creating or updating {entryFor} entry in {filePath}")
        with open(filePath,"w") as mountFile:
                mountFile.write(f"\n[org/gnome/desktop/media-handling]\n{entryValue}\n")

def disableAutoMounting():
    packageInstalled = ""
    profileName = "gdm"
    if os.system("command -v dpkg-query > /dev/null 2>&1") == 0:
        packageManager = "dpkg-query -W"
    elif os.system("command -v rpm > /dev/null 2>&1") == 0:
        packageManager = "rpm -q"
    else:
        return

    packageList = ["gdm", "gdm3"]
    for package in packageList:
        if os.system(f"{packageManager} {package} > /dev/null 2>&1") == 0:
            packageInstalled += f"\n - Package: \"{package}\" exists on the system\n - Remediating configuration if needed"

    if packageInstalled:
        print(packageInstalled)
        dbPath = "/etc/dconf/db/*.d/"
        mountFilepath = f"/etc/dconf/db/{profileName}.d/00-media-automount"
        mountFilepath2 = f"/etc/dconf/db/{profileName}.d/00-media-automount"
        autorunFilepath = f"/etc/dconf/db/{profileName}.d/00-media-autorun"
        
        
        mountFilepath = findFilepath(dbPath,"automount")
        mountFilepath2 =findFilepath(dbPath,"automount-open")
        autorunFilepath =findFilepath(dbPath,"autorun-never")
        if mountFilepath =="else":
            mountFilepath = f"/etc/dconf/db/{profileName}.d/00-media-automount"
        if mountFilepath2 == "else":
            mountFilepath2 = f"/etc/dconf/db/{profileName}.d/00-media-automount"
        if autorunFilepath == "else":
            autorunFilepath = f"/etc/dconf/db/{profileName}.d/00-media-autorun"

        
        if os.path.isfile(f"/etc/dconf/profile/{profileName}"):
            print(f"dconf database profile exit in: /etc/dconf/profile/{profileName}")
        else:
            print(f"Creating profile \"{profileName}\"")
            with open(f"/etc/dconf/profile/{profileName}", 'w') as profile_file:
                profile_file.write(f"user-db:user\nsystem-db:{profileName}\nfile-db:/usr/share/{profileName}/greeter-dconf-defaults")

        if  os.path.isdir(f"/etc/dconf/db/{profileName}.d/"):
            print(f" dconf database directory in /etc/dconf/db/{profileName}.d/")
        else:
            print(f"Creating dconf database directory \"/etc/dconf/db/{profileName}.d/\"")
            os.makedirs(f"/etc/dconf/db/{profileName}.d/")

        createupdateEntry(mountFilepath,"automount","automount=false")
        createupdateEntry(mountFilepath2,"automount-open","automount-open=false")
        createupdateEntry(autorunFilepath,"autorun-never","autorun-never=true")
        
    else:
        print(" - GNOME Desktop Manager package is not installed on the system\n - Recommendation is not applicable")
    os.system("dconf update")

def patternCheckmount(directory,pattern,something, fileName):
    if not directory:
            print(f" {something} is not set, so it cannot be locked\n - Please follow Recommendation \"Ensure GDM screen locks when the user is idle\" and follow this Recommendation again")
    else:
        for root,dirs, files in os.walk(directory):
            for file in files:
                path = os.path.join(root,file)
                try:
                    for line in open(path,"r").readlines():
                        if pattern in line:
                                print(f" {something} is locked in {path} ")
                                return
                except:
                    continue
        print(f"Creating entry to lock {something}")
        path = os.path.join(directory, 'locks', fileName)
        if os.path.isfile(path):
            with open(path, 'a') as lockFile:
                lockFile.write(f"\n# Lock desktop media-handling {something} setting\n{pattern}")
        else:
            os.makedirs(os.path.join(directory, 'locks'), exist_ok=True)
            with open(path, 'w') as lockFile:
                lockFile.write(f"\n# Lock desktop media-handling {something} setting\n{pattern}")
            
def getDirectory(path,setting):
    for root, dirs, files in os.walk(path):
            for file in files:
                    filepath = os.path.join(root,file)
                    try:
                        for line in open(filepath,"r").readlines():
                            if setting in line:
                                return root
                    except:
                        continue
def mountLockFile():
    packageInstalled = ""
    if os.system("command -v dpkg-query > /dev/null 2>&1") == 0:
        packageManager = "dpkg-query -W"
    elif os.system("command -v rpm > /dev/null 2>&1") == 0:
        packageManager = "rpm -q"
    else:
        return

    packageList = ["gdm", "gdm3"]
    for package in packageList:
        if os.system(f"{packageManager} {package} > /dev/null 2>&1") == 0:
            packageInstalled += f"\n - Package: \"{package}\" exists on the system\n - Remediating configuration if needed"
    if packageInstalled:
        print(packageInstalled)

        # Look for idle-delay to determine profile in use, needed for remaining tests
        directoryPath = "/etc/dconf/db/"

        keyfileDirectorymount = None
        keyfileDirectorymountOpen = None
        keyfileDirectoryautorun = None
        settingmount = "automount"
        settingmountopen = "automount-open"
        settingautorun = "autorun-never"
        mountPattern = '/org/gnome/desktop/media-handeling/aoutomount'
        mountOpenPattern = "/org/gnome/desktop/media-handeling/automount-open"
        autorunPattern = "/org/gnome/desktop/media-handeling/autorun-never"
        
        keyfileDirectorymount =getDirectory(directoryPath,settingmount)
        keyfileDirectorymountOpen = getDirectory(directoryPath,settingmountopen)
        keyfileDirectoryautorun = getDirectory(directoryPath,settingautorun)
        patternCheckmount(keyfileDirectorymount,mountPattern,"automount","00-media-automount")
        patternCheckmount(keyfileDirectorymountOpen,mountOpenPattern,"automount-open","00-media-automount")
        patternCheckmount(keyfileDirectoryautorun,autorunPattern,"autorun-never","00-media-autorun")
    else:
        print(" - GNOME Desktop Manager package is not installed on the system\n - Recommendation is not applicable")

def systemdTimesyncdEnabled():
    isEnabled = subprocess.run(["systemctl", "is-enabled", "systemd-timesyncd.service"], text=True, capture_output=True)
    isActive = subprocess.run(["systemctl", "is-active", "systemd-timesyncd.service"], text=True, capture_output=True)

    if isEnabled.stdout.strip() == "enabled":
        print("systemd-timesyncd.service is enabled\n")
    else:
        print("Enabling systemd-timesyncd.service\n")
        subprocess.run(["systemctl", "unmask", "systemd-timesyncd.service"])

    if isActive.stdout.strip() == "active":
        print("systemd-timesyncd.service is active\n")
    else:
        print("Activating systemd-timesyncd.service\n")
        subprocess.run(["systemctl", "--now", "enable", "systemd-timesyncd.service"])

def AuthTSforsystemdtimesyncd():
    ntpTS = "time.nist.gov"
    ntpFB = "time-a-g.nist.gov time-b-g.nist.gov time-d-g.nist.gov"
    findTS = "NTP="
    findFB = "FallbackNTP="
    confFile = ""
    timeDir = "/etc/systemd/timesyncd.conf.d"
    timeDropin = "/etc/systemd/timesyncd.conf.d/50-timesyncd.conf"

    for root,dirs,files in os.walk("/etc/systemd/"):
        for file in files:
            if file.endswith(".conf"):
                filepath = os.path.join(root,file)
                try:
                    for line in open(filepath,"r").readlines():
                        if findTS in line or findFB in line:
                            confFile = filepath
                            break
                except:
                    continue
    print(confFile)
    with open(confFile,"r") as timeFile:
        timeLines = timeFile.readlines()

    for i in range(len(timeLines)):
        if findTS in timeLines[i]:
            if ntpTS in timeLines[i]:
                print("NTP time server is set")
                break
            else:
                print("Setting NTP time Server")
                timeLines[i] = f"NTP=time.nist.gov\n"
                break
    for i in range(len(timeLines)):
        if findFB in timeLines[i]:
            if ntpFB in timeLines[i]:
                print("fallback  NTP servers are set ")
                break
            else:
                print("Setting NTP fallback Servers")
                timeLines[i] = f"FallbackNTP=time-a-g.nist.gov time-b-g.nist.gov time-d-g.nist.gov\n"
                break
    with open(confFile, "w") as timeFile:
        timeFile.writelines(timeLines)
    flag=0
    if os.path.isdir(timeDir):
        for file in os.listdir(timeDir):
            filepath = os.path.join(timeDir,file)
            for line in open(filepath, "r").readlines():
                if ntpTS in line:
                    print(f"time server set at in drop-in file  {filepath}")
                    flag+=1
                if ntpFB in line:
                    print(f"Fallback time sever server set in drop-in file {filepath}")
                    flag+=1
                if flag==2:
                    break
            if flag==2:
                break
    else:
        os.makedirs(timeDir)
        print("creating/updating drop-in files for NTP time servers and fallback server")
        with open(timeDropin,"w") as timeFile:
            timeFile.write(f"[Time]\n{findTS+ntpTS}\n{findFB+ntpFB}")
    os.system("systemctl try-reload-or-restart systemd-timesyncd")

#function to remove unessesarry packages
def removePackages():
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



disable_filesystem_loading()
disable_autofs()
installingAIDE()
schedulingAideChecks()
bootloaderPassword()
bootconfigPermission()
setTerminalvalue()
prelinkRmBinaryrestore()
disableAutomaticErrorReporting()
coreDumpRestriction()
configureApparmor()
cmdLineBanners()
loginBannerMsg()
disableLoginUserList()
screenLockIdle()
screenLockFile()
disableAutoMounting()
mountLockFile()
systemdTimesyncdEnabled()
AuthTSforsystemdtimesyncd()
removePackages()
localonlyMTA()



