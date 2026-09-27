"""Check web interface enable/disable behavior in the running container."""

import requests


def make_options(devices, owhttpd=True):
    return {
        "devices": devices if isinstance(devices, list) else [devices],
        "owhttpd": owhttpd,
        "temperature_scale": "Celsius",
        "debug": True,
    }


class TestOwhttpd:
    @staticmethod
    def is_owhttpd_running(host, port):
        try:
            requests.get(f"http://{host}:{port}/", timeout=2)
            return True
        except requests.ConnectionError:
            return False

    def test_owhttpd_is_up(self, start_with_config):
        logs = start_with_config(
            make_options({"device_type": "fake"}, owhttpd=True),
        )
        
        assert "starting owhttpd" in logs.lower()
        assert self.is_owhttpd_running("localhost", 8099)

    def test_owhttpd_is_down(self, start_with_config):
        logs = start_with_config(
            make_options({"device_type": "fake"}, owhttpd=False),
        )

        assert "owhttpd is disabled" in logs
        assert not self.is_owhttpd_running("localhost", 8099)
