#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:58:17 2020

@author: fatih
"""
import subprocess, sys, os


def main():
    def install(debianpackage):
        subprocess.call(["apt", "install", debianpackage, "-yq", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def reinstall(debianpackage):
        subprocess.call(["apt", "install", "--reinstall", debianpackage, "-yq", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def remove(packagename):
        subprocess.call(["apt", "remove", "--purge", packagename, "-yq", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    def downgrade(packagename):
        subprocess.call(["apt", "install", "--allow-downgrades", packagename, "-yq", "-o", "APT::Status-Fd=2"],
                        env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

    if len(sys.argv) > 1:
        if (sys.argv[1] == "install"):
            install(sys.argv[2])
        elif (sys.argv[1] == "remove"):
            remove(sys.argv[2])
        elif (sys.argv[1] == "reinstall"):
            reinstall(sys.argv[2])
        elif (sys.argv[1] == "downgrade"):
            downgrade(sys.argv[2])
    else:
        print("no argument passed")


if __name__ == "__main__":
    main()
