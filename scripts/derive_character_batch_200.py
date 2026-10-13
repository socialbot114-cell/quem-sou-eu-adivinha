#!/usr/bin/env python3
"""Derive the 200-character batch (Futebol and Artistas brasileiros) from Wikidata harvests.

Reads the harvest reports produced by harvest_wikidata_candidates.py and writes:
- scripts/character-batch-200.json: the people consumed by build_character_expansion.py,
  with explicit binary attributes for every category question;
- docs/content/character-sources-200.json: one provenance record per character (Wikidata
  item, source URL and the claims that justified each attribute).

Attributes that Wikidata cannot state reliably are not guessed: they are reported in the
"needsReview" list of the sources file so they can be checked before publication.
"""

from __future__ import annotations

import ast
import json
import re
import tempfile
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from harvest_wikidata_candidates import claim_values, get_json, resolve_labels  # noqa: E402

ROOT = Path(__file__).parents[1]
BATCH_OUT = ROOT / "scripts/character-batch-200.json"
SOURCES_OUT = ROOT / "docs/content/character-sources-200.json"
HARVEST_FUTEBOL = Path(sys.argv[1]) if len(sys.argv) > 1 else None
HARVEST_ARTISTAS = Path(sys.argv[2]) if len(sys.argv) > 2 else None

PER_CATEGORY = 100
WITHOUT_EDITORIAL_SOURCE = {"Maiara"}
MALE, FEMALE, BRAZIL = "Q6581097", "Q6581072", "Q155"
NATIONAL_TEAM_TYPE = "Q6979593"  # national association football team
BARCELONA = "Q7156"
BRAZIL_TEAM_LABELS = {"Seleção Brasileira de Futebol", "Brazil national football team"}
PREMIER_LEAGUE_CLUBS = (
    "Arsenal", "Chelsea", "Manchester United", "Manchester City", "Liverpool", "Tottenham",
    "Newcastle United", "Aston Villa", "Everton", "West Ham", "Leicester City", "Southampton",
    "Wolverhampton", "Blackburn Rovers", "Fulham", "Sunderland", "Bolton Wanderers",
    "Portsmouth", "Stoke City", "Swansea City", "Watford", "Norwich City", "Crystal Palace",
    "Brighton", "Brentford", "AFC Bournemouth", "Burnley", "Sheffield United", "Ipswich Town",
    "Middlesbrough", "Hull City", "Queens Park Rangers", "West Bromwich", "Reading",
    "Wigan Athletic", "Birmingham City", "Charlton Athletic", "Derby County", "Nottingham Forest",
    "Leeds United", "Coventry City", "Wimbledon", "Sheffield Wednesday", "Ipswich",
)
EUROPEAN_COUNTRIES = {
    "Alemanha", "França", "Espanha", "Itália", "Inglaterra", "Reino Unido", "Portugal",
    "Países Baixos", "Bélgica", "Escócia", "País de Gales", "Irlanda do Norte", "Irlanda",
    "Rússia", "Turquia", "Grécia", "Suíça", "Áustria", "Polônia", "Ucrânia", "Suécia",
    "Noruega", "Dinamarca", "Croácia", "Sérvia", "Romênia", "Bulgária", "Hungria",
    "República Tcheca", "Eslováquia", "Chipre", "Finlândia", "Islândia", "Eslovênia",
    "Bósnia e Herzegovina", "Montenegro", "Albânia", "Macedônia do Norte", "Bielorrússia",
    "Lituânia", "Letônia", "Estônia", "Malta", "Luxemburgo", "Mônaco", "Liechtenstein",
    "Geórgia", "Armênia", "Azerbaijão", "Cazaquistão",
}
# Wikidata position labels come in Portuguese (Brazil and Portugal) and English.
GOALKEEPER_TERMS = ("goleiro", "guarda-redes", "goalkeeper")
MIDFIELDER_TERMS = ("meio-campo", "meio-campista", "volante", "meia", "armador", "médio", "midfielder", "wing half")
FORWARD_TERMS = ("atacante", "avançado", "centroavante", "ponta", "extremo", "segundo atacante",
                 "forward", "striker", "winger", "centre-forward")

