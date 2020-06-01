#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

data_files = [
    ("/usr/share/applications", ["tr.org.pardus.package-installer.desktop"]),
    ("/usr/share/locale/tr/LC_MESSAGES", ["po/tr/pardus-package-installer.mo"]),
    ("/usr/share/pardus/pardus-package-installer", ["ui/MainWindow.glade", "icon.svg", "actions.py"]),
    ("/usr/bin", ["pardus-package-installer-action"]),
    ("/usr/share/polkit-1/actions", ["tr.org.pardus.pkexec.pardus-package-installer.policy"])
]

setup(
    name="Pardus Package Installer",
    version="0.2.0~Beta1",
    packages=find_packages(),
    scripts=["pardus-package-installer"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Fatih Altun",
    author_email="fatih.altun@pardus.org.tr",
    description="Pardus Deb Package Installer.",
    license="GPLv3",
    keywords="deb package installer",
    url="https://www.pardus.org.tr",
)
