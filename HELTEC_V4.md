# GhostESP for Heltec WiFi LoRa 32 V4

This target adapts the complete GhostESP v2.1 stable release to the Heltec WiFi
LoRa 32 V4. The upstream source tree and optional integrations are preserved;
the V4 port adds a board configuration, onboard GNSS power handling, CI
packaging, and hardware-specific documentation.

## Hardware mapping

| Function | GPIO / setting |
| --- | --- |
| MCU | ESP32-S3, 240 MHz |
| Flash | 16 MB |
| OLED | SSD1306-compatible, 128x64, I2C address `0x3C` |
| OLED SDA / SCL | GPIO17 / GPIO18 |
| OLED reset | GPIO21 |
| Vext | GPIO36, active low |
| PRG button | GPIO0 |
| USB CLI | USB Serial/JTAG, 115200 baud |
| GNSS receive | GPIO39, 9600 baud |
| GNSS power | GPIO34, active low |

The OLED and Vext wiring are unchanged from the upstream Heltec V3 target. The
V4 target changes the flash geometry and enables GhostESP's existing GPS stack
for the onboard GNSS receiver.

GhostESP does not currently contain an SX1262 backend, so the V4's onboard LoRa
radio is not used by this target. No upstream GhostESP feature or source file is
removed because of that hardware limitation.

## Build

Use ESP-IDF 6.0, matching the upstream CI workflow:

```sh
rm -f sdkconfig sdkconfig.defaults
cp configs/sdkconfig.heltecv4 sdkconfig.defaults
cp configs/sdkconfig.heltecv4 sdkconfig
idf.py set-target esp32s3
SDKCONFIG_DEFAULTS=sdkconfig.defaults idf.py build
```

The GitHub workflow packages `HeltecV4.zip` with `bootloader.bin`,
`partitions.bin`, `firmware.bin`, the ELF file, and a merged image.

## Android-backed storage

The Heltec V4 target uses a 12 MB wear-levelled FAT partition in internal flash
as its virtual SD card. That layout is isolated in
`partitions_heltecv4.csv`; other board configurations retain the shared
partition table appropriate to their flash size. Captures, wardriving CSV
files, and saved scan results are split into approximately 128 KiB closed
segments. Companion app version 0.8.4 or newer can copy those closed files to a
user-selected Android folder over USB, verify their exact byte count and CRC-32,
and then acknowledge them. GhostESP does not release a source file until that
acknowledgement matches.

The companion also publishes the selected Android volume's total and free
bytes. `sd status` reports that Android-backed capacity as the virtual SD size
and reports the protected flash transit queue separately as `spool_total` and
`spool_free`.

The virtual storage is formatted automatically only when its entire flash
partition is blank. A nonblank partition that cannot be mounted is retained for
recovery instead of being reformatted.

This is a finite spool, not unlimited storage by itself. For sustained capture,
keep the Android device connected, keep the selected Android destination
writable, and leave enough free space on the phone. If Android disconnects,
revokes folder access, or fills up, GhostESP retains unacknowledged files until
its internal spool is full rather than deleting unverified data.

## Flash

The ESP32-S3 bootloader is at offset `0x0`, the partition table at `0x8000`,
and the application at `0x10000`:

```sh
idf.py -p /dev/cu.usbmodemXXXX erase-flash
idf.py -p /dev/cu.usbmodemXXXX flash monitor
```

Erasing before the first GhostESP installation intentionally removes the
previous firmware and its saved settings.

Do not use `erase-flash` for a routine update when the virtual SD contains data
you still need. Flashing the generated merged image at offset `0x0` updates the
bootloader, partition table, and application while leaving the `storage`
partition at `0x400000` untouched:

```sh
esptool.py --chip esp32s3 -p /dev/cu.usbmodemXXXX write_flash \
  0x0 GhostESP-heltecv4-android-storage.bin
```
