#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:58:17 2020

@author: fatih
"""
import os
import re
import sys

import apt
import gi

gi.require_version('Gtk', '3.0')
gi.require_version("Notify", "0.7")
from gi.repository import Gtk, GObject, GLib, Gdk, Gio, Notify
import apt.debfile as aptdeb
from subprocess import PIPE, Popen
import threading

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
        self.packagedepcount = 0
        self.isinstalling = False
        self.isbroken = False
        self.debianpackage_errormsg = ""
        self.pid = None

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
        self.define_components()
        self.window.connect('delete_event', self.on_close)

        self.mainstack.set_visible_child_name("splash")

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.about_dialog.set_version(version)
        except:
            pass
        self.about_dialog.set_program_name(_("Pardus Package Installer"))
        if self.about_dialog.get_titlebar() is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("About Pardus Package Installer"))
            about_headerbar.pack_start(
                Gtk.Image.new_from_icon_name("pardus-package-installer", Gtk.IconSize.LARGE_TOOLBAR))
            about_headerbar.show_all()
            self.about_dialog.set_titlebar(about_headerbar)

        self.window.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [Gtk.TargetEntry.new("text/uri-list", 0, 0)],
            Gdk.DragAction.COPY
        )

        self.window.show_all()

        if self.isbroken:
            self.open_broken_dialog()

        self.openbutton.set_visible(False)
        self.progstack.set_visible(False)
        self.errorlabel.set_visible(False)
        self.BrokenBox.set_visible(False)
        self.outputSW.set_visible(False)

        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        result = self.initialize_backend()
        GLib.idle_add(self.initialize_ui, result)

    def initialize_backend(self):
        if not self.file:
            return {"state": "empty"}

        self.debianpackage = os.path.abspath(sys.argv[1])
        debianpackage_status = self.start(self.debianpackage)

        if debianpackage_status is None:
            return {
                "state": "broken",
                "error": self.debianpackage_errormsg
            }

        if debianpackage_status:
            return {
                "state": "ok",
                "firststatus": self.firststatus,
                "packagefailure": self.packagefailure
            }

        return {"state": "invalid"}

    def initialize_ui(self, result):
        state = result["state"]

        self.button1.set_label(_("Install"))
        self.button2.set_label(_("Uninstall"))

        if state == "empty":
            self.mainstack.set_visible_child_name("empty")
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self._clear_package_labels()

        elif state == "broken":
            self._clear_package_labels()
            self.debpackage_brokenmsg.set_text(result["error"])
            self.mainstack.set_visible_child_name("brokendeb")

        elif state == "invalid":
            self._clear_package_labels()
            self.open_broken_dialog()

        elif state == "ok":
            self.openbutton.set_visible(True)
            self.mainstack.set_visible_child_name("package")

            self.set_labels()
            self.package_main(
                False,
                result["firststatus"],
                result["packagefailure"]
            )

        return False

    def _clear_package_labels(self):
        self.pacname.set_text("")
        self.pacversion.set_text("")
        self.shortdesc.set_text("")
        self.installed_version_title.set_text("")
        self.installed_version.set_text("")

    def set_labels(self):
        self.depends.set_text("")
        self.missingdeps.set_text("")
        self.dependency_count_label.set_text("")
        self.dependency_count_box.set_visible(False)
        self.mainstack.set_visible_child_name("package")
        self.progstack.set_visible(False)
        self.doneinfolabel.set_text("")
        self.errorlabel.set_visible(False)

        self.pacname.set_markup(
            "<span size='x-large'><b>{}</b></span>".format(
                GLib.markup_escape_text(self.packagename, -1)
            )
        )

        self.pacversion.set_markup(
            "<small>{}</small>".format(
                GLib.markup_escape_text(self.packageversion, -1)
            )
        )

        self.shortdesc.set_markup(
            "<small>{}</small>".format(
                GLib.markup_escape_text(self.packageshortdescription, -1)
            )
        )
        self.shortdesc.set_tooltip_text(self.packagedescription)

        self.maintainername.set_text(self.packagemaintainername)

        if self.packagemaintainermail != "-":
            mail = GLib.markup_escape_text(self.packagemaintainermail, -1)
            self.maintainermail.set_markup(
                f"<a title='{mail}' href='mailto:{mail}'>{mail}</a>"
            )
        else:
            self.maintainermail.set_text(self.packagemaintainermail)

        if self.packagehomepage != "-":
            homepage = GLib.markup_escape_text(self.packagehomepage, -1)
            self.homepage.set_markup(
                f"<a title='{homepage}' href='{homepage}'>{homepage}</a>"
            )
        else:
            self.homepage.set_text(self.packagehomepage)

        self.section.set_text(self.packagesection)
        self.architecture.set_text(self.packagearchitecture)

        if self.packagesize != "-":
            self.size.set_text(f"{self.packagesize} KiB")
        else:
            self.size.set_text(self.packagesize)

        pd = self.packagedepends or ""
        items = [item.strip() for item in pd.split(",")]
        formatted = []
        for item in items:
            formatted.append(item.replace("|", " | "))
        pd = "\n\n".join(formatted)
        self.depends.set_markup("<small>{}</small>".format(GLib.markup_escape_text(pd, -1)))

        if self.packagemissingdeps:
            self.missingdeps.set_markup("<small>{}</small>".format(
                GLib.markup_escape_text(self.packagemissingdeps, -1)))

        self.installed_version_title.set_markup(
            "<small><span weight='light'>{}</span></small>".format(_("Installed Version :")))

        pkg = self.cache.get(self.packagename)
        if pkg and pkg.is_installed:
            systemversion = pkg.installed.version
            self.installed_version.set_markup(f"<small><span weight='light'>{systemversion}</span></small>")
        else:
            self.installed_version.set_markup(
                "<small><span weight='light'>{}</span></small>".format(_("Not installed")))

        if self.packagedepcount > 0:
            count_text = _("{} additional packages will be installed").format(self.packagedepcount)
            self.dependency_count_label.set_markup(
                "<small><span weight='light'>{}</span></small>".format(
                    GLib.markup_escape_text(count_text, -1)
                )
            )
            self.dependency_count_box.set_visible(True)
        else:
            self.dependency_count_box.set_visible(False)

        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)

        self.window.set_focus(None)

    def package_main(self, actioned, status, packagefailure):
        has_error = packagefailure and "A later version is already installed" not in packagefailure

        if has_error:
            self.errorlabel.set_visible(True)
            self.errorlabel.set_markup(
                "<b><span color='red'>{}</span></b>\n{}".format(
                    _("Error !"),
                    GLib.markup_escape_text(packagefailure, -1)
                )
            )

        # VERSION_NONE = 0
        # VERSION_OUTDATED = 1
        # VERSION_SAME = 2
        # VERSION_NEWER = 3
        config = {
            0: (_("Install"), self.installicon, False),
            1: (_("Downgrade"), self.downgradeicon, True),
            2: (_("Reinstall"), self.reinstallicon, True),
            3: (_("Upgrade"), self.upgradeicon, True),
        }

        label, icon, allow_remove = config.get(status, config[0])

        self.button1.set_label(label)
        self.button1.set_image(icon)
        self.button1.set_sensitive(not has_error)

        self.button2.set_sensitive(allow_remove and not has_error)

    def on_mainwindow_drag_data_received(self, treeview, context, posx, posy, selection, info, timestamp):
        if self.pid:
            print("There is a process currently running.")
            return
        for uri in selection.get_uris():
            file = Gio.File.new_for_uri(uri)
            path = file.get_path()
            self.from_file(path)

    def initialize(self):
        if self.file:
            self.debianpackage = os.path.abspath(sys.argv[1])
            debianpackage_status = self.start(self.debianpackage)
            if debianpackage_status is not None:
                if debianpackage_status:
                    self.openbutton.set_visible(True)
                    self.mainstack.set_visible_child_name("package")
                    self.openbutton.set_visible(True)

                    self.set_labels()

                    self.package_main(False, self.firststatus, self.packagefailure)
                else:
                    self.button1.set_sensitive(False)
                    self.button2.set_sensitive(False)
                    self.button1.set_label(_("Install"))
                    self.button2.set_label(_("Uninstall"))
                    self.pacname.set_text("")
                    self.pacversion.set_text("")
                    self.installed_version_title.set_text("")
                    self.installed_version.set_text("")
                    self.open_broken_dialog()
            else:
                # deb package is broken
                self.button1.set_sensitive(False)
                self.button2.set_sensitive(False)
                self.button1.set_label(_("Install"))
                self.button2.set_label(_("Uninstall"))
                self.pacname.set_text("")
                self.pacversion.set_text("")
                self.shortdesc.set_text("")
                self.installed_version_title.set_text("")
                self.installed_version.set_text("")
                self.debpackage_brokenmsg.set_text(self.debianpackage_errormsg)
                self.mainstack.set_visible_child_name("brokendeb")
        else:
            self.mainstack.set_visible_child_name("empty")
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.button1.set_label(_("Install"))
            self.button2.set_label(_("Uninstall"))
            self.pacname.set_text("")
            self.pacversion.set_text("")
            self.installed_version_title.set_text("")
            self.installed_version.set_text("")

    def define_components(self):
        self.button1 = self.builder.get_object("button1")
        self.button2 = self.builder.get_object("button2")
        self.openbutton = self.builder.get_object("openbutton")
        self.headerseperator = self.builder.get_object("headerseperator")
        self.filechooser = self.builder.get_object("filechooser")
        self.selectbutton = self.builder.get_object("selectbutton")
        self.aboutbutton = self.builder.get_object("aboutbutton")
        self.broken_close_button = self.builder.get_object("broken_close_button")
        self.debpackage_brokenmsg = self.builder.get_object("debpackage_brokenmsg")

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
        self.dependency_count_box = self.builder.get_object("dependency_count_box")
        self.dependency_count_label = self.builder.get_object("dependency_count_label")

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

        self.outputSW = self.builder.get_object("outputSW")

        self.BrokenBox = self.builder.get_object("BrokenBox")
        self.cannotclose_dialog = self.builder.get_object("cannotclose_dialog")
        self.about_dialog = self.builder.get_object("about_dialog")

    def start(self, debpackage):

        self.errorlabel.set_visible(False)
        self.errorlabel.set_text("")

        if self.update_cache():

            try:
                self.package = aptdeb.DebPackage(debpackage)
            except Exception as e:
                print("{}".format(e))
                self.debianpackage_errormsg = "{}".format(e)
                return None
            self.packagename = self.package.pkgname

            self.firststatus = self.package.compare_to_version_in_cache()

            self.installable = self.package.check()

            try:
                self.packageversion = self.package._sections["Version"]
            except Exception as e:
                print("{}".format(e))
                self.packageversion = "-"

            try:
                self.packagedescription = self.package._sections["Description"]
            except Exception as e:
                print("{}".format(e))
                self.packagedescription = ""

            try:
                self.packageshortdescription = self.package["Description"].split("\n")[0]
            except Exception as e:
                print("{}".format(e))
                self.packageshortdescription = ""

            try:
                self.packagemaintainer = self.package._sections["Maintainer"]
            except Exception as e:
                print("{}".format(e))
                self.packagemaintainer = "-"

            try:
                self.packagemaintainername = self.packagemaintainer.split(" <")[0]
            except Exception as e:
                print("{}".format(e))
                self.packagemaintainername = "-"

            try:
                self.packagemaintainermail = self.packagemaintainer.split(" <")[1].replace(">", "")
            except Exception as e:
                print("{}".format(e))
                self.packagemaintainermail = "-"

            try:
                self.packagehomepage = self.package._sections["Homepage"]
            except Exception as e:
                print("{}".format(e))
                self.packagehomepage = "-"

            try:
                self.packagesection = self.package._sections["Section"]
            except Exception as e:
                print("{}".format(e))
                self.packagesection = "-"

            try:
                self.packagesize = self.package._sections["Installed-Size"]
            except Exception as e:
                print("{}".format(e))
                self.packagesize = "-"

            try:
                self.packagearchitecture = self.package._sections["Architecture"]
            except Exception as e:
                print("{}".format(e))
                self.packagearchitecture = "-"

            depends = self.package._sections.get("Depends", "")
            recommends = self.package._sections.get("Recommends", "")
            if depends and recommends:
                self.packagedepends = f"{depends}, {recommends}"
            else:
                self.packagedepends = depends or recommends

            self.packagedepcount = 0
            if self.packagedepends:
                deps_list = [item.strip() for item in self.packagedepends.split(",")]
                self.packagedepcount = len(deps_list)

            missing = []
            try:
                missing = self.package.missing_deps or []
            except Exception:
                pass
            if not missing:
                try:
                    rc = self.package.required_changes
                    if isinstance(rc, dict):
                        missing = rc.get("missing", [])
                    elif isinstance(rc, (list, tuple)) and rc:
                        missing = rc[0]
                except Exception:
                    pass
            self.packagemissingdeps = "\n\n".join(map(str, missing))

            try:
                self.packagefailure = self.package._failure_string
            except Exception as e:
                print("{}".format(e))
                self.packagefailure = ""

            return True

        return False

    def update_cache(self):
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

    def compare_version(self):
        # VERSION_NEWER = 3
        # VERSION_NONE = 0
        # VERSION_OUTDATED = 1
        # VERSION_SAME = 2
        return aptdeb.DebPackage(self.debianpackage).compare_to_version_in_cache()

    def failure_control(self):
        return aptdeb.DebPackage(self.debianpackage)._failure_string

    def install_package(self, isupgrading):

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
            self.pid = self.start_process(self.command)
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
                    self.packagearchitecture))

    def remove_package(self):

        if self.cache[self.packagename].is_installed:
            self.progressbar.set_show_text(False)
            self.progressbar.set_fraction(0)
            self.button1.set_sensitive(False)
            self.button2.set_sensitive(False)
            self.openbutton.set_sensitive(False)
            self.closestatus = True
            self.notification = Notify.Notification.new(self.packagename + _(" uninstalled"))
            self.command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "remove",
                            self.packagename]
            self.pid = self.start_process(self.command)

    def reinstall_package(self):
        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)
        self.button1.set_sensitive(False)
        self.button2.set_sensitive(False)
        self.openbutton.set_sensitive(False)
        self.closestatus = True
        self.notification = Notify.Notification.new(self.packagename + _(" reinstalled"))
        self.command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "reinstall",
                        self.debianpackage]
        self.pid = self.start_process(self.command)

    def downgrade_package(self):
        self.progressbar.set_show_text(False)
        self.progressbar.set_fraction(0)
        self.button1.set_sensitive(False)
        self.button2.set_sensitive(False)
        self.openbutton.set_sensitive(False)
        self.closestatus = True
        self.notification = Notify.Notification.new(self.packagename + _(" downgraded"))
        self.command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "downgrade",
                        self.debianpackage]
        self.pid = self.start_process(self.command)

    def on_button1_clicked(self, button):
        print("debianpackage = " + self.debianpackage)
        packagestatus = self.compare_version()
        self.progstack.set_visible(True)
        self.progstack.set_visible_child_name("progress")
        self.outputSW.set_visible(True)

        if packagestatus == 0:
            print("Installing Button Clicked")
            self.packageaction = _("Installing")
            self.install_package(False)

        elif packagestatus == 1:
            self.packageaction = _("Downgrading")
            print("Downgrading Button Clicked")
            self.downgrade_package()

        elif packagestatus == 2:
            self.packageaction = _("Reinstalling")
            print("Reinstalling Button Clicked")
            self.reinstall_package()

        elif packagestatus == 3:
            self.packageaction = _("Upgrading")
            print("Upgrading Button Clicked")
            self.install_package(True)

    def on_button2_clicked(self, button):
        self.packageaction = _("Uninstalling")
        print("Uninstalling Button Clicked")
        self.progstack.set_visible(True)
        self.progstack.set_visible_child_name("progress")
        self.outputSW.set_visible(True)
        self.remove_package()

    def on_donebutton_clicked(self, button):
        self.window.get_application().quit()

    def on_openbutton_clicked(self, button):
        self.filechooser.run()
        self.filechooser.hide()
        print("Open Button Clicked")

    def on_selectbutton_clicked(self, widget):
        self.filename = self.filechooser.get_filename()
        self.filechooser.hide()
        self.from_file(self.filename)
        print("Select Button Clicked")

    def on_filechooser_file_activated(self, widget):
        self.filename = self.filechooser.get_filename()
        self.filechooser.hide()
        self.from_file(self.filename)
        print("Active Button Clicked")

    def on_aboutbutton_clicked(self, button):
        self.about_dialog.run()
        self.about_dialog.hide()

    def on_detailsbutton_toggled(self, button):
        if button.get_active():
            self.detailsrevealer.set_reveal_child(True)
        else:
            self.detailsrevealer.set_reveal_child(False)

    def open_broken_dialog(self):
        self.BrokenBox.set_visible(True)
        self.mainstack.set_visible_child_name("broken")

    def on_detailsbutton_clicked(self, button):
        if self.detailsrevealer.get_reveal_child():
            self.detailsrevealer.set_reveal_child(False)
            self.detailsbutton.set_label(_("Show Details"))
        else:
            self.detailsrevealer.set_reveal_child(True)
            self.detailsbutton.set_label(_("Hide Details"))

    def from_file(self, path):

        self.openbutton.set_visible(True)

        # clear output textbuffer
        self.outputSW.set_visible(False)
        start, end = self.textview.get_buffer().get_bounds()
        self.textview.get_buffer().delete(start, end)

        fileFormat = os.path.basename(path).split(".")[-1]
        if fileFormat == "deb":
            self.debianpackage = path
            debianpackage_status = self.start(self.debianpackage)
            if debianpackage_status is not None:
                if debianpackage_status:

                    self.set_labels()

                    self.package_main(False, self.firststatus, self.packagefailure)
                else:
                    self.button1.set_sensitive(False)
                    self.button2.set_sensitive(False)
                    self.button1.set_label(_("Install"))
                    self.button2.set_label(_("Uninstall"))
                    self.pacname.set_text("")
                    self.pacversion.set_text("")
                    self.installed_version_title.set_text("")
                    self.installed_version.set_text("")
                    self.open_broken_dialog()
            else:
                # deb package is broken
                self.button1.set_sensitive(False)
                self.button2.set_sensitive(False)
                self.button1.set_label(_("Install"))
                self.button2.set_label(_("Uninstall"))
                self.pacname.set_text("")
                self.pacversion.set_text("")
                self.shortdesc.set_text("")
                self.installed_version_title.set_text("")
                self.installed_version.set_text("")
                self.debpackage_brokenmsg.set_text(self.debianpackage_errormsg)
                self.mainstack.set_visible_child_name("brokendeb")
        else:
            print("Only .deb files.")

    def on_close(self, *args):
        if self.closestatus:
            self.cannotclose_dialog.run()
            self.cannotclose_dialog.hide()
            return True
        return self.closestatus

    def start_process(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.on_process_stdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.on_process_stderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, self.on_process_exit)

        return pid

    def on_process_stdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False

        self.textview.get_buffer().insert(self.textview.get_buffer().get_end_iter(), source.readline())
        self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)

        return True

    def on_process_stderr(self, source, condition):
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
            elif re.match(r"^[A-Za-zÇĞİÖŞÜçğıöşü]+:", line.strip()) and ".deb" in line:
                print("connection error")
                self.error = True
            elif re.match(r"^[A-Za-zÇĞİÖŞÜçğıöşü]+:", line.strip()) and "dpkg --configure -a" in line:
                print("dpkg --configure -a error")
                self.error = True
                self.dpkgconferror = True
            elif re.match(r"^[A-Za-zÇĞİÖŞÜçğıöşü]+:", line.strip()) and "/var/lib/dpkg/lock-frontend" in line:
                print("/var/lib/dpkg/lock-frontend error")
                self.error = True
                self.dpkglockerror = True

            self.textview.get_buffer().insert(self.textview.get_buffer().get_end_iter(), (line))
            self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)

        return True

    def on_process_exit(self, pid, retval):
        print(f"Done. exit code: {retval}")
        self.pid = None
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

        self.update_cache()
        self.status = self.compare_version()
        self.packagefailure = self.failure_control()
        self.package_main(True, self.status, self.packagefailure)

        pkg = self.cache.get(self.packagename)
        if pkg and pkg.is_installed:
            systemversion = pkg.installed.version
            self.installed_version.set_markup(f"<small><span weight='light'>{systemversion}</span></small>")
        else:
            self.installed_version.set_markup(
                "<small><span weight='light'>{}</span></small>".format(_("Not installed")))

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
        self.textview.scroll_to_iter(self.textview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)

    def notify(self):
        if not self.notificationstate:
            return

        if not Notify.is_initted():
            Notify.init("tr.org.pardus.package-installer")

        icon_theme = Gtk.IconTheme.get_default()

        icon_names = [self.packagename, "pardus-package-installer", "dialog-information", ]

        pixbuf = None
        for name in icon_names:
            try:
                pixbuf = icon_theme.load_icon(name, 64, Gtk.IconLookupFlags.FORCE_SIZE)
                break
            except GLib.Error:
                continue

        if pixbuf:
            self.notification.set_icon_from_pixbuf(pixbuf)

        if not self.window.is_active():
            self.notification.show()