# Ballon d'Or: Wikidata lists nominations as awards (e.g. Zlatan, Tévez), so winners come
# from France Football's official list. Only winners among the candidates are listed.
BALLON_DOR_CURATED = {
    **{name: 1 for name in (
        "Rivaldo", "Ricardo Kaká", "Johan Cruyff", "Franz Beckenbauer", "Gerd Müller", "Michel Platini",
        "Alfredo Di Stéfano", "Eusébio", "George Best", "Bobby Charlton", "Roberto Baggio",
        "Ruud Gullit", "Marco van Basten", "George Weah", "Luis Figo", "Andriy Shevchenko", "Kevin Keegan", "Oleg Blokhin",
        "Hristo Stoichkov", "Lothar Matthäus", "Oliver Kahn", "Michael Owen",
    )},
    **{name: 0 for name in ("Zlatan Ibrahimović", "Carlos Tévez", "Diego Maradona", "Paolo Maldini",
                            "Andrea Pirlo", "Francesco Totti", "Andrés Iniesta", "Xavi Hernández")},
}

# World Cup titles are not reliable in Wikidata (participation is stored, not squad membership),
# so they come from the official squads of the winning teams. None means "not verified":
# the attribute is left out, which the engine treats as no evidence.
WORLD_CUP_WINNER_CURATED = {
    **{name: 1 for name in (
        "Garrincha", "Didi", "Vavá", "Jairzinho", "Tostão", "Rivellino", "Gérson de Oliveira Nunes",
        "Carlos Alberto Torres", "Clodoaldo", "Dunga", "Bebeto", "Lúcio", "Dida", "Taffarel",
        "Gilberto Silva", "Nilton Santos", "Djalma Santos", "Zagallo", "Rivaldo", "Cafu", "Romário",
        "Diego Maradona", "Franz Beckenbauer", "Gerd Müller", "Francesco Totti", "Alessandro Del Piero",
        "Andrea Pirlo", "Patrick Vieira", "Toni Kroos", "Sergio Ramos", "Gerard Piqué", "Xavi Hernández",
        "Carles Puyol", "Sergio Busquets", "Andrés Iniesta", "David Villa", "Fernando Torres",
        "Xabi Alonso", "Iker Casillas", "Ángel Di María", "Manuel Neuer", "Philipp Lahm",
        "Bastian Schweinsteiger", "Thomas Müller", "Mesut Özil", "Miroslav Klose", "Lukas Podolski",
        "Jérôme Boateng", "Lothar Matthäus", "Jürgen Klinsmann", "Antoine Griezmann", "Paul Pogba",
        "N'Golo Kanté", "Raphaël Varane", "Hugo Lloris", "Olivier Giroud", "Lilian Thuram",
        "Marcel Desailly", "Youri Djorkaeff", "Bobby Charlton", "Bruno Conti", "Megan Rapinoe",
        "Alex Morgan", "Abby Wambach", "Mia Hamm", "Birgit Prinz",
    )},
    **{name: 0 for name in (
        "Thiago Silva", "Daniel Alves", "Rogério Ceni", "Ricardo Kaká", "Michel Platini",
        "Samuel Eto'o", "Diego Forlán", "Eusébio", "George Best", "Johan Cruyff", "Ferenc Puskás",
        "Alfredo Di Stéfano", "Zlatan Ibrahimović", "Roberto Baggio", "Gianluca Vialli",
        "Paolo Maldini", "Ruud van Nistelrooy", "Ruud Gullit", "Marco van Basten", "Frank Rijkaard",
        "Dennis Bergkamp", "Cristiane", "Sissi", "Debinha", "Sam Kerr", "Ada Hegerberg",
        "Christine Sinclair", "Wendie Renard", "Sócrates", "Carlos Tévez", "Sergio Agüero",
        "Gonzalo Higuaín", "Diego Forlán", "Luis Suárez", "Edinson Cavani", "James Rodríguez",
        "Radamel Falcao", "Arturo Vidal", "Alexis Sánchez", "Robin van Persie", "Wayne Rooney",
        "Steven Gerrard", "Frank Lampard", "John Terry", "Ryan Giggs", "David Beckham",
        "Paul Scholes", "Gary Neville", "Peter Shilton", "David Seaman", "Kevin Keegan",
        "Alan Shearer", "Michael Owen", "Sol Campbell", "Ashley Cole", "Harry Maguire",
        "Jack Grealish", "Bukayo Saka", "Jordan Henderson", "Harry Kane", "Yaya Touré",
        "Kolo Touré", "Michael Essien", "Sadio Mané", "Riyad Mahrez", "Virgil van Dijk",
        "George Weah", "Didier Drogba", "Luis Figo", "Deco", "Ricardo Carvalho", "Pepe", "Nani",
        "Bernardo Silva", "Bruno Fernandes", "Gheorghe Hagi", "Hristo Stoichkov",
        "Andriy Shevchenko", "Oleg Blokhin", "Joshua Kimmich", "Kai Havertz", "Oliver Kahn",
        "Eric Cantona", "Marcelo Gallardo", "Ricardo Quaresma",
    )},
}
INSTRUMENT_TERMS = {
    "instrumentista", "guitarrista", "pianista", "violonista", "baterista", "saxofonista",
    "flautista", "tecladista", "baixista", "percussionista", "cavaquinista", "acordeonista",
    "harmonicista", "trompetista", "multi-instrumentista",
}
MUSICIAN_TERMS = {"cantor", "cantora", "compositor", "compositora", "músico", "música", "instrumentista",
                  "guitarrista", "pianista", "violonista", "baterista", "saxofonista", "sanfoneiro", "rapper",
                  "produtor musical", "dj", "cantautor"} | INSTRUMENT_TERMS
