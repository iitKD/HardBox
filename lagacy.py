import subprocess
import re
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
    subprocess.run(['mount', '-o', 'remount', '/tmp'])

edit_fstab_add_nosuid()

def create_partition(device, size):
    try:

        fdisk_input = f"n\np\n\n\n+{size}\n\nw\n".encode()
        fdisk_process = subprocess.Popen(['fdisk', device], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        fdisk_process.communicate(fdisk_input)
        fdisk_output = subprocess.check_output(['fdisk', '-l', device]).decode('utf-8')
        partition_name = re.findall(r'^{}(\d+)'.format(device), fdisk_output, re.MULTILINE)[-1] 
        return partition_name
    except Exception as e:
        print("Error:", e)
        return None


device = '/dev/sda'
size  = "20G"#
direc = "/tmp"
partition_name = create_partition(device, size)
if partition_name:
    print("New partition created:", device + partition_name)
    deviceName = device+partition_name
    makefilesystem = subprocess.run(["mkfs.ext4",deviceName], capture_output=True)
    makedir = subprocess.run(["mkdir", f"/{direc[-3:]}"],capture_output=True)
    if makefilesystem.returncode ==0:
        mountFs = subprocess.run(["mount", deviceName,f"/{direc[-3:]}"])

