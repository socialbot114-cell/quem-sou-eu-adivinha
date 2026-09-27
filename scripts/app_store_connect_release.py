#!/usr/bin/env python3
"""Inspect and submit the iOS release through the App Store Connect API."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import jwt


API_ROOT = "https://api.appstoreconnect.apple.com/v1"
APP_ID = "6810873964"
BUNDLE_ID = "br.com.quemsoueu.adivinha"
APP_VERSION = "1.2.3"
BUILD_NUMBER = "41"
LOCALE = "pt-BR"
SCREENSHOT_DISPLAY_TYPE = "APP_IPHONE_65"
SCREENSHOT_SIZE = (1284, 2778)
SUBMIT_CONFIRMATION = f"SUBMIT {APP_VERSION} ({BUILD_NUMBER})"
SCREENSHOT_FILES = (
    "01-home.png",
    "02-categorias.png",
    "03-jogo.png",
)

METADATA = {
    "description": """Pense em alguém conhecido e deixe o Quem Sou Eu? Adivinha tentar descobrir quem é.

O jogo faz perguntas simples, combina suas respostas e apresenta o palpite mais provável. Você pode escolher uma categoria ou jogar com todas as personalidades disponíveis.

Recursos:

- Partidas rápidas com até 14 perguntas.
- Doze categorias temáticas e modo livre.
- Motor de descoberta que funciona totalmente offline.
- Pontos, moedas, sequência e conquistas salvos no aparelho.
- Princesa Detetive, coleção de descobertas e interface premium.

Não é necessário criar uma conta. O jogo não exibe anúncios, não exige internet e não coleta dados pessoais.""",
    "keywords": "adivinha,quiz,perguntas,jogo,personalidades,trivia,quem sou eu",
    "marketingUrl": "https://socialbot114-cell.github.io/quem-sou-eu-adivinha-site/",
    "promotionalText": "Pense em uma personalidade. Responda perguntas e veja o jogo descobrir quem você imaginou.",
    "supportUrl": "https://socialbot114-cell.github.io/quem-sou-eu-adivinha-site/",
    "whatsNew": "Uma nova experiência para o Quem Sou Eu? Adivinha.\n\n- Jogo de pistas e perguntas offline.\n- 305 personalidades em doze categorias temáticas.\n- 150 novas personalidades adicionadas às categorias existentes, com pistas ampliadas para K-pop, música, esportes, artistas brasileiros e criadores digitais.\n- Onboarding, retomada de partida e coleção de descobertas.\n- Novo visual com a Princesa Detetive.\n- Retratos, compartilhamento, pontos, moedas e sequência.",
}
COPYRIGHT = "2026 Gustavo De Melo Ferreira"
REVIEW_NOTES = """Olá,

O Quem Sou Eu? Adivinha é um jogo de perguntas totalmente offline para iPhone.

Para testar:

1. Abra o app.
2. Conclua ou pule a apresentação inicial.
3. Toque em `Jogar agora` ou abra a aba `Jogar`.
4. Escolha uma categoria ou o modo livre.
5. Responda usando `Sim`, `Provavelmente`, `Não sei`, `Acho que não` ou `Não`.
6. Continue até o app apresentar o palpite.

Não é necessário criar uma conta, fazer login, conceder permissões ou conectar-se à internet. O progresso é salvo localmente no dispositivo. Não há compras, anúncios, rastreamento ou conteúdo que exija autenticação.

