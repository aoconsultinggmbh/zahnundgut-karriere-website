#!/usr/bin/env python3
"""
google-indexing.py – meldet Stellenseiten an die Google Indexing API (offiziell für JobPosting-Seiten gedacht).

Warum: Ohne Meldung wartet eine neue oder geänderte Stelle Tage bis Wochen auf den nächsten Google-Crawl.
Mit der Meldung holt Google die Seite in der Regel innerhalb von Minuten bis Stunden – und nimmt eine
gelöschte Stelle sofort aus dem Job-Kasten, statt Bewerber auf eine 404 zu schicken.

Was gemeldet wird:
  URL_UPDATED  für jede Stelle aus website/stellen.json (sichtbar: aktiv und initiativ)
  URL_DELETED  für jede Stelle, die beim letzten Lauf gemeldet war und jetzt fehlt (Stand in doku/indexing-stand.json)

Voraussetzungen (einmalig je Kunde, macht der Mitarbeiter mit dem Google-Konto des Kunden – Klickweg in
references/reichweite.md): Google-Cloud-Projekt, „Web Search Indexing API“ aktiviert, Dienstkonto mit
JSON-Schlüssel, die Dienstkonto-Adresse in der Search Console der Live-Domain als **Inhaber** eintragen.
Der JSON-Schlüssel kommt als GitHub-Secret GOOGLE_INDEXING_KEY in das Projekt (nie in eine Datei).

Aufruf (im Livegang-Ablauf und monatlich): GOOGLE_INDEXING_KEY='<json>' python3 scripts/google-indexing.py [--projekt .] [--probe]
Ohne Secret beendet sich das Skript still mit 0 – die Vorschau und Kunden ohne Google-Konto bleiben unberührt.
Kontingent: 200 Meldungen je Tag und Projekt – für Praxen mit 5–20 Stellen mehr als genug.
Braucht nur die Standardbibliothek plus `cryptography` (pip install cryptography) für die JWT-Signatur.
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TOKEN_URL = "https://oauth2.googleapis.com/token"
PUBLISH_URL = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPE = "https://www.googleapis.com/auth/indexing"


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def zugangstoken(schluessel: dict) -> str:
    """Dienstkonto-JWT signieren und gegen ein OAuth-Token tauschen (ohne google-auth-Paket)."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    jetzt = int(time.time())
    kopf = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    inhalt = b64url(json.dumps({"iss": schluessel["client_email"], "scope": SCOPE, "aud": TOKEN_URL,
                                "iat": jetzt, "exp": jetzt + 3600}).encode())
    privat = serialization.load_pem_private_key(schluessel["private_key"].encode(), password=None)
    signatur = privat.sign(f"{kopf}.{inhalt}".encode(), padding.PKCS1v15(), hashes.SHA256())
    jwt = f"{kopf}.{inhalt}.{b64url(signatur)}"
    daten = f"grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion={jwt}".encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=daten, method="POST"), timeout=30) as r:
        return json.load(r)["access_token"]


def melden(token: str, url: str, typ: str) -> tuple[bool, str]:
    req = urllib.request.Request(PUBLISH_URL, data=json.dumps({"url": url, "type": typ}).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, str(r.status)
    except urllib.error.HTTPError as e:
        return False, f"{e.code} {e.read().decode('utf-8', 'ignore')[:200]}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projekt", default=".")
    ap.add_argument("--probe", action="store_true", help="nur anzeigen, nichts senden")
    a = ap.parse_args()
    projekt = Path(a.projekt).resolve()
    roh = os.environ.get("GOOGLE_INDEXING_KEY", "").strip()
    kunde = json.loads((projekt / "kunde.json").read_text(encoding="utf-8"))
    if not kunde.get("google_for_jobs", {}).get("indexing_api", False):
        print("Indexing API in kunde.json nicht eingeschaltet – nichts zu tun.")
        return 0
    if kunde.get("vorschau", False):
        print("kunde.json → vorschau: true – an Google wird nur die Live-Domain gemeldet. Nichts gesendet.")
        return 0
    if not roh:
        print("Kein GOOGLE_INDEXING_KEY gesetzt – Meldung an Google übersprungen (Einrichtung: references/reichweite.md).")
        return 0

    stellen = json.loads((projekt / "website" / "stellen.json").read_text(encoding="utf-8"))
    aktuell = {s["url"] for s in (stellen.get("stellen") if isinstance(stellen, dict) else stellen)}
    stand_datei = projekt / "doku" / "indexing-stand.json"
    vorher = set(json.loads(stand_datei.read_text(encoding="utf-8")).get("gemeldet", [])) if stand_datei.exists() else set()
    auftraege = [(u, "URL_UPDATED") for u in sorted(aktuell)] + [(u, "URL_DELETED") for u in sorted(vorher - aktuell)]
    if a.probe:
        for u, typ in auftraege:
            print(f"PROBE {typ:12} {u}")
        return 0

    token = zugangstoken(json.loads(roh))
    fehler = 0
    for u, typ in auftraege:
        ok, info = melden(token, u, typ)
        print(f"{'OK  ' if ok else 'FEHL'} {typ:12} {u} {'' if ok else info}")
        fehler += 0 if ok else 1
        time.sleep(0.3)
    stand_datei.parent.mkdir(exist_ok=True)
    stand_datei.write_text(json.dumps({"gemeldet": sorted(aktuell), "zuletzt": time.strftime("%Y-%m-%d %H:%M")},
                                      ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(auftraege) - fehler} gemeldet, {fehler} Fehler.")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
