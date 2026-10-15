"""Privileged-helper contract tests; no package operations are executed."""
import contextlib
import io
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "src/Actions.py"


class ActionsTests(unittest.TestCase):
    def run_helper(self, arguments, apt_status=0, locked=False):
        with patch.object(sys, "argv", [str(SCRIPT), *arguments]), \
                patch("apt_pkg.init_system"), \
                patch("apt_pkg.pkgsystem_lock", side_effect=SystemError("busy") if locked else None), \
                patch("apt_pkg.pkgsystem_unlock"), \
                patch("subprocess.call", return_value=apt_status) as command, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                runpy.run_path(str(SCRIPT), run_name="__main__")
            except SystemExit as result:
                status = result.code
            else:
                status = 0
        return status, command

    def test_successful_apt_commands_exit_successfully(self):
        for action in ("install", "reinstall", "downgrade", "remove"):
            with self.subTest(action=action):
                status, command = self.run_helper([action, "/tmp/local package.deb"])
                self.assertEqual(status, 0)
                command.assert_called_once()
                self.assertIn("/tmp/local package.deb", command.call_args.args[0])

    def test_apt_failure_is_returned_for_every_action(self):
        for action in ("install", "reinstall", "downgrade", "remove"):
            with self.subTest(action=action):
                status, command = self.run_helper([action, "fixture"], apt_status=100)
                self.assertEqual(status, 100)
                command.assert_called_once()

    def test_lock_failure_does_not_start_apt(self):
        status, command = self.run_helper(["install", "fixture"], locked=True)
        self.assertEqual(status, 1)
        command.assert_not_called()

    def test_invalid_arguments_fail_before_starting_apt(self):
        for arguments in ([], ["install"], ["unknown", "fixture"]):
            with self.subTest(arguments=arguments):
                status, command = self.run_helper(arguments)
                self.assertEqual(status, 2)
                command.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
