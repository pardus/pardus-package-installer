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
import gi,apt,os,sys
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
        
    
    # debianpackage = "/home/pardus/Masaüstü/pdebi/black.deb"
        
    debianpackage = ""
    
    installable = False
    
    packagename = ""
        
    def start(debpackage):
    
        package = aptdeb.DebPackage(debpackage)
        
        packagename = package.pkgname
        
        firststatus = package.compare_to_version_in_cache()
        
        installable = package.check()
        
        packageversion = package._sections["Version"]
        packagedescription = package._sections["Description"]
        
        return package,packagename,firststatus,installable,packageversion,packagedescription
    
    
    def cacheControl():
        cache = apt.Cache()
        cache.open()
        return aptdeb.DebPackage(debianpackage).compare_to_version_in_cache()
    
    def installPackage():
        
        if installable:
    
            spinner.start()
            progress.set_text("Installing..")
            
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
            progress.set_text("Uninstalling..")
            
            button1.set_sensitive(False)
            button2.set_sensitive(False)
            
            command = ["/usr/bin/pkexec", "/usr/bin/pdebi-gtk", "remove", packagename]
            
            pid = spawn.run(command)
            
            print(pid)
            
    def reinstallPackage():
    
        spinner.start()
        progress.set_text("Reinstalling..")
        
        button1.set_sensitive(False)
        button2.set_sensitive(False)
        
        command = ["/usr/bin/pkexec", "/usr/bin/pdebi-gtk", "reinstall", debianpackage]
        
        pid = spawn.run(command)
        
        print(pid)
            
    def downgradePackage():
        
        spinner.start()
        progress.set_text("Downgrading..")
        
        button1.set_sensitive(False)
        button2.set_sensitive(False)
        
        command = ["/usr/bin/pkexec", "/usr/bin/pdebi-gtk", "downgrade", debianpackage]
        
        pid = spawn.run(command)
        
        print(pid)
    
    
    class Handler:
        def onDestroy(self, window):
            Gtk.main_quit()
    
        def onButton1Clicked(self, button1):
            
            print("debianpackage = " + debianpackage)
            
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

        def onOpenClicked(self, openbutton):
            filechooser.run()
            filechooser.hide()
            print("Open Button Clicked")
            
        def onSelectClicked(self, openbutton):
            filename = filechooser.get_filename()
            filechooser.hide()
            fromFile(filename)
            print("Select Button Clicked")    
            
        def onActivated(self, openbutton):
            filename = filechooser.get_filename()
            filechooser.hide()
            fromFile(filename)
            print("Active Button Clicked")  
        
    
    builder = Gtk.Builder()
    builder.add_from_file("/home/pardus/Masaüstü/pdebi/main.glade")
    builder.connect_signals(Handler())
    
    window = builder.get_object("mainwindow")
    
    button1 = builder.get_object("button1")
    button2 = builder.get_object("button2")
    openbutton = builder.get_object("openbutton")
    filechooser = builder.get_object("filechooser")
    selectbutton = builder.get_object("selectbutton")


    label1 = builder.get_object("label1")
    label2 = builder.get_object("label2")
    
    spinner = builder.get_object("spinner")
    progress = builder.get_object("progress")
    
    textview = builder.get_object("textview")
    
    installicon = builder.get_object("install_icon")
    upgradeicon = builder.get_object("upgrade_icon")
    downgradeicon = builder.get_object("downgrade_icon")
    reinstallicon = builder.get_object("reinstall_icon")
    
    installed_version = builder.get_object("installed_version")
    installed_version_title = builder.get_object("installed_version_title")
    
    
    
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
    

    def on_process_done(sender, retval):
        spinner.stop()
        textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)
        print("Done. exit code: %s" % (retval))
        if retval == 0:
            textview.get_buffer().insert(textview.get_buffer().get_end_iter(),  "Operation was successfully completed ! \n \n")
            textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)
        status = cacheControl()
        packageMain(True,status)
        getInstalledVersion(status)
        progress.set_text("Completed")
    
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
    
    
    def getInstalledVersion(status):
        
        if status != 0:

            cache = apt.Cache()
            pkg = cache[packagename]
            systemversion = pkg.versions[0].version
            installed_version.set_text(systemversion)
            
        else:
            installed_version.set_text("Not installed")

    

    if len(sys.argv) > 1:
        
        debianpackage = sys.argv[1]
        aa = start(debianpackage)
        
        firststatus = aa[2]
        packagename = aa[1]
        installable = aa[3]
        packageversion =  aa[4]
        packagedescription = aa[5]
    

        label1.set_text(packagename + " ( " + packageversion + " )")
        label2.set_text(packagedescription )
        
        if firststatus != 0:
            cache = apt.Cache()
            pkg = cache[packagename]
            systemversion = pkg.versions[0].version
            installed_version.set_text(systemversion)
            
        packageMain(False,firststatus)
        
    else:
        
        button1.set_sensitive(False)
        button2.set_sensitive(False)
        button1.set_label("Install")
        button2.set_label("Uninstall")
        label1.set_text("")
        installed_version_title.set_text("")
        installed_version.set_text("")
        
        
    def fromFile(path):
        
        nonlocal debianpackage,packagename,installable,packageversion,packagedescription,firststatus
        
        debianpackage = path

        aa = start(debianpackage)
        
        firststatus = aa[2]
        packagename = aa[1]
        installable = aa[3]
        packageversion =  aa[4]
        packagedescription = aa[5]
    

        label1.set_text(packagename + " ( " + packageversion + " )")
        label2.set_text(packagedescription )
        progress.set_text("")
        
        if firststatus != 0:
            cache = apt.Cache()
            pkg = cache[packagename]
            systemversion = pkg.versions[0].version
            installed_version_title.set_text("Installed Version : ")
            installed_version.set_text(systemversion)
        else:
            installed_version_title.set_text("Installed Version : ")
            installed_version.set_text("Not installed")
            
        packageMain(False,firststatus)
        
        
    


    
    
    window.show_all()
    
    Gtk.main()



if __name__ == "__main__":
    main()
