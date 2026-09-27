# Home Assistant App: owserver

[![Releases][releases-shield]][releases]

![amd64][amd64-shield]
![aarch64][aarch64-shield]

## About

This app connects DS9490 USB 1-Wire adapters to Home Assistant through the native 1-Wire integration. Fake DS18B20 devices are available for testing without hardware.

### Supported devices

- DS9490R and DS9490B USB adapters (DS2490-based).
- Fake devices for testing.

For HAOS in a QEMU VM, pass the USB adapter through to the VM before configuring the app.

## Installation and configuration

### Installation

1. Access your Home Assistant, go to **Apps** -> **Install app** and add this URL as an additional repository: 
`https://github.com/Kitsok/hassio-owserver`
1. Find the "owserver (1-Wire)" app and click the "INSTALL" button.
1. Configure the app and click on "START". With default configuration app starts with fake (mocked) devices.
1. Add to Home Assistant through the Integrations. Go to Integrations, Add Integration, Choose 1-Wire
    - Host: `provide app's hostname (from app details page)`
    - Port: `4304` _(default)_
1. ... or use Home Asistant auto discovery (since 2025.2.0). Go to Integrations, find discovered app and Add it.
1. That's it. On the integrations page wou will find 1-Wire integration with discovered devices.

### Configuration
Please check the **[full documentation page](https://github.com/Kitsok/hassio-owserver/blob/master/DOCS.md)**.

## Screenshots

![Integration setup 1](https://github.com/Kitsok/hassio-owserver/raw/master/images/screenshot_setup1.png)
![Integration setup 2](https://github.com/Kitsok/hassio-owserver/raw/master/images/screenshot_setup2.png)
![Integrations page](https://github.com/Kitsok/hassio-owserver/raw/master/images/screenshot_integrations.jpg)
![owhttpd](https://github.com/Kitsok/hassio-owserver/raw/master/images/screenshot_owhttpd.png)

[releases-shield]: https://img.shields.io/github/release/Kitsok/hassio-owserver.svg
[releases]: https://github.com/Kitsok/hassio-owserver/releases

[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
