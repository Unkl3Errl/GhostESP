#!/usr/bin/env python3
"""Source contract for selecting the correct Wi-Fi backend per board."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs"


def read(name: str) -> str:
    return (CONFIGS / name).read_text(encoding="utf-8")


def require(fragment: str, source: str, message: str) -> None:
    if fragment not in source:
        raise AssertionError(message)


def main() -> None:
    remote_disabled = "# CONFIG_ESP_WIFI_REMOTE_ENABLED is not set"
    hosted_disabled = "# CONFIG_ESP_HOSTED_ENABLED is not set"

    # Both Heltec releases run on an ESP32-S3 with a native radio. IDF 6.1's
    # Wi-Fi Remote default must not be allowed to add a second backend.
    for name in ("sdkconfig.heltecv3", "sdkconfig.heltecv4"):
        source = read(name)
        require(remote_disabled, source, f"{name} enables the remote Wi-Fi backend")
        require(hosted_disabled, source, f"{name} enables ESP-Hosted on a native-radio board")

    # P4 has no native Wi-Fi and intentionally reaches its C6 through Hosted.
    p4 = read("sdkconfig.crowpanel_advanced_p4_mipi_1024x600")
    if remote_disabled in p4:
        raise AssertionError("P4 remote Wi-Fi backend is disabled")
    require("CONFIG_ESP_HOSTED_ENABLED=y", p4, "P4 ESP-Hosted backend is disabled")

    print("GhostESP Wi-Fi backend contract: PASS")


if __name__ == "__main__":
    main()
