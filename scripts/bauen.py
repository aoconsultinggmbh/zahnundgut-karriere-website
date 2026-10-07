#!/usr/bin/env python3
"""
bauen.py – baut aus kunde.json und stellen/*.json alles, was Stellen betrifft:

  website/stellen/<kennung>.html      eine Seite je Stelle (mit JobPosting-JSON-LD)
  website/index.html                  Stellenliste zwischen <!-- STELLEN:ANFANG --> und <!-- STELLEN:ENDE -->
  website/assets/css/ci.css           Farben und Schriften aus kunde.json
  website/sitemap.xml                 alle Seiten, Stellen mit lastmod
  website/indeed-feed.xml             XML-Feed im Indeed-Format
  website/bewerbung-konfiguration.php Empfänger je Stelle (liest bewerbung-senden.php, nie der Browser)
  website/stellen.json                Liste für Prüfungen und Kollegen
  website/robots.txt                  mit Sitemap-Zeile der Live-Domain
  website/assets/js/konfiguration.js  Matomo-Kennung und Domain für die Skripte

Aufruf:  python3 scripts/bauen.py            (im Projektordner)
         python3 scripts/bauen.py --projekt /pfad/zum/projekt

Nur Python-Standardbibliothek, keine Installation nötig. Läuft auf dem Mac und in GitHub Actions.
Alle Texte kommen aus den JSON-Dateien – das Skript erfindet nichts.
"""
import argparse
import html
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

MARKER_ANFANG = "<!-- STELLEN:ANFANG -->"
MARKER_ENDE = "<!-- STELLEN:ENDE -->"
GENERIERT = "generiert von scripts/bauen.py"

STATUS_TEXT = {
    "aktiv": "Offene Stelle",
    "initiativ": "Aktuell besetzt, Initiativbewerbung willkommen",
}
BESCHAEFTIGUNG_TEXT = {
    "VOLLZEIT": "Vollzeit", "TEILZEIT": "Teilzeit", "AUSBILDUNG": "Ausbildung",
    "MINIJOB": "Minijob", "BEFRISTET": "befristet", "PRAKTIKUM": "Praktikum",
    "WERKSTUDENT": "Werkstudent",
}
# Google-Schema-Werte für employmentType
BESCHAEFTIGUNG_SCHEMA = {
    "VOLLZEIT": "FULL_TIME", "TEILZEIT": "PART_TIME", "AUSBILDUNG": "INTERN",
    "MINIJOB": "PART_TIME", "BEFRISTET": "TEMPORARY", "PRAKTIKUM": "INTERN",
    "WERKSTUDENT": "PART_TIME",
}
INDEED_JOBTYPE = {
    "VOLLZEIT": "fulltime", "TEILZEIT": "parttime", "AUSBILDUNG": "internship",
    "MINIJOB": "parttime", "BEFRISTET": "contract", "PRAKTIKUM": "internship",
    "WERKSTUDENT": "parttime",
}
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]


def lesbar(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day}. {MONATE[d.month - 1]} {d.year}"


