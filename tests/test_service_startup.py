"""Exercise the production launch scripts without Docker or hardware."""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "rootfs/etc/s6-overlay/s6-rc.d"


class TestServiceStartup(unittest.TestCase):
    def launch(self, service, enabled):
        # Override exec to capture the command instead of starting a daemon.
        harness = r"""
        bashio::config.true() { [ "$1" = "$ENABLED" ]; }
        bashio::log.info() { :; }
        bashio::net.wait_for() { :; }
        exec() { printf '%s\n' "$*"; exit 0; }
        source "$SCRIPT"
        """
        import os
        result = subprocess.run(
            ["bash", "-c", harness],
            env={**os.environ, "ENABLED": enabled, "SCRIPT": str(SERVICES / service / "run")},
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()

    def test_normal_server_stays_foreground(self):
        self.assertEqual(self.launch("owserver", ""),
                         "/opt/owfs/bin/owserver --foreground -c /etc/owfs.conf")

    def test_debug_server_stays_foreground(self):
        self.assertEqual(self.launch("owserver", "debug"),
                         "/opt/owfs/bin/owserver --foreground --debug -c /etc/owfs.conf")

    def test_http_server_stays_foreground(self):
        self.assertEqual(self.launch("owhttpd", "owhttpd"),
                         "/opt/owfs/bin/owhttpd --foreground -r -c /etc/owfs.conf")

    def test_disabled_http_server_waits(self):
        self.assertEqual(self.launch("owhttpd", ""), "/usr/bin/s6-pause")
