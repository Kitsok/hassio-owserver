# Move gnus 1-Wire into the Home Assistant VM

Prepared from read-only inspection on 2026-09-27. None of these migration
steps have been executed. The `hassos` VM is currently **shut off**. The
working tree has local DS9490-only changes that are not all committed.

Target:

```text
DS18B20 probes → DS9490 → USB passthrough → hassos VM
                                           └─ owserver app → HA 1-Wire integration
```

## 1. On gnus.nigde.ru, before starting the VM

Run this section in an SSH session on gnus as `kostik`.

### Record and back up the current configuration

```bash
ssh -F /dev/null gnus.nigde.ru
virsh -c qemu:///system domstate hassos
lsusb -d 04fa:2490
lsusb -d 2341:0042

migration_dir="$HOME/onewire-migration-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 "$migration_dir"
virsh -c qemu:///system dumpxml hassos --inactive > "$migration_dir/hassos-before.xml"
cp /etc/owfs.conf "$migration_dir/owfs.conf"
systemctl is-enabled owserver.socket owserver.service owfs.service owhttpd.service wire2ha.service > "$migration_dir/enabled-before.txt"
systemctl is-active owserver.socket owserver.service owfs.service owhttpd.service wire2ha.service > "$migration_dir/active-before.txt"
```

Keep the path printed by `echo "$migration_dir"` for rollback. The systemctl
checks may return nonzero because the old `wire2ha` service is disabled.
The XML backup contains VM configuration, not the VM disk or HA data.

Verified hardware:

| Device | USB vendor:product | Current host address |
|---|---|---|
| DS9490 / DS1490F 1-Wire adapter | `04fa:2490` | Bus 002, device 006 |
| Arduino Mega, already assigned to HA | `2341:0042` | Bus 002, device 005 |

The existing Arduino assignment uses bus 2/device 5. Preserve it. Do not
replace it with the DS9490 assignment. Recheck `lsusb` before starting if
hardware has been unplugged, since bus/device numbers can change.

### Stop host 1-Wire consumers and release the adapter

The four OWFS services/socket below were enabled and active during inspection.
The legacy REST pusher `wire2ha.service` was already disabled and inactive.

```bash
sudo systemctl disable --now wire2ha.service owhttpd.service owfs.service
sudo systemctl disable --now owserver.socket owserver.service
sudo systemctl mask owserver.socket owserver.service owhttpd.service owfs.service wire2ha.service

systemctl is-active owserver.socket owserver.service owfs.service owhttpd.service wire2ha.service
pgrep -a -x owserver
pgrep -a -x owhttpd
pgrep -a -x owfs
ss -lnt | grep -E ':(4304|2121)[[:space:]]'
```

Expect inactive services and no matching processes or listeners. These checks
normally return nonzero when nothing is found. Stop here if a process still
owns the adapter; inspect `systemctl status` and its journal before proceeding.
Masking the socket matters: otherwise a connection can reactivate OWServer.

The host has an OWFS mount at `/1wire`, while its service also references
`/run/owfs`. Check for a leftover mount after stopping the service:

```bash
findmnt /1wire
findmnt /run/owfs
```

If either remains mounted as an OWFS/FUSE filesystem, unmount that path with
`sudo umount /1wire` or `sudo umount /run/owfs` as appropriate. If it is busy,
identify and stop its consumer before continuing. Do not delete mount directories
or use a lazy unmount to conceal a running consumer.

### Add persistent USB passthrough

There was exactly one `04fa:2490` adapter during inspection. Select it by
vendor/product, so the assignment survives USB device-number changes.

```bash
cat > "$migration_dir/ds9490.xml" <<'XML'
<hostdev mode='subsystem' type='usb' managed='yes'>
  <source>
    <vendor id='0x04fa'/>
    <product id='0x2490'/>
  </source>
</hostdev>
XML

virsh -c qemu:///system attach-device hassos "$migration_dir/ds9490.xml" --config
virsh -c qemu:///system dumpxml hassos --inactive > "$migration_dir/hassos-after.xml"
diff -u "$migration_dir/hassos-before.xml" "$migration_dir/hassos-after.xml"
```

Expect a new USB host device for `04fa:2490`; the Arduino entry must remain.
Run `attach-device` only once. If resuming this guide, inspect the inactive XML
first. With multiple identical DS9490 adapters, this vendor/product selection
would need disambiguation.

