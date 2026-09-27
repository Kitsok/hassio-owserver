# owserver

The app connects DS9490R and DS9490B USB adapters to Home Assistant. Fake devices are available for testing without hardware.

## Configuration

Restart the app after changing its configuration.

For HAOS in a QEMU VM, pass the USB adapter through to the VM first. Device paths below refer to devices inside the VM.

Use all attached DS9490 adapters:

```yaml
devices:
  - device_type: usb
owhttpd: true
temperature_scale: Celsius
debug: false
```

Select a specific adapter:

```yaml
devices:
  - device_type: usb
    device: /dev/bus/usb/001/002
owhttpd: true
temperature_scale: Celsius
```

The default configuration uses `device_type: fake` to simulate a DS18B20 sensor.

### Option: `devices`

A list of adapters or simulated devices.

#### Sub-option: `device_type`

- `usb`: DS9490 USB adapters (DS2490-based).
- `fake`: simulated DS18B20 sensor for testing.

#### Sub-option: `device`

For `usb`, omit `device` to use all attached DS9490 adapters. To select one adapter, set its `/dev/bus/usb/<bus>/<device>` path. The app converts this to the numeric address required by OWFS.

USB bus and device numbers can change after reconnecting or restarting the VM, so omitting `device` is preferable when only one adapter is passed through. Multiple adapters can be selected using separate entries in `devices`.

### Migrating existing configurations

Only `usb` and `fake` are supported. Serial, USB-serial, PBM, and Ethernet bus masters are no longer supported. Existing configurations using those adapters must be replaced with a DS9490 USB configuration; remove the old `server` and `ha7net_server` fields as well.

### Option: `owhttpd`

Enable to start the embedded owhttpd server _(Default true)_.
owhttpd server is exposed via **Ingress (Open Web UI)**

### Option: `temperature_scale`

Specify temperature scale used by owserver from the options below:
- Celsius _default_
- Fahrenheit
- Kelvin
- Rankine

### Option: `debug`

Enable verbose owserver logging for troubleshooting. The server remains available to Home Assistant in debug mode.

## Network: Exposing owserver port to LAN

By default, the owserver port (4304) is only accessible within the Home Assistant network. If you need other devices on your LAN to query owserver directly, you can optionally expose the port.

To enable:
1. Go to **Settings → Add-ons → owserver → Configuration → Network**
2. Set the port number (e.g. `4304`) in the **"owserver 1-Wire (set port number to expose to LAN)"** field
3. Click **Save** and restart the addon

To disable, clear the port field, save and restart.

## Home Assistant integration

1. Configure and start app. With default configuration app starts with fake (mocked) devices.
1. Add to Home Assistant through the Integrations. Go to Integrations, Add Integration, Choose 1-Wire
    - Host: `provide app's hostname (from app details page)`
    - Port: `4304` _(default)_
1. ... or use Home Asistant auto discovery (since 2025.2.0). Go to Integrations, find discovered app and Add it.
1. That's it. On the integrations page wou will find 1-Wire integration with 1-Wire devices.
