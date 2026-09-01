#!/usr/bin/env python3
"""Source contract for Karma probe capture and orderly shutdown."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main/managers/wifi_manager.c").read_text(encoding="utf-8")


def body(function: str) -> str:
    match = re.search(
        rf"(?:static\s+)?(?:void|bool|esp_err_t)\s+{function}\s*\([^)]*\)\s*\{{",
        SOURCE,
    )
    assert match, f"missing {function}"
    depth = 1
    index = match.end()
    while index < len(SOURCE) and depth:
        if SOURCE[index] == "{":
            depth += 1
        elif SOURCE[index] == "}":
            depth -= 1
        index += 1
    assert depth == 0, f"unterminated {function}"
    return SOURCE[match.end() : index - 1]


probe = body("karma_probe_request_callback")
assert "frame_length < sizeof(wifi_ieee80211_hdr_t) + 2" in probe
assert "ssid_offset + 2 + element_length > payload_length" in probe
assert "xQueueSend(karma_event_queue, &event, 0)" in probe

worker = body("karma_task")
cleanup_calls = [
    "karma_disable_probe_capture();",
    "karma_log_queued_events();",
    "scan_file_close(&karma_scan_file);",
    "vQueueDelete(karma_event_queue);",
    "karma_stop_portal_if_active();",
]
cleanup = worker[worker.find("karma_disable_probe_capture();") :]
positions = [cleanup.find(call) for call in cleanup_calls]
assert all(position >= 0 for position in positions), "worker cleanup is incomplete"
assert positions == sorted(positions), "worker cleanup order changed"

start = body("wifi_manager_start_karma")
assert "karma_running || karma_task_handle != NULL" in start
assert "xQueueCreate(KARMA_EVENT_QUEUE_LENGTH, sizeof(karma_event_t))" in start

stop = body("wifi_manager_stop_karma")
assert "karma_running = false;" in stop
assert "vTaskDelete(karma_task_handle)" not in stop
assert "cleanup is still in progress" in stop

print("Karma lifecycle contract: PASS")
