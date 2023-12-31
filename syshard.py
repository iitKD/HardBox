#disabling automounting of file systems
import subprocess
def disable_autofs():
    depRes = subprocess.run(["apt-cache", "depends", "autofs"], capture_output=True, text=True)
    rdepRes = subprocess.run(["apt-cache", "depends", "autofs"], capture_output=True, text=True)

    if "Depnds" in depRes.stdout or "Reverse Depends" in rdepRes.stdout:
        subprocess.run(["system", "stop", "autofs"])
        subprocess.run(["system", "mask", "autofs"])
    else:
        print("No dependencies found, uninstalling  autofs")
        subprocess.run(["apt", "purge", "autofs"])