No new USB controller is needed: the VM already has USB 2.0 controllers.
The adapter must be plugged in when starting the VM with this configuration.

### Start the VM

```bash
virsh -c qemu:///system start hassos
virsh -c qemu:///system domstate hassos
```

Expect `running`. If startup fails, read the error and, if needed,
`sudo tail -n 80 /var/log/libvirt/qemu/hassos.log`. Verify both USB devices
are present and the host OWServer is stopped. Do not remove the Arduino
assignment to work around an unrelated DS9490 failure.

## 2. In Home Assistant, after the VM starts

Open <https://newbie.nigde.ru:23223/> and log in normally. The API token in
`secrets.py` is for API authentication, not a browser password.

### Check hardware and make a backup

1. In **Settings → System → Hardware → All hardware**, look for the USB
   adapter identified by vendor `04fa`, product `2490`. A terminal with
   `lsusb` can also confirm it. This adapter does not appear as a serial
   `/dev/ttyUSB*` device.
2. Create and download a Home Assistant backup before changing integrations.
3. The existing 1-Wire integration may temporarily show unavailable entities:
   its old endpoint `172.28.0.33:4304` has been stopped intentionally.

### Install the owserver app

The configured remote is your fork, `https://github.com/Kitsok/hassio-owserver`.
The working changes now point `config.yaml` at
`ghcr.io/kitsok/owserver/{arch}`, and the deploy workflow builds that image
under the fork owner. The current edits are still uncommitted, so the fork
and its image do not contain them yet. To migrate before pushing and publishing
these changes, use the local app route below. After publishing, add the fork
URL directly as the Home Assistant app repository. No separate
`addon-repository` fork is required.

**Install the current working tree as a local app.** On the workstation that
can access `/home/kostik/work/hassio-owserver`, package the worktree contents,
including uncommitted edits but excluding Git metadata and test artifacts:

```bash
source_dir=/home/kostik/work/hassio-owserver
stage_dir=$(mktemp -d /tmp/owserver-ha-local.XXXXXX)
mkdir "$stage_dir/owserver-reviewed"
tar -C "$source_dir" \
  --exclude=.git --exclude=.pytest_cache --exclude=__pycache__ \
  -cf - . | tar -C "$stage_dir/owserver-reviewed" -xf -
python3 - "$stage_dir/owserver-reviewed" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
config = p / 'config.yaml'
lines = config.read_text().splitlines()
lines = [line for line in lines if not line.startswith('image:')]
lines = ['slug: owserver-reviewed' if line.startswith('slug:') else line for line in lines]
lines = ['version: "0.7.0-local.1"' if line.startswith('version:') else line for line in lines]
config.write_text('\n'.join(lines) + '\n')
dockerfile = p / 'Dockerfile'
dockerfile.write_text(dockerfile.read_text().replace(
    'ARG BUILD_FROM\n',
    'ARG BUILD_FROM=ghcr.io/hassio-addons/base/amd64:21.0.2\n', 1))
PY
printf '%s\n' "$stage_dir/owserver-reviewed"
```

Copy the printed directory to HA OS at `/addons/owserver-reviewed` using an
available file transfer method, such as the Samba app's `addons` share. This
is a directory inside HA OS, not `/config` and not a path on the gnus host.
Refresh **Settings → Apps → Local apps**, install **owserver-reviewed**, and
inspect the build/install logs. Removing the remote `image:` setting makes
Supervisor build the local Dockerfile. The explicit `BUILD_FROM` default
supports HA versions that no longer pass it automatically. The local app uses
the current worktree; it does not publish or alter the GitHub fork. Its build
and physical adapter support still need validation during this migration.

The first published release build creates one package per architecture:
`kitsok/owserver/amd64` and `kitsok/owserver/aarch64`. The deploy workflow
needs `packages: write` permission; it is now declared in the workflow. After
the first successful release build:

1. Open the repository's **Packages** section on GitHub.
2. Open each `owserver/amd64` and `owserver/aarch64` package.
3. In **Package settings**, change visibility to **Public** so HA can pull
the image without registry credentials.

Then add `https://github.com/Kitsok/hassio-owserver` to HA's app repositories.
The manifest version must match a published release image; the current
`config.yaml` declares `0.7.0`, so publish the matching `v0.7.0` release or
update the manifest version and publish that matching version.

### Configure the adapter before starting the app

Replace the default fake-device configuration with:

```yaml
devices:
  - device_type: usb
owhttpd: true
temperature_scale: Celsius
debug: false
```

