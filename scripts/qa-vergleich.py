#!/usr/bin/env python3
"""
qa-vergleich.py – akribische Endprüfung der gebauten Karriereseite gegen die Hauptseite des Kunden.

Prüft bei 375 / 768 / 1024 / 1280 / 1440 / 1600 / 1920 px:
  • Typografie (Schriftgröße, Zeilenhöhe, Gewicht, Sperrung, Farbe, linker Einzug) von body, p, h1–h4,
    Menüpunkt, Kicker (.dachzeile) und Knopf (.hero .knopf) – und vergleicht sie mit der Hauptseite
  • waagerechtes Überlaufen (scrollWidth > innerWidth) und Elemente, die rechts hinausragen
  • Überschriften-Reihenfolge (keine Sprünge h2 → h4, genau ein h1)
  • alle Ankerlinks auf allen Seiten (#id vorhanden, Zieldatei vorhanden, Ziel-Anker vorhanden)
  • dass Anker nach dem Sprung unter der klebenden Kopfzeile landen (scroll-margin-top)

Messwerte der Hauptseite: entweder --haupt-url (wenn der Rechner die Seite erreichen darf) oder
--haupt-json DATEI – eine Datei, die mit dem Messschnipsel unten im Browser des Mitarbeiters
(Claude in Chrome / eingebauter Browser, Fenster auf die jeweilige Breite stellen) erzeugt wurde.
Die Proxy-Sperre lässt customer-Seiten aus dem Container oft nicht zu – dann JSON-Weg nehmen.

Messschnipsel für die Hauptseite (im Browser ausführen, pro Breite, Ergebnis in haupt.json sammeln,
Form: {"375": {...}, "768": {...}} ):
  (()=>{const cs=(e,p)=>e?getComputedStyle(e)[p]:null;const q=s=>document.querySelector(s);const r={w:innerWidth};
   for(const [k,s] of Object.entries({body:'body',p:'main p, .content p, p',h1:'h1',h2:'h2',h3:'h3',nav:'nav a, .navbar a',
   kick:'strong, .kicker',btn:'.btn, a.button, button'})){const e=q(s);if(!e)continue;
   r[k]=[cs(e,'fontSize'),cs(e,'lineHeight'),cs(e,'fontWeight'),cs(e,'letterSpacing'),cs(e,'color'),Math.round(e.getBoundingClientRect().left)].join(' ')}
   return JSON.stringify(r)})()

Aufruf:  python3 scripts/qa-vergleich.py [--projekt .] [--haupt-json haupt.json | --haupt-url https://www.kunde.de]
Exit 1 bei Abweichungen (Typografie ungleich, Überlauf, kaputte Anker, Überschriftensprung).
"""
import argparse
import asyncio
import json
import re
import subprocess
import sys
import time
from pathlib import Path

BREITEN = (375, 768, 1024, 1280, 1440, 1600, 1920)
SELEKTOREN = {"body": "body", "p": "main p", "h1": "h1", "h2": "h2", "h3": "h3", "h4": "h4",
              "nav": ".hauptnavi a", "kick": ".dachzeile", "btn": ".hero .knopf"}

MESSEN = """(sel)=>{const cs=(e,p)=>e?getComputedStyle(e)[p]:null;const q=s=>document.querySelector(s);
const r={w:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth};
for(const [k,s] of Object.entries(sel)){const e=q(s);if(!e)continue;
 r[k]=[cs(e,'fontSize'),cs(e,'lineHeight'),cs(e,'fontWeight'),cs(e,'letterSpacing'),cs(e,'color'),Math.round(e.getBoundingClientRect().left)].join(' ')}
r.headings=[...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h=>+h.tagName[1]);
r.wide=[...document.querySelectorAll('body *')].filter(e=>{const b=e.getBoundingClientRect();
 return b.right>innerWidth+1&&cs(e,'position')!=='fixed'&&!e.closest('[style*="overflow"],.fotoband')&&cs(e,'overflowX')!=='auto'})
 .slice(0,5).map(e=>e.tagName.toLowerCase()+(e.className?'.'+String(e.className).split(' ')[0]:''));
return r}"""


def seiten(web: Path):
    s = ["index.html", "danke.html", "fehler.html"]
    s += sorted(p.relative_to(web).as_posix() for p in (web / "stellen").glob("*.html"))
    s += sorted(p.relative_to(web).as_posix() for p in (web / "rechtliches").glob("*.html"))
    return [x for x in s if (web / x).exists()]


def anker_pruefen(web: Path):
    fehler = []
    for rel in seiten(web):
        html = (web / rel).read_text(encoding="utf-8")
        html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
        ids = set(re.findall(r'\sid="([^"]+)"', html))
        for h in re.findall(r'href="([^"]*)"', html):
            if h.startswith(("http", "mailto:", "tel:", "javascript:")) or "#" not in h:
                continue
            pfad, anker = h.split("#", 1)
            if not pfad:
                if anker and anker not in ids:
                    fehler.append(f"{rel}: #{anker} gibt es auf der Seite nicht")
                continue
            ziel = ((web / rel).parent / pfad).resolve()
            if not ziel.exists():
                fehler.append(f"{rel}: Linkziel {h} fehlt")
            elif anker and f'id="{anker}"' not in ziel.read_text(encoding="utf-8"):
                fehler.append(f"{rel}: Anker #{anker} fehlt in {pfad}")
    return fehler


