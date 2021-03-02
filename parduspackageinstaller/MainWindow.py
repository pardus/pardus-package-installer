#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:58:17 2020

@author: fatih
"""

import gi, apt, os, sys

gi.require_version('Gtk', '3.0')
gi.require_version("Notify", "0.7")
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gdk
from gi.repository import Notify
import apt.debfile as aptdeb
from subprocess import PIPE, Popen

import locale
from locale import gettext as _

locale.bindtextdomain('pardus-package-installer', '/usr/share/locale')
locale.textdomain('pardus-package-installer')


class MainWindow:
    def __init__(self, application, file):

        self.closestatus = False
        self.error = False
        self.dpkglockerror = False
        self.dpkgconferror = False
        self.debianpackage = ""
        self.installable = False
        self.packagename = ""
        self.packagefailure = ""
        self.file = file
        self.notificationstate = True
        self.isinstalling = False
        self.isbroken = False

        # Gtk Builder
        self.builder = Gtk.Builder()
        self.builder.add_from_file("/usr/share/pardus/pardus-package-installer/MainWindow.glade")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("mainwindow")
        self.window.set_application(application)
        self.defineComponents()
        self.controlDisplay()
        self.initialize()
        self.donebutton.get_style_context().add_class("suggested-action")
        self.window.connect('delete_event', self.onClose)

        # Set version
        # If not getted from Version.py file then accept version in MainWindow.glade file
        try:
            from parduspackageinstaller.Version import version
            self.about_dialog.set_version(version)
        except:
            pass

        self.window.show_all()

        if self.isbroken:
            self.openBrokenDialog()

    def onClose(self, *args):
        if self.closestatus:
            self.cannotclose_dialog.run()
            self.cannotclose_dialog.hide()
            return True
        return self.closestatus

    def initialize(self):
        if self.file:
            self.debianpackage = os.path.abspath(sys.argv[1])
            if self.start(self.debianpackage):
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
        self.aboutbutton = self.builder.get_object("aboutbutton")
        self.broken_close_button = self.builder.get_object("broken_close_button")

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
        self.stack1 = self.builder.get_object("stack1")
        self.donebutton = self.builder.get_object("donebutton")

        self.installicon = self.builder.get_object("install_icon")
        self.upgradeicon = self.builder.get_object("upgrade_icon")
        self.downgradeicon = self.builder.get_object("downgrade_icon")
        self.reinstallicon = self.builder.get_object("reinstall_icon")

        self.installed_version = self.builder.get_object("installed_version")
        self.installed_version_title = self.builder.get_object("installed_version_title")

        self.cannotclose_dialog = self.builder.get_object("cannotclose_dialog")
        self.about_dialog = self.builder.get_object("about_dialog")
        self.broken_dialog = self.builder.get_object("broken_dialog")

    def start(self, debpackage):

        if self.updateCache():

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

            return True

        return False

    def updateCache(self):
        try:
            self.cache = apt.Cache()
        except:
            self.isbroken = True
            return False
        if self.cache.broken_count > 0:
            self.isbroken = True
            return False
        self.isbroken = False
        return True

    def compareVersion(self):
        # VERSION_NEWER = 3
        # VERSION_NONE = 0
        # VERSION_OUTDATED = 1
        # VERSION_SAME = 2
        return aptdeb.DebPackage(self.debianpackage).compare_to_version_in_cache()

    def failureControl(self):
        return aptdeb.DebPackage(self.debianpackage)._failure_string

    def installPackage(self, isupgrading):

        if self.installable:
            self.isinstalling = True
            self.progressbar.set_show_text(False)
            self.progressbar.set_fraction(0)
            self.spinner.start()
            self.progress.set_text(_("Installing ..."))
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.openbutton.set_sensitive(False)
            self.closestatus = True
            if isupgrading:
                self.notification = Notify.Notification.new(self.packagename + _(" upgraded"))
            else:
                self.notification = Notify.Notification.new(self.packagename + _(" installed"))
            self.command = ["/usr/bin/pkexec", "/usr/bin/pardus-package-installer-action", "install",
                            self.debianpackage]
            self.pid = self.startProcess(self.command)
            print(self.pid)
        else:
            print("package is not installable")
            try:
                self.systemarchitecture = Popen(["/usr/bin/dpkg", "--print-architecture"],
                                                stdout=PIPE, universal_newlines=True).communicate()[0].strip()
            except:
                self.systemarchitecture = "not detected"
            if self.packagearchitecture != self.systemarchitecture:
                print("Error : Package Architecture = " + self.packagearchitecture
                      + ", System Architecture = " + self.systemarchitecture)
                self.button1.set_sensitive(False)
                self.button2.set_sensitive(False)
                self.progress.set_markup(_("<b><span color='red'>Error :</span> Package Architecture = ")
                                         + self.packagearchitecture + _(", System Architecture = ")
                                         + self.systemarchitecture + "</b>")

    def removePackage(self):

        if self.cache[self.packagename].is_installed:
            self.progressbar.set_show_text(False)
            self.progressbar.set_fraction(0)
            self.spinner.start()
            self.progress.set_text(_("Uninstalling ..."))
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.openbutton.set_sensitive(False)
            self.closestatus = True
            self.notification = Notify.Notification.new(self.packagename + _(" uninstalled"))
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
        self.closestatus = True
        self.notification = Notify.Notification.new(self.packagename + _(" reinstalled"))
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
        self.closestatus = True
        self.notification = Notify.Notification.new(self.packagename + _(" downgraded"))
        self.command = ["/usr/bin/pkexec", "/usr/bin/pardus-package-installer-action", "downgrade", self.debianpackage]
        self.pid = self.startProcess(self.command)
        print(self.pid)

    def onDestroy(self, window):
        self.window.get_application().quit()

    def onButton1Clicked(self, button):
        self.stack1.set_visible_child_name("page0")
        print("debianpackage = " + self.debianpackage)
        packagestatus = self.compareVersion()

        if packagestatus == 0:
            print("Installing Button Clicked")
            self.installPackage(False)

        elif packagestatus == 1:
            print("Downgrading Button Clicked")
            self.downgradePackage()

        elif packagestatus == 2:
            print("Reinstalling Button Clicked")
            self.reinstallPackage()

        elif packagestatus == 3:
            print("Upgrading Button Clicked")
            self.installPackage(True)

    def onButton2Clicked(self, button):
        self.stack1.set_visible_child_name("page0")
        print("Uninstalling Button Clicked")
        self.removePackage()

    def onDoneButtonClicked(self, button):
        self.window.get_application().quit()

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

    def onAboutClicked(self, button):
        self.about_dialog.run()
        self.about_dialog.hide()

    def on_broken_close_button_clicked(self, button):
        self.broken_dialog.hide()
        self.window.get_application().quit()

    def on_broken_dialog_delete_event(self, widget, event):
        print("on_broken_dialog_delete_event")
        self.broken_dialog.hide()
        self.window.get_application().quit()

    def openBrokenDialog(self):
        self.broken_dialog.run()
        self.broken_dialog.hide()

    def packageMain(self, actioned, status, packagefailure):

        if not packagefailure or "A later version is already installed" in packagefailure:

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

        self.stack1.set_visible_child_name("page0")
        self.debianpackage = path
        if self.start(self.debianpackage):
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
        else:
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.button1.set_label(_("Install"))
            self.button2.set_label(_("Uninstall"))
            self.label1.set_text("")
            self.versionlabel.set_text("")
            self.installed_version_title.set_text("")
            self.installed_version.set_text("")
            self.openBrokenDialog()

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
            elif "E:" in line and "dpkg --configure -a" in line:
                print("dpkg --configure -a error")
                self.error = True
                self.dpkgconferror = True
                self.textview.get_buffer().insert(self.textview.get_buffer().get_end_iter(), (line))
                self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)
            elif "E:" in line and "/var/lib/dpkg/lock-frontend" in line:
                print("/var/lib/dpkg/lock-frontend error")
                self.error = True
                self.dpkglockerror = True
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
                self.notificationstate = True
                self.stack1.set_visible_child_name("page1")
                if self.progressbar.get_show_text():
                    self.progressbar.set_text("100 %")
                    self.progressbar.set_fraction(1)
            else:
                self.progress.set_markup(_("<b>Not Completed !</b>"))
                self.notificationstate = False
        else:
            errormessage = _("<b><span color='red'>Connection Error !</span></b>")
            if self.dpkglockerror:
                errormessage = _("<b><span color='red'>Dpkg Lock Error !</span></b>")
            elif self.dpkgconferror:
                errormessage = _("<b><span color='red'>Dpkg Interrupt Error !</span></b>")
            self.progress.set_markup(errormessage)
            self.notificationstate = False
            if self.progressbar.get_show_text():
                self.progressbar.set_show_text(False)
                self.progressbar.set_fraction(0)
        self.updateCache()
        self.status = self.compareVersion()
        self.packagefailure = self.failureControl()
        self.packageMain(True, self.status, self.packagefailure)
        self.getInstalledVersion(self.status)
        self.openbutton.set_sensitive(True)
        self.closestatus = False
        if self.isinstalling and self.status == 0 and retval == 0:
            print("connection lost")
            self.stack1.set_visible_child_name("page0")
            errormessage = _("<b><span color='red'>Connection Error !</span></b>")
            if self.dpkglockerror:
                errormessage = _("<b><span color='red'>Dpkg Lock Error !</span></b>")
            elif self.dpkgconferror:
                errormessage = _("<b><span color='red'>Dpkg Interrupt Error !</span></b>")
            self.progress.set_markup(errormessage)
            if self.progressbar.get_show_text():
                self.progressbar.set_show_text(False)
                self.progressbar.set_fraction(0)
            self.notificationstate = False
        self.error = False
        self.dpkglockerror = False
        self.dpkgconferror = False
        self.isinstalling = False
        self.notify()

    def notify(self):
        if self.notificationstate:
            if Notify.is_initted():
                Notify.uninit()

            Notify.init(self.packagename)
            try:
                pixbuf = Gtk.IconTheme.get_default().load_icon(self.packagename, 64, Gtk.IconLookupFlags(16))
            except:
                try:
                    parduspixbuf = Gtk.IconTheme.new()
                    parduspixbuf.set_custom_theme("pardus")
                    pixbuf = parduspixbuf.load_icon(self.packagename, 64, Gtk.IconLookupFlags(16))
                except:
                    try:
                        pixbuf = Gtk.IconTheme.get_default().load_icon("pardus-package-installer", 64,
                                                                       Gtk.IconLookupFlags(16))
                    except:
                        try:
                            pixbuf = parduspixbuf.load_icon("pardus-package-installer", 64, Gtk.IconLookupFlags(16))
                        except:
                            pixbuf = Gtk.IconTheme.get_default().load_icon("gtk-dialog-info", 64,
                                                                           Gtk.IconLookupFlags(16))
            self.notification.set_icon_from_pixbuf(pixbuf)
            self.notification.show()
