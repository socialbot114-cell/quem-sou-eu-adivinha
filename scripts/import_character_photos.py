#!/usr/bin/env python3
"""Import selected Commons portraits, optimize them, and record attribution."""
from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageCms, ImageOps

ROOT = Path(__file__).parents[1]
PHOTO_DIR = ROOT / "iosApp/Resources/Characters"
CREDITS_PATH = ROOT / "docs/content/image-credits.json"
USER_AGENT = "QuemSouEuOfflineCatalog/1.0 (https://github.com/socialbot114-cell/quem-sou-eu-adivinha)"

PHOTOS = [
    {
        "id": "anitta",
        "name": "Anitta",
        "sourceCache": "commons-anitta.jpg",
        "sourceImageURL": "https://upload.wikimedia.org/wikipedia/commons/0/03/5_-_Anitta_%285%29_%2816295636217%29_-_cropped.jpg",
        "url": "https://commons.wikimedia.org/wiki/File:5_-_Anitta_(5)_(16295636217)_-_cropped.jpg",
        "sourceFile": "File:5 - Anitta (5) (16295636217) - cropped.jpg",
        "author": "Renan Katayama",
        "license": "CC BY-SA 2.0",
        "licenseURL": "https://creativecommons.org/licenses/by-sa/2.0",
        "centering": [0.50, 0.30],
    },
    {
        "id": "caetano-veloso",
        "name": "Caetano Veloso",
        "sourceCache": "commons-caetano.jpg",
        "sourceImageURL": "https://upload.wikimedia.org/wikipedia/commons/8/8f/Caetano_Veloso_%28cropped%29.jpg",
        "url": "https://commons.wikimedia.org/wiki/File:Caetano_Veloso_(cropped).jpg",
        "sourceFile": "File:Caetano Veloso (cropped).jpg",
        "author": "Secretaría de Cultura Ciudad de México",
        "license": "CC BY 2.0",
        "licenseURL": "https://creativecommons.org/licenses/by/2.0",
        "centering": [0.50, 0.37],
    },
    {
        "id": "gilberto-gil",
        "name": "Gilberto Gil",
        "sourceCache": "commons-gilberto.jpg",
        "sourceImageURL": "https://upload.wikimedia.org/wikipedia/commons/c/c4/Gilberto_Gil_2012.jpg",
        "url": "https://commons.wikimedia.org/wiki/File:Gilberto_Gil_2012.jpg",
        "sourceFile": "File:Gilberto Gil 2012.jpg",
        "author": "simenon",
        "license": "CC BY-SA 2.0",
        "licenseURL": "https://creativecommons.org/licenses/by-sa/2.0",
        "centering": [0.50, 0.40],
    },
    {
        "id": "marisa-monte",
        "name": "Marisa Monte",
        "sourceCache": "commons-marisa.jpg",
        "sourceImageURL": "https://upload.wikimedia.org/wikipedia/commons/7/75/Marisa_Monte_-_Ao_Vivo_%282012%29.jpg",
        "url": "https://commons.wikimedia.org/wiki/File:Marisa_Monte_-_Ao_Vivo_(2012).jpg",
        "sourceFile": "File:Marisa Monte - Ao Vivo (2012).jpg",
        "author": "Larissa Barreto",
        "license": "CC BY 2.0",
        "licenseURL": "https://creativecommons.org/licenses/by/2.0",
        "centering": [0.62, 0.42],
    },
    {
        "id": "xuxa",
        "name": "Xuxa Meneghel",
        "sourceCache": "commons-xuxa.jpg",
        "sourceImageURL": "https://upload.wikimedia.org/wikipedia/commons/2/27/Xuxa_Meneghel.jpg",
        "url": "https://commons.wikimedia.org/wiki/File:Xuxa_Meneghel.jpg",
        "sourceFile": "File:Xuxa Meneghel.jpg",
        "author": "Antonio Cruz/Agência Brasil",
        "license": "CC BY 3.0 br",
        "licenseURL": "https://creativecommons.org/licenses/by/3.0/br/deed.en",
        "centering": [0.50, 0.37],
    },
    {
        "id": "djavan",
        "name": "Djavan",
        "sourceCache": "commons-djavan.jpg",
        "sourceImageURL": "https://upload.wikimedia.org/wikipedia/commons/0/08/Djavan_San_Javier_Jazz_2023_26_%28cropped%29.jpg",
        "url": "https://commons.wikimedia.org/wiki/File:Djavan_San_Javier_Jazz_2023_26_(cropped).jpg",
        "sourceFile": "File:Djavan San Javier Jazz 2023 26 (cropped).jpg",
        "author": "Tsaorin",
        "license": "CC BY-SA 4.0",
        "licenseURL": "https://creativecommons.org/licenses/by-sa/4.0",
        "centering": [0.63, 0.43],
    },
]


def source_bytes(photo: dict, cache: Path) -> bytes:
    cached = cache / photo["sourceCache"]
    if cached.is_file():
        return cached.read_bytes()
    request = Request(photo["sourceImageURL"], headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        return response.read()


def process(photo: dict, cache: Path, destination: Path) -> None:
    raw = source_bytes(photo, cache)
    from io import BytesIO

    with Image.open(BytesIO(raw)) as opened:
        image = ImageOps.exif_transpose(opened)
        if image.mode not in ("RGB", "L"):
            if "A" in image.getbands():
                rgba = image.convert("RGBA")
                background = Image.new("RGBA", rgba.size, "white")
                image = Image.alpha_composite(background, rgba).convert("RGB")
            else:
                image = image.convert("RGB")
        else:
            image = image.convert("RGB")
        image = ImageOps.fit(
            image,
            (1024, 1024),
            method=Image.Resampling.LANCZOS,
            centering=tuple(photo["centering"]),
        )
        icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        image.save(destination, format="JPEG", quality=85, optimize=True, progressive=True, icc_profile=icc)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cache", type=Path, default=Path("/tmp/opencode"))
    args = parser.parse_args()
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(CREDITS_PATH.read_text(encoding="utf-8"))
    existing = {item["id"]: item for item in manifest["items"]}
    for photo in PHOTOS:
        asset = PHOTO_DIR / f"{photo['id']}.jpg"
        process(photo, args.source_cache, asset)
        item = {
            "id": photo["id"],
            "name": photo["name"],
            "file": f"iosApp/Resources/Characters/{photo['id']}.jpg",
            "sourceCategory": "artistas",
            "sourceFile": photo["sourceFile"],
            "url": photo["url"],
            "author": photo["author"],
            "license": photo["license"],
            "licenseURL": photo["licenseURL"],
            "modifications": "Recorte quadrado com enquadramento manual, redimensionamento Lanczos para 1024x1024, JPEG qualidade 85 e perfil sRGB ICC incorporado.",
            "reviewStatus": "approved-visual-and-credit-review",
            "reviewedAt": date.today().isoformat(),
        }
        existing[photo["id"]] = item
        print(f"Processed {asset.name}: {asset.stat().st_size} bytes")
        time.sleep(0.1)
    manifest["generatedAt"] = date.today().isoformat()
    manifest["items"] = list(existing.values())
    CREDITS_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated image credits: {len(manifest['items'])} portraits")


if __name__ == "__main__":
    main()