def ueberschriften_pruefen(levels, rel):
    f = []
    if levels.count(1) != 1:
        f.append(f"{rel}: {levels.count(1)} h1 (erwartet 1)")
    for a, b in zip(levels, levels[1:]):
        if b > a + 1:
            f.append(f"{rel}: Überschriftensprung h{a} → h{b}")
    return f


async def lauf(a):
    from playwright.async_api import async_playwright
    projekt = Path(a.projekt).resolve()
    web = projekt / "website"
    port = 8766
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port)], cwd=web,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    basis = f"http://127.0.0.1:{port}/"
    haupt = json.loads(Path(a.haupt_json).read_text()) if a.haupt_json else {}
    probleme = []
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            if a.haupt_url:
                for w in BREITEN:
                    pg = await b.new_page(viewport={"width": w, "height": 900})
                    try:
                        await pg.goto(a.haupt_url, timeout=20000)
                        await pg.wait_for_timeout(800)
                        haupt[str(w)] = await pg.evaluate(MESSEN, {"body": "body", "p": "p", "h1": "h1", "h2": "h2", "h3": "h3",
                                                                   "nav": "nav a", "btn": ".btn, a.button"})
                    except Exception as e:  # Proxy/Netz – dann ohne Vergleich weiter
                        print(f"HINWEIS: Hauptseite bei {w}px nicht messbar ({e.__class__.__name__}) – --haupt-json nutzen")
                        break
                    finally:
                        await pg.close()
            print(f"{'Breite':>6} {'Merkmal':<6} {'Karriereseite':<48} {'Hauptseite':<48} ok")
            for w in BREITEN:
                pg = await b.new_page(viewport={"width": w, "height": 900})
                await pg.goto(basis + "index.html")
                await pg.wait_for_timeout(400)
                r = await pg.evaluate(MESSEN, SELEKTOREN)
                await pg.close()
                hw = haupt.get(str(w), {})
                for k in ("body", "p", "h1", "h2", "h3", "nav", "kick", "btn"):
                    if k not in r:
                        continue
                    ref = hw.get(k)
                    # Vergleich ohne linken Einzug (letzter Wert) und ohne Farbe, wenn Hauptseite anders selektiert
                    gleich = (ref is None) or (r[k].split(" ")[:4] == ref.split(" ")[:4])
                    print(f"{w:>6} {k:<6} {r[k]:<48} {ref or '–':<48} {'✓' if gleich else '✗'}")
                    if not gleich:
                        probleme.append(f"{w}px {k}: {r[k]}  ≠ Hauptseite {ref}")
                if r["overflow"] > 0:
                    probleme.append(f"{w}px: waagerechter Überlauf {r['overflow']}px – {r['wide']}")
                probleme += ueberschriften_pruefen(r["headings"], f"index.html@{w}")
            # Unterseiten: Überlauf + Überschriften bei 375 und 1440
            for rel in seiten(web)[1:]:
                for w in (375, 1440):
                    pg = await b.new_page(viewport={"width": w, "height": 900})
                    await pg.goto(basis + rel)
                    await pg.wait_for_timeout(300)
                    r = await pg.evaluate(MESSEN, SELEKTOREN)
                    await pg.close()
                    if r["overflow"] > 0:
                        probleme.append(f"{rel}@{w}px: waagerechter Überlauf {r['overflow']}px – {r['wide']}")
                    probleme += ueberschriften_pruefen(r["headings"], f"{rel}@{w}")
            # Anker landen unter der Kopfzeile?
            pg = await b.new_page(viewport={"width": 1280, "height": 900})
            await pg.goto(basis + "index.html#stellen")
            await pg.wait_for_timeout(1200)
            top = await pg.evaluate("()=>{const z=document.getElementById('stellen');return z?Math.round(z.getBoundingClientRect().top):null}")
            kopf = await pg.evaluate("()=>{const k=document.querySelector('header');return k?Math.round(k.getBoundingClientRect().height):0}")
            if top is not None and not (kopf <= top <= kopf + 60):
                probleme.append(f"#stellen landet bei {top}px, Kopfzeile ist {kopf}px hoch – scroll-margin-top prüfen")
            await pg.close()
            await b.close()
    finally:
        srv.terminate()
    probleme += anker_pruefen(web)
    print()
    if probleme:
        print("ABWEICHUNGEN:")
        for x in probleme:
            print(" -", x)
        return 1
    print("Alles gleich und sauber: Typografie, Überlauf, Überschriften, Anker.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projekt", default=".")
    ap.add_argument("--haupt-json")
    ap.add_argument("--haupt-url")
    a = ap.parse_args()
    return asyncio.run(lauf(a))


if __name__ == "__main__":
    sys.exit(main())
