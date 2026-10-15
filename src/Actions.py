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
    def control_lock():
        apt_pkg.init_system()
        try:
            apt_pkg.pkgsystem_lock()
        except SystemError:
            return False
        apt_pkg.pkgsystem_unlock()
        return True

    def install(debianpackage):
        return subprocess.call(["apt", "install", debianpackage, "-yq", "-o", "APT::Status-Fd=2",
                         "-o", "Dpkg::Options::=--force-confnew"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def reinstall(debianpackage):
        return subprocess.call(
            ["apt", "install", "--reinstall", "--allow-downgrades", debianpackage, "-yq", "-o", "APT::Status-Fd=2",
             "-o", "Dpkg::Options::=--force-confnew"],
            env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def remove(packagename):
        return subprocess.call(["apt", "remove", "--purge", packagename, "-yq", "-o", "APT::Status-Fd=2",
                         "-o", "Dpkg::Options::=--force-confnew"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def downgrade(packagename):
        return subprocess.call(["apt", "install", "--allow-downgrades", packagename, "-yq", "-o", "APT::Status-Fd=2",
                         "-o", "Dpkg::Options::=--force-confnew"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    actions = {"install": install, "remove": remove,
               "reinstall": reinstall, "downgrade": downgrade}
    if len(sys.argv) != 3 or sys.argv[1] not in actions:
        print("expected an action and a package", file=sys.stderr)
        return 2
    if not control_lock():
        print("lock error")
        return 1
    return actions[sys.argv[1]](sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
