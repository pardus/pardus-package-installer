#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:58:17 2020

@author: fatih
"""

import gi, apt, os, sys

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


class MainWindow:
    def __init__(self, application, file):

        self.closestatus = False
        self.error = False
        self.debianpackage = ""
        self.installable = False
        self.packagename = ""
        self.packagefailure = ""
        self.file = file

        # Gtk Builder
        self.builder = Gtk.Builder()
        self.builder.add_from_file("/usr/share/pardus/pardus-package-installer/MainWindow.glade")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("mainwindow")
        self.window.set_application(application)
        self.defineComponents()
        self.controlDisplay()
        self.initialize()
        self.window.connect('delete_event', self.onClose)
        self.window.show_all()

    def onClose(self, *args):
        if self.closestatus:
            self.cannotclose_dialog.run()
            self.cannotclose_dialog.hide()
            return True
        return self.closestatus

    def initialize(self):
        if self.file:
            self.debianpackage = os.path.abspath(sys.argv[1])
            self.start(self.debianpackage)
            self.label1.set_text(self.packagename)
            self.versionlabel.set_text(" | " + self.packageversion)
            self.label2.set_text(self.packagedescription)
            self.maintainer.set_text(self.packagemaintainer)
            self.priority.set_text(self.packagepriority)
            self.section.set_text(self.packagesection)
            self.size.set_text(self.packagesize + " KiB")
            self.architecture.set_text(self.packagearchitecture)

            if self.packagedepends != "":
                pd = self.packagedepends.split(", ")
                for p in pd:
                    self.depends.get_buffer().insert(self.depends.get_buffer().get_end_iter(), p + "\n")

            if self.packagemissingdeps:
                for pmd in self.packagemissingdeps:
                    self.missingdeps.get_buffer().insert(self.missingdeps.get_buffer().get_end_iter(), pmd + "\n")

            if self.firststatus != 0:
                pkg = self.cache[self.packagename]
                systemversion = str(pkg.installed).split("=")[1]
                self.installed_version.set_text(systemversion)

            self.packageMain(False, self.firststatus, self.packagefailure)

        else:

            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.button1.set_label(_("Install"))
            self.button2.set_label(_("Uninstall"))
            self.label1.set_text("")
            self.versionlabel.set_text("")
            self.installed_version_title.set_text("")
            self.installed_version.set_text("")

    def controlDisplay(self):
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geometry = monitor.get_geometry()
        scale_factor = monitor.get_scale_factor()
        width = scale_factor * geometry.width
        height = scale_factor * geometry.height

        if width <= 800 and height <= 600:
            self.window.resize(400, 400)
            self.descriptionscrolledwindow.set_min_content_height(50)
            self.namegrid.set_margin_top(9)
            self.namegrid.set_margin_bottom(9)
            self.progress.set_margin_top(9)
            self.progress.set_margin_bottom(9)
            self.installedversiongrid.set_margin_top(9)
            self.bottomseparator.set_margin_top(9)
            self.bottomlabel.set_margin_top(5)
            self.bottomlabel.set_margin_bottom(5)

    def defineComponents(self):
        self.button1 = self.builder.get_object("button1")
        self.button2 = self.builder.get_object("button2")
        self.openbutton = self.builder.get_object("openbutton")
        self.filechooser = self.builder.get_object("filechooser")
        self.selectbutton = self.builder.get_object("selectbutton")
        self.quitbutton = self.builder.get_object("quitbutton")
        self.aboutbutton = self.builder.get_object("aboutbutton")

        self.label1 = self.builder.get_object("label1")
        self.label2 = self.builder.get_object("label2")
        self.versionlabel = self.builder.get_object("versionlabel")
        self.namegrid = self.builder.get_object("namegrid")
        self.installedversiongrid = self.builder.get_object("installedversiongrid")
        self.bottomseparator = self.builder.get_object("bottomseparator")
        self.bottomlabel = self.builder.get_object("bottomlabel")

        self.maintainer = self.builder.get_object("maintainer")
        self.priority = self.builder.get_object("priority")
        self.section = self.builder.get_object("section")
        self.size = self.builder.get_object("size")
        self.architecture = self.builder.get_object("architecture")
        self.depends = self.builder.get_object("depends")
        self.missingdeps = self.builder.get_object("missingdeps")

        self.spinner = self.builder.get_object("spinner")
        self.progress = self.builder.get_object("progress")
        self.progressbar = self.builder.get_object("progressbar")

        self.textview = self.builder.get_object("textview")
        self.descriptionscrolledwindow = self.builder.get_object("descriptionscrolledwindow")

        self.installicon = self.builder.get_object("install_icon")
        self.upgradeicon = self.builder.get_object("upgrade_icon")
        self.downgradeicon = self.builder.get_object("downgrade_icon")
        self.reinstallicon = self.builder.get_object("reinstall_icon")

        self.installed_version = self.builder.get_object("installed_version")
        self.installed_version_title = self.builder.get_object("installed_version_title")

        self.cannotclose_dialog = self.builder.get_object("cannotclose_dialog")
        self.about_dialog = self.builder.get_object("about_dialog")

    def start(self, debpackage):

        self.updateCache()

        self.package = aptdeb.DebPackage(debpackage)

        self.packagename = self.package.pkgname

        self.firststatus = self.package.compare_to_version_in_cache()

        self.installable = self.package.check()

        try:
            self.packageversion = self.package._sections["Version"]
        except:
            self.packageversion = _("Version is not avaible")

        try:
            self.packagedescription = self.package._sections["Description"]
        except:
            self.packagedescription = _("Description is not avaible")

        try:
            self.packagemaintainer = self.package._sections["Maintainer"]
        except:
            self.packagemaintainer = _("Maintainer is not avaible")

        try:
            self.packagepriority = self.package._sections["Priority"]
        except:
            self.packagepriority = _("Priority is not avaible")

        try:
            self.packagesection = self.package._sections["Section"]
        except:
            self.packagesection = _("Section is not avaible")

        try:
            self.packagesize = self.package._sections["Installed-Size"]
        except:
            self.packagesize = _("Size is not avaible")

        try:
            self.packagearchitecture = self.package._sections["Architecture"]
        except:
            self.packagearchitecture = _("Architecture is not avaible")

        try:
            self.packagedepends = self.package._sections["Depends"]
        except:
            self.packagedepends = ""

        self.packagemissingdeps = self.package.missing_deps

        self.packagefailure = self.package._failure_string

    def updateCache(self):
        self.cache = apt.Cache()

    def compareVersion(self):
        # VERSION_NEWER = 3
        # VERSION_NONE = 0
        # VERSION_OUTDATED = 1
        # VERSION_SAME = 2
        return aptdeb.DebPackage(self.debianpackage).compare_to_version_in_cache()

    def failureControl(self):
        return aptdeb.DebPackage(self.debianpackage)._failure_string

    def installPackage(self):

        if self.installable:
            self.progressbar.set_show_text(False)
            self.progressbar.set_fraction(0)
            self.spinner.start()
            self.progress.set_text(_("Installing ..."))
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.openbutton.set_sensitive(False)
            self.quitbutton.set_sensitive(False)
            self.closestatus = True
            self.command = ["/usr/bin/pkexec", "/usr/bin/pardus-package-installer-action", "install",
                            self.debianpackage]
            self.pid = self.startProcess(self.command)
            print(self.pid)

    def removePackage(self):

        if self.cache[self.packagename].is_installed:
            self.progressbar.set_show_text(False)
            self.progressbar.set_fraction(0)
            self.spinner.start()
            self.progress.set_text(_("Uninstalling ..."))
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.openbutton.set_sensitive(False)
            self.quitbutton.set_sensitive(False)
            self.closestatus = True
            self.command = ["/usr/bin/pkexec", "/usr/bin/pardus-package-installer-action", "remove", self.packagename]
            self.pid = self.startProcess(self.command)
            print(self.pid)

    def reinstallPackage(self):
        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)
        self.spinner.start()
        self.progress.set_text(_("Reinstalling ..."))
        self.button1.set_sensitive(False)
        self.button2.set_sensitive(False)
        self.openbutton.set_sensitive(False)
        self.quitbutton.set_sensitive(False)
        self.closestatus = True
        self.command = ["/usr/bin/pkexec", "/usr/bin/pardus-package-installer-action", "reinstall", self.debianpackage]
        self.pid = self.startProcess(self.command)
        print(self.pid)

    def downgradePackage(self):
        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)
        self.spinner.start()
        self.progress.set_text(_("Downgrading ..."))
        self.button1.set_sensitive(False)
        self.button2.set_sensitive(False)
        self.openbutton.set_sensitive(False)
        self.quitbutton.set_sensitive(False)
        self.closestatus = True
        self.command = ["/usr/bin/pkexec", "/usr/bin/pardus-package-installer-action", "downgrade", self.debianpackage]
        self.pid = self.startProcess(self.command)
        print(self.pid)

    def onDestroy(self, window):
        self.window.get_application().quit()

    def onButton1Clicked(self, button):
        print("debianpackage = " + self.debianpackage)
        packagestatus = self.compareVersion()

        if packagestatus == 0:
            print("Installing Button Clicked")
            self.installPackage()

        elif packagestatus == 1:
            print("Downgrading Button Clicked")
            self.downgradePackage()

        elif packagestatus == 2:
            print("Reinstalling Button Clicked")
            self.reinstallPackage()

        elif packagestatus == 3:
            print("Upgrading Button Clicked")
            self.installPackage()

    def onButton2Clicked(self, button):
        print("Uninstalling Button Clicked")
        self.removePackage()

    def onOpenClicked(self, button):
        self.filechooser.run()
        self.filechooser.hide()
        print("Open Button Clicked")

    def onSelectClicked(self, widget):
        self.filename = self.filechooser.get_filename()
        self.filechooser.hide()
        self.fromFile(self.filename)
        print("Select Button Clicked")

    def onActivated(self, widget):
        self.filename = self.filechooser.get_filename()
        self.filechooser.hide()
        self.fromFile(self.filename)
        print("Active Button Clicked")

    def onQuitClicked(self, button):
        self.window.get_application().quit()

    def onAboutClicked(self, button):
        self.about_dialog.run()
        self.about_dialog.hide()

    def packageMain(self, actioned, status, packagefailure):

        if not "satisfiable" in packagefailure:

            if status == 0:
                self.button1.set_sensitive(True)
                self.button1.set_label(_("Install"))
                self.button1.set_image(self.installicon)
                self.button2.set_sensitive(False)
            elif status == 1:
                self.button1.set_sensitive(True)
                self.button1.set_label(_("Downgrade"))
                self.button1.set_image(self.downgradeicon)
                self.button2.set_sensitive(True)
            elif status == 2:
                self.button1.set_sensitive(True)
                self.button1.set_label(_("Reinstall"))
                self.button1.set_image(self.reinstallicon)
                self.button2.set_sensitive(True)
            elif status == 3:
                self.button1.set_sensitive(True)
                self.button1.set_label(_("Upgrade"))
                self.button1.set_image(self.upgradeicon)
                self.button2.set_sensitive(True)

        else:
            self.progress.set_markup(_("<b><span color='red'>Error ! </span></b>") + packagefailure)
            if status == 0:
                self.button1.set_sensitive(False)
                self.button1.set_label(_("Install"))
                self.button1.set_image(self.installicon)
                self.button2.set_sensitive(False)
            elif status == 1:
                self.button1.set_sensitive(False)
                self.button1.set_label(_("Downgrade"))
                self.button1.set_image(self.downgradeicon)
                self.button2.set_sensitive(False)
            elif status == 2:
                self.button1.set_sensitive(False)
                self.button1.set_label(_("Reinstall"))
                self.button1.set_image(self.reinstallicon)
                self.button2.set_sensitive(False)
            elif status == 3:
                self.button1.set_sensitive(False)
                self.button1.set_label(_("Upgrade"))
                self.button1.set_image(self.upgradeicon)
                self.button2.set_sensitive(False)

    def getInstalledVersion(self, status):

        if status != 0:
            pkg = self.cache[self.packagename]
            systemversion = str(pkg.installed).split("=")[1]
            self.installed_version.set_text(systemversion)
        else:
            self.installed_version.set_text(_("Not installed"))

    def fromFile(self, path):

        self.debianpackage = path
        self.start(self.debianpackage)
        self.depends.get_buffer().delete(self.depends.get_buffer().get_start_iter(),
                                         self.depends.get_buffer().get_end_iter())
        self.missingdeps.get_buffer().delete(self.missingdeps.get_buffer().get_start_iter(),
                                             self.missingdeps.get_buffer().get_end_iter())

        if self.packagedepends != "":
            pd = self.packagedepends.split(", ")
            for p in pd:
                self.depends.get_buffer().insert(self.depends.get_buffer().get_end_iter(), p + "\n")

        if self.packagemissingdeps:
            for pmd in self.packagemissingdeps:
                self.missingdeps.get_buffer().insert(self.missingdeps.get_buffer().get_end_iter(), pmd + "\n")

        self.label1.set_text(self.packagename)
        self.versionlabel.set_text(" | " + self.packageversion)
        self.label2.set_text(self.packagedescription)
        self.progress.set_text("")
        self.maintainer.set_text(self.packagemaintainer)
        self.priority.set_text(self.packagepriority)
        self.section.set_text(self.packagesection)
        self.size.set_text(self.packagesize + " KiB")
        self.architecture.set_text(self.packagearchitecture)

        if self.firststatus != 0:
            pkg = self.cache[self.packagename]
            systemversion = pkg.versions[0].version
            self.installed_version_title.set_text(_("Installed Version : "))
            self.installed_version.set_text(systemversion)
        else:
            self.installed_version_title.set_text(_("Installed Version : "))
            self.installed_version.set_text(_("Not installed"))

        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)

        self.packageMain(False, self.firststatus, self.packagefailure)

    def startProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.onProcessExit)

        return pid

    def onProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        self.textview.get_buffer().insert(self.textview.get_buffer().get_end_iter(), source.readline())
        self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)

        return True

    def onProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        if line is not None:
            print("Error : " + line)
            if "dlstatus" in line:
                percent = line.split(":")[2].split(".")[0]
                self.progressbar.set_show_text(True)
                if self.packagemissingdeps:
                    print("Downloading dependencies " + percent + " %")
                    self.progressbar.set_text(_("Downloading dependencies : ") + percent + " %")
                else:
                    print("Controlling dependencies : " + percent + " %")
                    self.progressbar.set_text(_("Controlling dependencies : ") + percent + " %")
                self.progressbar.set_fraction(int(percent) / 100)
            elif "pmstatus" in line:
                percent = line.split(":")[2].split(".")[0]
                print("Processing : " + percent)
                self.progressbar.set_show_text(True)
                self.progressbar.set_text((self.progress.get_text()).split("...")[0] + ": " + percent + " %")
                self.progressbar.set_fraction(int(percent) / 100)
            elif "E:" in line and ".deb" in line:
                print("connection error")
                self.error = True
                self.textview.get_buffer().insert(self.textview.get_buffer().get_end_iter(), (line))
                self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)

        return True

    def onProcessExit(self, pid, retval):
        self.spinner.stop()
        self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)
        print("Done. exit code: %s" % (retval))
        if self.error is False:
            if retval == 0:
                self.textview.get_buffer().insert(self.textview.get_buffer().get_end_iter(),
                                                  (_("Operation was successfully completed ! \n \n")))
                self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)
                self.progress.set_markup(_("<b>Completed !</b>"))
                if self.progressbar.get_show_text():
                    self.progressbar.set_text("100 %")
                    self.progressbar.set_fraction(1)
            else:
                self.progress.set_markup(_("<b>Not Completed !</b>"))
        else:
            self.progress.set_markup(_("<b><span color='red'>Connection Error !</span></b>"))
            if self.progressbar.get_show_text():
                self.progressbar.set_show_text(False)
                self.progressbar.set_fraction(0)
            self.error = False
        self.updateCache()
        self.status = self.compareVersion()
        self.packagefailure = self.failureControl()
        self.packageMain(True, self.status, self.packagefailure)
        self.getInstalledVersion(self.status)
        self.openbutton.set_sensitive(True)
        self.quitbutton.set_sensitive(True)
        self.closestatus = False
