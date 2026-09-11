#!/usr/bin/env python3
"""Create the app's Apple bundle ID through App Store Connect API."""
import base64
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

KEY_ID = "S96HVY2BYT"
ISSUER = "aa5a3fcd-f139-4b1f-beb2-47fd125148d9"
TEAM_ID = "SRN7AW424S"
BUNDLE = "br.com.quemsoueu.adivinha"
KEY = Path("/home/richard/Documentos/play store/AuthKey_S96HVY2BYT.p8")

def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()

header = b64(json.dumps({"alg": "ES256", "kid": KEY_ID, "typ": "JWT"}, separators=(",", ":")).encode())
payload = b64(json.dumps({"iss": ISSUER, "iat": int(time.time()), "exp": int(time.time()) + 900, "aud": "appstoreconnect-v1"}, separators=(",", ":")).encode())
unsigned = f"{header}.{payload}".encode()
private_key = serialization.load_pem_private_key(KEY.read_bytes(), password=None)
der_signature = private_key.sign(unsigned, ec.ECDSA(hashes.SHA256()))
r, s = decode_dss_signature(der_signature)
signature = r.to_bytes(32, "big") + s.to_bytes(32, "big")
token = f"{header}.{payload}.{b64(signature)}"

body = json.dumps({"data": {"type": "bundleIds", "attributes": {"identifier": BUNDLE, "name": "Quem Sou Eu Adivinha", "platform": "IOS"}}}).encode()
request = urllib.request.Request("https://api.appstoreconnect.apple.com/v1/bundleIds", data=body, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(request) as response:
        print(response.read().decode())
except urllib.error.HTTPError as error:
    print(error.read().decode())
    raise
