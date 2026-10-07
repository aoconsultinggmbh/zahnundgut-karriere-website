#!/usr/bin/env python3
"""
pruefen.py – prüft die gebaute Karriereseite, bevor sie hochgeladen wird.

Prüft:
  1. Jede Stellenseite hat genau ein JobPosting-JSON-LD mit allen Pflichtfeldern von Google
     (title, description, datePosted, validThrough, hiringOrganization, jobLocation) und validThrough liegt in der Zukunft.
  2. Ortsnamen-Konsistenz: Kein Ortsname eines anderen Projekts/Standorts im <title> oder in der Beschreibung
     (der Klassiker: "ZFA Job bei Whiteblick Bruchsal" – kopiert aus einer anderen Seite).
  3. Keine externen Schriften, Skripte oder Tracker (Regel der AO Consulting: alles liegt im Paket).
  4. Interne Links zeigen auf vorhandene Dateien; Bilder vorhanden; alt-Texte gesetzt.
  5. Keine übrig gebliebenen Platzhalter ({{...}}, "Muster", "Lorem", "TODO", "XXX").
  6. Jede Seite hat <title>, <meta name="description">, canonical, lang="de", genau ein <h1>.
  7. Formular: action zeigt auf bewerbung-senden.php, Honigtopf und Datenschutz-Haken vorhanden.
  8. Datenschutz erwähnt Bewerberdaten, Löschfrist und den Hoster; Impressum vorhanden.
  9. robots.txt, sitemap.xml, indeed-feed.xml vorhanden und gültig.

Aufruf: python3 scripts/pruefen.py [--projekt PFAD] [--fremde-orte Bruchsal,Karlsruhe]
Rückgabe 1 bei Fehlern (damit GitHub-Abläufe rot werden), Hinweise sind nur Ausgabe.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ERLAUBTE_FREMDHOSTS = {"statistik.ao-consult.de"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projekt", default=".")
    ap.add_argument("--fremde-orte", default="", help="Kommagetrennt: Orte, die NICHT vorkommen dürfen (z. B. Orte anderer Kunden)")
    a = ap.parse_args()
    projekt = Path(a.projekt).resolve()
    web = projekt / "website"
    kunde = json.loads((projekt / "kunde.json").read_text(encoding="utf-8"))
    eigene_orte = {st["ort"] for st in kunde["standorte"]}
    fremde = {o.strip() for o in a.fremde_orte.split(",") if o.strip()} - eigene_orte
    fehler, hinweise = [], []
    seiten = sorted(p for p in web.rglob("*.html") if "_alte-dateinamen" not in p.parts)

    for seite in seiten:
        rel = seite.relative_to(web).as_posix()
        t = seite.read_text(encoding="utf-8")
        t = re.sub(r"<!--.*?-->", "", t, flags=re.S)   # Kommentare sind keine Inhalte (sonst zählen auskommentierte <img> als fehlend)
        ist_stelle = seite.parent.name == "stellen"

        # 6. Grundgerüst
        if 'lang="de"' not in t[:300]:
            fehler.append(f"{rel}: <html lang=\"de\"> fehlt")
        if not re.search(r"<title>[^<]{5,}</title>", t):
            fehler.append(f"{rel}: <title> fehlt oder zu kurz")
        if not re.search(r'<meta name="description" content="[^"]{20,}"', t):
            fehler.append(f"{rel}: meta description fehlt oder zu kurz")
        if '<link rel="canonical"' not in t:
            fehler.append(f"{rel}: canonical fehlt")
        h1 = len(re.findall(r"<h1[\s>]", t))
        if h1 != 1:
            fehler.append(f"{rel}: {h1} <h1> gefunden, erwartet genau eins")

        # 5. Platzhalter
        for muster in (r"\{\{\{?\w+\}?\}\}", r"\bLorem\b", r"\bTODO\b", r"\bXXX\b", r"Musterpraxis", r"Musterstraße", r"JJJJ-MM-TT",
                       r"\[(?:[A-ZÄÖÜ][^\]\n]{1,60}|\+49…|domain|alte-domain|kunde|jobs@|farbe_primaer)\]"):
            if re.search(muster, t):
                fehler.append(f"{rel}: Platzhalter gefunden ({muster})")

        # 2. fremde Orte
        for ort in fremde:
            if seite.parent.name != "rechtliches" and re.search(rf"\b{re.escape(ort)}\b", t):
                fehler.append(f"{rel}: fremder Ortsname '{ort}' – aus einer anderen Seite kopiert?")

        # 3. externe Ressourcen
        for m in re.finditer(r'(?:src|href)="(https?://[^"]+)"', t):
            url = m.group(1)
            try:
                host = urlparse(url).hostname or ""
            except ValueError:
                host = ""
            tag_anfang = t.rfind("<", 0, m.start())
            tag = t[tag_anfang:m.end()]
            ist_ressource = tag.startswith("<script") or (tag.startswith("<link") and "stylesheet" in tag)
            if ist_ressource and host not in ERLAUBTE_FREMDHOSTS and host != kunde["domain"]:
                fehler.append(f"{rel}: externe Ressource {url} – Schriften/Skripte gehören ins Paket")
            if "fonts.googleapis" in url or "googletagmanager" in url or "google-analytics" in url:
                fehler.append(f"{rel}: {url} ist nicht erlaubt (Datenschutz)")

        # 4. interne Links und Bilder
        for m in re.finditer(r'(?:href|src)="([^"#:?][^"#?]*)"', t):
            ziel = m.group(1)
            if ziel.startswith(("mailto", "tel", "data:")) or "://" in ziel:
                continue
            pfad = (web / ziel.lstrip("/")).resolve() if ziel.startswith("/") else (seite.parent / ziel).resolve()
            if pfad.is_dir():
                pfad = pfad / "index.html"
            if not pfad.exists():
                fehler.append(f"{rel}: Link/Bild zeigt ins Leere: {ziel}")
        for m in re.finditer(r"<img\b[^>]*>", t):
            if 'alt="' not in m.group(0):
                fehler.append(f"{rel}: <img> ohne alt-Text")

        # 1. JobPosting
        ld = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', t, flags=re.S)
        jobpostings = []
        for block in ld:
            try:
                d = json.loads(block)
            except json.JSONDecodeError as e:
                fehler.append(f"{rel}: JSON-LD ungültig: {e}")
                continue
            if d.get("@type") == "JobPosting":
                jobpostings.append(d)
        if ist_stelle:
            if len(jobpostings) != 1:
                fehler.append(f"{rel}: {len(jobpostings)} JobPosting-Blöcke, erwartet genau einer")
            for jp in jobpostings:
                for pflicht in ("title", "description", "datePosted", "validThrough", "hiringOrganization", "jobLocation"):
                    if not jp.get(pflicht):
                        fehler.append(f"{rel}: JobPosting ohne {pflicht}")
                adr = (jp.get("jobLocation") or {}).get("address") or {}
                for pflicht in ("streetAddress", "addressLocality", "postalCode", "addressCountry"):
                    if not adr.get(pflicht):
                        fehler.append(f"{rel}: JobPosting-Adresse ohne {pflicht}")
                try:
                    if date.fromisoformat(jp["validThrough"][:10]) < date.today():
                        fehler.append(f"{rel}: validThrough {jp['validThrough'][:10]} ist abgelaufen")
                    if date.fromisoformat(jp["datePosted"][:10]) > date.today():
                        fehler.append(f"{rel}: datePosted {jp['datePosted'][:10]} liegt in der Zukunft – Google wertet das als ungültig")
                except (KeyError, ValueError):
                    pass
                if not jp.get("baseSalary"):
                    hinweise.append(f"{rel}: kein Gehalt – Google spielt Anzeigen mit Gehalt besser aus (mit Kunde klären)")
                if len(re.sub("<[^>]+>", "", jp.get("description", ""))) < 300:
                    hinweise.append(f"{rel}: Beschreibung sehr kurz (<300 Zeichen) – Google und Indeed bevorzugen vollständige Texte")
            # 7. Formular
            if 'action="../bewerbung-senden.php"' not in t:
                fehler.append(f"{rel}: Formular zeigt nicht auf bewerbung-senden.php")
            if 'name="webseite"' not in t or 'name="datenschutz"' not in t:
                fehler.append(f"{rel}: Honigtopf oder Datenschutz-Haken fehlt")
        elif jobpostings:
            fehler.append(f"{rel}: JobPosting auf einer Nicht-Stellenseite – Google wertet das als Fehler")

    # 8. Rechtliches
    ds = web / "rechtliches" / "datenschutz.html"
    if not ds.exists():
        fehler.append("rechtliches/datenschutz.html fehlt")
    else:
        d = ds.read_text(encoding="utf-8")
        for begriff in ("Bewerb", "gelöscht", "ALL-INKL"):
            if begriff not in d:
                fehler.append(f"datenschutz.html erwähnt '{begriff}' nicht (Bewerberdaten, Löschfrist, Hoster müssen drinstehen)")
        if kunde.get("statistik", {}).get("matomo_id") and "Matomo" not in d:
            fehler.append("datenschutz.html: Matomo ist aktiv, aber nicht erwähnt")
    if not (web / "rechtliches" / "impressum.html").exists():
        fehler.append("rechtliches/impressum.html fehlt")

    # 9. Dateien
    for name in ("robots.txt", "sitemap.xml", "bewerbung-senden.php", "bewerbung-konfiguration.php", ".htaccess"):
        if not (web / name).exists():
            fehler.append(f"website/{name} fehlt")
    for xmlname in ("sitemap.xml", "indeed-feed.xml"):
        p = web / xmlname
        if p.exists():
            try:
                ET.parse(p)
            except ET.ParseError as e:
                fehler.append(f"{xmlname} ist kein gültiges XML: {e}")
    if (web / "robots.txt").exists():
        r = (web / "robots.txt").read_text(encoding="utf-8")
        if "Sitemap:" not in r:
            fehler.append("robots.txt ohne Sitemap-Zeile")
        if "Disallow: /" in r.replace("Disallow: /bewerbung", ""):
            hinweise.append("robots.txt sperrt etwas – vor dem Livegang prüfen, dass das gewollt ist")

    print(f"{len(seiten)} Seiten geprüft – {len(fehler)} Fehler, {len(hinweise)} Hinweise")
    for h in hinweise:
        print("HINWEIS:", h)
    for f in fehler:
        print("FEHLER:", f)
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