def kuerzen(text: str, maximum: int) -> str:
    """Schneidet am Wortende ab – eine abgeschnittene Meta-Beschreibung sieht in Google schlampig aus."""
    if len(text) <= maximum:
        return text
    return text[:maximum - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def fuellen(vorlage: str, werte: dict) -> str:
    """{{{x}}} = roh (fertiges HTML), {{x}} = escaped. Unbekannte Platzhalter bleiben sichtbar stehen,
    damit sie beim Prüfen auffallen statt leise zu verschwinden."""
    def roh(m):
        k = m.group(1)
        return str(werte[k]) if k in werte else m.group(0)

    def sicher(m):
        k = m.group(1)
        return esc(werte[k]) if k in werte else m.group(0)

    vorlage = re.sub(r"\{\{\{(\w+)\}\}\}", roh, vorlage)
    return re.sub(r"\{\{(\w+)\}\}", sicher, vorlage)


def liste_html(eintraege) -> str:
    return "".join(f"<li>{esc(e)}</li>" for e in (eintraege or []))


def text_zu_html(absatz: str) -> str:
    return "".join(f"<p>{esc(a.strip())}</p>" for a in (absatz or "").split("\n\n") if a.strip())


def lade_json(pfad: Path) -> dict:
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FEHLER: {pfad} ist kein gültiges JSON: {e}")


def lade_stellen(ordner: Path, fehler: list) -> list:
    stellen = []
    for pfad in sorted(ordner.glob("*.json")):
        if pfad.name.startswith("_"):
            continue
        s = lade_json(pfad)
        if pfad.stem != s.get("kennung"):
            fehler.append(f"{pfad.name}: Dateiname und kennung '{s.get('kennung')}' stimmen nicht überein")
        if s.get("kennung", "").startswith("beispiel"):
            fehler.append(f"{pfad.name}: Beispiel-Stelle noch im Projekt – umbenennen oder löschen")
        if s.get("status") not in ("aktiv", "initiativ", "pausiert"):
            fehler.append(f"{pfad.name}: status muss aktiv, initiativ oder pausiert sein")
        for pflicht in ("titel", "titel_kurz", "standort", "beschaeftigungsart", "kurz", "einleitung",
                        "aufgaben", "profil", "veroeffentlicht", "gueltig_bis"):
            if not s.get(pflicht):
                fehler.append(f"{pfad.name}: Pflichtfeld '{pflicht}' fehlt oder ist leer")
        stellen.append(s)
    return stellen


def jobposting(k: dict, s: dict, st: dict, url: str, basis: str) -> dict:
    beschreibung = (
        text_zu_html(s["einleitung"])
        + "<h3>Dein Aufgabenbereich</h3><ul>" + liste_html(s["aufgaben"]) + "</ul>"
        + "<h3>Dein Profil</h3><ul>" + liste_html(s["profil"]) + "</ul>"
        + "<h3>Wir bieten</h3><ul>" + liste_html(s["wir_bieten"]) + "</ul>"
    )
    if s.get("status") == "initiativ":
        beschreibung = "<p><strong>Diese Stelle ist aktuell besetzt. Initiativbewerbungen sind ausdrücklich willkommen.</strong></p>" + beschreibung
    org = {
        "@type": "Organization",
        "name": k["firma"],
        "sameAs": k.get("hauptseite") or basis,
    }
    if k.get("ci", {}).get("logo"):
        org["logo"] = f"{basis}/{k['ci']['logo']}"
    jp = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": s["titel"],
        "description": beschreibung,
        "identifier": {"@type": "PropertyValue", "name": k["firma"], "value": s["kennung"]},
        "datePosted": s["veroeffentlicht"],
        "validThrough": f"{s['gueltig_bis']}T23:59:59+02:00",
        "employmentType": [BESCHAEFTIGUNG_SCHEMA[b] for b in s["beschaeftigungsart"]],
        "hiringOrganization": org,
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": st["strasse"],
                "addressLocality": st["ort"],
                "postalCode": st["plz"],
                "addressRegion": st["region"],
                "addressCountry": st.get("land", "DE"),
            },
        },
        "directApply": True,
        "url": url,
    }
    g = s.get("gehalt") or {}
    if g.get("min") or g.get("max"):
        wert = {"@type": "QuantitativeValue", "unitText": g.get("einheit", "MONTH")}
        if g.get("min"):
            wert["minValue"] = g["min"]
        if g.get("max"):
            wert["maxValue"] = g["max"]
        if g.get("min") and not g.get("max"):
            wert["value"] = g["min"]
        jp["baseSalary"] = {"@type": "MonetaryAmount", "currency": g.get("waehrung", "EUR"), "value": wert}
    if s.get("qualifikation_erforderlich"):
        jp["qualifications"] = s["qualifikation_erforderlich"]
    if s.get("erfahrung_monate"):
        jp["experienceRequirements"] = {"@type": "OccupationalExperienceRequirements",
                                        "monthsOfExperience": s["erfahrung_monate"]}
    return jp


def wa_text(s: dict) -> str:
    from urllib.parse import quote
    return esc(quote(f"Hallo, ich interessiere mich für die Stelle {s['titel_kurz']}."))


