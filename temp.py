import os
import re
from subprocess import check_output

def check_grub_config():
  """Checks if Grub configuration disables IPv6."""
  grub_file = next(
      (f for f in os.listdir('/boot') if f in ['grubenv', 'grub.conf', 'grub.cfg']), None)
  if grub_file:
    with open(os.path.join('/boot', grub_file), 'r') as f:
      for line in f:
        if re.search(r"^\s*(kernelopts=|linux|kernel)", line):
          if re.search(r"ipv6\.disable=1", line):
            return f"IPv6 Disabled in \"/boot/{grub_file}\""
  return None


def check_sysctl_config():
    """Checks if sysctl configuration disables IPv6."""
    search_dirs = [
        "/run/sysctl.d", "/etc/sysctl.d",
        "/usr/local/lib/sysctl.d", "/usr/lib/sysctl.d",
        "/lib/sysctl.d", "/etc/",
    ]
    disabled_all = disabled_default = False
  
    for dir in search_dirs:
        try:
            for file in os.listdir(dir):
                if file.endswith(".conf"):
                    with open(os.path.join(dir, file), 'r') as f:
                        for line in f:
                            if line.startswith("#"):
                                continue
                            if re.match(r"^\s*net\.ipv6\.conf\.all\.disable_ipv6\s*=\s*1\s*$", line):
                                disabled_all = True
                            if re.match(r"^\s*net\.ipv6\.conf\.default\.disable_ipv6\s*=\s*1\s*$", line):
                                disabled_default = True
        except FileNotFoundError:
            continue
    if disabled_all and disabled_default:
        output_all = check_output(["sysctl", "net.ipv6.conf.all.disable_ipv6"]).decode()
        output_default = check_output(["sysctl", "net.ipv6.conf.default.disable_ipv6"]).decode()
        if re.search(r"^\s*net\.ipv6\.conf\.all\.disable_ipv6\s*=\s*1\s*$", output_all) \
            and re.search(r"^\s*net\.ipv6\.conf\.default\.disable_ipv6\s*=\s*1\s*$", output_default):
            return "ipv6 disabled in sysctl config"
    return None


message_grub = check_grub_config()
message_sysctl = check_sysctl_config()

if message_grub:
    print(f"\nIPv6 Disabled: {message_grub}")
elif message_sysctl:
    print(f"\n{message_sysctl}")
else:
    print("\nIPv6 is enabled on the system")