WRITER_TERMS = {"escritor", "escritora", "poeta", "romancista", "cronista", "dramaturgo", "dramaturga"}
DIRECTOR_TERMS = {"diretor", "diretora", "cineasta", "realizador", "realizadora"}


def slugify(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_name = "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")


def birth_year(record: dict) -> int | None:
    times = record["claims"]["P569"]
    if not times:
        return None
    match = re.match(r"[+-]?(\d{4})", times[0]["time"])
    return int(match.group(1)) if match else None


def labels_of(record: dict, prop: str) -> list[str]:
    return [label.lower() for label in record["claimLabels"].get(prop, []) if isinstance(label, str)]


def occupation_tokens(record: dict) -> set[str]:
    tokens: set[str] = set()
    for label in labels_of(record, "P106"):
        tokens.update(re.split(r"[\s/-]+", label))
        tokens.add(label)
    return tokens


def profession(record: dict) -> str:
    occupations = [label for label in record["claimLabels"].get("P106", []) if isinstance(label, str)][:3]
    if not occupations:
        return "Personalidade"
    capitalized = [occupations[0][:1].upper() + occupations[0][1:]] + occupations[1:]
    if len(capitalized) == 1:
        return capitalized[0]
    return ", ".join(capitalized[:-1]) + " e " + capitalized[-1]


def gender_of(record: dict) -> str | None:
    values = record["claims"]["P21"]
    if MALE in values:
        return "M"
    if FEMALE in values:
        return "F"
    return None


def country_of(record: dict) -> str | None:
    """Brazil when the player is a Brazilian citizen or has played for Brazil's national team
    (Wikidata sometimes lists only the other citizenship); otherwise the first listed citizenship."""
    if is_brazilian(record) or any(label in BRAZIL_TEAM_LABELS for label in record["claimLabels"].get("P54", [])):
        return "Brasil"
    countries = record["claimLabels"].get("P27", [])
    return countries[0] if countries else None


