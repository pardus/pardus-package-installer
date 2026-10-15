"""Real GTK result tests; APT and privileged helpers are not run."""
import contextlib
import io
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import MainWindow as module
from gi.repository import Gtk, GLib, Gio


class OperationResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Gtk.Application(application_id="tr.org.pardus.installerresulttest",
                                  flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.app.register(None)

    def setUp(self):
        redirect = contextlib.redirect_stdout(io.StringIO())
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)
        self.errors = []
        exception_hook = patch.object(sys, "excepthook", lambda *args: self.errors.append(args[1]))
        exception_hook.start()
        self.addCleanup(exception_hook.stop)
        with patch.object(module.threading, "Thread"):
            self.w = module.MainWindow(self.app, None)
        self.w.packagename = "fixture"
        self.w.packageaction = "Installing"
        self.w.cache = {"fixture": SimpleNamespace(is_installed=True,
                                                   installed=SimpleNamespace(version="1.0"))}
        self.w.update_cache = Mock(return_value=True)
        self.w.compare_version = Mock(return_value=2)
        self.w.failure_control = Mock(return_value="")
        self.w.notify = Mock()

    def tearDown(self):
        context = GLib.MainContext.default()
        for _ in range(1000):
            if not context.pending():
                break
            context.iteration(False)
        for obj in self.w.builder.get_objects():
            if isinstance(obj, Gtk.Window):
                obj.destroy()
        self.assertEqual(self.errors, [])

    def stderr(self, line):
        self.w.on_process_stderr(io.StringIO(line), GLib.IO_IN)

    def assert_success(self):
        self.assertEqual(self.w.progstack.get_visible_child_name(), "done")
        self.assertTrue(self.w.notificationstate)
        self.assertFalse(self.w.closestatus)
        self.assertTrue(self.w.openbutton.get_sensitive())

    def test_warning_about_deb_does_not_turn_success_into_failure(self):
        for message in (
            "N: Download is performed unsandboxed as root: '/home/user/private/package.deb'.\n",
            "Notice: Local package.deb could not be accessed by user '_apt'.\n",
            "Uyarı: '/home/user/private/package.deb' _apt kullanıcısı tarafından okunamadı.\n",
        ):
            with self.subTest(message=message):
                self.stderr(message)
                self.w.on_process_exit(123, 0)
                self.assert_success()
                buffer = self.w.textview.get_buffer()
                self.assertIn(message, buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True))

    def test_apt_failure_is_not_reported_as_success(self):
        self.w.on_process_exit(123, 100 << 8)
        self.assertEqual(self.w.progstack.get_visible_child_name(), "doneinfo")
        self.assertFalse(self.w.notificationstate)
        self.assertIn(module._("Not Completed !"), self.w.doneinfolabel.get_text())

    def test_failed_removal_keeps_error_and_installed_version(self):
        self.w.packageaction = "Uninstalling"
        self.stderr("E: Sub-process /usr/bin/dpkg returned an error code (1)\n")
        self.w.on_process_exit(123, 100 << 8)
        self.assertEqual(self.w.progstack.get_visible_child_name(), "doneinfo")
        self.assertFalse(self.w.notificationstate)
        self.assertIn("1.0", self.w.installed_version.get_text())

    def test_warning_does_not_mislabel_failure_as_connection_error(self):
        self.stderr("N: Local package.deb cannot be read by _apt.\n")
        self.w.on_process_exit(123, 100 << 8)
        self.assertEqual(self.w.doneinfolabel.get_text(), module._("Not Completed !"))

    def test_successful_removal_does_not_require_installed_version(self):
        self.w.cache = {}
        self.w.compare_version.return_value = 0
        self.w.on_process_exit(123, 0)
        self.assert_success()
        self.assertEqual(self.w.installed_version.get_text(), module._("Not installed"))

    def test_permission_cancellation_and_signal_are_not_success(self):
        for status in (126 << 8, 127 << 8, 15):
            with self.subTest(status=status):
                self.w.on_process_exit(123, status)
                self.assertEqual(self.w.progstack.get_visible_child_name(), "doneinfo")
                self.assertFalse(self.w.notificationstate)

    def test_lock_preflight_preserves_existing_explanation(self):
        self.w.on_process_exit(123, 1 << 8)
        self.assertFalse(self.w.notificationstate)
        self.assertIn(module._("Only one software management tool is allowed to run at the same time.\n"
                               "Please close the other application\ne.g. 'Update Manager', 'aptitude' or 'Synaptic' first."),
                      self.w.doneinfolabel.get_text())

    def test_dpkg_diagnostics_are_only_errors_on_failed_exit(self):
        for line, expected in (
            ("E: Run dpkg --configure -a first.\n", module._("<b><span color='red'>Dpkg Interrupt Error !</span></b>")),
            ("E: Could not acquire /var/lib/dpkg/lock-frontend.\n", module._("<b><span color='red'>Dpkg Lock Error !</span></b>")),
        ):
            with self.subTest(line=line):
                self.stderr(line)
                self.w.on_process_exit(123, 100 << 8)
                self.assertEqual(self.w.doneinfolabel.get_label(), expected)
                self.assertFalse(self.w.notificationstate)
                self.stderr(line)
                self.w.on_process_exit(123, 0)
                self.assert_success()

    def test_process_output_is_drained_before_completion(self):
        script = ("import os,sys; "
                  "os.write(1, b'output line\\n' * 300 + b'last stdout\\n'); "
                  "os.write(2, b'warning line\\n' * 300 + b'last stderr\\n' "
                  "+ b'E: Could not acquire /var/lib/dpkg/lock-frontend.'); "
                  "sys.exit(100)")
        self.run_process(script)
        buffer = self.w.textview.get_buffer()
        output = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        self.assertIn("last stdout\n", output)
        self.assertIn("last stderr\n", output)
        self.assertEqual(output.count("output line\n"), 300)
        self.assertEqual(output.count("warning line\n"), 300)
        self.assertEqual(self.w.progstack.get_visible_child_name(), "doneinfo")
        self.assertEqual(self.w.doneinfolabel.get_label(),
                         module._("<b><span color='red'>Dpkg Lock Error !</span></b>"))

    def test_closed_pipes_wait_for_child_exit_and_next_operation_is_independent(self):
        # EOF can precede child exit; an empty successful operation can follow
        # a failed one without retaining its result or diagnostics.
        self.run_process("import os,time,sys; os.close(1); os.close(2); time.sleep(0.1); sys.exit(100)")
        self.assertFalse(self.w.notificationstate)
        self.run_process("pass")
        self.assert_success()

    def run_process(self, script):
        self.w.pid = self.w.start_process([sys.executable, "-c", script])
        context = GLib.MainContext.default()
        deadline = time.monotonic() + 10
        while self.w.pid is not None and time.monotonic() < deadline:
            context.iteration(False)
            time.sleep(0.001)
        self.assertIsNone(self.w.pid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
