#!/usr/bin/env python

import os
def patternCheck(directory,pattern,something):
    if not directory:
            print(f" idle-delay is not set, so it cannot be locked\n - Please follow Recommendation \"Ensure GDM screen locks when the user is idle\" and follow this Recommendation again")
    else:
        for root,dirs, files in os.walk(directory):
            for file in files:
                path = os.path.join(root,file)
                try:
                    for line in open(path,"r").readlines():
                        if pattern in line:
                                print(f" \"ideal-delay\" is locked in {path} ")
                                return
                except:
                    continue
        print(f"Creating entry to lock idel-delay")
        path = os.path.join(directory, 'locks', '00-screensaver')
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
        patternCheck(keyfileDirectoryidle,idledelayPattern,"idle")
        patternCheck(keyfileDirectorylock,lockdelayPattern,"lock")
        os.system("dconf update")
    else:
        print(" - GNOME Desktop Manager package is not installed on the system\n - Recommendation is not applicable")