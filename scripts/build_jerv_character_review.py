#!/usr/bin/env python3
"""Build the JERV/TypeSafe editorial input from the local expansion and sources."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
EXPANSION_PATH = ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json"
SOURCES_PATH = ROOT / "docs/content/character-sources.json"
OUTPUT_PATH = ROOT / "docs/content/jerv-character-review-input.json"
CLAIM_OVERRIDES = {
    "ariana-grande": "Ariana Grande is an American singer, songwriter, and actress.",
    "elon-musk": "Elon Musk is a businessman and the CEO of Tesla and SpaceX.",
    "tim-cook": "Tim Cook is an American business executive and the executive chairman of Apple Inc.",
    "jack-ma": "Jack Ma is a Chinese businessman and co-founder of Alibaba Group.",
    "bernard-arnault": "Bernard Arnault is a French businessman and the chairman and CEO of LVMH, a luxury goods company.",
    "djavan": "Djavan is a Brazilian singer-songwriter and guitarist.",
    "psy": "PSY is a South Korean singer and rapper.",
    "g-dragon": "G-Dragon is a South Korean rapper, singer, songwriter, and member of BigBang.",
    "boa": "BoA is a South Korean singer and songwriter.",
    "steve-jobs": "Steve Jobs was an American businessman and co-founder of Apple.",
    "sheryl-sandberg": "Sheryl Sandberg is an American technology executive and author.",
    "zhang-yiming": "Zhang Yiming is a Chinese internet entrepreneur and founder of ByteDance.",
    "maria-bethania": "Maria Bethânia is a Brazilian singer and songwriter.",
    "milton-nascimento": "Milton Nascimento is a Brazilian singer-songwriter and multi-instrumentalist.",
    "roberto-carlos": "Roberto Carlos is a Brazilian singer-songwriter.",
    "jorge-ben-jor": "Jorge Ben Jor is a Brazilian popular musician.",
    "eliana": "Eliana is a Brazilian television host and former singer.",
    "maria-rita": "Maria Rita is a Brazilian singer.",
    "paris-hilton": "Paris Hilton is an American media personality and businesswoman.",
    "alcione": "Alcione is a Brazilian samba singer.",
    "simone-mendes": "Simone Mendes is a Brazilian singer-songwriter and instrumentalist.",
    "joaquin-phoenix": "Joaquin Phoenix is an American actor.",
    "ryan-gosling": "Ryan Gosling is a Canadian actor.",
    "quentin-tarantino": "Quentin Tarantino is an American filmmaker.",
    "sofia-coppola": "Sofia Coppola is an American filmmaker.",
    "pewdiepie": "PewDiePie is a Swedish YouTuber and content creator.",
    "ishowspeed": "IShowSpeed is an American online streamer and influencer.",
    "charli-damelio": "Charli D'Amelio is an American social media personality and dancer.",
    "emma-chamberlain": "Emma Chamberlain is an American influencer and podcaster.",
    "dhar-mann": "Dhar Mann is an American entrepreneur and film producer who creates scripted videos with moral lessons.",
    "susan-b-anthony": "Susan B. Anthony was an American social reformer and women's rights activist.",
    "anne-frank": "Anne Frank was a German-born Jewish diarist.",
    "joan-of-arc": "Joan of Arc was a French military leader.",
    "julius-caesar": "Julius Caesar was a Roman statesman and military general.",
    "taemin": "Taemin is a South Korean singer and a member of the boy band Shinee.",
    "hyunjin": "Hyunjin is a South Korean rapper and singer and a member of Stray Kids.",
    "jeon-soyeon": "Jeon So-yeon is a South Korean rapper, singer, songwriter, and member of (G)I-dle.",
    "cindy-crawford": "Cindy Crawford is an American model and actress.",
    "victoria-beckham": "Victoria Beckham is an English fashion designer and singer.",
    "kimora-lee-simmons": "Kimora Lee Simmons is an American fashion designer and former fashion model.",
    "alexa-chung": "Alexa Chung is an English model and television personality.",
    "bruno-mars": "Bruno Mars is an American singer-songwriter and record producer.",
    "usher": "Usher is an American singer, songwriter, and actor.",
    "j-cole": "J. Cole is an American rapper and record producer.",
    "celine-dion": "Celine Dion is a Canadian singer.",
    "rosalia": "Rosalía is a Spanish singer-songwriter and actress.",
    "j-balvin": "J Balvin is a Colombian singer.",
    "oprah-winfrey": "Oprah Winfrey is an American media mogul, actress, and television personality.",
    "mother-teresa": "Mother Teresa was an Albanian-Indian Catholic nun.",
    "elton-john": "Elton John is a British singer, composer, and pianist.",
    "yoko-ono": "Yoko Ono is a Japanese artist, musician, and peace activist.",
    "lech-walesa": "Lech Wałęsa is a Polish statesman and former president of Poland.",
    "daniel-ek": "Daniel Ek is a Swedish businessman and founder of Spotify.",
    "tobias-lutke": "Tobias Lütke is a German-Canadian entrepreneur and co-founder and CEO of Shopify.",
}


def build_review_input(expansion: dict, source_manifest: dict) -> dict:
    sources = {item["id"]: item for item in source_manifest["items"]}
    questions = [
        {
            "id": item["id"],
            "text": item["text"],
            "category": item["categories"][0],
            "attribute": item["attribute"],
        }
        for item in expansion["questions"]
    ]
    claims = []
    unresolved = []
    for person in expansion["people"]:
        source = sources.get(person["id"])
        if not source or not source.get("sourceExcerpt"):
            unresolved.append(person["id"])
            continue
        claim_id = f"{person['id']}-main-role"
        claims.append({
            "id": claim_id,
            "person_id": person["id"],
            "person_name": person["name"],
            "answer": 1,
            "claim": CLAIM_OVERRIDES.get(
                person["id"],
                f"The source identifies {person['name']} as: {person['profession']}.",
            ),
            "source_url": source["sourceURL"],
            "source_title": source["sourceTitle"],
            "source_excerpt": source["sourceExcerpt"],
            "source_license": source["sourceLicense"],
            "source_license_url": source["sourceLicenseURL"],
            "last_verified": source["lastVerified"],
        })
    if unresolved:
        raise ValueError(f"missing source excerpts for: {', '.join(unresolved)}")
    return {"questions": questions, "claims": claims}


def main() -> None:
    expansion = json.loads(EXPANSION_PATH.read_text(encoding="utf-8"))
    source_manifest = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    data = build_review_input(expansion, source_manifest)
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(data['questions'])} questions and {len(data['claims'])} sourced profile claims for JERV")


if __name__ == "__main__":
    main()
