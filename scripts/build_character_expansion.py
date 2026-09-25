#!/usr/bin/env python3
"""Build the offline expansion from the deduplicated first editorial batch."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "iosApp/Resources/KnowledgeBase/character-expansion.json"

QUESTION_SPECS = {
    "Outros esportes": [
        ("basketball", "É conhecido por jogar basquete?"),
        ("tennis", "É conhecido por jogar tênis?"),
        ("motorsport", "Compete ou competiu no automobilismo?"),
        ("team_sport", "Seu esporte é praticado principalmente em equipe?"),
        ("olympic_medalist", "Conquistou medalha olímpica?"),
        ("nba_champion", "Conquistou um título da NBA?"),
        ("american_football", "É conhecido por jogar futebol americano?"),
        ("sports_born_before_1985", "Nasceu em 1984 ou antes?"),
    ],
    "Música internacional": [
        ("pop_music", "É conhecido principalmente pela música pop?"),
        ("hip_hop", "É conhecido por hip-hop ou rap?"),
        ("latin_music", "É conhecido por cantar música latina em espanhol?"),
        ("r_and_b", "É conhecido por R&B?"),
        ("country_music", "Gravou álbuns do gênero country?"),
        ("acted_in_film", "Também atuou em filmes ou séries?"),
        ("born_in_barbados", "Nasceu em Barbados?"),
    ],
    "K-pop": [
        ("bts_member", "É integrante do BTS?"),
        ("blackpink_member", "É integrante do BLACKPINK?"),
        ("solo_artist", "Começou a carreira musical como artista solo, não como integrante de um grupo?"),
        ("rapper", "Também atua como rapper?"),
        ("born_before_1994", "Nasceu antes de 1994?"),
        ("born_before_1993", "Nasceu antes de 1993?"),
        ("born_in_south_korea", "Nasceu na Coreia do Sul?"),
        ("known_for_dance", "É conhecido também por dançar?"),
        ("kpop_born_before_1996", "O artista de K-pop nasceu até 1995?"),
    ],
    "Cinema e TV": [
        ("oscar_winner", "Recebeu um Oscar por atuação ou produção?"),
        ("superhero_film", "Atuou em um filme de super-herói?"),
        ("tv_series_lead", "Protagonizou uma série de televisão?"),
        ("cinema_director", "Dirigiu um longa-metragem?"),
        ("born_before_1980", "Nasceu antes de 1980?"),
        ("science_fiction_franchise", "Atuou em uma franquia de ficção científica?"),
        ("action_franchise", "Atuou em mais de um filme da mesma franquia de ação?"),
    ],
    "Moda e reality": [
        ("kardashian_family", "Faz parte da família Kardashian-Jenner?"),
        ("fashion_model", "Trabalhou como modelo de moda?"),
        ("reality_tv", "Participou de reality shows como figura central?"),
        ("beauty_brand_founder", "Fundou uma marca de beleza?"),
        ("fashion_brand_owner", "Fundou ou lidera uma marca de moda?"),
        ("lifestyle_brand", "Fundou uma marca própria de produtos, moda, beleza ou estilo de vida?"),
        ("fashion_born_before_1996", "Nasceu em 1995 ou antes?"),
    ],
    "Tecnologia e negócios": [
        ("technology_company_founder", "Fundou ou cofundou uma empresa de tecnologia?"),
        ("software_company_founder", "Fundou ou cofundou uma empresa de software?"),
        ("social_network_founder", "Fundou uma rede social?"),
        ("ecommerce_founder", "Fundou uma empresa de comércio eletrônico?"),
        ("hardware_company", "É conhecido por uma empresa que fabrica chips ou aparelhos eletrônicos?"),
        ("born_in_russia", "Nasceu na Rússia?"),
        ("founded_outside_us", "A empresa de tecnologia que fundou tem sede fora dos EUA?"),
        ("luxury_goods_leader", "Lidera ou liderou uma empresa de marcas de luxo?"),
    ],
}

# id, display name, country, profession, gender, birth year, bits matching
# QUESTION_SPECS for that category, optional distinctive SF Symbol.
CANDIDATES = {
    "Outros esportes": [
        ("lebron-james", "LeBron James", "Estados Unidos", "Jogador de basquete", "M", 1984, "10011101"),
        ("stephen-curry", "Stephen Curry", "Estados Unidos", "Jogador de basquete", "M", 1988, "10011100"),
        ("giannis-antetokounmpo", "Giannis Antetokounmpo", "Grécia", "Jogador de basquete", "M", 1994, "10010100"),
        ("luka-doncic", "Luka Dončić", "Eslovênia", "Jogador de basquete", "M", 1999, "10010000"),
        ("nikola-jokic", "Nikola Jokić", "Sérvia", "Jogador de basquete", "M", 1995, "10011100"),
        ("serena-williams", "Serena Williams", "Estados Unidos", "Tenista", "F", 1981, "01001001"),
        ("roger-federer", "Roger Federer", "Suíça", "Tenista", "M", 1981, "01001001"),
        ("novak-djokovic", "Novak Djokovic", "Sérvia", "Tenista", "M", 1987, "01001000"),
        ("lewis-hamilton", "Lewis Hamilton", "Reino Unido", "Piloto de automobilismo", "M", 1985, "00100000"),
        ("max-verstappen", "Max Verstappen", "Países Baixos", "Piloto de automobilismo", "M", 1997, "00100000"),
        ("simone-biles", "Simone Biles", "Estados Unidos", "Ginasta", "F", 1997, "00001000"),
        ("tom-brady", "Tom Brady", "Estados Unidos", "Jogador de futebol americano", "M", 1977, "00010011"),
    ],
    "Música internacional": [
        ("taylor-swift", "Taylor Swift", "Estados Unidos", "Cantora e compositora", "F", 1989, "1000100"),
        ("beyonce", "Beyoncé", "Estados Unidos", "Cantora e compositora", "F", 1981, "1001010"),
        ("rihanna", "Rihanna", "Barbados", "Cantora, compositora e empresária", "F", 1988, "1001011"),
        ("lady-gaga", "Lady Gaga", "Estados Unidos", "Cantora, compositora e atriz", "F", 1986, "1000010"),
        ("adele", "Adele", "Reino Unido", "Cantora e compositora", "F", 1988, "1000000"),
        ("justin-bieber", "Justin Bieber", "Canadá", "Cantor", "M", 1994, "1000000"),
        ("ariana-grande", "Ariana Grande", "Estados Unidos", "Cantora e atriz", "F", 1993, "1000010"),
        ("drake", "Drake", "Canadá", "Rapper, cantor e ator", "M", 1986, "0101010"),
        ("eminem", "Eminem", "Estados Unidos", "Rapper", "M", 1972, "0100000"),
        ("bad-bunny", "Bad Bunny", "Porto Rico", "Cantor e rapper", "M", 1994, "0110010"),
        ("shakira", "Shakira", "Colômbia", "Cantora e compositora", "F", 1977, "1010010"),
        ("the-weeknd", "The Weeknd", "Canadá", "Cantor e compositor", "M", 1990, "1001010"),
    ],
    "K-pop": [
        ("jungkook", "Jungkook", "Coreia do Sul", "Cantor e integrante do BTS", "M", 1997, "100000110"),
        ("jimin", "Jimin", "Coreia do Sul", "Cantor e integrante do BTS", "M", 1995, "100000111"),
        ("v-kim-taehyung", "V (Kim Taehyung)", "Coreia do Sul", "Cantor e integrante do BTS", "M", 1995, "100000101"),
        ("suga", "Suga", "Coreia do Sul", "Rapper e integrante do BTS", "M", 1993, "100110101"),
        ("jin-bts", "Jin", "Coreia do Sul", "Cantor e integrante do BTS", "M", 1992, "100111101"),
        ("rm-bts", "RM", "Coreia do Sul", "Rapper e integrante do BTS", "M", 1994, "100100101"),
        ("j-hope", "J-Hope", "Coreia do Sul", "Rapper e integrante do BTS", "M", 1994, "100100111"),
        ("lisa-blackpink", "Lisa", "Tailândia", "Rapper e cantora", "F", 1997, "010100010"),
        ("jennie-blackpink", "Jennie", "Coreia do Sul", "Cantora e integrante do BLACKPINK", "F", 1996, "010100100"),
        ("rose-blackpink", "Rosé", "Nova Zelândia", "Cantora e integrante do BLACKPINK", "F", 1997, "010000000"),
        ("jisoo-blackpink", "Jisoo", "Coreia do Sul", "Cantora e integrante do BLACKPINK", "F", 1995, "010000101"),
        ("iu", "IU", "Coreia do Sul", "Cantora e atriz", "F", 1993, "001000111"),
    ],
    "Cinema e TV": [
        ("tom-cruise", "Tom Cruise", "Estados Unidos", "Ator e produtor", "M", 1962, "0000101"),
        ("leonardo-dicaprio", "Leonardo DiCaprio", "Estados Unidos", "Ator e produtor", "M", 1974, "1000100"),
        ("brad-pitt", "Brad Pitt", "Estados Unidos", "Ator e produtor", "M", 1963, "1000101"),
        ("meryl-streep", "Meryl Streep", "Estados Unidos", "Atriz", "F", 1949, "1010100"),
        ("angelina-jolie", "Angelina Jolie", "Estados Unidos", "Atriz e diretora", "F", 1975, "1101100"),
        ("keanu-reeves", "Keanu Reeves", "Canadá", "Ator e músico", "M", 1964, "0101101"),
        ("denzel-washington", "Denzel Washington", "Estados Unidos", "Ator e produtor", "M", 1954, "1001100"),
        ("zendaya", "Zendaya", "Estados Unidos", "Atriz e cantora", "F", 1996, "0110001"),
        ("timothee-chalamet", "Timothée Chalamet", "Estados Unidos", "Ator", "M", 1995, "0000001"),
        ("tom-holland", "Tom Holland", "Reino Unido", "Ator", "M", 1996, "0110001"),
        ("jenna-ortega", "Jenna Ortega", "Estados Unidos", "Atriz", "F", 2002, "0010000"),
        ("pedro-pascal", "Pedro Pascal", "Chile", "Ator", "M", 1975, "0110110"),
    ],
    "Moda e reality": [
        ("kim-kardashian", "Kim Kardashian", "Estados Unidos", "Empresária e personalidade de reality", "F", 1980, "1011111"),
        ("kylie-jenner", "Kylie Jenner", "Estados Unidos", "Empresária e personalidade de reality", "F", 1997, "1011000"),
        ("kendall-jenner", "Kendall Jenner", "Estados Unidos", "Modelo e personalidade de reality", "F", 1995, "1110001"),
        ("khloe-kardashian", "Khloé Kardashian", "Estados Unidos", "Empresária e personalidade de reality", "F", 1984, "1010111"),
        ("kourtney-kardashian", "Kourtney Kardashian", "Estados Unidos", "Empresária e personalidade de reality", "F", 1979, "1010011"),
        ("kris-jenner", "Kris Jenner", "Estados Unidos", "Empresária e personalidade de reality", "F", 1955, "1010010"),
        ("gigi-hadid", "Gigi Hadid", "Estados Unidos", "Modelo", "F", 1995, "0100001"),
        ("bella-hadid", "Bella Hadid", "Estados Unidos", "Modelo", "F", 1996, "0100000"),
        ("gisele-bundchen", "Gisele Bündchen", "Brasil", "Modelo e ativista", "F", 1980, "0100001"),
        ("naomi-campbell", "Naomi Campbell", "Reino Unido", "Modelo e atriz", "F", 1970, "0110001"),
        ("paris-hilton", "Paris Hilton", "Estados Unidos", "Empresária e personalidade de reality", "F", 1981, "0010111"),
        ("tyra-banks", "Tyra Banks", "Estados Unidos", "Modelo e personalidade de televisão", "F", 1973, "0110011"),
    ],
    "Tecnologia e negócios": [
        ("elon-musk", "Elon Musk", "Estados Unidos", "Empresário e executivo de tecnologia", "M", 1971, "10001000"),
        ("mark-zuckerberg", "Mark Zuckerberg", "Estados Unidos", "Empresário e programador", "M", 1984, "11100000"),
        ("jeff-bezos", "Jeff Bezos", "Estados Unidos", "Empresário e fundador da Amazon", "M", 1964, "10010000"),
        ("bill-gates", "Bill Gates", "Estados Unidos", "Empresário e filantropo", "M", 1955, "11000000"),
        ("warren-buffett", "Warren Buffett", "Estados Unidos", "Investidor e filantropo", "M", 1930, "00000000"),
        ("larry-page", "Larry Page", "Estados Unidos", "Cofundador de empresa de tecnologia", "M", 1973, "11000000"),
        ("sergey-brin", "Sergey Brin", "Estados Unidos", "Cofundador de empresa de tecnologia", "M", 1973, "11000100"),
        ("jensen-huang", "Jensen Huang", "Taiwan", "Executivo de tecnologia e engenheiro elétrico", "M", 1963, "10001000"),
        ("sam-altman", "Sam Altman", "Estados Unidos", "Empresário e investidor", "M", 1985, "10000000"),
        ("tim-cook", "Tim Cook", "Estados Unidos", "Executivo de tecnologia", "M", 1960, "00001000"),
        ("jack-ma", "Jack Ma", "China", "Empresário e cofundador do Alibaba Group", "M", 1964, "10010010"),
        ("bernard-arnault", "Bernard Arnault", "França", "Empresário de produtos de luxo", "M", 1949, "00000001"),
    ],
}

SYMBOLS = {
    "Outros esportes": "sportscourt.fill",
    "Música internacional": "music.note",
    "K-pop": "music.mic",
    "Cinema e TV": "theatermasks.fill",
    "Moda e reality": "sparkles",
    "Tecnologia e negócios": "lightbulb.fill",
}
ARTIST_CATEGORIES = {"Música internacional", "K-pop", "Cinema e TV"}


def build() -> dict:
    people = []
    questions = []
    seen_ids: set[str] = set()
    for category, specifications in QUESTION_SPECS.items():
        for attribute, text in specifications:
            questions.append({
                "id": f"{attribute.replace('_', '-')}",
                "text": text,
                "attribute": attribute,
                "categories": [category],
            })
        traits = [attribute for attribute, _ in specifications]
        candidates = CANDIDATES.get(category, [])
        if len(candidates) < 12:
            raise ValueError(f"{category} needs at least 12 people")
        for identifier, name, country, profession, gender, birth_year, values in candidates:
            if identifier in seen_ids:
                raise ValueError(f"duplicate expansion id: {identifier}")
            if len(values) != len(traits) or any(bit not in "01" for bit in values):
                raise ValueError(f"invalid trait vector for {identifier}: expected {len(traits)} binary values")
            seen_ids.add(identifier)
            attributes = {
                "brazilian": 1 if country == "Brasil" else 0,
                "alive": 1,
                "male": 1 if gender == "M" else 0,
                "born_before_1970": 1 if birth_year < 1970 else 0,
                "born_before_1990": 1 if birth_year < 1990 else 0,
                "football": 0,
                "artist": 1 if category in ARTIST_CATEGORIES else 0,
                "creator": 0,
                "politician": 0,
                "historical": 0,
            }
            attributes.update({attribute: int(value) for attribute, value in zip(traits, values)})
            people.append({
                "id": identifier,
                "name": name,
                "categories": [category],
                "country": country,
                "profession": profession,
                "attributes": attributes,
                "avatarSymbol": SYMBOLS[category],
            })

    # A directly sourced Brazilian artist joins the existing Artistas brasileiros category.
    people.append({
        "id": "djavan",
        "name": "Djavan",
        "categories": ["Artistas brasileiros"],
        "country": "Brasil",
        "profession": "Cantor, compositor e guitarrista",
        "attributes": {
            "brazilian": 1,
            "alive": 1,
            "male": 1,
            "born_before_1970": 1,
            "born_before_1990": 1,
            "football": 0,
            "artist": 1,
            "creator": 0,
            "politician": 0,
            "historical": 0,
            "singer": 1,
            "actor": 0,
            "presenter": 0,
            "writer": 1,
            "instrumentalist": 1,
            "director": 0,
        },
        "avatarSymbol": "music.note",
        "imageName": "djavan.jpg",
    })
    return {"people": people, "questions": questions}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {category: sum(category in person["categories"] for person in result["people"]) for category in QUESTION_SPECS}
    print(f"Wrote {len(result['people'])} people and {len(result['questions'])} questions to {args.output}")
    for category, count in counts.items():
        print(f"- {category}: {count}")


if __name__ == "__main__":
    main()
