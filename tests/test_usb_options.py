"""Check the real startup normalizer without Docker or USB hardware."""

import json
import subprocess
import unittest
from pathlib import Path

FILTER = Path(__file__).resolve().parents[1] / "rootfs/etc/owfs-options.jq"


class TestUsbOptions(unittest.TestCase):
    def normalize(self, devices):
        return subprocess.run(
            ["jq", "-f", str(FILTER)], input=json.dumps({"devices": devices}),
            text=True, capture_output=True,
        )

    def test_usb_path_becomes_numeric_address(self):
        result = self.normalize([{"device_type": "usb", "device": "/dev/bus/usb/002/006"}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["devices"][0]["device"], "2:6")

    def test_unspecified_usb_and_fake_are_unchanged(self):
        devices = [{"device_type": "usb"},
                   {"device_type": "fake"}]
        result = self.normalize(devices)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["devices"], devices)

    def test_unsupported_paths_fail_instead_of_selecting_first_adapter(self):
        for path in ["/dev/ttyUSB0", "/dev/ds9490", "/dev/bus/usb/002/006junk"]:
            with self.subTest(path=path):
                result = self.normalize([{"device_type": "usb", "device": path}])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("USB device must be", result.stderr)

    def test_removed_and_unknown_adapters_are_rejected(self):
        for device_type in ("serial", "passive", "pbm", "ha7net", "link",
                            "enet", "etherweather", "w1", "i2c", "unknown", None):
            with self.subTest(device_type=device_type):
                result = self.normalize([{"device_type": device_type}])
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Unsupported device_type", result.stderr)

    def test_multiple_usb_adapters_keep_distinct_addresses(self):
        devices = [{"device_type": "usb", "device": f"/dev/bus/usb/001/{n:03}"}
                   for n in (2, 3)]
        result = self.normalize(devices)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([d["device"] for d in json.loads(result.stdout)["devices"]],
                         ["1:2", "1:3"])