def is_brazilian(record: dict) -> bool:
    return BRAZIL in record["claims"]["P27"]


def football_attributes(record: dict, club_info: dict) -> tuple[dict, list[str]]:
    review: list[str] = []
    positions = " ".join(labels_of(record, "P413"))
    # Without any position on Wikidata the player is unknown, not a non-goalkeeper.
    position_known = bool(positions.strip())

    def position(terms: tuple[str, ...]) -> int | None:
        if not position_known:
            return None
        return int(any(term in positions for term in terms))

    attributes = {
        "goalkeeper": position(GOALKEEPER_TERMS),
        "midfielder": position(MIDFIELDER_TERMS),
        "forward": position(FORWARD_TERMS),
        "ballon_dor": BALLON_DOR_CURATED.get(record["name"], 0),
    }
    clubs = [club for club in record["claims"]["P54"] if isinstance(club, str)]
    club_names = [club_info["labels"].get(club, "") for club in clubs]
    attributes["played_barcelona"] = int(BARCELONA in clubs)
    attributes["brazil_team"] = int(any(label in BRAZIL_TEAM_LABELS for label in record["claimLabels"]["P54"]))
    attributes["played_premier_league"] = int(any(
        any(name.startswith(prefix) or prefix in name for prefix in PREMIER_LEAGUE_CLUBS)
        for name in club_names if name
    ))
    attributes["played_in_europe"] = int(any(
        club_info["countries"].get(club) in EUROPEAN_COUNTRIES
        for club in clubs if club in club_info["countries"] and club not in club_info["national"]
    ))
    attributes["world_cup_winner"] = WORLD_CUP_WINNER_CURATED.get(record["name"])
    if not clubs:
        review.append("sem clubes no Wikidata")
    if not position_known:
        review.append("posição não encontrada")
    if attributes["world_cup_winner"] is None:
        review.append("título de Copa não verificado")
    return attributes, review


# Federative units, matched exactly against the birthplace's administrative chain.
NORTHEAST_STATES = (
    "bahia", "pernambuco", "ceará", "maranhão", "paraíba", "rio grande do norte", "alagoas",
    "sergipe", "piauí",
)
SOUTH_STATES = ("rio grande do sul", "paraná", "santa catarina")
RIO_STATE = ("rio de janeiro",)
MINAS_STATE = ("minas gerais",)
SAO_PAULO_STATE = ("são paulo",)
BIRTH_ANCESTORS: dict[str, set[str]] = {}


def ancestor_labels(place_qids: set[str], levels: int = 4) -> dict[str, set[str]]:
    """Labels of each place and of its containing places (P131), up to `levels` steps."""
    result: dict[str, set[str]] = {qid: set() for qid in place_qids}
    current = {qid: qid for qid in place_qids}
    for _ in range(levels):
        nodes = {node for node in current.values() if node}
        if not nodes:
            break
        entities: dict[str, dict] = {}
        ordered = sorted(nodes)
        for start in range(0, len(ordered), 50):
            chunk = ordered[start:start + 50]
            data = get_json({"action": "wbgetentities", "ids": "|".join(chunk), "props": "claims|labels", "languages": "pt|en"})
            entities.update(data["entities"])
        next_current: dict[str, str | None] = {}
        for origin, node in current.items():
            if not node or node not in entities:
                next_current[origin] = None
                continue
            entity = entities[node]
            label = entity.get("labels", {})
            name = (label.get("pt") or label.get("en") or {}).get("value")
            if name:
                result[origin].add(name.lower())
            parents = [value for value in claim_values(entity.get("claims", {}), "P131") if isinstance(value, str)]
            next_current[origin] = parents[0] if parents else None
        current = next_current
    return result


def prepare_birthplaces(records: list[dict]) -> None:
    """Resolve birthplace containment once for every record that has a birthplace (P19)."""
    places = {qid for record in records for qid in record["claims"].get("P19", []) if isinstance(qid, str)}
    BIRTH_ANCESTORS.clear()
    BIRTH_ANCESTORS.update(ancestor_labels(places))


