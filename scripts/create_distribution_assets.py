#!/usr/bin/env python3
import base64, json, subprocess, time, urllib.request, urllib.error
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

ROOT = Path(__file__).parents[1]
KEY_ID = "S96HVY2BYT"; ISSUER = "aa5a3fcd-f139-4b1f-beb2-47fd125148d9"
API_KEY = Path("/home/richard/Documentos/play store/AuthKey_S96HVY2BYT.p8")
BUNDLE_ID = "XS57YRQC46"

def b64(value): return base64.urlsafe_b64encode(value).rstrip(b"=").decode()
header = b64(json.dumps({"alg":"ES256","kid":KEY_ID,"typ":"JWT"}, separators=(",",":")).encode())
payload = b64(json.dumps({"iss":ISSUER,"iat":int(time.time()),"exp":int(time.time())+900,"aud":"appstoreconnect-v1"}, separators=(",",":")).encode())
key = serialization.load_pem_private_key(API_KEY.read_bytes(), password=None)
r, s = decode_dss_signature(key.sign(f"{header}.{payload}".encode(), ec.ECDSA(hashes.SHA256())))
token = f"{header}.{payload}.{b64(r.to_bytes(32,'big') + s.to_bytes(32,'big'))}"
auth = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

private_key = ROOT / "scripts/.quem-sou-eu-distribution.key"
csr = ROOT / "scripts/.quem-sou-eu-distribution.csr"
subprocess.run(["openssl", "genrsa", "-out", str(private_key), "2048"], check=True, capture_output=True)
subprocess.run(["openssl", "req", "-new", "-key", str(private_key), "-outform", "DER", "-out", str(csr), "-subj", "/CN=Quem Sou Eu Adivinha Distribution"], check=True, capture_output=True)
certificate_body = json.dumps({"data":{"type":"certificates","attributes":{"certificateType":"IOS_DISTRIBUTION","csrContent":base64.b64encode(csr.read_bytes()).decode()}}}).encode()
request = urllib.request.Request("https://api.appstoreconnect.apple.com/v1/certificates", data=certificate_body, headers=auth, method="POST")
try:
    with urllib.request.urlopen(request) as response: certificate = json.loads(response.read())
except urllib.error.HTTPError as error:
    print(error.read().decode()); raise
certificate_data = certificate["data"]
certificate_path = ROOT / "scripts/.quem-sou-eu-distribution.cer"
certificate_path.write_bytes(base64.b64decode(certificate_data["attributes"]["certificateContent"]))
profile_body = json.dumps({"data":{"type":"profiles","attributes":{"name":"Quem Sou Eu Adivinha App Store 2026 v2","profileType":"IOS_APP_STORE"},"relationships":{"bundleId":{"data":{"type":"bundleIds","id":BUNDLE_ID}},"certificates":{"data":[{"type":"certificates","id":certificate_data["id"]}]}}}}).encode()
request = urllib.request.Request("https://api.appstoreconnect.apple.com/v1/profiles", data=profile_body, headers=auth, method="POST")
with urllib.request.urlopen(request) as response: profile = json.loads(response.read())
profile_data = profile["data"]
(ROOT / "scripts/.quem-sou-eu.mobileprovision").write_bytes(base64.b64decode(profile_data["attributes"]["profileContent"]))
print(json.dumps({"certificateId": certificate_data["id"], "profileId": profile_data["id"], "profileUUID": profile_data["attributes"]["uuid"]}))
