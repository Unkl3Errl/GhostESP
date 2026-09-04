#!/usr/bin/env python3
"""Source contract for GhostESP phone-backed storage durability and migration."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANAGER = (ROOT / "main/managers/sd_card_manager.c").read_text(encoding="utf-8")
COMMANDS = (ROOT / "main/core/commands/cmd_sd.c").read_text(encoding="utf-8")
PARTITIONS = (ROOT / "partitions_heltecv4.csv").read_text(encoding="utf-8")


def require(fragment: str, source: str, message: str) -> None:
    if fragment not in source:
        raise AssertionError(message)


def main() -> None:
    for fragment in (
        'esp_vfs_fat_spiflash_mount_rw_wl("/mnt", "storage", &mount_config, &s_wl_handle)',
        'free_bytes == 0 && !virtual_storage_has_payload("/mnt", 0)',
        "An unreadable entry is never safe to erase",
        'esp_vfs_fat_spiflash_format_cfg_rw_wl("/mnt", "storage", &mount_config)',
        "genuinely full or unreadable spool is never erased",
    ):
        require(fragment, MANAGER, f"missing safe mount recovery: {fragment}")

    for fragment in (
        "fflush(f) == 0",
        "fsync(fd) == 0",
        "sd_cli_file_crc32(path, &durable_size, &durable_checksum)",
        "durable_size != olen",
        "durable_size != original_size + olen",
        "SD:ERR:durability_check_failed:",
    ):
        require(fragment, COMMANDS, f"missing durable host write check: {fragment}")
    if COMMANDS.index("SD:ERR:durability_check_failed:") > COMMANDS.index("SD:OK:created:"):
        raise AssertionError("write success is emitted before durable readback")

    require("0xCF0000,0x300000", PARTITIONS.replace(" ", ""), "shared spool range changed")
    print("GhostESP mobile storage contract: PASS")


if __name__ == "__main__":
    main()