def zusatzfragen_html(fragen) -> str:
    teile = []
    for f in fragen or []:
        name, frage = f["name"], f["frage"]
        pflicht = " required" if f.get("pflicht") else ""
        stern = " *" if f.get("pflicht") else ""
        if f.get("typ") == "auswahl":
            opts = "".join(f'<option value="{esc(o)}">{esc(o)}</option>' for o in f.get("optionen", []))
            teile.append(
                f'<div class="feld"><label for="zf-{esc(name)}">{esc(frage)}{stern}</label>'
                f'<select id="zf-{esc(name)}" name="zusatz[{esc(name)}]"{pflicht}>'
                f'<option value="">Bitte wählen</option>{opts}</select></div>')
        elif f.get("typ") == "janein":
            teile.append(
                f'<fieldset class="feld"><legend>{esc(frage)}{stern}</legend>'
                f'<label><input type="radio" name="zusatz[{esc(name)}]" value="ja"{pflicht}> Ja</label> '
                f'<label><input type="radio" name="zusatz[{esc(name)}]" value="nein"> Nein</label></fieldset>')
        else:
            teile.append(
                f'<div class="feld"><label for="zf-{esc(name)}">{esc(frage)}{stern}</label>'
                f'<input id="zf-{esc(name)}" name="zusatz[{esc(name)}]" type="text"{pflicht}></div>')
    return "\n".join(teile)


RAHMEN_KOPF = ("<!-- RAHMEN:KOPF -->", "<!-- /RAHMEN:KOPF -->")
RAHMEN_FUSS = ("<!-- RAHMEN:FUSS -->", "<!-- /RAHMEN:FUSS -->")


def nebenseiten_rahmen(web: Path, fehler: list) -> None:
    """Kopfzeile (Menü) und Fuß aus index.html in danke.html, fehler.html und rechtliches/*.html einsetzen.
    Beim ersten Lauf werden sie nach <body> bzw. vor </body> eingefügt, danach zwischen den Markern erneuert."""
    txt = (web / "index.html").read_text(encoding="utf-8")
    mk = re.search(r"<header class=\"kopf[^\"]*\">.*?</header>", txt, flags=re.S)
    mf = re.search(r"<footer class=\"fuss\">.*?</footer>", txt, flags=re.S)
    mw = re.search(r"<a class=\"whatsapp-schwebend\".*?</a>", txt, flags=re.S)
    if not (mk and mf):
        fehler.append("website/index.html: <header class=\"kopf\"> oder <footer class=\"fuss\"> nicht gefunden")
        return
    seiten = [web / "danke.html", web / "fehler.html"] + sorted(web.glob("rechtliches/*.html"))
    for seite in seiten:
        if not seite.exists():
            continue
        praefix = "../" if seite.parent != web else ""

        def pfade(h: str) -> str:
            h = re.sub(r'href="#([^"]*)"', lambda m: f'href="{praefix}index.html#{m.group(1)}"', h)
            h = h.replace('href="index.html"', f'href="{praefix}index.html"')
            h = h.replace('src="assets/', f'src="{praefix}assets/')
            h = h.replace('href="rechtliches/', f'href="{praefix}rechtliches/')
            return h

        kopf = f'{RAHMEN_KOPF[0]}\n<a class="skip" href="#inhalt">Zum Inhalt springen</a>\n{pfade(weisser_kopf(mk.group(0)))}\n{RAHMEN_KOPF[1]}'
        fuss = (f'{RAHMEN_FUSS[0]}\n{pfade(mf.group(0))}\n{mw.group(0) if mw else ""}\n' + skripte(praefix) + f'\n{RAHMEN_FUSS[1]}')
        s = seite.read_text(encoding="utf-8")
        if RAHMEN_KOPF[0] in s:
            s = re.sub(re.escape(RAHMEN_KOPF[0]) + r".*?" + re.escape(RAHMEN_KOPF[1]), lambda m: kopf, s, flags=re.S)
        else:
            s = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + kopf, s, count=1)
            s = s.replace('<main class="wrap"', '<main id="inhalt" class="wrap"', 1) if 'id="inhalt"' not in s else s
        if RAHMEN_FUSS[0] in s:
            s = re.sub(re.escape(RAHMEN_FUSS[0]) + r".*?" + re.escape(RAHMEN_FUSS[1]), lambda m: fuss, s, flags=re.S)
        else:
            s = s.replace("</body>", fuss + "\n</body>", 1)
        seite.write_text(s, encoding="utf-8")


def weisser_kopf(h: str) -> str:
    """Nur die Startseite hat den durchsichtigen Kopf über dem Foto, alle anderen Seiten den weißen."""
    return re.sub(r'<header class="kopf[^"]*">', '<header class="kopf">', h, count=1)


