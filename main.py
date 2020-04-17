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
from gi.repository import Gdk
import apt.debfile as aptdeb

import locale
from locale import gettext as _

locale.bindtextdomain('pdebi', '/usr/share/locale')
locale.textdomain('pdebi')

closestatus = False

error = False

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


    debianpackage = ""
    
    installable = False
    
    packagename = ""

    packagefailure = ""
        
    def start(debpackage):

        package = aptdeb.DebPackage(debpackage)

        packagename = package.pkgname

        firststatus = package.compare_to_version_in_cache()

        installable = package.check()

        try:
            packageversion = package._sections["Version"]
        except:
            packageversion = _("Version is not avaible")

        try:
            packagedescription = package._sections["Description"]
        except:
            packagedescription = _("Description is not avaible")

        try:
            packagemaintainer = package._sections["Maintainer"]
        except:
            packagemaintainer = _("Maintainer is not avaible")

        try:
            packagepriority = package._sections["Priority"]
        except:
            packagepriority = _("Priority is not avaible")

        try:
            packagesection = package._sections["Section"]
        except:
            packagesection = _("Section is not avaible")

        try:
            packagesize = package._sections["Installed-Size"]
        except:
            packagesize = _("Size is not avaible")

        try:
            packagearchitecture = package._sections["Architecture"]
        except:
            packagearchitecture = _("Architecture is not avaible")

        try:
            packagedepends = package._sections["Depends"]
        except:
            packagedepends = ""

        packagemissingdeps = package.missing_deps

        packagefailure = package._failure_string
        
        return package,packagename,firststatus,installable,packageversion,packagedescription,packagefailure,packagemaintainer,packagepriority,packagesection,packagesize,packagearchitecture,packagedepends,packagemissingdeps

    def cacheControl():
        cache = apt.Cache()
        cache.open()
        return aptdeb.DebPackage(debianpackage).compare_to_version_in_cache()
    
    def failureControl():
        return aptdeb.DebPackage(debianpackage)._failure_string

    def installPackage():
        global closestatus
        
        if installable:
    
            spinner.start()
            progress.set_text(_("Installing ..."))
            
            button1.set_sensitive(False)
            button2.set_sensitive(False)
            openbutton.set_sensitive(False)
            quitbutton.set_sensitive(False)

            closestatus = True

            command = ["/usr/bin/pkexec", "/usr/bin/pdebi-action", "install", debianpackage]
            
            pid = spawn.run(command)
            
            print(pid)
    
    def removePackage():
        global closestatus
        cache = apt.Cache()
        cache.open()
        if cache[packagename].is_installed:
            
            spinner.start()
            progress.set_text(_("Uninstalling ..."))
            
            button1.set_sensitive(False)
            button2.set_sensitive(False)
            openbutton.set_sensitive(False)
            quitbutton.set_sensitive(False)

            closestatus = True

            command = ["/usr/bin/pkexec", "/usr/bin/pdebi-action", "remove", packagename]
            
            pid = spawn.run(command)
            
            print(pid)
            
    def reinstallPackage():
        global closestatus
        spinner.start()
        progress.set_text(_("Reinstalling ..."))
        
        button1.set_sensitive(False)
        button2.set_sensitive(False)
        openbutton.set_sensitive(False)
        quitbutton.set_sensitive(False)

        closestatus = True

        command = ["/usr/bin/pkexec", "/usr/bin/pdebi-action", "reinstall", debianpackage]
        
        pid = spawn.run(command)
        
        print(pid)
            
    def downgradePackage():
        global closestatus
        spinner.start()
        progress.set_text(_("Downgrading ..."))
        
        button1.set_sensitive(False)
        button2.set_sensitive(False)
        openbutton.set_sensitive(False)
        quitbutton.set_sensitive(False)

        closestatus = True

        command = ["/usr/bin/pkexec", "/usr/bin/pdebi-action", "downgrade", debianpackage]
        
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

        def onQuitClicked(self, quitbutton):
            Gtk.main_quit()

        def onAboutClicked(self, quitbutton):
            about_dialog.run()
            about_dialog.hide()


    builder = Gtk.Builder()
    builder.add_from_file("/usr/share/pardus/pdebi/main.glade")
    builder.connect_signals(Handler())
    
    window = builder.get_object("mainwindow")
    
    button1 = builder.get_object("button1")
    button2 = builder.get_object("button2")
    openbutton = builder.get_object("openbutton")
    filechooser = builder.get_object("filechooser")
    selectbutton = builder.get_object("selectbutton")
    quitbutton = builder.get_object("quitbutton")
    aboutbutton = builder.get_object("aboutbutton")

    label1 = builder.get_object("label1")
    label2 = builder.get_object("label2")

    maintainer = builder.get_object("maintainer")
    priority = builder.get_object("priority")
    section = builder.get_object("section")
    size = builder.get_object("size")
    architecture = builder.get_object("architecture")
    depends = builder.get_object("depends")
    missingdeps = builder.get_object("missingdeps")
    
    spinner = builder.get_object("spinner")
    progress = builder.get_object("progress")
    
    textview = builder.get_object("textview")
    descriptionscrolledwindow = builder.get_object("descriptionscrolledwindow")

    installicon = builder.get_object("install_icon")
    upgradeicon = builder.get_object("upgrade_icon")
    downgradeicon = builder.get_object("downgrade_icon")
    reinstallicon = builder.get_object("reinstall_icon")
    
    installed_version = builder.get_object("installed_version")
    installed_version_title = builder.get_object("installed_version_title")
    
    cannotclose_dialog = builder.get_object("cannotclose_dialog")
    about_dialog = builder.get_object("about_dialog")
    
    def packageMain(actioned,status,packagefailure):

        if not "satisfiable" in packagefailure:

                if status == 0:
                    button1.set_sensitive(True)
                    button1.set_label(_("Install"))
                    button1.set_image(installicon)
                    button2.set_sensitive(False)
                elif status == 1:
                    button1.set_sensitive(True)
                    button1.set_label(_("Downgrade"))
                    button1.set_image(downgradeicon)
                    button2.set_sensitive(True)
                elif status == 2:
                    button1.set_sensitive(True)
                    button1.set_label(_("Reinstall"))
                    button1.set_image(reinstallicon)
                    button2.set_sensitive(True)
                elif status == 3:
                    button1.set_sensitive(True)
                    button1.set_label(_("Upgrade"))
                    button1.set_image(upgradeicon)
                    button2.set_sensitive(True)

        else:
            progress.set_markup(_("<b><span color='red'>Error ! </span></b>") + packagefailure)
            if status == 0:
                button1.set_sensitive(False)
                button1.set_label(_("Install"))
                button1.set_image(installicon)
                button2.set_sensitive(False)
            elif status == 1:
                button1.set_sensitive(False)
                button1.set_label(_("Downgrade"))
                button1.set_image(downgradeicon)
                button2.set_sensitive(False)
            elif status == 2:
                button1.set_sensitive(False)
                button1.set_label(_("Reinstall"))
                button1.set_image(reinstallicon)
                button2.set_sensitive(False)
            elif status == 3:
                button1.set_sensitive(False)
                button1.set_label(_("Upgrade"))
                button1.set_image(upgradeicon)
                button2.set_sensitive(False)
    

    def on_process_done(sender, retval):
        global closestatus,error
        spinner.stop()
        textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)
        print("Done. exit code: %s" % (retval))
        if error is False:
            if retval == 0:
                textview.get_buffer().insert(textview.get_buffer().get_end_iter(),  (_("Operation was successfully completed ! \n \n")))
                textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)
                progress.set_markup(_("<b>Completed !</b>"))
            else:
                progress.set_markup(_("<b>Not Completed !</b>"))
        else:
            progress.set_markup(_("<b><span color='red'>Connection Error !</span></b>"))
            error = False
        status = cacheControl()
        packagefailure = failureControl()
        packageMain(True,status,packagefailure)
        getInstalledVersion(status)
        openbutton.set_sensitive(True)
        quitbutton.set_sensitive(True)
        closestatus = False
    
    def on_stdout_data(sender, line):
        textview.get_buffer().insert(textview.get_buffer().get_end_iter(),  line)
        textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)
    
    def on_stderr_data(sender, line):
        global error
        if line is not None:
            print("Error : " +line)
            if "E:" in line and ".deb" in line:
                print("connection error")
                error = True
                textview.get_buffer().insert(textview.get_buffer().get_end_iter(),  (line))
                textview.scroll_to_iter(textview.get_buffer().get_end_iter(), 0.0, False, 0.0,0.0)

        

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
            installed_version.set_text(_("Not installed"))

    

    if len(sys.argv) > 1:
        
        debianpackage = sys.argv[1]
        aa = start(debianpackage)
        
        firststatus = aa[2]
        packagename = aa[1]
        installable = aa[3]
        packageversion =  aa[4]
        packagedescription = aa[5]
        packagefailure = aa[6]
        packagemaintainer = aa[7]
        packagepriority = aa[8]
        packagesection = aa[9]
        packagesize = aa[10]
        packagearchitecture = aa[11]
        packagedepends = aa[12]
        packagemissingdeps = aa[13]

        label1.set_text(packagename + " ( " + packageversion + " )")
        label2.set_text(packagedescription)
        maintainer.set_text(packagemaintainer)
        priority.set_text(packagepriority)
        section.set_text(packagesection)
        size.set_text(packagesize + " KiB")
        architecture.set_text(packagearchitecture)

        if packagedepends != "":
            pd = packagedepends.split(", ")
            for p in pd:
                depends.get_buffer().insert(depends.get_buffer().get_end_iter(),  p+"\n")

        if packagemissingdeps:
            for pmd in packagemissingdeps:
                missingdeps.get_buffer().insert(missingdeps.get_buffer().get_end_iter(),  pmd+"\n")

        if firststatus != 0:
            cache = apt.Cache()
            pkg = cache[packagename]
            systemversion = pkg.versions[0].version
            installed_version.set_text(systemversion)
            
        packageMain(False,firststatus,packagefailure)
        
    else:
        
        button1.set_sensitive(False)
        button2.set_sensitive(False)
        button1.set_label(_("Install"))
        button2.set_label(_("Uninstall"))
        label1.set_text("")
        installed_version_title.set_text("")
        installed_version.set_text("")
        
        
    def fromFile(path):
        
        nonlocal debianpackage,packagename,installable,packageversion,packagedescription,firststatus,packagefailure,packagemaintainer,packagepriority,packagesection,packagesize,packagearchitecture,packagemissingdeps
        
        debianpackage = path

        aa = start(debianpackage)
        
        firststatus = aa[2]
        packagename = aa[1]
        installable = aa[3]
        packageversion =  aa[4]
        packagedescription = aa[5]
        packagefailure = aa[6]
        packagemaintainer = aa[7]
        packagepriority = aa[8]
        packagesection = aa[9]
        packagesize = aa[10]
        packagearchitecture = aa[11]
        packagedepends = aa[12]
        packagemissingdeps = aa[13]

        depends.get_buffer().delete(depends.get_buffer().get_start_iter(), depends.get_buffer().get_end_iter())
        missingdeps.get_buffer().delete(missingdeps.get_buffer().get_start_iter(), missingdeps.get_buffer().get_end_iter())

        if packagedepends != "":
            pd = packagedepends.split(", ")
            for p in pd:
                depends.get_buffer().insert(depends.get_buffer().get_end_iter(),  p+"\n")

        if packagemissingdeps:
            for pmd in packagemissingdeps:
                missingdeps.get_buffer().insert(missingdeps.get_buffer().get_end_iter(),  pmd+"\n")

        label1.set_text(packagename + " ( " + packageversion + " )")
        label2.set_text(packagedescription )
        progress.set_text("")
        maintainer.set_text(packagemaintainer)
        priority.set_text(packagepriority)
        section.set_text(packagesection)
        size.set_text(packagesize + " KiB")
        architecture.set_text(packagearchitecture)
        
        if firststatus != 0:
            cache = apt.Cache()
            pkg = cache[packagename]
            systemversion = pkg.versions[0].version
            installed_version_title.set_text(_("Installed Version : "))
            installed_version.set_text(systemversion)
        else:
            installed_version_title.set_text(_("Installed Version : "))
            installed_version.set_text(_("Not installed"))
            
        packageMain(False,firststatus,packagefailure)


    def close(self, *args):
        if closestatus:
            cannotclose_dialog.run()
            cannotclose_dialog.hide()
            return True
        return closestatus

    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor()
    geometry = monitor.get_geometry()
    scale_factor = monitor.get_scale_factor()
    width = scale_factor * geometry.width
    height = scale_factor * geometry.height

    if width <= 800 and height <= 600:
        descriptionscrolledwindow.set_min_content_height(50)
        window.resize(500,500)

    window.connect('delete_event', close)
    
    window.show_all()
    
    Gtk.main()


if __name__ == "__main__":
    main()
