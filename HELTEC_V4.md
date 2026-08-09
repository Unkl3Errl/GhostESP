# GhostESP for Heltec WiFi LoRa 32 V4

This target adapts the complete GhostESP `Development-deki` firmware to the
Heltec WiFi LoRa 32 V4. The upstream source tree and optional integrations are
preserved; the V4 port adds a board configuration, onboard GNSS power handling,
CI packaging, and hardware-specific documentation.

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

## Flash

The ESP32-S3 bootloader is at offset `0x0`, the partition table at `0x8000`,
and the application at `0x10000`:

```sh
idf.py -p /dev/cu.usbmodemXXXX erase-flash
idf.py -p /dev/cu.usbmodemXXXX flash monitor
```

Erasing before the first GhostESP installation intentionally removes the
previous firmware and its saved settings.
