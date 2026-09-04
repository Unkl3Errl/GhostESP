#!/usr/bin/env python3
"""Source contract for durable GhostESP wardrive POI tagging."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (ROOT / "main/core/commands/cmd_system.c").read_text(encoding="utf-8")
COMMANDLINE = (ROOT / "main/core/commandline.c").read_text(encoding="utf-8")
LOGGER = (ROOT / "main/vendor/GPS/gps_logger.c").read_text(encoding="utf-8")
HELP = (ROOT / "main/core/commands/cmd_help.c").read_text(encoding="utf-8")
WEB_COMMANDS = (ROOT / "webui/src/commands.js").read_text(encoding="utf-8")
WEB_APP = (ROOT / "webui/src/app.js").read_text(encoding="utf-8")


def body(source: str, function: str) -> str:
    match = re.search(
        rf"(?:static\s+)?(?:void|bool|esp_err_t)\s+{function}\s*\([^)]*\)\s*\{{",
        source,
    )
    assert match, f"missing {function}"
    depth = 1
    index = match.end()
    while index < len(source) and depth:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
        index += 1
    assert depth == 0, f"unterminated {function}"
    return source[match.end() : index - 1]


assert 'register_command("tagpoi", handle_tagpoi);' in COMMANDLINE
assert "tagpoi [label]" in HELP
assert "tagPoi:" in WEB_COMMANDS and "cmd: 'tagpoi'" in WEB_COMMANDS
assert "label: 'Tag POI'" in WEB_APP and "CMD.tagPoi().cmd" in WEB_APP

handler = body(COMMANDS, "handle_tagpoi")
handler_order = [
    handler.find("wardriving_is_active()"),
    handler.find("gps_manager_get_recent_active_gps_snapshot"),
    handler.find("csv_tag_poi("),
    handler.find("POI tagged:"),
]
assert all(position >= 0 for position in handler_order), "tagpoi handler is incomplete"
assert handler_order == sorted(handler_order), "tagpoi validation/write ordering changed"
assert "wardriving is not active" in handler
assert "GPS fix is unavailable or stale" in handler
assert "POI file is unavailable" in handler

writer = body(LOGGER, "csv_tag_poi")
assert 'strcmp(csv_base_name, "wardriving")' in writer
assert "csv_poi_choose_paths()" in writer
assert 'poi_tag_count == 0 ? "wb" : "ab"' in writer
assert "POI_CSV_HEADER" in writer
assert "csv_escape_field" in writer
assert "fflush(poi_file)" in writer
assert "fsync(fd)" in writer
assert "poi_file_created = true" in writer

paths = body(LOGGER, "csv_poi_choose_paths")
assert 'SD_DIR_GPS "/wardrive_poi_%d.csv"' in paths
assert 'SD_DIR_GPS "/wardrive_poi_%d.csv.part"' in paths
assert "sd_card_exists(poi_final_path)" in paths
assert "sd_card_exists(poi_part_path)" in paths

active_path = body(LOGGER, "csv_file_is_active_path")
assert "poi_file_created" in active_path and "poi_part_path" in active_path

finalize = body(LOGGER, "csv_poi_finalize")
assert "rename(poi_part_path, poi_final_path)" in finalize
assert "POI log finalized:" in finalize
assert "retaining %s" in finalize

close = body(LOGGER, "csv_file_close")
assert "csv_poi_finalize();" in close
assert close.find("csv_poi_finalize();") < close.find("free(csv_buffer)")

print("Wardrive POI tagging contract: PASS")
