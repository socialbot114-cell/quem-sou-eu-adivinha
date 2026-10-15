#!/usr/bin/env python3
"""Champion squads of every men's and women's FIFA World Cup, read from the English Wikipedia squad pages.

A player is a World Cup champion when his article is linked in the squad of the team that won that
tournament. Only winning squads are read, which is enough: any champion is in one of them. So a player
who is in none of them is a verified "not champion", as long as the page of every winning tournament
is read. Writes docs/content/world-cup-champion-squads.json.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "docs/content/world-cup-champion-squads.json"
CACHE_DIR = ROOT / "novos personagens/.cache/world-cup-squads"
USER_AGENT = {"User-Agent": "QuemSouEuCharacterBank/1.0 (https://github.com/socialbot114-cell/quem-sou-eu-adivinha)"}

MEN = {
    1930: "Uruguay", 1934: "Italy", 1938: "Italy", 1950: "Uruguay", 1954: "West Germany", 1958: "Brazil",
    1962: "Brazil", 1966: "England", 1970: "Brazil", 1974: "West Germany", 1978: "Argentina", 1982: "Italy",
    1986: "Argentina", 1990: "West Germany", 1994: "Brazil", 1998: "France", 2002: "Brazil", 2006: "Italy",
    2010: "Spain", 2014: "Germany", 2018: "France", 2022: "Argentina",
}
WOMEN = {1991: "United States", 1995: "Norway", 1999: "United States", 2003: "Germany", 2007: "Germany",
         2011: "Japan", 2015: "United States", 2019: "United States", 2023: "Spain"}

HEADING = re.compile(r"^(=+)\s*(.*?)\s*\1\s*$", re.M)
PLAYER_LINK = re.compile(r"name=\[\[([^\]|#]+)")


def page_title(year: int, women: bool) -> str:
    return f"{year} FIFA Women's World Cup squads" if women else f"{year} FIFA World Cup squads"


def fetch_wikitext(title: str) -> str:
    cache = CACHE_DIR / (re.sub(r"[^A-Za-z0-9]+", "_", title) + ".txt")
    if cache.is_file():
        return cache.read_text(encoding="utf-8")
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "parse", "page": title, "prop": "wikitext", "format": "json"})
    data = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=USER_AGENT), timeout=60) as response:
                data = json.load(response)
                break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 4:
                raise
            time.sleep(30 * (attempt + 1))
    text = data["parse"]["wikitext"]["*"]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    time.sleep(0.5)
    return text


def winning_squad(text: str, team: str) -> list[str]:
    """Player links inside the section of the winning team (up to the next heading)."""
    headings = list(HEADING.finditer(text))
    for index, heading in enumerate(headings):
        if heading.group(2).strip() == team:
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            return sorted(set(PLAYER_LINK.findall(text[heading.end():end])))
    raise SystemExit(f"winning team {team!r} not found in squad page")


def build() -> dict:
    tournaments = []
    champions: dict[str, list[str]] = {}
    for women, winners in ((False, MEN), (True, WOMEN)):
        for year, team in winners.items():
            title = page_title(year, women)
            players = winning_squad(fetch_wikitext(title), team)
            prefix = "Women's " if women else ""
            label = f"{year} FIFA {prefix}World Cup"
            tournaments.append({"tournament": label, "winner": team, "page": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                "players": len(players)})
            for player in players:
                champions.setdefault(player, []).append(label)
    return {
        "generatedAt": date.today().isoformat(),
        "method": "Player articles linked in the squads of the winning teams; only winning squads are read.",
        "license": "CC BY-SA 4.0",
        "tournaments": tournaments,
        "champions": dict(sorted(champions.items())),
    }


def main() -> None:
    data = build()
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"tournaments: {len(data['tournaments'])} | champion articles: {len(data['champions'])} -> {OUTPUT}")


if __name__ == "__main__":
    main()
