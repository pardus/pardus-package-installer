#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:58:17 2020

@author: fatih
"""
import apt_pkg
import os
import subprocess
import sys


def main():
    def check_package_size(debianpackage, expected_size):
        try:
            return os.path.isfile(debianpackage) and os.path.getsize(debianpackage) == expected_size
        except OSError:
            return False

    def control_lock():
        apt_pkg.init_system()
        try:
            apt_pkg.pkgsystem_lock()
        except SystemError:
            return False
        apt_pkg.pkgsystem_unlock()
        return True

    def install(debianpackage):
        subprocess.call(["apt", "install", debianpackage, "-yq", "-o", "APT::Status-Fd=2",
                         "-o", "Dpkg::Options::=--force-confnew"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def reinstall(debianpackage):
        subprocess.call(
            ["apt", "install", "--reinstall", "--allow-downgrades", debianpackage, "-yq", "-o", "APT::Status-Fd=2",
             "-o", "Dpkg::Options::=--force-confnew"],
            env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def remove(packagename):
        subprocess.call(["apt", "remove", "--purge", packagename, "-yq", "-o", "APT::Status-Fd=2",
                         "-o", "Dpkg::Options::=--force-confnew"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def downgrade(packagename):
        subprocess.call(["apt", "install", "--allow-downgrades", packagename, "-yq", "-o", "APT::Status-Fd=2",
                         "-o", "Dpkg::Options::=--force-confnew"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    if len(sys.argv) < 2:
        print("no argument passed")
        sys.exit(2)

    action = sys.argv[1]

    if action in ("install", "reinstall", "downgrade"):
        if len(sys.argv) != 4:
            print("invalid arguments")
            sys.exit(2)

        debianpackage = sys.argv[2]

        try:
            expected_size = int(sys.argv[3])
        except ValueError:
            print("invalid package size")
            sys.exit(3)

        if expected_size < 0:
            print("invalid package size")
            sys.exit(3)

    elif action == "remove":
        if len(sys.argv) != 3:
            print("invalid arguments")
            sys.exit(2)

    else:
        print("invalid action")
        sys.exit(2)

    if not control_lock():
        print("lock error")
        sys.exit(1)

    if action in ("install", "reinstall", "downgrade"):
        if not check_package_size(debianpackage, expected_size):
            print("package file size changed")
            sys.exit(3)

    if action == "install":
        install(debianpackage)
    elif action == "remove":
        remove(sys.argv[2])
    elif action == "reinstall":
        reinstall(debianpackage)
    elif action == "downgrade":
        downgrade(debianpackage)


if __name__ == "__main__":
    main()