def skripte(praefix: str) -> str:
    """Skripte am Seitenende, auf allen Seiten gleich (AO-Standard: Einwilligung und Barrierefreiheit)."""
    return "\n".join([
        f'<script src="{praefix}assets/js/konfiguration.js"></script>',
        f'<script src="{praefix}assets/js/ao-konfiguration.js" defer></script>',
        f'<script src="{praefix}assets/js/einwilligung.js" defer></script>',
        f'<script src="{praefix}assets/js/messung.js" defer></script>',
        f'<script src="{praefix}assets/js/barrierefreiheit.js" defer></script>',
        f'<script src="{praefix}assets/js/app.js" defer></script>',
        f'<script src="{praefix}assets/js/statistik.js" defer></script>'])


def versionen(web: Path) -> None:
    """Hängt an CSS- und JS-Adressen ?v=<Prüfsumme>, damit Browser nach Änderungen nichts Altes aus dem Zwischenspeicher zeigen."""
    import hashlib
    cache = {}

    def v(datei: str) -> str:
        if datei not in cache:
            p = web / "assets" / datei
            cache[datei] = hashlib.md5(p.read_bytes()).hexdigest()[:8] if p.exists() else ""
        return cache[datei]

    muster = re.compile(r'((?:\.\./|/)?assets/((?:css|js)/[\w.-]+\.(?:css|js)))(?:\?v=\w*)?"')
    for seite in web.rglob("*.html"):
        t = seite.read_text(encoding="utf-8")
        neu = muster.sub(lambda m: f'{m.group(1)}?v={v(m.group(2))}"' if v(m.group(2)) else m.group(0), t)
        if neu != t:
            seite.write_text(neu, encoding="utf-8")


def stellen_rahmen(web: Path) -> tuple:
    """Kopf und Fuß der Startseite für die Stellenseiten (Unterordner stellen/ → Pfade mit ../)."""
    txt = (web / "index.html").read_text(encoding="utf-8")
    mk = re.search(r"<header class=\"kopf[^\"]*\">.*?</header>", txt, flags=re.S)
    mf = re.search(r"<footer class=\"fuss\">.*?</footer>", txt, flags=re.S)
    mw = re.search(r"<a class=\"whatsapp-schwebend\".*?</a>", txt, flags=re.S)

    def pfade(h: str) -> str:
        h = re.sub(r'href="#([^"]*)"', lambda m: f'href="../index.html#{m.group(1)}"', h)
        h = h.replace('href="index.html', 'href="../index.html')
        h = h.replace('src="assets/', 'src="../assets/')
        h = h.replace('href="rechtliches/', 'href="../rechtliches/')
        return h
    return (pfade(weisser_kopf(mk.group(0))) if mk else "", pfade(mf.group(0)) if mf else "", mw.group(0) if mw else "")


