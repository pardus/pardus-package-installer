# Pardus Package Installer

Pardus Package Installer is a application for install, uninstall or view deb packages.

It is currently a work in progress. Maintenance is done by <a href="https://www.pardus.org.tr/">Pardus</a> team.

## **Dependencies**

This application is developed based on Python3 and GTK+ 3. Dependencies:
```bash
gir1.2-glib-2.0 gir1.2-gtk-3.0 gir1.2-notify-0.7 python3-apt
```

### **Run Application from Source**

Install dependencies
```bash
gir1.2-glib-2.0 gir1.2-gtk-3.0 gir1.2-notify-0.7 python3-apt
```
Clone the repository
```bash
git clone https://github.com/pardus/pardus-package-installer.git ~/pardus-package-installer
```
Run application
```bash
python3 ~/pardus-package-installer/src/Main.py
```

### **Build deb package**

```bash
sudo apt install devscripts git-buildpackage
sudo mk-build-deps -ir
gbp buildpackage --git-export-dir=/tmp/build/pardus-package-installer -us -uc
```

### **Tests**

With the application dependencies and `xvfb` installed, run as a regular user:

```bash
python3 tests/actions.py
xvfb-run -a python3 tests/operation_result.py
```

These tests cover helper exit statuses and the GTK operation result, including
warning messages, failed removal, authorization cancellation, and draining both
output pipes before completion. APT and privilege escalation are mocked; the
pipe tests run harmless Python children. No packages are installed or removed.

### **Screenshots**

![Pardus Package Installer 1](screenshots/pardus-package-installer-1.png)

![Pardus Package Installer 2](screenshots/pardus-package-installer-2.png)

![Pardus Package Installer 3](screenshots/pardus-package-installer-3.png)

![Pardus Package Installer 4](screenshots/pardus-package-installer-4.png)

![Pardus Package Installer 5](screenshots/pardus-package-installer-5.png)

![Pardus Package Installer 6](screenshots/pardus-package-installer-6.png)
