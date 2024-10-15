# HardBox: Linux System Hardening Tool

## Overview
**HardBox** is an automated system hardening tool for Linux systems, specifically designed for Ubuntu 22.04. It implements security configurations based on the Center for Internet Security (CIS) benchmarks, helping you strengthen your system's security posture.

## Features
- **Automated Hardening**: Applies CIS benchmark recommendations to secure your Ubuntu system.
- **CIS Compliance**: Achieves compliance with Level 1 and Level 2 server and workstation profiles.
- **Customizable**: Modular design allows customization based on your specific needs.
- **Detailed Logs**: Provides detailed logs for auditing and review.
- **Rollback Functionality**: Easily revert changes if needed.
- **Pre-checks**: Ensures the system is ready for the hardening process before applying changes.

## Supported System
- **Operating System**: Ubuntu 22.04 LTS
- **CIS Benchmark**: Level 1 and Level 2 profiles

## Prerequisites
- Ubuntu 22.04 LTS
- Root or sudo privileges
- Python 3.8+ installed

## Installation

1. Clone the HardBox repository:
   ```bash
   git clone https://github.com/yourusername/HardBox.git
   cd HardBox
   ```

2. Install necessary dependencies:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```

3. Run HardBox:
   ```bash
   sudo python3 hardening.py
   ```



## Key CIS Benchmark Implementations
HardBox applies a variety of hardening measures, such as:
- User and Group Security
- File Permissions
- Network Security (Firewall and Configuration)
- System Logging and Monitoring
- Service and Process Security
- System Integrity Verification

For a comprehensive list, refer to the CIS Benchmark documentation or the code within `hardening.py`.

## Contributing
Contributions are welcome! If you'd like to contribute to HardBox, feel free to open an issue or submit a pull request.
