#!/usr/bin/env python3
"""Source contract for DNS task sizing and orderly socket shutdown."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "main/core/dns_server.c").read_text(encoding="utf-8")


def body(function: str) -> str:
    match = re.search(
        rf"(?:static\s+)?(?:void|dns_server_handle_t)\s+{function}\s*\([^)]*\)\s*\{{",
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


stack_size = re.search(r"#define DNS_SERVER_TASK_STACK_SIZE \((\d+)\)", SOURCE)
assert stack_size, "missing DNS task stack-size constant"
assert int(stack_size.group(1)) >= 6144, "DNS task stack regressed below 6144 bytes"

task = body("dns_server_task")
assert "SO_RCVTIMEO" in task, "legacy DNS socket can block shutdown indefinitely"
assert "if (err < 0)" in task and "Socket unable to bind" in task
assert "task_done:" in task and "for (;;) vTaskSuspend(NULL);" in task
assert "vTaskDelete(NULL)" not in task, "DNS task must not bypass socket cleanup"

start = body("start_dns_server")
assert "DNS_SERVER_TASK_STACK_SIZE" in start
assert "task_result != pdPASS" in start, "DNS task creation failure is unchecked"

stop = body("stop_dns_server")
cleanup_calls = [
    "handle->started = false;",
    "eTaskGetState(handle->task) == eSuspended",
    "vTaskDelete(handle->task);",
    "free(handle);",
]
positions = [stop.find(call) for call in cleanup_calls]
assert all(position >= 0 for position in positions), "DNS stop cleanup is incomplete"
assert positions == sorted(positions), "DNS stop cleanup order changed"

print("DNS server lifecycle contract: PASS")