Obrigado."""

TOKEN: str | None = None


class ReleaseError(RuntimeError):
    """A release precondition or App Store Connect request failed."""


def make_token() -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "iss": os.environ["APPLE_API_ISSUER_ID"],
            "iat": now,
            "exp": now + 15 * 60,
            "aud": "appstoreconnect-v1",
        },
        os.environ["APPLE_API_KEY_P8"],
        algorithm="ES256",
        headers={"kid": os.environ["APPLE_API_KEY_ID"], "typ": "JWT"},
    )


def api_token() -> str:
    global TOKEN
    if TOKEN is None:
        TOKEN = make_token()
    return TOKEN


def request_json(url: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        url if url.startswith("https://") else f"{API_ROOT}{url}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_token()}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            payload = response.read()
            return json.loads(payload) if payload else {}
    except HTTPError as error:
        payload = error.read().decode("utf-8", errors="replace")
        try:
            errors = json.loads(payload).get("errors", [])
            details = [
                ": ".join(part for part in (item.get("code"), item.get("title"), item.get("detail")) if part)
                for item in errors
            ]
        except (json.JSONDecodeError, AttributeError):
            details = []
        message = "; ".join(details) or "Apple returned an API error"
        raise ReleaseError(f"App Store Connect returned HTTP {error.code}: {message}") from None
    except URLError as error:
        raise ReleaseError(f"Could not reach App Store Connect: {error.reason}") from None


def optional_request(path: str) -> dict[str, Any] | None:
    try:
        return request_json(path)
    except ReleaseError as error:
        if "HTTP 404" in str(error):
            return None
        raise


def list_pages(path: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    next_url: str | None = path
    while next_url:
        response = request_json(next_url)
        results.extend(response.get("data", []))
        next_url = response.get("links", {}).get("next")
    return results


def query_path(path: str, **params: str) -> str:
    return f"{path}?{urlencode(params)}"


def verify_app() -> dict[str, Any]:
    app = request_json(f"/apps/{APP_ID}").get("data")
    if not app:
        raise ReleaseError(f"App Store Connect app {APP_ID} was not found")
    attributes = app.get("attributes", {})
    if attributes.get("bundleId") != BUNDLE_ID:
        raise ReleaseError(
            f"App Store Connect app {APP_ID} has bundle ID {attributes.get('bundleId')!r}, expected {BUNDLE_ID!r}"
        )
    return app


def all_versions() -> list[dict[str, Any]]:
    return list_pages(query_path(f"/apps/{APP_ID}/appStoreVersions", **{"filter[platform]": "IOS", "limit": "200"}))


def matching_versions(versions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        version
        for version in versions
        if version.get("attributes", {}).get("versionString") == APP_VERSION
        and version.get("attributes", {}).get("platform") == "IOS"
    ]


def get_release_build(wait_for_valid: bool = False) -> dict[str, Any]:
    timeout = int(os.environ.get("APP_STORE_PROCESSING_TIMEOUT_MINUTES", "30")) if wait_for_valid else 0
    deadline = time.monotonic() + timeout * 60
    while True:
        candidates = []
        for build in list_pages(f"/apps/{APP_ID}/builds?limit=200"):
            attributes = build.get("attributes", {})
            if str(attributes.get("version", "")) != BUILD_NUMBER:
                continue
            pre_release = optional_request(f"/builds/{build['id']}/preReleaseVersion")
            pre_release_attributes = (pre_release or {}).get("data", {}).get("attributes", {})
            if pre_release_attributes.get("version") == APP_VERSION:
                candidates.append((build, pre_release_attributes))

        if candidates:
            candidates.sort(
                key=lambda pair: pair[0].get("attributes", {}).get("uploadedDate", ""), reverse=True
            )
            build, pre_release_attributes = candidates[0]
            attributes = build.get("attributes", {})
            state = attributes.get("processingState", "UNKNOWN")
            result = {
                "id": build["id"],
                "version": pre_release_attributes.get("version"),
                "buildNumber": attributes.get("version"),
                "processingState": state,
                "uploadedDate": attributes.get("uploadedDate"),
                "expired": attributes.get("expired", False),
            }
            if attributes.get("expired"):
                raise ReleaseError(f"Build {APP_VERSION} ({BUILD_NUMBER}) has expired")
            if state == "VALID":
                return result
            if state in {"FAILED", "INVALID"}:
                raise ReleaseError(f"App Store Connect rejected build {APP_VERSION} ({BUILD_NUMBER}): {state}")
            if not wait_for_valid or time.monotonic() >= deadline:
                return result
            print(f"Build {APP_VERSION} ({BUILD_NUMBER}) is still processing: {state}", flush=True)
        elif not wait_for_valid or time.monotonic() >= deadline:
            raise ReleaseError(f"Build {APP_VERSION} ({BUILD_NUMBER}) was not found in App Store Connect")
        time.sleep(30)


def version_state(version: dict[str, Any]) -> str:
    attributes = version.get("attributes", {})
    return attributes.get("appVersionState") or attributes.get("appStoreState") or "UNKNOWN"


def get_version_localizations(version_id: str) -> list[dict[str, Any]]:
    return list_pages(f"/appStoreVersions/{version_id}/appStoreVersionLocalizations?limit=200")


def get_screenshot_sets(localization_id: str) -> list[dict[str, Any]]:
    path = query_path(
        f"/appStoreVersionLocalizations/{localization_id}/appScreenshotSets",
        **{"filter[screenshotDisplayType]": SCREENSHOT_DISPLAY_TYPE, "limit": "200"},
    )
    return list_pages(path)


def get_screenshots(screenshot_set_id: str) -> list[dict[str, Any]]:
    return list_pages(f"/appScreenshotSets/{screenshot_set_id}/appScreenshots?limit=200")


def get_review_detail(version_id: str) -> dict[str, Any] | None:
    response = optional_request(f"/appStoreVersions/{version_id}/appStoreReviewDetail")
    return (response or {}).get("data")


def get_submission_report() -> list[dict[str, Any]]:
    submissions = list_pages(
        query_path(f"/apps/{APP_ID}/reviewSubmissions", **{"filter[platform]": "IOS", "limit": "200"})
    )
    report = []
    for submission in submissions:
        attributes = submission.get("attributes", {})
        items = list_pages(f"/reviewSubmissions/{submission['id']}/items?limit=200")
        report.append(
            {
                "id": submission["id"],
                "state": attributes.get("state", "UNKNOWN"),
                "items": [
                    {
                        "id": item["id"],
                        "state": item.get("attributes", {}).get("state", "UNKNOWN"),
                        "appStoreVersionId": (item.get("relationships", {}).get("appStoreVersion", {}).get("data") or {}).get("id"),
                    }
                    for item in items
                ],
            }
        )
    return report


def inspect() -> dict[str, Any]:
    app = verify_app()
    build = get_release_build()
    versions = matching_versions(all_versions())
    if len(versions) > 1:
        raise ReleaseError(f"Found multiple App Store version records for {APP_VERSION}")

    version_report: dict[str, Any] | None = None
    if versions:
        version = versions[0]
        localizations = get_version_localizations(version["id"])
        locale = next((item for item in localizations if item.get("attributes", {}).get("locale") == LOCALE), None)
        screenshot_report = []
        if locale:
            for screenshot_set in get_screenshot_sets(locale["id"]):
                screenshots = get_screenshots(screenshot_set["id"])
                screenshot_report.append(
                    {
                        "displayType": screenshot_set.get("attributes", {}).get("screenshotDisplayType"),
                        "assets": [
                            {
                                "fileName": item.get("attributes", {}).get("fileName"),
                                "state": item.get("attributes", {}).get("assetDeliveryState", {}).get("state", "UNKNOWN"),
                            }
                            for item in screenshots
                        ],
                    }
                )
        detail = get_review_detail(version["id"])
        version_report = {
            "id": version["id"],
            "version": version.get("attributes", {}).get("versionString"),
            "state": version_state(version),
            "releaseType": version.get("attributes", {}).get("releaseType"),
            "buildId": (version.get("relationships", {}).get("build", {}).get("data") or {}).get("id"),
            "locales": [item.get("attributes", {}).get("locale") for item in localizations],
            "ptBRLocalizationId": locale.get("id") if locale else None,
            "screenshots": screenshot_report,
            "reviewNotesPresent": bool((detail or {}).get("attributes", {}).get("notes")),
            "reviewContactPresent": all(
                (detail or {}).get("attributes", {}).get(key)
                for key in ("contactFirstName", "contactLastName", "contactPhone", "contactEmail")
            ),
        }

    return {
        "app": {
            "id": app["id"],
            "bundleId": app.get("attributes", {}).get("bundleId"),
            "name": app.get("attributes", {}).get("name"),
        },
        "targetBuild": build,
        "targetAppStoreVersion": version_report,
        "reviewSubmissions": get_submission_report(),
    }


def validate_screenshot_package(directory: Path) -> list[dict[str, Any]]:
    limits = {"description": 4000, "keywords": 100, "promotionalText": 170, "supportUrl": 255, "marketingUrl": 255, "whatsNew": 4000}
    for field, limit in limits.items():
        if len(METADATA[field]) > limit:
            raise ReleaseError(f"App Store metadata field {field} exceeds its {limit}-character limit")
    results = []
    for file_name in SCREENSHOT_FILES:
        path = directory / file_name
        if not path.is_file():
            raise ReleaseError(f"Required App Store screenshot is missing: {path}")
        with path.open("rb") as file:
            header = file.read(24)
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            raise ReleaseError(f"Screenshot is not a valid PNG: {path}")
        dimensions = struct.unpack(">II", header[16:24])
        if dimensions != SCREENSHOT_SIZE:
            raise ReleaseError(
                f"Screenshot {path} is {dimensions[0]}x{dimensions[1]}; expected {SCREENSHOT_SIZE[0]}x{SCREENSHOT_SIZE[1]}"
            )
        size = path.stat().st_size
        if size == 0:
            raise ReleaseError(f"Screenshot is empty: {path}")
        results.append(
            {
                "fileName": file_name,
                "width": dimensions[0],
                "height": dimensions[1],
                "fileSize": size,
                "md5": hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest(),
            }
        )
    return results


def get_previous_review_contact(versions: list[dict[str, Any]], current_version_id: str | None) -> dict[str, Any] | None:
    candidates = [version for version in versions if version.get("id") != current_version_id]
    candidates.sort(key=lambda item: item.get("attributes", {}).get("createdDate", ""), reverse=True)
    fields = (
        "contactFirstName",
        "contactLastName",
        "contactPhone",
        "contactEmail",
        "demoAccountName",
        "demoAccountPassword",
        "demoAccountRequired",
    )
    for version in candidates:
        detail = get_review_detail(version["id"])
        attributes = (detail or {}).get("attributes", {})
        if all(attributes.get(key) for key in ("contactFirstName", "contactLastName", "contactPhone", "contactEmail")):
            return {key: attributes.get(key) for key in fields}
    return None


def ensure_version(build: dict[str, Any], versions: list[dict[str, Any]]) -> dict[str, Any]:
    matches = matching_versions(versions)
    if len(matches) > 1:
        raise ReleaseError(f"Found multiple App Store version records for {APP_VERSION}")
    build_linkage = {"data": {"type": "builds", "id": build["id"]}}
    if matches:
        version = matches[0]
        state = version_state(version)
        if state in {"WAITING_FOR_REVIEW", "IN_REVIEW", "PENDING_APPLE_RELEASE", "READY_FOR_DISTRIBUTION", "ACCEPTED"}:
            return version
        if state not in {"PREPARE_FOR_SUBMISSION", "READY_FOR_REVIEW", "UNKNOWN"}:
            raise ReleaseError(f"App Store version {APP_VERSION} is not editable (state: {state})")
        body = {
            "data": {
                "type": "appStoreVersions",
                "id": version["id"],
                "attributes": {"copyright": COPYRIGHT, "reviewType": "APP_STORE", "releaseType": "AFTER_APPROVAL"},
                "relationships": {"build": build_linkage},
            }
        }
        return request_json(f"/appStoreVersions/{version['id']}", method="PATCH", body=body)["data"]

    body = {
        "data": {
            "type": "appStoreVersions",
            "attributes": {
                "platform": "IOS",
                "versionString": APP_VERSION,
                "copyright": COPYRIGHT,
                "reviewType": "APP_STORE",
                "releaseType": "AFTER_APPROVAL",
            },
            "relationships": {
                "app": {"data": {"type": "apps", "id": APP_ID}},
                "build": build_linkage,
            },
        }
    }
    return request_json("/appStoreVersions", method="POST", body=body)["data"]


def ensure_localization(version_id: str) -> dict[str, Any]:
    localizations = get_version_localizations(version_id)
    matches = [item for item in localizations if item.get("attributes", {}).get("locale") == LOCALE]
    if len(matches) > 1:
        raise ReleaseError(f"Found multiple {LOCALE} localizations for version {APP_VERSION}")
    if matches:
        localization = matches[0]
        body = {
            "data": {
                "type": "appStoreVersionLocalizations",
                "id": localization["id"],
                "attributes": METADATA,
            }
        }
        return request_json(f"/appStoreVersionLocalizations/{localization['id']}", method="PATCH", body=body)["data"]

    body = {
        "data": {
            "type": "appStoreVersionLocalizations",
            "attributes": {"locale": LOCALE, **METADATA},
            "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}}},
        }
    }
    return request_json("/appStoreVersionLocalizations", method="POST", body=body)["data"]


def upload_screenshot(path: Path, screenshot_set_id: str) -> dict[str, Any]:
    content = path.read_bytes()
    # App Store Connect requires MD5 for the committed asset checksum.
    checksum = hashlib.md5(content, usedforsecurity=False).hexdigest()
    created = request_json(
        "/appScreenshots",
        method="POST",
        body={
            "data": {
                "type": "appScreenshots",
                "attributes": {"fileName": path.name, "fileSize": len(content)},
                "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": screenshot_set_id}}},
            }
        },
    )["data"]
    attributes = created.get("attributes", {})
    operations = attributes.get("uploadOperations", [])
    if not operations:
        raise ReleaseError(f"App Store Connect returned no upload operations for {path.name}")

    for operation in operations:
        offset = int(operation["offset"])
        length = int(operation["length"])
        chunk = content[offset : offset + length]
        if len(chunk) != length:
            raise ReleaseError(f"App Store Connect requested an invalid upload range for {path.name}")
        headers = {header["name"]: header["value"] for header in operation.get("requestHeaders", [])}
        request = Request(operation["url"], data=chunk, method=operation.get("method", "PUT"), headers=headers)
        try:
            with urlopen(request, timeout=120) as response:
                response.read()
        except HTTPError as error:
            raise ReleaseError(
                f"Screenshot upload for {path.name} returned HTTP {error.code}"
            ) from None
        except URLError as error:
            raise ReleaseError(
                f"Could not reach the screenshot upload service for {path.name}: {error.reason}"
            ) from None

    screenshot_id = created["id"]
    request_json(
        f"/appScreenshots/{screenshot_id}",
        method="PATCH",
        body={
            "data": {
                "type": "appScreenshots",
                "id": screenshot_id,
                "attributes": {"sourceFileChecksum": checksum, "uploaded": True},
            }
        },
    )
    return wait_for_screenshot(screenshot_id)


def wait_for_screenshot(screenshot_id: str) -> dict[str, Any]:
    timeout = int(os.environ.get("APP_STORE_ASSET_TIMEOUT_MINUTES", "20"))
    deadline = time.monotonic() + timeout * 60
    while True:
        screenshot = request_json(f"/appScreenshots/{screenshot_id}")["data"]
        state = screenshot.get("attributes", {}).get("assetDeliveryState", {}).get("state", "UNKNOWN")
        if state == "COMPLETE":
            return screenshot
        if state == "FAILED":
            errors = screenshot.get("attributes", {}).get("assetDeliveryState", {}).get("errors", [])
            raise ReleaseError(f"App Store Connect failed to process screenshot: {json.dumps(errors, ensure_ascii=False)}")
        if time.monotonic() >= deadline:
            raise ReleaseError(f"Screenshot {screenshot_id} did not reach COMPLETE (state: {state})")
        print(f"Waiting for App Store screenshot processing: {state}", flush=True)
        time.sleep(20)


def ensure_screenshots(localization_id: str, directory: Path) -> list[str]:
    sets = get_screenshot_sets(localization_id)
    if len(sets) > 1:
        raise ReleaseError(f"Found multiple {SCREENSHOT_DISPLAY_TYPE} screenshot sets; refusing to choose one")
    if sets:
        screenshot_set = sets[0]
    else:
        screenshot_set = request_json(
            "/appScreenshotSets",
            method="POST",
            body={
                "data": {
                    "type": "appScreenshotSets",
                    "attributes": {"screenshotDisplayType": SCREENSHOT_DISPLAY_TYPE},
                    "relationships": {
                        "appStoreVersionLocalization": {
                            "data": {"type": "appStoreVersionLocalizations", "id": localization_id}
                        }
                    },
                }
            },
        )["data"]

    existing = get_screenshots(screenshot_set["id"])
    if len(existing) > 10:
        raise ReleaseError("The App Store screenshot set already contains more than ten images")
    uploaded_names: list[str] = []
    for file_name in SCREENSHOT_FILES:
        match = next((item for item in existing if item.get("attributes", {}).get("fileName") == file_name), None)
        if match:
            state = match.get("attributes", {}).get("assetDeliveryState", {}).get("state", "UNKNOWN")
            if state == "COMPLETE":
                uploaded_names.append(file_name)
                continue
            if state != "FAILED":
                wait_for_screenshot(match["id"])
                uploaded_names.append(file_name)
                continue
            request_json(f"/appScreenshots/{match['id']}", method="DELETE")
        if len(existing) >= 10:
            raise ReleaseError("The App Store screenshot set is full; remove obsolete images before retrying")
        path = directory / file_name
        print(f"Uploading App Store screenshot {file_name}", flush=True)
        upload_screenshot(path, screenshot_set["id"])
        uploaded_names.append(file_name)
        existing.append({"attributes": {"fileName": file_name}})
    return uploaded_names


def ensure_review_detail(version_id: str, versions: list[dict[str, Any]]) -> dict[str, Any]:
    detail = get_review_detail(version_id)
    if detail:
        detail_id = detail["id"]
        attributes = detail.get("attributes", {})
        contact_fields = ("contactFirstName", "contactLastName", "contactPhone", "contactEmail")
        missing_contact = [key for key in contact_fields if not attributes.get(key)]
        if missing_contact:
            previous_contact = get_previous_review_contact(versions, version_id)
            if not previous_contact or any(not previous_contact.get(key) for key in missing_contact):
                raise ReleaseError(
                    "The current App Review contact details are incomplete and no complete prior contact was found. "
                    "Update the review contact in App Store Connect, then rerun the workflow."
                )
            attributes_to_update = {key: previous_contact[key] for key in missing_contact}
        else:
            attributes_to_update = {}
        body = {
            "data": {
                "type": "appStoreReviewDetails",
                "id": detail_id,
                "attributes": {**attributes_to_update, "notes": REVIEW_NOTES, "demoAccountRequired": False},
            }
        }
        return request_json(f"/appStoreReviewDetails/{detail_id}", method="PATCH", body=body)["data"]

    contact = get_previous_review_contact(versions, version_id)
    if not contact:
        raise ReleaseError(
            "No existing App Review contact details were found to copy to this version. "
            "Add the review contact in App Store Connect, then rerun the workflow."
        )
    body = {
        "data": {
            "type": "appStoreReviewDetails",
            "attributes": {**contact, "notes": REVIEW_NOTES, "demoAccountRequired": False},
            "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}}},
        }
    }
    return request_json("/appStoreReviewDetails", method="POST", body=body)["data"]


def get_submission_items(submission_id: str) -> list[dict[str, Any]]:
    return list_pages(f"/reviewSubmissions/{submission_id}/items?limit=200")


def create_or_submit_review(version_id: str) -> dict[str, str]:
    submissions = list_pages(
        query_path(f"/apps/{APP_ID}/reviewSubmissions", **{"filter[platform]": "IOS", "limit": "200"})
    )
    open_states = {"READY_FOR_REVIEW", "WAITING_FOR_REVIEW", "IN_REVIEW", "CANCELING", "COMPLETING"}
    active = [submission for submission in submissions if submission.get("attributes", {}).get("state") in open_states]

    for submission in active:
        items = get_submission_items(submission["id"])
        target_item = next(
            (
                item
                for item in items
                if (item.get("relationships", {}).get("appStoreVersion", {}).get("data") or {}).get("id") == version_id
            ),
            None,
        )
        state = submission.get("attributes", {}).get("state", "UNKNOWN")
        if target_item:
            if state != "READY_FOR_REVIEW":
                return {"id": submission["id"], "state": state}
            return submit_review_submission(submission["id"])
        if state != "READY_FOR_REVIEW" or items:
            raise ReleaseError(
                f"Another App Store review submission is active ({submission['id']}, state {state}); "
                "not changing its contents."
            )
        request_json(
            "/reviewSubmissionItems",
            method="POST",
            body={
                "data": {
                    "type": "reviewSubmissionItems",
                    "relationships": {
                        "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": submission["id"]}},
                        "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}},
                    },
                }
            },
        )
        return submit_review_submission(submission["id"])

    submission = request_json(
        "/reviewSubmissions",
        method="POST",
        body={
            "data": {
                "type": "reviewSubmissions",
                "attributes": {"platform": "IOS"},
                "relationships": {"app": {"data": {"type": "apps", "id": APP_ID}}},
            }
        },
    )["data"]
    submission_id = submission["id"]
    request_json(
        "/reviewSubmissionItems",
        method="POST",
        body={
            "data": {
                "type": "reviewSubmissionItems",
                "relationships": {
                    "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": submission_id}},
                    "appStoreVersion": {"data": {"type": "appStoreVersions", "id": version_id}},
                },
            }
        },
    )
    return submit_review_submission(submission_id)


def submit_review_submission(submission_id: str) -> dict[str, str]:
    request_json(
        f"/reviewSubmissions/{submission_id}",
        method="PATCH",
        body={"data": {"type": "reviewSubmissions", "id": submission_id, "attributes": {"submitted": True}}},
    )
    current = request_json(f"/reviewSubmissions/{submission_id}")["data"]
    return {"id": submission_id, "state": current.get("attributes", {}).get("state", "UNKNOWN")}


def write_summary(result: dict[str, Any]) -> None:
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## App Store Connect release result\n\n```json\n")
            summary.write(rendered)
            summary.write("\n```\n")


def run_submission(screenshots_dir: Path) -> dict[str, Any]:
    if os.environ.get("CONFIRM_SUBMISSION", "") != SUBMIT_CONFIRMATION:
        raise ReleaseError(f"Submission requires CONFIRM_SUBMISSION={SUBMIT_CONFIRMATION!r}")
    assets = validate_screenshot_package(screenshots_dir)
    app = verify_app()
    if app.get("attributes", {}).get("bundleId") != BUNDLE_ID:
        raise ReleaseError("App bundle ID verification failed")
    build = get_release_build(wait_for_valid=True)
    if build.get("processingState") != "VALID":
        raise ReleaseError(f"Build {APP_VERSION} ({BUILD_NUMBER}) is not VALID")

    versions = all_versions()
    matches = matching_versions(versions)
    if len(matches) > 1:
        raise ReleaseError(f"Found multiple App Store version records for {APP_VERSION}")
    existing_version = matches[0] if matches else None
    current_state = version_state(existing_version) if existing_version else "NEW"
    if current_state in {"WAITING_FOR_REVIEW", "IN_REVIEW", "PENDING_APPLE_RELEASE", "READY_FOR_DISTRIBUTION", "ACCEPTED"}:
        report = inspect()
        return {"result": "already_submitted_or_released", "versionState": current_state, **report}
    if current_state not in {"NEW", "PREPARE_FOR_SUBMISSION", "READY_FOR_REVIEW", "UNKNOWN"}:
        raise ReleaseError(f"App Store version {APP_VERSION} cannot be submitted from state {current_state}")

    if not existing_version:
        contact = get_previous_review_contact(versions, None)
        if not contact:
            raise ReleaseError(
                "No existing App Review contact details were found to copy to this version. "
                "Add the review contact in App Store Connect, then rerun the workflow."
            )
    else:
        detail = get_review_detail(existing_version["id"])
        attributes = (detail or {}).get("attributes", {})
        missing_contact = [
            key
            for key in ("contactFirstName", "contactLastName", "contactPhone", "contactEmail")
            if not attributes.get(key)
        ]
        previous_contact = get_previous_review_contact(versions, existing_version["id"]) if missing_contact else None
        if missing_contact and (not previous_contact or any(not previous_contact.get(key) for key in missing_contact)):
            raise ReleaseError(
                "Complete App Review contact details were not found to copy to this version. "
                "Add the review contact in App Store Connect, then rerun the workflow."
            )

    version = ensure_version(build, versions)
    version_id = version["id"]
    version_state_now = version_state(version)
    if version_state_now in {"WAITING_FOR_REVIEW", "IN_REVIEW", "PENDING_APPLE_RELEASE", "READY_FOR_DISTRIBUTION", "ACCEPTED"}:
        return {"result": "already_submitted_or_released", "versionId": version_id, "versionState": version_state_now}

    localization = ensure_localization(version_id)
    uploaded_screenshots = ensure_screenshots(localization["id"], screenshots_dir)
    ensure_review_detail(version_id, versions)
    submission = create_or_submit_review(version_id)
    result = {
        "result": "submitted_for_review" if submission["state"] != "READY_FOR_REVIEW" else "submission_created",
        "appId": app["id"],
        "bundleId": BUNDLE_ID,
        "version": APP_VERSION,
        "buildNumber": BUILD_NUMBER,
        "buildId": build["id"],
        "buildState": build["processingState"],
        "appStoreVersionId": version_id,
        "versionState": version_state(request_json(f"/appStoreVersions/{version_id}")["data"]),
        "locale": LOCALE,
        "screenshotDisplayType": SCREENSHOT_DISPLAY_TYPE,
        "screenshots": uploaded_screenshots,
        "validatedScreenshotCount": len(assets),
        "reviewSubmissionId": submission["id"],
        "reviewSubmissionState": submission["state"],
    }
    return result


def main() -> int:
    operation = sys.argv[1] if len(sys.argv) > 1 else "inspect"
    screenshots_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("store-kit/screenshots/iphone")
    if operation == "validate-assets":
        write_summary({"screenshots": validate_screenshot_package(screenshots_dir), "displayType": SCREENSHOT_DISPLAY_TYPE})
        return 0
    if operation == "inspect":
        result = inspect()
    elif operation == "submit":
        result = run_submission(screenshots_dir)
    else:
        raise ReleaseError("Operation must be one of: inspect, submit, validate-assets")
    write_summary(result)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
