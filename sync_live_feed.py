#!/usr/bin/env python3
from pathlib import Path

source = Path("docs/sports_calendar.ics")
target = Path("sports_calendar.ics")

if not source.exists():
    raise FileNotFoundError(f"Updater did not create {source}")

target.write_bytes(source.read_bytes())
print(f"Copied {source} to {target}")
