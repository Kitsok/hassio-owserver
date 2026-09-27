"""Template rendering tests — fast, no container restart needed."""

import pytest

pytestmark = pytest.mark.template


def make_options(devices, temperature_scale="Celsius", owhttpd=True, debug=True):
    return {
        "devices": devices if isinstance(devices, list) else [devices],
        "owhttpd": owhttpd,
        "temperature_scale": temperature_scale,
        "debug": debug,
    }


class TestDeviceTypes:
    def test_fake(self, render_template):
        conf = render_template(make_options({"device_type": "fake"}))
        assert "server: FAKE = DS18B20" in conf

    def test_usb_all(self, render_template):
        conf = render_template(make_options({"device_type": "usb"}))
        assert "server: usb = all" in conf

    def test_usb_specific(self, render_template):
        conf = render_template(make_options({"device_type": "usb", "device": "/dev/bus/usb/001/002"}))
        assert "server: usb = 1:2" in conf

class TestTemperatureScales:
    @pytest.mark.parametrize("scale", ["Celsius", "Fahrenheit", "Kelvin", "Rankine"])
    def test_temperature_scale(self, render_template, scale):
        conf = render_template(make_options({"device_type": "fake"}, temperature_scale=scale))
        assert scale in conf


class TestMultiDevice:
    def test_two_devices(self, render_template):
        devices = [
            {"device_type": "fake"},
            {"device_type": "usb", "device": "/dev/bus/usb/001/002"},
        ]
        conf = render_template(make_options(devices))
        assert "server: FAKE = DS18B20" in conf
        assert "server: usb = 1:2" in conf

    def test_common_config_present(self, render_template):
        conf = render_template(make_options({"device_type": "fake"}))
        assert "server: port = 4304" in conf
        assert "http: port = 8099" in conf
