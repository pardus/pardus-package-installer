#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
from setuptools import setup, find_packages


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "pardus-package-installer.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pardus-package-installer.mo"]))
    return mo


changelog = "debian/changelog"
version = "0.1.0"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
    ("/usr/share/applications", ["tr.org.pardus.package-installer.desktop"]),
    ("/usr/share/locale/tr/LC_MESSAGES", ["po/tr/pardus-package-installer.mo"]),
    ("/usr/share/pardus/pardus-package-installer/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/pardus/pardus-package-installer/src",
     ["src/Actions.py", "src/Main.py", "src/MainWindow.py", "src/__version__"]),
    ("/usr/bin", ["pardus-package-installer"]),
    ("/usr/share/polkit-1/actions", ["tr.org.pardus.pkexec.pardus-package-installer.policy"]),
    ("/usr/share/icons/hicolor/scalable/apps/", ["images/pardus-package-installer.svg"])
] + create_mo_files()

setup(
    name="Pardus Package Installer",
    version=version,
    packages=find_packages(),
    scripts=["pardus-package-installer"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Fatih Altun",
    author_email="fatih.altun@pardus.org.tr",
    description="Pardus Deb Package Installer.",
    license="GPLv3",
    keywords="deb package installer",
    url="https://github.com/pardus/pardus-package-installer",
)