def birthplace(record: dict, terms: tuple[str, ...]) -> int | None:
    """1/0 from the federative units containing the birthplace; None when Wikidata has no birthplace."""
    places = [qid for qid in record["claims"].get("P19", []) if isinstance(qid, str)]
    if not places:
        return None
    chain = set().union(*(BIRTH_ANCESTORS.get(qid, set()) for qid in places))
    return int(any(term in chain for term in terms))


def artist_attributes(record: dict, birth: int) -> tuple[dict, dict]:
    occupations = occupation_tokens(record)
    genres = " ".join(labels_of(record, "P136"))  # "música sertaneja" (feminine) is the usual pt label
    awards = " ".join(labels_of(record, "P166"))
    attributes = {
        "singer": int(bool(occupations & {"cantor", "cantora"})),
        "actor": int(bool(occupations & {"ator", "atriz"})),
        "presenter": int(bool(occupations & {"apresentador", "apresentadora"})),
        "writer": int(bool(occupations & WRITER_TERMS)),
        "instrumentalist": int(bool(occupations & INSTRUMENT_TERMS)),
        "director": int(bool(occupations & DIRECTOR_TERMS)),
        "grammy_winner": int("grammy" in awards),
    }
    genre_list = labels_of(record, "P136")

    musician = bool(occupations & MUSICIAN_TERMS)

    def genre(*terms: str) -> int | None:
        # A genre on Wikidata answers the question. Without one, a musician's genre is unknown,
        # while a non-musician (actor, writer, presenter) is not known for any musical genre.
        if genre_list:
            return int(any(term in label for label in genre_list for term in terms))
        return None if musician else 0

    optional = {
        "genre_mpb": genre("música popular brasileira", "mpb"),
        "genre_rock": genre("rock"),
        "genre_pop": genre("pop"),
        "genre_funk": genre("funk"),
        "genre_bossa": genre("bossa nova"),
        "genre_pagode": genre("pagode"),
        "born_before_1960": int(birth < 1960),
        "born_before_1985": int(birth < 1985),
        "born_before_1945": int(birth < 1945),
        "born_before_1965": int(birth < 1965),
        "born_in_bahia": birthplace(record, ("bahia",)),
        "genre_axe": genre("axé"),
        "genre_rap": genre("rap", "hip hop", "hip-hop"),
        "genre_choro": genre("choro"),
        "genre_jazz": genre("jazz"),
        "genre_electronic": genre("eletrônica", "eletronica", "house", "techno", "eletro"),
        "composer": int(bool(occupations & {"compositor", "compositora", "cantautor", "cantautora"})),
        "born_before_1955": int(birth < 1955),
        "born_in_minas_gerais": birthplace(record, MINAS_STATE),
        "born_in_rio": birthplace(record, RIO_STATE),
        "born_in_sao_paulo": birthplace(record, SAO_PAULO_STATE),
        "born_in_northeast": birthplace(record, NORTHEAST_STATES),
        "born_in_south": birthplace(record, SOUTH_STATES),
    }
    dynamic = {
        **optional,
        "born_before_1975": int(birth < 1975),
        "samba_artist": int(any(
            label == "samba" or label.startswith(("samba de", "samba-enredo", "samba-rock", "pagode"))
            for label in labels_of(record, "P136")
        )),
        "sertanejo_artist": int("sertane" in genres),
    }
    return attributes, dynamic


