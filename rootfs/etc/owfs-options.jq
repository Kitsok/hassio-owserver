# OWFS expects a USB bus:device address, not a Linux device-node path.
.devices |= map(
  if .device_type == "usb" and (.device // "") != "" then
    if (.device | test("^/dev/bus/usb/[0-9]+/[0-9]+$")) then
      .device |= (
        capture("^/dev/bus/usb/(?<bus>[0-9]+)/(?<address>[0-9]+)$")
        | "\(.bus | tonumber):\(.address | tonumber)"
      )
    else
      error("USB device must be a /dev/bus/usb/<bus>/<device> path; omit device to use all adapters")
    end
  else
    .
  end
)