def baue(projekt: Path) -> int:
    fehler, hinweise = [], []
    kunde = lade_json(projekt / "kunde.json")
    stellen = lade_stellen(projekt / "stellen", fehler)
    web = projekt / "website"
    vorlagen = projekt / "vorlagen"
    vorlage_stelle = (vorlagen / "stelle.html").read_text(encoding="utf-8")
    vorlage_eintrag = (vorlagen / "stellenliste-eintrag.html").read_text(encoding="utf-8")
    kopf_html, fuss_html, whatsapp_html = stellen_rahmen(web)

    basis = f"https://{kunde['domain']}"
    standorte = {st["kennung"]: st for st in kunde["standorte"]}
    bew = kunde.get("bewerbungen", {})
    heute = date.today()

    # --- ci.css ---
    ci = kunde.get("ci", {})
    (web / "assets" / "css").mkdir(parents=True, exist_ok=True)
    (web / "assets" / "css" / "ci.css").write_text(
        "/* " + GENERIERT + " aus kunde.json → ci. Nicht von Hand ändern. */\n"
        ":root{\n"
        f"  --primaer: {ci.get('farbe_primaer', '#1f2a33')};\n"
        f"  --akzent: {ci.get('farbe_akzent', '#b08d57')};\n"
        f"  --hintergrund: {ci.get('farbe_hintergrund', '#ffffff')};\n"
        f"  --text: {ci.get('farbe_text', '#1a1a1a')};\n"
        f"  --schrift-ueberschrift: \"{ci.get('schrift_ueberschrift', 'Inter')}\", system-ui, sans-serif;\n"
        f"  --schrift-text: \"{ci.get('schrift_text', 'Inter')}\", system-ui, sans-serif;\n"
        "}\n", encoding="utf-8")

    # --- alte generierte Stellenseiten entfernen (nur unsere eigenen) ---
    stellen_ordner = web / "stellen"
    stellen_ordner.mkdir(parents=True, exist_ok=True)
    for alt in stellen_ordner.glob("*.html"):
        if GENERIERT in alt.read_text(encoding="utf-8", errors="ignore"):
            alt.unlink()

    for s in stellen:
        if not s.get("wir_bieten"):
            if kunde.get("benefits_standard"):
                s["wir_bieten"] = list(kunde["benefits_standard"])
                hinweise.append(f"{s.get('kennung')}: kein eigenes wir_bieten – benefits_standard aus kunde.json übernommen")
            else:
                fehler.append(f"{s.get('kennung')}: wir_bieten fehlt und kunde.json hat kein benefits_standard")
    # Reihenfolge: offene Stellen zuerst, dann Feld "reihenfolge" (kleine Zahl = weiter oben), dann Kennung
    stellen.sort(key=lambda s: (0 if s.get("status") == "aktiv" else 1, s.get("reihenfolge", 50), s.get("kennung", "")))
    sichtbar = [s for s in stellen if s.get("status") in ("aktiv", "initiativ")]
    eintraege, sitemap_stellen, indeed_jobs, empfaenger, uebersicht = [], [], [], {}, []

    for s in sichtbar:
        st = standorte.get(s["standort"])
        if not st:
            fehler.append(f"{s['kennung']}: Standort '{s['standort']}' gibt es in kunde.json nicht")
            continue
        if date.fromisoformat(s["gueltig_bis"]) < heute:
            hinweise.append(f"{s['kennung']}: gueltig_bis liegt in der Vergangenheit – stellen-aktualisieren.py laufen lassen")
        url = f"{basis}/stellen/{s['kennung']}.html"
        arten = [BESCHAEFTIGUNG_TEXT[b] for b in s["beschaeftigungsart"]]
        empf = s.get("bewerbungen_an") or bew.get("standard_empfaenger") or []
        if not empf:
            fehler.append(f"{s['kennung']}: keine Empfängeradresse (bewerbungen_an oder bewerbungen.standard_empfaenger)")
        empfaenger[s["kennung"]] = {"empfaenger": empf, "titel": s["titel"], "standort": st["ort"]}
        ap = s.get("ansprechpartner") or kunde.get("ansprechpartner") or {}

        g = s.get("gehalt") or {}
        gehalt_fakt = ""
        if g.get("min") or g.get("max"):
            einheit = {"MONTH": "/ Monat", "YEAR": "/ Jahr", "HOUR": "/ Stunde"}.get(g.get("einheit", "MONTH"), "")
            spanne = " bis ".join(f"{v:,}".replace(",", ".") + " €" for v in (g.get("min"), g.get("max")) if v)
            gehalt_fakt = f"<div><dt>Gehalt</dt><dd>{esc(spanne)} {esc(einheit)}</dd></div>"

        werte = {
            "kopf_html": kopf_html, "fuss_html": fuss_html, "whatsapp_schwebend": whatsapp_html,
            "kennung": s["kennung"], "titel": s["titel"], "titel_kurz": s["titel_kurz"],
            "status": s["status"], "status_text": STATUS_TEXT[s["status"]],
            "marken_html": (f'<span class="marke marke-gruen">Offen</span><span class="marke marke-gruen">{esc(s.get("beginn") or "nach Vereinbarung")}</span>'
                            if s["status"] == "aktiv" else '<span class="marke marke-orange">Initiativ</span>'),
            "einleitung_html": text_zu_html(s["einleitung"]),
            # seo_titel (optional, bis etwa 60 Zeichen) geht vor: Google kürzt längere Titel ab
            "seitentitel": s["seo_titel"] if s.get("seo_titel") else f"{s['titel_kurz']} (m/w/d) in {st['ort']} | {kunde['firma']}"
            if "(m/w/d)" not in s["titel_kurz"] else f"{s['titel_kurz']} in {st['ort']} | {kunde['firma']}",
            "meta_beschreibung": kuerzen(f"{s['titel_kurz']} in {st['ort']} bei {kunde['firma']}: {s['kurz']}", 155),
            "url": url, "og_bild": f"{basis}/{s.get('bild') or kunde.get('seo', {}).get('og_bild', '')}",
            "farbe_primaer": ci.get("farbe_primaer", "#1f2a33"), "logo": ci.get("logo", "assets/img/logo.svg"),
            "firma": kunde["firma"], "kurz": s["kurz"], "einleitung": s["einleitung"],
            "standort_name": st.get("name", kunde["firma"]), "standort_strasse": st["strasse"],
            "standort_plz": st["plz"], "standort_ort": st["ort"],
            "standort_karte_link": f'<p><a href="{esc(st["google_maps"])}" rel="noopener" target="_blank">Route planen</a></p>' if st.get("google_maps") else "",
            "beschaeftigungsart_text": " / ".join(arten),
            "arbeitszeit_zusatz": f" ({s['arbeitszeit']})" if s.get("arbeitszeit") else "",
            "beginn": s.get("beginn") or "nach Vereinbarung",
            "gehalt_fakt": gehalt_fakt,
            "aufgaben_html": liste_html(s["aufgaben"]), "profil_html": liste_html(s["profil"]),
            "wir_bieten_html": liste_html(s["wir_bieten"]),
            "seitenkopf_klasse": " mit-bild" if s.get("bild") else "",
            "kopf_bild": (('<div class="seitenkopf-bild" data-parallax><picture>'
                           + (f'<source srcset="../{esc(Path(s["bild"]).with_suffix(".webp").as_posix())}" type="image/webp">'
                              if (web / Path(s["bild"]).with_suffix(".webp")).exists() else "")
                           + f'<img src="../{esc(s["bild"])}" alt="{esc(s.get("bild_alt", ""))}" width="1920" height="1080" fetchpriority="high"></picture></div>')
                          if s.get("bild") else ""),
            "whatsapp_knopf_hell": (f'<a class="knopf knopf-rand-hell" href="https://wa.me/{esc(ap["whatsapp"].lstrip("+").replace(" ", ""))}?text={wa_text(s)}" rel="noopener" target="_blank">Per WhatsApp schreiben</a>'
                                    if ap.get("whatsapp") else ""),
            "zusatzfragen_html": zusatzfragen_html(s.get("formular_zusatzfragen")),
            "max_dateien": bew.get("max_dateien", 3), "max_mb": bew.get("max_mb_je_datei", 10),
            "antwortzeit": bew.get("antwortzeit", ""),
            "empfaenger_anzeige": empf[0] if empf else "",
            "mail_betreff": html.escape(f"Bewerbung: {s['titel_kurz']}").replace(" ", "%20"),
            "branche": kunde.get("branche", ""),
            "standort_region_html": f"<br>{esc(st['region'])}" if st.get("region") else "",
            # Ansprechpartner als Karte in der rechten Spalte (Vorbild ao-karriere.de): rundes Foto, Name, Rolle, Mail-Knopf, Telefon
            "ansprechpartner_block": (
                '<div class="ansprech-karte">'
                '<p class="klein-titel">' + esc(ap.get("titel") or "Deine Ansprechpartnerin") + '</p>'
                + (f'<img src="../{esc(ap["foto"])}" alt="{esc(ap.get("name"))}" width="116" height="116" loading="lazy">' if ap.get("foto") else "")
                + f'<p class="ansprech-name"><strong>{esc(ap.get("name"))}</strong>'
                + (f'<br><span>{esc(ap["rolle"])}</span>' if ap.get("rolle") else "") + "</p>"
                + '<a class="knopf" href="#bewerben">Jetzt bewerben</a>'
                + (f'<a class="knopf knopf-rand" href="https://wa.me/{esc(ap["whatsapp"].lstrip("+").replace(" ", ""))}?text={wa_text(s)}" rel="noopener" target="_blank">Per WhatsApp schreiben</a>' if ap.get("whatsapp") else "")
                + (f'<p class="ansprech-kontakt"><a href="tel:+49{esc(ap["telefon"].replace(" ", "").lstrip("0"))}">Telefon {esc(ap["telefon"])}</a></p>' if ap.get("telefon") else "")
                + (f'<p class="ansprech-kontakt"><a href="mailto:{esc(ap["email"])}">{esc(ap["email"])}</a></p>' if ap.get("email") else "")
                + "</div>") if ap.get("name") else "",
            "veroeffentlicht_lesbar": lesbar(s["veroeffentlicht"]), "gueltig_bis_lesbar": lesbar(s["gueltig_bis"]),
            "jsonld": json.dumps(jobposting(kunde, s, st, url, basis), ensure_ascii=False, indent=2),
            "jsonld_breadcrumb": json.dumps({
                "@context": "https://schema.org", "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Karriere", "item": basis + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Offene Stellen", "item": basis + "/#stellen"},
                    {"@type": "ListItem", "position": 3, "name": s["titel_kurz"], "item": url},
                ]}, ensure_ascii=False),
        }
        seite = fuellen(vorlage_stelle, werte)
        offen = re.findall(r"\{\{\{?(\w+)\}?\}\}", seite)
        if offen:
            fehler.append(f"{s['kennung']}: Platzhalter ohne Wert in der Vorlage: {sorted(set(offen))}")
        (stellen_ordner / f"{s['kennung']}.html").write_text(seite, encoding="utf-8")

        eintraege.append(fuellen(vorlage_eintrag, werte))
        sitemap_stellen.append((url, s["veroeffentlicht"]))
        if kunde.get("google_for_jobs", {}).get("indeed_feed", True):
            indeed_jobs.append(
                "  <job>\n"
                f"    <title><![CDATA[{s['titel']}]]></title>\n"
                f"    <date><![CDATA[{datetime.fromisoformat(s['veroeffentlicht']).strftime('%a, %d %b %Y 09:00:00 +0200')}]]></date>\n"
                f"    <referencenumber><![CDATA[{s['kennung']}]]></referencenumber>\n"
                f"    <url><![CDATA[{url}?utm_source=indeed]]></url>\n"
                f"    <company><![CDATA[{kunde['firma']}]]></company>\n"
                f"    <city><![CDATA[{st['ort']}]]></city>\n"
                f"    <state><![CDATA[{st['region']}]]></state>\n"
                f"    <country><![CDATA[{st.get('land', 'DE')}]]></country>\n"
                f"    <postalcode><![CDATA[{st['plz']}]]></postalcode>\n"
                f"    <streetaddress><![CDATA[{st['strasse']}]]></streetaddress>\n"
                f"    <description><![CDATA[{jobposting(kunde, s, st, url, basis)['description']}]]></description>\n"
                f"    <jobtype><![CDATA[{', '.join(INDEED_JOBTYPE[b] for b in s['beschaeftigungsart'])}]]></jobtype>\n"
                f"    <category><![CDATA[{kunde.get('branche', '')}]]></category>\n"
                f"    <expirationdate><![CDATA[{s['gueltig_bis']}]]></expirationdate>\n"
                "  </job>\n")
        uebersicht.append({"kennung": s["kennung"], "titel": s["titel"], "status": s["status"],
                           "ort": st["ort"], "url": url, "veroeffentlicht": s["veroeffentlicht"],
                           "gueltig_bis": s["gueltig_bis"], "empfaenger": empf})

    # --- Stellenliste in index.html ---
    index = web / "index.html"
    if index.exists():
        txt = index.read_text(encoding="utf-8")
        if MARKER_ANFANG in txt and MARKER_ENDE in txt:
            block = "\n".join(eintraege) if eintraege else '<p class="keine-stellen">Aktuell sind alle Stellen besetzt. Wir freuen uns über Initiativbewerbungen.</p>'
            itemlist = json.dumps({
                "@context": "https://schema.org", "@type": "ItemList",
                "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": u["url"]} for i, u in enumerate(uebersicht)],
            }, ensure_ascii=False)
            neu = re.sub(
                re.escape(MARKER_ANFANG) + r".*?" + re.escape(MARKER_ENDE),
                lambda m: f"{MARKER_ANFANG}\n<!-- {GENERIERT} – Änderungen in stellen/*.json -->\n{block}\n"
                          f'<script type="application/ld+json">{itemlist}</script>\n{MARKER_ENDE}',
                txt, flags=re.S)
            index.write_text(neu, encoding="utf-8")
        else:
            fehler.append("website/index.html hat keine Marker <!-- STELLEN:ANFANG --> / <!-- STELLEN:ENDE -->")
    else:
        fehler.append("website/index.html fehlt")

    # --- Kopf und Fuß der Startseite auf die Nebenseiten übertragen (Impressum, Datenschutz, Danke …) ---
    # Jede Seite der Karriereseite trägt Menü und Fuß der Startseite – sonst wirken Rechtsseiten wie eine fremde Seite
    # und der Besucher findet nicht zurück. Quelle ist immer index.html, damit nichts auseinanderläuft.
    if index.exists():
        nebenseiten_rahmen(web, fehler)

    # --- sitemap.xml ---
    feste = [f"{basis}/"] + [f"{basis}/{p.relative_to(web).as_posix()}" for p in sorted(web.glob("rechtliches/*.html"))]
    heute_iso = heute.isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{esc(u)}</loc><lastmod>{heute_iso}</lastmod></url>" for u in feste]
    sm += [f"  <url><loc>{esc(u)}</loc><lastmod>{d}</lastmod><changefreq>monthly</changefreq></url>" for u, d in sitemap_stellen]
    sm.append("</urlset>\n")
    (web / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # --- indeed-feed.xml ---
    if kunde.get("google_for_jobs", {}).get("indeed_feed", True):
        (web / "indeed-feed.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n<source>\n'
            f"  <publisher><![CDATA[{kunde['firma']}]]></publisher>\n"
            f"  <publisherurl><![CDATA[{basis}]]></publisherurl>\n"
            f"  <lastBuildDate><![CDATA[{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0200')}]]></lastBuildDate>\n"
            + "".join(indeed_jobs) + "</source>\n", encoding="utf-8")

    # --- Empfänger-Konfiguration für PHP (liegt in website/, ist aber PHP → nicht von außen lesbar) ---
    php = ["<?php", f"// {GENERIERT} – Empfänger je Stelle. Nicht von Hand ändern.", "return ["]
    php.append(f"  '_absender' => {json.dumps(bew.get('absender', ''), ensure_ascii=False)},")
    php.append(f"  '_absender_name' => {json.dumps(bew.get('absender_name', kunde['firma']), ensure_ascii=False)},")
    php.append(f"  '_firma' => {json.dumps(kunde['firma'], ensure_ascii=False)},")
    php.append(f"  '_antwortzeit' => {json.dumps(bew.get('antwortzeit', ''), ensure_ascii=False)},")
    php.append(f"  '_max_dateien' => {int(bew.get('max_dateien', 3))},")
    php.append(f"  '_max_mb' => {int(bew.get('max_mb_je_datei', 10))},")
    php.append(f"  '_loeschfrist_monate' => {int(bew.get('loeschfrist_monate', 6))},")
    for kennung, e in empfaenger.items():
        adressen = ", ".join(json.dumps(a, ensure_ascii=False) for a in e["empfaenger"])
        php.append(f"  {json.dumps(kennung)} => ['empfaenger' => [{adressen}], 'titel' => {json.dumps(e['titel'], ensure_ascii=False)}, 'standort' => {json.dumps(e['standort'], ensure_ascii=False)}],")
    php.append("];\n")
    (web / "bewerbung-konfiguration.php").write_text("\n".join(php), encoding="utf-8")

    (web / "stellen.json").write_text(json.dumps({"stand": heute_iso, "stellen": uebersicht}, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- robots.txt (Sitemap-Zeile mit der Live-Domain; der Vorschau-Ablauf überschreibt sie mit Disallow) ---
    (web / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nDisallow: /bewerbung-senden.php\nDisallow: /bewerbung-konfiguration.php\n\n"
        f"Sitemap: {basis}/sitemap.xml\n", encoding="utf-8")

    # --- konfiguration.js (Matomo-Kennung u. a. für statistik.js) ---
    stat = kunde.get("statistik", {})
    (web / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (web / "assets" / "js" / "konfiguration.js").write_text(
        f"/* {GENERIERT} aus kunde.json. Nicht von Hand ändern. */\n"
        "window.KARRIERE = " + json.dumps({"matomoId": str(stat.get("matomo_id", "") or ""),
                                           "matomoUrl": stat.get("matomo_url", "https://statistik.ao-consult.de/"),
                                           "domain": kunde["domain"]}, ensure_ascii=False) + ";\n", encoding="utf-8")

    # --- Versionsnummern an CSS/JS (gegen alte Dateien im Zwischenspeicher) ---
    versionen(web)

    # --- Bericht ---
    print(f"Gebaut: {len(sichtbar)} Stellen sichtbar ({sum(1 for s in sichtbar if s['status']=='aktiv')} aktiv, "
          f"{sum(1 for s in sichtbar if s['status']=='initiativ')} initiativ), "
          f"{len(stellen) - len(sichtbar)} pausiert.")
    for h in hinweise:
        print("HINWEIS:", h)
    for f in fehler:
        print("FEHLER:", f)
    return 1 if fehler else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projekt", default=".", help="Projektordner (enthält kunde.json, stellen/, website/, vorlagen/)")
    args = ap.parse_args()
    sys.exit(baue(Path(args.projekt).resolve()))
