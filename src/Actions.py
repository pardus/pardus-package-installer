#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:58:17 2020

@author: fatih
"""
import apt_pkg
import os
import re
import subprocess
import sys

ALLOWED_ACTIONS = {"install", "remove", "reinstall", "downgrade"}
PACKAGE_NAME_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+.-]*$")


def control_lock():
    apt_pkg.init_system()
    try:
        apt_pkg.pkgsystem_lock()
    except SystemError:
        return False
    apt_pkg.pkgsystem_unlock()
    return True


def validate_package_arg(action, package_arg):
    if not package_arg or package_arg.startswith("-") or "\n" in package_arg or "\r" in package_arg:
        return False

    if action == "remove":
        return bool(PACKAGE_NAME_REGEX.match(package_arg))

    # For install, reinstall, downgrade: can be a local .deb file or repository package name
    if package_arg.endswith(".deb"):
        return os.path.isfile(package_arg)
    return bool(PACKAGE_NAME_REGEX.match(package_arg))


def install(debianpackage):
    cmd = [
        "apt", "install", "-yq",
        "-o", "APT::Status-Fd=2",
        "-o", "Dpkg::Options::=--force-confnew",
        "--", debianpackage
    ]
    return subprocess.call(cmd, env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})


def reinstall(debianpackage):
    cmd = [
        "apt", "install", "--reinstall", "--allow-downgrades", "-yq",
        "-o", "APT::Status-Fd=2",
        "-o", "Dpkg::Options::=--force-confnew",
        "--", debianpackage
    ]
    return subprocess.call(cmd, env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})


def remove(packagename):
    cmd = [
        "apt", "remove", "--purge", "-yq",
        "-o", "APT::Status-Fd=2",
        "-o", "Dpkg::Options::=--force-confnew",
        "--", packagename
    ]
    return subprocess.call(cmd, env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})


def downgrade(packagename):
    cmd = [
        "apt", "install", "--allow-downgrades", "-yq",
        "-o", "APT::Status-Fd=2",
        "-o", "Dpkg::Options::=--force-confnew",
        "--", packagename
    ]
    return subprocess.call(cmd, env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})


def main():
    if len(sys.argv) < 3:
        sys.stderr.write(f"Usage: {sys.argv[0]} <install|remove|reinstall|downgrade> <package>\n")
        sys.exit(1)

    action = sys.argv[1].strip()
    target = sys.argv[2].strip()

    if action not in ALLOWED_ACTIONS:
        sys.stderr.write(f"Error: Unsupported action '{action}'. Allowed: {', '.join(sorted(ALLOWED_ACTIONS))}\n")
        sys.exit(1)

    if not validate_package_arg(action, target):
        sys.stderr.write(f"Error: Invalid or nonexistent package argument '{target}'.\n")
        sys.exit(1)

    if not control_lock():
        sys.stderr.write("Error: APT system lock could not be acquired.\n")
        sys.exit(1)

    if action == "install":
        rc = install(target)
    elif action == "remove":
        rc = remove(target)
    elif action == "reinstall":
        rc = reinstall(target)
    elif action == "downgrade":
        rc = downgrade(target)
    else:
        rc = 1

    sys.exit(rc)


if __name__ == "__main__":
    main()