def club_lookup(records: list[dict]) -> dict:
    clubs = {club for record in records for club in record["claims"]["P54"] if isinstance(club, str)}
    labels = resolve_labels(clubs) if clubs else {}
    countries: dict[str, str] = {}
    national: set[str] = set()
    ordered = sorted(clubs)
    for start in range(0, len(ordered), 50):
        chunk = ordered[start:start + 50]
        data = get_json({"action": "wbgetentities", "ids": "|".join(chunk), "props": "claims", "languages": "pt"})
        for qid, entity in data["entities"].items():
            claims = entity.get("claims", {})
            if NATIONAL_TEAM_TYPE in claim_values(claims, "P31"):
                national.add(qid)
            country_ids = [value for value in claim_values(claims, "P17") if isinstance(value, str)]
            if country_ids:
                countries[qid] = country_ids[0]
    country_labels = resolve_labels({country for country in countries.values()})
    countries = {club: country_labels.get(country, country) for club, country in countries.items()}
    for club, label in labels.items():
        if re.search(r"seleç|seleção|national|under-|sub-", label, re.IGNORECASE):
            national.add(club)
    return {"labels": labels, "countries": countries, "national": national}


def ordered_pool(valid: list[dict], women_quota: int) -> list[dict]:
    """Curation order, with the first women_quota women moved up so women are represented."""
    women = [record for record in valid if gender_of(record) == "F"]
    front = women[:women_quota]
    rest = [record for record in valid if not any(record is item for item in front)]
    return front + rest


FOOTBALL_CLUB_COUNTRIES = {
    "played_in_brazil": "Brasil", "played_in_italy": "Itália", "played_in_spain": "Espanha",
    "played_in_germany": "Alemanha", "played_in_france": "França", "played_in_portugal": "Portugal",
}
FIFA_BEST_TERMS = ("melhor jogador do mundo", "the best fifa", "fifa world player", "world player of the year")


def football_optional(record: dict, club_info: dict) -> dict:
    """Objective extras for Futebol (optional questions): club countries, FIFA best player, birth year."""
    clubs = [club for club in record["claims"]["P54"] if isinstance(club, str) and club not in club_info["national"]]
    countries = {club_info["countries"].get(club) for club in clubs if club in club_info["countries"]}
    values: dict = {"born_before_1985": int(birth_year(record) < 1985)}
    for attribute, country in FOOTBALL_CLUB_COUNTRIES.items():
        values[attribute] = int(country in countries) if clubs else None
    awards = " ".join(labels_of(record, "P166"))
    values["fifa_best"] = int(any(term in awards for term in FIFA_BEST_TERMS))
    return values


def football_entry(record: dict, clubs: dict) -> tuple[dict, dict]:
    attributes, review = football_attributes(record, clubs)
    attributes = attributes | football_optional(record, clubs)
    entry = {
        "id": slugify(record["name"]),
        "name": record["name"],
        "country": country_of(record),
        "profession": profession(record),
        "gender": gender_of(record),
        "birthYear": birth_year(record),
        "alive": int(not record["claims"]["P570"]),
        "attributes": attributes,
    }
    source = {"id": entry["id"], "category": "Futebol", "qid": record["qid"], "sourceUrl": record["sourceUrl"], "needsReview": review}
    return entry, source


def artist_entry(record: dict) -> tuple[dict, dict]:
    attributes, dynamic = artist_attributes(record, birth_year(record))
    entry = {
        "id": slugify(record["name"]),
        "name": record["name"],
        "country": country_of(record),
        "profession": profession(record),
        "gender": gender_of(record),
        "birthYear": birth_year(record),
        "alive": int(not record["claims"]["P570"]),
        "attributes": attributes | dynamic,
    }
    source = {"id": entry["id"], "category": "Artistas brasileiros", "qid": record["qid"], "sourceUrl": record["sourceUrl"], "needsReview": []}
    return entry, source


def first_collision(batch: dict) -> tuple[str | None, list[list[str]]]:
    """Run the content validator on the whole catalog with this batch; return the first failing category and its groups."""
    import build_character_expansion as build_module
    import validate_content as validator

    original = build_module.BATCH_200
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(batch, handle, ensure_ascii=False)
        temporary = Path(handle.name)
    build_module.BATCH_200 = temporary
    try:
        result = build_module.build()
    finally:
        build_module.BATCH_200 = original
        temporary.unlink(missing_ok=True)
    # The validator sees the whole catalog: base people and questions plus the expansion.
    primary = json.loads(build_module.PRIMARY.read_text(encoding="utf-8"))
    people = primary["people"] + result["people"]
    questions = primary["questions"] + result["questions"]
    try:
        validator.validate_coverage_and_signatures(people, questions)
    except AssertionError as error:
        message = str(error)
        match = re.match(r"Pessoas indistinguíveis em (.+?): (.*)$", message)
        if not match:
            raise SystemExit(f"Validação falhou por outro motivo: {message}")
        return match.group(1), ast.literal_eval(match.group(2))
    return None, []


