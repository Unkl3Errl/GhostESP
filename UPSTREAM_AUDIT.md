# Upstream completeness audit

Audit date: 2026-08-09

## Source identity

| Item | Value |
| --- | --- |
| Upstream repository | `https://github.com/GhostESP-Revival/GhostESP.git` |
| Upstream branch | `Development-deki` |
| Audited upstream commit | `8e3be0579a237f3df733d57496c66da27e35e776` |
| Remote branch head at audit time | `8e3be0579a237f3df733d57496c66da27e35e776` |
| Local adaptation branch | `agent/heltec-v4` |
| Upstream tracked paths | 4,258 |
| Deleted upstream paths | **0** |

The local branch begins directly at the audited upstream commit. The complete
upstream tracked tree remains present. The Heltec V4 adaptation changes seven
tracked files and originally adds two board-specific files; this audit report
is an additional documentation file.

## Intentional tracked changes

| Path | Purpose |
| --- | --- |
| `.github/workflows/compile_all.yml` | Add the `HeltecV4.zip` CI build target. |
| `README.md` | Add Heltec V4 to the upstream support matrix. |
| `components/esp_audio_codec/CMakeLists.txt` | Avoid an incompatible redundant library search path under ESP-IDF 6.0. |
| `main/Kconfig.projbuild` | Add optional board-controlled GPS power configuration. |
| `main/managers/gps_manager.c` | Enable and disable an active-level-configurable onboard GPS supply. |
| `main/core/serial_manager.c` | Count successful USB Serial/JTAG writes in the shared output path. |
| `main/core/glog.c` | Deliver CLI results through the shared UART and USB Serial/JTAG output manager. |

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
- The Heltec V4 firmware built successfully with ESP-IDF 6.0.
- The hardware-validation application image `build/Ghost_ESP_IDF.bin`, built
  from this source state before the final source commit, has SHA-256:
  `4dc63c6b9ea14c8c3ee1e1f2577629fb45f9c9b6498ebc411e5b1446d0dc0986`.
- The flashed application image was verified byte-for-byte by the ESP-IDF
  flashing tools after programming.

## Reproduce the source audit

```sh
base=8e3be0579a237f3df733d57496c66da27e35e776
git ls-remote origin refs/heads/Development-deki
git ls-tree -r --name-only "$base" | wc -l
git diff --name-status "$base" --
git diff --diff-filter=D --name-only "$base" --
git ls-files --others --exclude-standard
git diff --check
git fsck --no-dangling --no-progress
shasum -a 256 build/Ghost_ESP_IDF.bin
```
