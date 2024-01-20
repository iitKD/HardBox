import os
import subprocess
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