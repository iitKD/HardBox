import os
settingIdle = "idle-delay = uint32"
for root,dirs,files in os.walk("/mnt/c/Users/kunda/Desktop/Minor project/"):
    for file in files:
        filepath = os.path.join(root,file)
        try:
            for line in open(filepath,"r").readlines():
                if settingIdle in line:
                    print(filepath)
                    break
        except:
            continue