Leave `device` unset: there is one passed-through DS9490, and `usb = all`
avoids relying on its USB address inside the VM. Host bus 002/device 006
is not necessarily its address inside HA OS.

Leave the app's **Network → 4304/tcp** host-port mapping blank. HA Core
can connect over the internal app network. Enable **Start on boot**, save,
and start the app. Keep protection mode enabled unless logs demonstrate
an actual permission problem; USB access is declared in the app manifest.

Check the logs for a discovered DS9490 and the real probe IDs. In **Open
Web UI**, verify these devices and their temperature values:

| Device | Purpose |
|---|---|
| `28.70B9D5030000` | Outdoor DS18B20 |
| `28.A8BED5030000` | Boiler-room DS18B20 |
| `81.D89A30000000` | Adapter identification device; not a temperature probe |

If only a random fake DS18B20 appears, correct the configuration and restart
before changing HA's integration. If the UI reports an unsupported DS1420
family, check that the two actual temperature probes still work.

### Reconfigure the existing 1-Wire integration

1. Open **Settings → Devices & services → 1-Wire**.
2. Find the existing entry titled `172.28.0.33`.
3. From its entry menu, choose **Reconfigure**. This integration advertised
   reconfiguration support during the earlier HA inspection.
4. Set **Host** to the owserver app's internal hostname from its information
   page, and **Port** to `4304`. Copy the actual hostname; a local installation
   and a repository installation have different prefixes. Do not use
   `localhost`, the external HTTPS address, or the old gnus address.
5. Save, and reload the integration if it does not reload automatically.

Reconfigure the existing entry rather than deleting and re-adding it. This
preserves its registry associations, names, and entity IDs. If an automatic
discovery card appears for the app, do not create a second integration while
migrating the existing entry. If Reconfigure is unexpectedly unavailable,
stop here and check the installed HA version instead of deleting the entry.

### Verify completion

In **Developer tools → States**, confirm both existing entities have fresh,
plausible readings in degrees Celsius:

```text
sensor.28_70b9d5030000_temperature   — outdoor temperature
sensor.28_a8bed5030000_temperature  — boiler-room temperature
```

Check their temperature-resolution selectors; both previously read `12`.
Confirm there are no unwanted `_2` duplicates, and that names, history,
and dashboard references remain associated with the original entities.
Allow a few polling cycles and look for renewed state reports; an unchanged
temperature alone is not evidence of a stalled sensor.

Restart the owserver app once and check recovery. When convenient, reboot
HA OS and repeat the checks to validate USB attachment and app autostart.
On gnus, confirm the host OWFS services/socket remain masked and inactive.
Keep the old configuration and packages until this verification succeeds.

## Rollback

1. In HA, stop the owserver app and disable its **Start on boot**.
2. Shut down HA OS cleanly from its system power controls. On gnus, confirm
   `virsh -c qemu:///system domstate hassos` reports `shut off`.
3. In the original gnus shell, or after setting `migration_dir` to the saved
   backup directory, remove only the DS9490 assignment:

```bash
virsh -c qemu:///system detach-device hassos "$migration_dir/ds9490.xml" --config
sudo systemctl unmask owserver.socket owserver.service owhttpd.service owfs.service wire2ha.service
sudo systemctl enable --now owserver.socket owserver.service
sudo systemctl enable --now owfs.service owhttpd.service
virsh -c qemu:///system start hassos
```

Leave `wire2ha.service` disabled; it was not the active HA data path before
migration. If detaching fails, inspect the inactive VM XML and remove only
the `04fa:2490` hostdev entry with `virsh edit`; retain the Arduino entry.
The saved full XML is available for comparison, but do not overwrite unrelated
VM changes made since the backup.

4. In HA, reconfigure the same 1-Wire integration back to host
   `172.28.0.33`, port `4304`, and verify the original sensors update.

## References

- [Your source fork](https://github.com/Kitsok/hassio-owserver)
- [Upstream published add-on repository](https://github.com/lrybak/addon-repository)
- [Upstream application source](https://github.com/lrybak/hassio-owserver)
- [Home Assistant 1-Wire integration](https://www.home-assistant.io/integrations/onewire/)
- [Libvirt USB host-device XML](https://libvirt.org/formatdomain.html#usb-pci-scsi-devices)
- [Home Assistant app configuration and build arguments](https://developers.home-assistant.io/docs/apps/configuration/)
