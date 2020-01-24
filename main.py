#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:58:17 2020

@author: fatih
"""

"""

VERSION_NEWER = 3

VERSION_NONE = 0

VERSION_OUTDATED = 1

VERSION_SAME = 2

"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk




import apt.debfile as aptdeb

import apt


# def main():
debianpackage = "/home/fatih/Desktop/pdebi/game.deb"

package = aptdeb.DebPackage(debianpackage)

packagename = package.pkgname

installable = package.check()

packagestatus = package.compare_to_version_in_cache()


def installPackage():
    
    if installable:
        package.install()

def removePackage():
    cache = apt.Cache()
    cache.open()
    if cache[packagename].is_installed:
        cache[packagename].mark_delete()
        cache.commit()





if packagestatus == 0:
    print("not installed")
    # installPackage()
elif packagestatus == 1:
    print("outdated")
elif packagestatus == 2:
    print("same version")
    # removePackage()
elif packagestatus == 3:
    print("newer version")
    
    

    
class Handler:
    def onDestroy(self, window):
        Gtk.main_quit()

    def onButtonPressed(self, button):
        print("Hello World!")

builder = Gtk.Builder()
builder.add_from_file("main.glade")
builder.connect_signals(Handler())

window = builder.get_object("mainwindow")
window.show_all()

Gtk.main()



# if __name__ == "__main__":
#     main()