def fit_catalog(
    football_pool: list[tuple[dict, dict]],
    artist_pool: list[tuple[dict, dict]],
    football_count: int,
    artist_count: int,
) -> tuple[list[tuple[dict, dict]], list[tuple[dict, dict]]]:
    """Choose the new characters in curation order, replacing any the validator reports as indistinguishable."""
    pools = {"Futebol": football_pool, "Artistas brasileiros": artist_pool}
    counts = {"Futebol": football_count, "Artistas brasileiros": artist_count}
    selected = {name: pool[:counts[name]] for name, pool in pools.items()}
    cursor = {name: counts[name] for name in pools}
    for _ in range(80):
        batch = {"people": {name: [entry for entry, _ in selected[name]] for name in pools}}
        category, groups = first_collision(batch)
        if category is None:
            return selected["Futebol"], selected["Artistas brasileiros"]
        new_ids = {entry["id"] for entry, _ in selected[category]}
        dropped = set()
        for group in groups:
            members = [identifier for identifier in group if identifier in new_ids and identifier not in dropped]
            if len(members) == len(group):
                members = members[1:]  # keep the first in curation order
            if not members:
                raise SystemExit(f"Pessoas indistinguíveis só entre personagens existentes em {category}: {group}")
            dropped.update(members)
        selected[category] = [pair for pair in selected[category] if pair[0]["id"] not in dropped]
        while len(selected[category]) < counts[category]:
            if cursor[category] >= len(pools[category]):
                raise SystemExit(f"Pool de {category} esgotado antes de fechar sem colisões")
            selected[category].append(pools[category][cursor[category]])
            cursor[category] += 1
    raise SystemExit("Não convergiu ao remover colisões")


def main() -> None:
    football = json.loads(HARVEST_FUTEBOL.read_text(encoding="utf-8"))["records"]
    artists = json.loads(HARVEST_ARTISTAS.read_text(encoding="utf-8"))["records"]
    prepare_birthplaces(artists)

    def usable(record: dict) -> bool:
        return birth_year(record) is not None and gender_of(record) is not None and country_of(record) is not None

    football = ordered_pool([record for record in football if usable(record)], women_quota=15)
    clubs = club_lookup(football)
    football_pool = [football_entry(record, clubs) for record in football]
    # Without a linked Wikipedia article there is no editorial source to cite, so the character is skipped.
    artist_pool = [artist_entry(record) for record in artists
                   if is_brazilian(record) and usable(record) and record["name"] not in WITHOUT_EDITORIAL_SOURCE]
    football_pairs, artist_pairs = fit_catalog(football_pool, artist_pool, PER_CATEGORY, PER_CATEGORY)

    people_football = [entry for entry, _ in football_pairs]
    people_artists = [entry for entry, _ in artist_pairs]
    sources = [source for _, source in football_pairs] + [source for _, source in artist_pairs]
    ids = [entry["id"] for entry in people_football + people_artists]
    if len(ids) != len(set(ids)):
        raise SystemExit("ids duplicados no lote")

    batch = {"people": {"Futebol": people_football, "Artistas brasileiros": people_artists}}
    BATCH_OUT.write_text(json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SOURCES_OUT.write_text(json.dumps({"characters": sources}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Futebol: {len(people_football)}  Artistas brasileiros: {len(people_artists)}")
    print(f"Revisão sugerida: {sum(1 for s in sources if s['needsReview'])} personagens")


if __name__ == "__main__":
    main()
