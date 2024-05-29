#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 13 01:20:31 2020

@author: fatih
"""

import os.path
import sys

import gi

from MainWindow import MainWindow

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk, GLib


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="tr.org.pardus.package-installer",
                         flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE, **kwargs)
        self.window = None
        self.emptyfile = None
        GLib.set_prgname("tr.org.pardus.package-installer")

    def do_activate(self):
        self.window = MainWindow(self, self.emptyfile)

    def do_open(self, files, filecount, hint):
        if filecount == 1:
            file = files[0]
            if os.path.exists(file.get_path()):
                fileFormat = file.get_basename().split(".")[-1]
                if fileFormat == "deb":
                    self.window = MainWindow(self, file)
                else:
                    print("Only .deb files.")
            else:
                print("File not exists : " + file.get_path())
        else:
            print("Only one file.")


app = Application()
app.run(sys.argv)
