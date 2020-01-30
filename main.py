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
import gi,apt,os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
import apt.debfile as aptdeb


def main():

    class GAsyncSpawn(GObject.GObject):
        """ GObject class to wrap GLib.spawn_async().
        
        Use:
            s = GAsyncSpawn()
            s.connect('process-done', mycallback)
            s.run(command)
                #command: list of strings
        """
        __gsignals__ = {
            'process-done' : (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE,
                                (GObject.TYPE_INT, )),
            'stdout-data'  : (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE,
                                (GObject.TYPE_STRING, )),
            'stderr-data'  : (GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE,
                                (GObject.TYPE_STRING, )),
        }
        def __init__(self):
            GObject.GObject.__init__(self)
    
        def run(self, cmd):
            r  = GLib.spawn_async(cmd,flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD, standard_output=True, standard_error=True)
            self.pid, idin, idout, iderr = r        
            fout = os.fdopen(idout, "r")
            ferr = os.fdopen(iderr, "r")
    
            GLib.child_watch_add(self.pid,self._on_done)
            GLib.io_add_watch(fout, GLib.IO_IN, self._on_stdout)
            GLib.io_add_watch(ferr, GLib.IO_IN, self._on_stderr)
            return self.pid
    
        def _on_done(self, pid, retval, *argv):
            self.emit("process-done", retval)
    
        def _emit_std(self, name, value):
            self.emit(name+"-data", value)
        
        def _on_stdout(self, fobj, cond):
            self._emit_std("stdout", fobj.readline())
            return True
    
        def _on_stderr(self, fobj, cond):
            self._emit_std("stderr", fobj.readline())
            return True
        
    
    debianpackage = "/home/fatih/Desktop/pdebi/game16.deb"
    
    package = aptdeb.DebPackage(debianpackage)
    
    packagename = package.pkgname
    
    firststatus = package.compare_to_version_in_cache()
    
    installable = package.check()
    
    packageversion = package._sections["Version"]
    packagedescription = package._sections["Description"]
    
    
    def cacheControl():
        cache = apt.Cache()
        cache.open()
        return aptdeb.DebPackage(debianpackage).compare_to_version_in_cache()
    
    def installPackage():
        
        if installable:
    
            spinner.start()
            
            button1.set_sensitive(False)
            button2.set_sensitive(False)
            
            command = ["/usr/bin/pkexec", "/usr/bin/pdebi-gtk", "install", debianpackage]
            
            pid = spawn.run(command)
            
            print(pid)
    
    def removePackage():
        cache = apt.Cache()
        cache.open()
        if cache[packagename].is_installed:
            
            spinner.start()
            
            button1.set_sensitive(False)
            button2.set_sensitive(False)
            
            command = ["/usr/bin/pkexec", "/usr/bin/pdebi-gtk", "remove", packagename]
            
            pid = spawn.run(command)
            
            print(pid)
            
    def reinstallPackage():
    
        spinner.start()
        
        button1.set_sensitive(False)
        button2.set_sensitive(False)
        
        command = ["/usr/bin/pkexec", "/usr/bin/pdebi-gtk", "reinstall", debianpackage]
        
        pid = spawn.run(command)
        
        print(pid)
            
    def downgradePackage():
        
        spinner.start()
        
        button1.set_sensitive(False)
        button2.set_sensitive(False)
        
        command = ["/usr/bin/pkexec", "/usr/bin/pdebi-gtk", "downgrade", debianpackage]
        
        pid = spawn.run(command)
        
        print(pid)
    
    
    class Handler:
        def onDestroy(self, window):
            Gtk.main_quit()
    
        def onButton1Clicked(self, button1):
            
            packagestatus = cacheControl()
            
            if packagestatus == 0:
                print("Installing Button Clicked")
                installPackage()
    
            elif packagestatus == 1:
                print("Downgrading Button Clicked")
                downgradePackage()
    
            elif packagestatus == 2:
                print("Reinstalling Button Clicked")
                reinstallPackage()
    
            elif packagestatus == 3:
                print("Upgrading Button Clicked")
                installPackage()
    
        def onButton2Clicked(self, button2):
                print("Uninstalling Button Clicked")
                removePackage()
    
    builder = Gtk.Builder()
    builder.add_from_file("/home/fatih/Desktop/pdebi/main.glade")
    builder.connect_signals(Handler())
    
    window = builder.get_object("mainwindow")
    
    button1 = builder.get_object("button1")
    button2 = builder.get_object("button2")
    
    label1 = builder.get_object("label1")
    label2 = builder.get_object("label2")
    
    spinner = builder.get_object("spinner")
    
    textview = builder.get_object("textview")
    
    installicon = builder.get_object("install_icon")
    upgradeicon = builder.get_object("upgrade_icon")
    downgradeicon = builder.get_object("downgrade_icon")
    reinstallicon = builder.get_object("reinstall_icon")
    
    
    def packageMain(actioned,status):
        if actioned is True:
            
            if status == 0:
                button1.set_sensitive(True)
                button1.set_label("Install")
                button1.set_image(installicon)
                button2.set_sensitive(False)
            elif status == 1:
                button1.set_sensitive(True)
                button1.set_label("Downgrade")
                button1.set_image(downgradeicon)
                button2.set_sensitive(True)
            elif status == 2:
                button1.set_sensitive(True)
                button1.set_label("Reinstall")
                button1.set_image(reinstallicon)
                button2.set_sensitive(True)
            elif status == 3:
                button1.set_sensitive(True)
                button1.set_label("Upgrade")
                button1.set_image(upgradeicon)
                button2.set_sensitive(True)
        
        else:
            
            if firststatus == 0:
                button1.set_sensitive(True)
                button1.set_label("Install")
                button2.set_sensitive(False)
            elif firststatus == 1:
                button1.set_sensitive(True)
                button1.set_label("Downgrade")
                button1.set_image(downgradeicon)
            elif firststatus == 2:
                button1.set_sensitive(True)
                button1.set_label("Reinstall")
                button1.set_image(reinstallicon)
            elif firststatus == 3:
                button1.set_sensitive(True)
                button1.set_label("Upgrade")
                button1.set_image(upgradeicon)
    

    def on_process_done(sender, retval):
        spinner.stop()
        textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)
        print("Done. exit code: %s" % (retval))
        if retval == 0:
            textview.get_buffer().insert(textview.get_buffer().get_end_iter(),  "Operation was successfully completed ! \n \n")
            textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)
        packageMain(True,cacheControl())
    
    def on_stdout_data(sender, line):
        textview.get_buffer().insert(textview.get_buffer().get_end_iter(),  line)
        textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)
    
    def on_stderr_data(sender, line):
        if line is not None:
            print("Error : " +line)
        

    spawn = GAsyncSpawn()
    spawn.connect("process-done", on_process_done)
    spawn.connect("stdout-data", on_stdout_data)
    spawn.connect("stderr-data", on_stderr_data)
    
    label1.set_text(packagename + " ( " + packageversion + " )")
    label2.set_text("Description : " + packagedescription )
    
    packageMain(False,5)
    
    window.show_all()
    
    Gtk.main()



if __name__ == "__main__":
    main()
