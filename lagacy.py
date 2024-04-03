import subprocess
import shutil

def edit_fstab_add_nosuid():
    fstab_path = 'new.txt'
    flag=0
    optionsList = ["nosuid", "noexec", "nodev"]
    fsysList = ["/temp", "/var", "/var/tmp", "/var/log"]
    with open(fstab_path, 'r') as f:
        fstab_content = f.readlines()
    for i in range(len(fstab_content)):

        fields = fstab_content[i].split()
    
        if len(fields) >= 2 and fields[1] == '/tmp':
            flag=1
            for j in optionsList:
                if j not in fields[3]:
                    fields[3] += ','+j
                    fstab_content[i] = ' '.join(fields) + '\n'
                
    if flag==1:
        with open(fstab_path, 'w') as f:
            f.writelines(fstab_content)

def remount_tmp():
    # Run the mount command to remount /tmp
    subprocess.run(['mount', '-o', 'remount', '/tmp'])


edit_fstab_add_nosuid()


