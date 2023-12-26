#!/usr/bin/env python

import subprocess
import sys
def disable_filesystem_loading(l_mname):
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
    # except FileNotFoundError:
    #     with open(modprobe_conf_path, 'w') as f:
    #         print(f" - deny listing \"{l_mname}\"")
    #         f.write(blacklist_line)

if __name__ == "__main__":
    while True:
        print("Select an option:")
        print("1 to disable SquashFS")
        print("2 to disable cramFs")
        print("3 to disable udf")
        print("4 to disable all 3")
        print("Selcet 5 to exit")

        try:
            choice = int(input("Enter your choice:"))
        except ValueError:
            print("Invalid Choice please select from given options.")
            continue

        if choice==1:
            disable_filesystem_loading("squashfs")
        elif choice==2:
            disable_filesystem_loading("cramfs")
        elif choice==3:
            disable_filesystem_loading("udf")
        elif choice==4:
            disable_filesystem_loading("squashfs")
            disable_filesystem_loading("cramfs")
            disable_filesystem_loading("udf")
        elif choice==5:
            print("Exiting...")
            sys.exit(0)

# the above function can be called for "cramfs", "squashfs" and "udf" for Ubuntu.