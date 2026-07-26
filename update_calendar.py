#!/usr/bin/env python3
from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dateutil import parser as dateparser
from icalendar import Calendar, Event

ROOT = Path(__file__).resolve().parent
PRIMARY = ROOT / "sports_calendar.ics"
COMPAT = ROOT / "sports_calendar_v2.ics"
DOCS = ROOT / "docs" / "sports_calendar.ics"
NOW = datetime.now(timezone.utc)
YEAR = NOW.year
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TerrySportsCalendar/2.0)"}
TIMEOUT = 30

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def fetch_json(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def as_utc(value: str) -> datetime:
    dt = dateparser.isoparse(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def add_event(cal: Calendar, *, uid: str, title: str, start: datetime,
              duration_hours: float = 3, description: str = "",
              location: str = "", url: str = "") -> None:
    start_utc = start.astimezone(timezone.utc)
    item = Event()
    item.add("uid", uid)
    item.add("dtstamp", NOW)
    item.add("dtstart", start_utc)
    item.add("dtend", start_utc + timedelta(hours=duration_hours))
    item.add("summary", title)
    if description:
        item.add("description", description)
    if location:
        item.add("location", location)
    if url:
        item.add("url", url)
    item.add("status", "CONFIRMED")
    cal.add_component(item)


def add_team_schedule(cal: Calendar, sport: str, league: str, team: str,
                      emoji: str, season: int) -> int:
    endpoint = (
        f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/"
        f"teams/{team}/schedule?season={season}"
    )
    data = fetch_json(endpoint)
    count = 0
    for raw in data.get("events", []):
        competition = (raw.get("competitions") or [{}])[0]
        names = {
            row.get("homeAway"): row.get("team", {}).get("displayName", "")
            for row in competition.get("competitors", [])
        }
        title = f"{names.get('away', '')} at {names.get('home', '')}".strip()
        if not title:
            continue
        broadcasts = []
        for broadcast in competition.get("broadcasts", []):
            broadcasts.extend(broadcast.get("names", []))
        links = raw.get("links") or []
        add_event(
            cal,
            uid=f"{league}-{raw.get('id')}@terry-sports",
            title=f"{emoji} {title}",
            start=as_utc(raw["date"]),
            duration_hours=3 if league == "wnba" else 4,
            description=(
                f"Watch: {', '.join(dict.fromkeys(broadcasts)) or 'TBD'}\n"
                "Source times converted from UTC and intended for display at fixed UTC-05:00."
            ),
            location=competition.get("venue", {}).get("fullName", ""),
            url=links[0].get("href", "") if links else "",
        )
        count += 1
    return count


def add_scoreboard(cal: Calendar, sport: str, league: str,
                   label: str, emoji: str) -> int:
    start_date = NOW.strftime("%Y%m%d")
    end_date = (NOW + timedelta(days=365)).strftime("%Y%m%d")
    endpoint = (
        f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/"
        f"scoreboard?dates={start_date}-{end_date}&limit=1000"
    )
    data = fetch_json(endpoint)
    count = 0
    for raw in data.get("events", []):
        competition = (raw.get("competitions") or [{}])[0]
        broadcasts = []
        for broadcast in competition.get("broadcasts", []):
            broadcasts.extend(broadcast.get("names", []))
        links = raw.get("links") or []
        title = raw.get("name") or raw.get("shortName") or label
        add_event(
            cal,
            uid=f"{league}-{raw.get('id')}@terry-sports",
            title=f"{emoji} {title}",
            start=as_utc(raw["date"]),
            duration_hours=5 if sport in {"mma", "boxing"} else 3,
            description=(
                f"Series: {label}\n"
                f"Watch: {', '.join(dict.fromkeys(broadcasts)) or 'TBD'}\n"
                "Source times converted from UTC and intended for display at fixed UTC-05:00."
            ),
            location=competition.get("venue", {}).get("fullName", ""),
            url=links[0].get("href", "") if links else "",
        )
        count += 1
    return count


def add_formula_one(cal: Calendar, season: int) -> int:
    data = fetch_json(f"https://api.jolpi.ca/ergast/f1/{season}.json")
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    count = 0
    for race in races:
        if not race.get("time"):
            continue
        start = as_utc(f"{race['date']}T{race['time']}")
        if start < NOW - timedelta(days=2):
            continue
        add_event(
            cal,
            uid=f"f1-{season}-{race.get('round')}@terry-sports",
            title=f"🏎️ F1: {race.get('raceName', 'Grand Prix')}",
            start=start,
            duration_hours=3,
            description="Watch in the U.S.: ESPN networks / ESPN app; exact channel may vary.",
            location=race.get("Circuit", {}).get("circuitName", ""),
            url=race.get("url", "https://www.formula1.com/en/racing"),
        )
        count += 1
    return count


def main() -> None:
    calendar = Calendar()
    calendar.add("prodid", "-//Terry Sports Calendar//EN")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add("x-wr-calname", "Combat Sports, Colts, Fever, F1 and MotoGP")

    sources = [
        ("Indianapolis Colts", lambda: add_team_schedule(calendar, "football", "nfl", "ind", "🏈", YEAR)),
        ("Indiana Fever", lambda: add_team_schedule(calendar, "basketball", "wnba", "ind", "🏀", YEAR)),
        ("Formula 1", lambda: add_formula_one(calendar, YEAR)),
        ("UFC", lambda: add_scoreboard(calendar, "mma", "ufc", "UFC", "🥋")),
        ("PFL", lambda: add_scoreboard(calendar, "mma", "pfl", "PFL", "🥋")),
        ("ONE Championship", lambda: add_scoreboard(calendar, "mma", "one", "ONE Championship", "🥋")),
        ("Boxing", lambda: add_scoreboard(calendar, "boxing", "boxing", "Boxing", "🥊")),
        ("MotoGP", lambda: add_scoreboard(calendar, "racing", "motogp", "MotoGP", "🏍️")),
    ]

    total = 0
    for name, loader in sources:
        try:
            count = loader()
            total += count
            logging.info("%s: %d events", name, count)
        except Exception as exc:
            logging.warning("%s source failed: %s", name, exc)

    data = calendar.to_ical()
    PRIMARY.write_bytes(data)
    COMPAT.write_bytes(data)
    DOCS.parent.mkdir(parents=True, exist_ok=True)
    DOCS.write_bytes(data)
    logging.info("Wrote %d events to primary and compatibility feeds", total)


if __name__ == "__main__":
    main()
