#!/usr/bin/env python3
import base64, json, time, urllib.request, urllib.error
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

KEY_ID = "S96HVY2BYT"
ISSUER = "aa5a3fcd-f139-4b1f-beb2-47fd125148d9"
KEY = Path("/home/richard/Documentos/play store/AuthKey_S96HVY2BYT.p8")
BUNDLE_ID = "XS57YRQC46"
CERTIFICATE_ID = "69BADS22K3"

def b64(value): return base64.urlsafe_b64encode(value).rstrip(b"=").decode()
header = b64(json.dumps({"alg":"ES256","kid":KEY_ID,"typ":"JWT"}, separators=(",",":")).encode())
payload = b64(json.dumps({"iss":ISSUER,"iat":int(time.time()),"exp":int(time.time())+900,"aud":"appstoreconnect-v1"}, separators=(",",":")).encode())
key = serialization.load_pem_private_key(KEY.read_bytes(), password=None)
r, s = decode_dss_signature(key.sign(f"{header}.{payload}".encode(), ec.ECDSA(hashes.SHA256())))
token = f"{header}.{payload}.{b64(r.to_bytes(32,'big') + s.to_bytes(32,'big'))}"

body = json.dumps({"data": {"type":"profiles", "attributes":{"name":"Quem Sou Eu Adivinha App Store 2026","profileType":"IOS_APP_STORE"}, "relationships":{"bundleId":{"data":{"type":"bundleIds","id":BUNDLE_ID}},"certificates":{"data":[{"type":"certificates","id":CERTIFICATE_ID}]}}}}).encode()
request = urllib.request.Request("https://api.appstoreconnect.apple.com/v1/profiles", data=body, headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"}, method="POST")
try:
    with urllib.request.urlopen(request) as response: print(response.read().decode())
except urllib.error.HTTPError as error:
    print(error.read().decode())
    raise
