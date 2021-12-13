#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:58:17 2020

@author: fatih
"""
import math
import re

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

class MainWindow(object):
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
        self.MainWindowUIFileName = os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        try:
            self.builder = Gtk.Builder.new_from_file(self.MainWindowUIFileName)
            self.builder.connect_signals(self)
        except GObject.GError:
            print("Error reading GUI file: " + self.MainWindowUIFileName)
            raise

        self.window = self.builder.get_object("mainwindow")
        self.window.set_application(application)
        self.defineComponents()
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

        self.openbutton.set_visible(False)
        # self.headerseperator.set_visible(False)
        self.progstack.set_visible(False)
        self.errorlabel.set_visible(False)
        self.BrokenBox.set_visible(False)

        self.initialize()

    def onClose(self, *args):
        if self.closestatus:
            self.cannotclose_dialog.run()
            self.cannotclose_dialog.hide()
            return True
        return self.closestatus

    def setLabels(self):

        self.depends.set_text("")
        self.missingdeps.set_text("")
        self.mainstack.set_visible_child_name("package")
        self.progstack.set_visible(False)
        self.doneinfolabel.set_text("")

        self.pacname.set_markup("<span size='x-large'><b>{}</b></span>".format(self.packagename))
        self.pacversion.set_markup("<small>{}</small>".format(GLib.markup_escape_text(self.packageversion, -1)))
        self.shortdesc.set_markup("<small>{}</small>".format(GLib.markup_escape_text(self.packageshortdescription, -1)))
        self.shortdesc.set_tooltip_text("{}".format(self.packagedescription))

        self.maintainername.set_text(self.packagemaintainername)

        if self.packagemaintainermail != "-":
            self.maintainermail.set_markup("<a title='{}' href='mailto:{}'>{}</a>".format(
                GLib.markup_escape_text(self.packagemaintainermail, -1),
                GLib.markup_escape_text(self.packagemaintainermail, -1),
                GLib.markup_escape_text(self.packagemaintainermail, -1)))
        else:
            self.maintainermail.set_text(self.packagemaintainermail)

        if self.packagehomepage != "-":
            self.homepage.set_markup("<a title='{}' href='{}'>{}</a>".format(
                GLib.markup_escape_text(self.packagehomepage, -1),
                GLib.markup_escape_text(self.packagehomepage, -1),
                GLib.markup_escape_text(self.packagehomepage, -1)))
        else:
            self.homepage.set_text(self.packagehomepage)

        self.section.set_text(self.packagesection)

        if self.packagesize != "-":
            self.size.set_text(self.packagesize + " KiB")
        else:
            self.size.set_text(self.packagesize)

        self.architecture.set_text(self.packagearchitecture)

        try:
            pd = re.split('\||, ', self.packagedepends)
            lenpd = len(pd)
            for i in range(0, lenpd):
                if pd[i][0] == " ":
                    pd[i] = "|" + pd[i].strip()
            pd = "\n\n".join(pd)

        except Exception as e:
            print("{}".format(e))
            pd = ""
        self.depends.set_markup("<small>{}</small>".format(GLib.markup_escape_text(pd, -1)))

        if self.packagemissingdeps:
            self.missingdeps.set_markup("<span size='smaller'>{}</span>".format(
                GLib.markup_escape_text(self.packagemissingdeps, -1)))

        if self.firststatus != 0:
            pkg = self.cache[self.packagename]
            systemversion = pkg.versions[0].version
            self.installed_version_title.set_markup(
                "<small><span weight='light'>{}</span></small>".format(_("Installed Version :")))
            self.installed_version.set_markup("<small><span weight='light'>{}</span></small>".format(systemversion))
        else:
            self.installed_version_title.set_markup(
                "<small><span weight='light'>{}</span></small>".format(_("Installed Version :")))
            self.installed_version.set_markup(
                "<small><span weight='light'>{}</span></small>".format(_("Not installed")))

        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)

    def initialize(self):
        if self.file:
            self.debianpackage = os.path.abspath(sys.argv[1])
            if self.start(self.debianpackage):
                self.openbutton.set_visible(True)
                # self.headerseperator.set_visible(True)
                self.mainstack.set_visible_child_name("package")
                self.openbutton.set_visible(True)
                # self.headerseperator.set_visible(True)

                self.setLabels()

                self.packageMain(False, self.firststatus, self.packagefailure)
            else:
                self.button1.set_sensitive(False)
                self.button2.set_sensitive(False)
                self.button1.set_label(_("Install"))
                self.button2.set_label(_("Uninstall"))
                self.pacname.set_text("")
                self.pacversion.set_text("")
                self.installed_version_title.set_text("")
                self.installed_version.set_text("")
                self.openBrokenDialog()
        else:
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.button1.set_label(_("Install"))
            self.button2.set_label(_("Uninstall"))
            self.pacname.set_text("")
            self.pacversion.set_text("")
            self.installed_version_title.set_text("")
            self.installed_version.set_text("")

    def defineComponents(self):
        self.button1 = self.builder.get_object("button1")
        self.button2 = self.builder.get_object("button2")
        self.openbutton = self.builder.get_object("openbutton")
        self.headerseperator = self.builder.get_object("headerseperator")
        self.filechooser = self.builder.get_object("filechooser")
        self.selectbutton = self.builder.get_object("selectbutton")
        self.aboutbutton = self.builder.get_object("aboutbutton")
        self.broken_close_button = self.builder.get_object("broken_close_button")

        self.pacname = self.builder.get_object("pacname")
        self.shortdesc = self.builder.get_object("shortdesc")
        self.pacversion = self.builder.get_object("pacversion")
        self.namegrid = self.builder.get_object("namegrid")
        self.installedversiongrid = self.builder.get_object("installedversiongrid")
        self.bottomseparator = self.builder.get_object("bottomseparator")
        self.bottomlabel = self.builder.get_object("bottomlabel")
        self.errorlabel = self.builder.get_object("errorlabel")

        self.maintainername = self.builder.get_object("maintainername")
        self.maintainermail = self.builder.get_object("maintainermail")
        self.homepage = self.builder.get_object("homepage")
        self.section = self.builder.get_object("section")
        self.size = self.builder.get_object("size")
        self.architecture = self.builder.get_object("architecture")
        self.depends = self.builder.get_object("depends")
        self.missingdeps = self.builder.get_object("missingdeps")

        self.spinner = self.builder.get_object("spinner")
        self.progress = self.builder.get_object("progress")

        self.detailsbutton = self.builder.get_object("detailsbutton")
        self.detailsrevealer = self.builder.get_object("detailsrevealer")

        self.progstack = self.builder.get_object("progstack")
        self.progressbar = self.builder.get_object("progressbar")
        self.donebutton = self.builder.get_object("donebutton")
        self.doneinfolabel = self.builder.get_object("doneinfolabel")

        self.textview = self.builder.get_object("textview")
        self.descriptionscrolledwindow = self.builder.get_object("descriptionscrolledwindow")
        self.stack1 = self.builder.get_object("stack1")
        self.mainstack = self.builder.get_object("mainstack")

        self.installicon = self.builder.get_object("install_icon")
        self.upgradeicon = self.builder.get_object("upgrade_icon")
        self.downgradeicon = self.builder.get_object("downgrade_icon")
        self.reinstallicon = self.builder.get_object("reinstall_icon")

        self.installed_version = self.builder.get_object("installed_version")
        self.installed_version_title = self.builder.get_object("installed_version_title")

        self.BrokenBox = self.builder.get_object("BrokenBox")
        self.cannotclose_dialog = self.builder.get_object("cannotclose_dialog")
        self.about_dialog = self.builder.get_object("about_dialog")

    def start(self, debpackage):

        self.errorlabel.set_visible(False)
        self.errorlabel.set_text("")

        if self.updateCache():

            self.package = aptdeb.DebPackage(debpackage)

            self.packagename = self.package.pkgname

            self.firststatus = self.package.compare_to_version_in_cache()

            self.installable = self.package.check()

            try:
                self.packageversion = self.package._sections["Version"]
            except:
                self.packageversion = "-"

            try:
                self.packagedescription = self.package._sections["Description"]
            except:
                self.packagedescription = "-"

            try:
                self.packageshortdescription = self.package["Description"].split("\n")[0]
                looplen = 0
                pd = ""
                if len(self.packageshortdescription) > 75:
                    looplen = math.ceil(len(self.packageshortdescription) / 75)
                    pd = "".join(self.packageshortdescription[:75])
                    for ll in range(1, looplen):
                        pd += "\n" + "".join(self.packageshortdescription[ll*75:(ll+1)*75])
                    self.packageshortdescription = pd
            except Exception as e:
                print("{}".format(e))
                self.packageshortdescription = ""

            try:
                self.packagemaintainer = self.package._sections["Maintainer"]
            except:
                self.packagemaintainer = "-"

            try:
                self.packagemaintainername = self.packagemaintainer.split(" <")[0]
            except:
                self.packagemaintainername = "-"

            try:
                self.packagemaintainermail = self.packagemaintainer.split(" <")[1].replace(">", "")
            except:
                self.packagemaintainermail = "-"

            try:
                self.packagehomepage = self.package._sections["Homepage"]
            except:
                self.packagehomepage = "-"

            try:
                self.packagesection = self.package._sections["Section"]
            except:
                self.packagesection = "-"

            try:
                self.packagesize = self.package._sections["Installed-Size"]
            except:
                self.packagesize = "-"

            try:
                self.packagearchitecture = self.package._sections["Architecture"]
            except:
                self.packagearchitecture = "-"

            try:
                self.packagedepends = self.package._sections["Depends"]
            except:
                self.packagedepends = ""

            try:
                self.packagemissingdeps = "\n\n".join(self.package.missing_deps)
            except:
                self.packagemissingdeps = ""

            self.packagefailure = self.package._failure_string
            try:
                looplen = 0
                pf = ""
                if len(self.packagefailure) > 75:
                    looplen = math.ceil(len(self.packagefailure) / 75)
                    pf = "".join(self.packagefailure[:75])
                    for pll in range(1, looplen):
                        pf += "\n" + "".join(self.packagefailure[pll*75:(pll+1)*75])
                    self.packagefailure = pf
            except Exception as e:
                print("{}".format(e))
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
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.openbutton.set_sensitive(False)
            self.closestatus = True
            if isupgrading:
                self.notification = Notify.Notification.new(self.packagename + _(" upgraded"))
            else:
                self.notification = Notify.Notification.new(self.packagename + _(" installed"))
            self.command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "install",
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
                self.progstack.set_visible(True)
                self.progstack.set_visible_child_name("doneinfo")
                self.doneinfolabel.set_markup("<b><span color='red'>{}\n</span>{}:{}, {}:{}".format(
                    _("Package Architecture Error"), _("System"), self.systemarchitecture, _("Package"),
                    self.packagearchitecture ))

    def removePackage(self):

        if self.cache[self.packagename].is_installed:
            self.progressbar.set_show_text(False)
            self.progressbar.set_fraction(0)
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.openbutton.set_sensitive(False)
            self.closestatus = True
            self.notification = Notify.Notification.new(self.packagename + _(" uninstalled"))
            self.command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "remove", self.packagename]
            self.pid = self.startProcess(self.command)
            print(self.pid)

    def reinstallPackage(self):
        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)
        self.button1.set_sensitive(False)
        self.button2.set_sensitive(False)
        self.openbutton.set_sensitive(False)
        self.closestatus = True
        self.notification = Notify.Notification.new(self.packagename + _(" reinstalled"))
        self.command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "reinstall", self.debianpackage]
        self.pid = self.startProcess(self.command)
        print(self.pid)

    def downgradePackage(self):
        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)
        self.button1.set_sensitive(False)
        self.button2.set_sensitive(False)
        self.openbutton.set_sensitive(False)
        self.closestatus = True
        self.notification = Notify.Notification.new(self.packagename + _(" downgraded"))
        self.command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "downgrade", self.debianpackage]
        self.pid = self.startProcess(self.command)
        print(self.pid)

    def onDestroy(self, window):
        self.window.get_application().quit()

    def on_button1_clicked(self, button):
        print("debianpackage = " + self.debianpackage)
        packagestatus = self.compareVersion()
        self.progstack.set_visible(True)
        self.progstack.set_visible_child_name("progress")

        if packagestatus == 0:
            print("Installing Button Clicked")
            self.packageaction = _("Installing")
            self.installPackage(False)

        elif packagestatus == 1:
            self.packageaction = _("Downgrading")
            print("Downgrading Button Clicked")
            self.downgradePackage()

        elif packagestatus == 2:
            self.packageaction = _("Reinstalling")
            print("Reinstalling Button Clicked")
            self.reinstallPackage()

        elif packagestatus == 3:
            self.packageaction = _("Upgrading")
            print("Upgrading Button Clicked")
            self.installPackage(True)

    def on_button2_clicked(self, button):
        # self.stack1.set_visible_child_name("page0")
        self.packageaction = _("Uninstalling")
        print("Uninstalling Button Clicked")
        self.progstack.set_visible(True)
        self.progstack.set_visible_child_name("progress")
        self.removePackage()

    def on_donebutton_clicked(self, button):
        self.window.get_application().quit()

    def on_openbutton_clicked(self, button):
        self.filechooser.run()
        self.filechooser.hide()
        print("Open Button Clicked")

    def on_selectbutton_clicked(self, widget):
        self.filename = self.filechooser.get_filename()
        self.filechooser.hide()
        self.fromFile(self.filename)
        print("Select Button Clicked")

    def onActivated(self, widget):
        self.filename = self.filechooser.get_filename()
        self.filechooser.hide()
        self.fromFile(self.filename)
        print("Active Button Clicked")

    def on_aboutbutton_clicked(self, button):
        self.about_dialog.run()
        self.about_dialog.hide()

    def on_detailsbutton_toggled(self, button):
        if button.get_active():
            self.detailsrevealer.set_reveal_child(True)
        else:
            self.detailsrevealer.set_reveal_child(False)

    def openBrokenDialog(self):
        self.BrokenBox.set_visible(True)
        self.mainstack.set_visible_child_name("broken")

    def on_detailsbutton_clicked(self, button):
        if self.detailsrevealer.get_reveal_child():
            self.detailsrevealer.set_reveal_child(False)
            self.detailsbutton.set_label(_("Show Details"))
        else:
            self.detailsrevealer.set_reveal_child(True)
            self.detailsbutton.set_label(_("Hide Details"))

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
            self.errorlabel.set_visible(True)
            self.errorlabel.set_markup("<b><span color='red'>{}</span></b>\n{}".format(
                _("Error !"),  GLib.markup_escape_text(packagefailure, -1)))
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
            self.installed_version.set_markup("<small><span weight='light'>{}</span></small>".format(systemversion))
        else:
            self.installed_version.set_markup(
                "<small><span weight='light'>{}</span></small>".format(_("Not installed")))

    def fromFile(self, path):

        self.openbutton.set_visible(True)
        # self.headerseperator.set_visible(True)
        fileFormat = os.path.basename(path).split(".")[-1]
        if fileFormat == "deb":
            self.debianpackage = path
            if self.start(self.debianpackage):

                self.setLabels()

                self.packageMain(False, self.firststatus, self.packagefailure)
            else:
                self.button1.set_sensitive(False)
                self.button2.set_sensitive(False)
                self.button1.set_label(_("Install"))
                self.button2.set_label(_("Uninstall"))
                self.pacname.set_text("")
                self.pacversion.set_text("")
                self.installed_version_title.set_text("")
                self.installed_version.set_text("")
                self.openBrokenDialog()
        else:
            print("Only .deb files.")

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
        source.readline()
        return True

    def onProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        if line is not None:
            print(line)
            if "dlstatus" in line:
                percent = line.split(":")[2].split(".")[0]
                self.progressbar.set_show_text(True)
                self.progressbar.set_text("{} %".format(percent))
                self.progressbar.set_fraction(int(percent) / 100)
            elif "pmstatus" in line:
                percent = line.split(":")[2].split(".")[0]
                self.progressbar.set_show_text(True)
                self.progressbar.set_text("{} {} %".format(self.packageaction, percent))
                self.progressbar.set_text("{} {} %".format(self.packageaction, percent))
                self.progressbar.set_fraction(int(percent) / 100)
            elif "E:" in line and ".deb" in line:
                print("connection error")
                self.error = True
            elif "E:" in line and "dpkg --configure -a" in line:
                print("dpkg --configure -a error")
                self.error = True
                self.dpkgconferror = True
            elif "E:" in line and "/var/lib/dpkg/lock-frontend" in line:
                print("/var/lib/dpkg/lock-frontend error")
                self.error = True
                self.dpkglockerror = True
        return True

    def onProcessExit(self, pid, retval):
        print("Done. exit code: %s" % (retval))
        if self.error is False:
            if retval == 0:
                self.notificationstate = True
                if self.progressbar.get_show_text():
                    self.progressbar.set_text("100 %")
                    self.progressbar.set_fraction(1)
                self.progstack.set_visible_child_name("done")
            else:
                self.progstack.set_visible_child_name("doneinfo")
                self.doneinfolabel.set_markup("<b>{}</b>".format(_("Not Completed !")))
                self.notificationstate = False
        else:
            errormessage = _("<b><span color='red'>Connection Error !</span></b>")
            if self.dpkglockerror:
                errormessage = _("<b><span color='red'>Dpkg Lock Error !</span></b>")
            elif self.dpkgconferror:
                errormessage = _("<b><span color='red'>Dpkg Interrupt Error !</span></b>")
            self.doneinfolabel.set_markup(errormessage)
            self.notificationstate = False
            if self.progressbar.get_show_text():
                self.progressbar.set_show_text(False)
                self.progressbar.set_fraction(0)
            self.progstack.set_visible_child_name("doneinfo")
        self.updateCache()
        self.status = self.compareVersion()
        self.packagefailure = self.failureControl()
        self.packageMain(True, self.status, self.packagefailure)
        self.getInstalledVersion(self.status)
        self.openbutton.set_sensitive(True)
        self.closestatus = False
        if self.isinstalling and self.status == 0 and retval == 0:
            print("connection lost")
            errormessage = _("<b><span color='red'>Connection Error !</span></b>")
            if self.dpkglockerror:
                errormessage = _("<b><span color='red'>Dpkg Lock Error !</span></b>")
            elif self.dpkgconferror:
                errormessage = _("<b><span color='red'>Dpkg Interrupt Error !</span></b>")
            self.doneinfolabel.set_markup(errormessage)
            if self.progressbar.get_show_text():
                self.progressbar.set_show_text(False)
                self.progressbar.set_fraction(0)
            self.progstack.set_visible_child_name("doneinfo")
            self.notificationstate = False
        if retval == 256:
            errormessage = _("Only one software management tool is allowed to run at the same time.\n"
                                  "Please close the other application\ne.g. 'Update Manager', 'aptitude' or 'Synaptic' first.")
            self.doneinfolabel.set_markup(errormessage)
            if self.progressbar.get_show_text():
                self.progressbar.set_show_text(False)
                self.progressbar.set_fraction(0)
            self.progstack.set_visible_child_name("doneinfo")
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