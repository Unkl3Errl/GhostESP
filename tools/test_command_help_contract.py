#!/usr/bin/env python3
"""Ensure newly exposed commands remain discoverable in device help."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMANDLINE = (ROOT / "main/core/commandline.c").read_text(encoding="utf-8")
HELP = (ROOT / "main/core/commands/cmd_help.c").read_text(encoding="utf-8")


def main() -> None:
    commands = (
        "badble",
        "c6ota",
        "fav",
        "favorites",
        "lcdclock",
        "lcddiag",
        "lcdsimd",
        "loglevel",
    )
    for command in commands:
        registration = f'register_command("{command}"'
        if registration not in COMMANDLINE:
            raise AssertionError(f"missing command registration: {command}")
        if command not in HELP:
            raise AssertionError(f"missing device help entry: {command}")

    print("GhostESP command help contract: PASS")


if __name__ == "__main__":
    main()
