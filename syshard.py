import subprocess
import getpass
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
     cmd1 = ["chown" "root:root" "/boot/grub/grub.cfg"]
     cmd2 = ["chmod" "u-wx,go-rwx" "/boot/grub/grub.cfg"]
     subprocess.run(cmd1)
     subprocess.run(cmd2)