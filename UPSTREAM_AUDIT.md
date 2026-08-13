# Upstream completeness audit

Audit date: 2026-08-13

## Source identity

| Item | Value |
| --- | --- |
| Upstream repository | `https://github.com/GhostESP-Revival/GhostESP.git` |
| Upstream release | `v2.1` (stable) |
| Audited upstream commit | `9151548e8d841afb38f97ac9bc31d4e33e71a243` |
| Local adaptation branch | `agent/ghostesp-2.1-mobile.5-stable` |
| Upstream tracked paths | 4,258 |
| Deleted upstream paths | **0** |

The local branch begins directly at the audited stable tag. The complete
upstream tracked tree remains present. The V4 adaptation modifies 25 tracked
files and adds four board-specific or provenance files.

## Intentional tracked changes

| Path | Purpose |
| --- | --- |
| `.github/workflows/compile_all.yml`, `README.md` | Add the `HeltecV4.zip` CI target and support-matrix row. |
| `components/esp_audio_codec/CMakeLists.txt` | Avoid an incompatible redundant library search path under ESP-IDF 6.0. |
| `configs/sdkconfig.heltecv4`, `main/Kconfig.projbuild`, `main/managers/gps_manager.c` | Configure the V4 hardware, display, USB console, GNSS, and virtual storage. |
| `main/core/glog.c`, `main/core/serial_manager.c` | Deliver CLI output through USB Serial/JTAG. |
| `main/core/commands/cmd_sd.c`, capture writers and headers | Segment captures and expose CRC-verified archive acknowledgement without releasing active files. |
| `main/managers/sd_card_manager.c`, partition tables | Mount a V4-only 12 MB wear-levelled FAT spool and preserve nonblank mount failures for recovery. |
| `main/managers/ap_manager.c`, `webui/`, embedded Web UI header | Persist settings correctly and serve the matching rebuilt Web UI. |
| `include/core/ghostesp_version.h`, `CHANGELOG.md`, `HELTEC_V4.md` | Identify and document the mobile release. |

## Added board files

| Path | Purpose |
| --- | --- |
| `configs/sdkconfig.heltecv4` | Complete ESP32-S3/16 MB/OLED/GPS Heltec V4 build configuration. |
| `HELTEC_V4.md` | Hardware map and build/flash instructions. |
| `UPSTREAM_AUDIT.md` | This permanent provenance and completeness record. |

## Verification results

- `git diff --diff-filter=D` reported no tracked deletions.
- `git diff --check` reported no whitespace errors.
- `git fsck --no-dangling --no-progress` reported no repository errors.
- The retained Doom example submodule resolves to
  `f64baf56a852a29be7107e7da3b19cd10feae48a`.
- Build and hardware verification are recorded with the release artifacts.

## Reproduce the source audit

```sh
base=9151548e8d841afb38f97ac9bc31d4e33e71a243
git ls-remote origin refs/tags/v2.1
git ls-tree -r --name-only "$base" | wc -l
git diff --name-status "$base" --
git diff --diff-filter=D --name-only "$base" --
git ls-files --others --exclude-standard
git diff --check
git fsck --no-dangling --no-progress
shasum -a 256 build/Ghost_ESP_IDF.bin
```
