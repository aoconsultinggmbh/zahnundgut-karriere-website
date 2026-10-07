#!/usr/bin/env python3
"""
vorschau-datei.py – schreibt „Vorschau öffnen.html“ in den Kundenordner (den Ordner ÜBER dem Projekt).

Eine einzige, vollständig eigenständige Datei: Stylesheet, Schriften, Bilder, Videos und ALLE Seiten
(Startseite, jede Stelle, Impressum, Datenschutz, Danke/Fehler) stecken drin. Sie braucht keine
Nachbardateien – deshalb läuft sie in jedem Browser aus jedem Ordner, auch vom Schreibtisch, auch in
Chrome, ohne Berechtigungen (macOS lässt Chrome bei Doppelklick nur DIESE Datei lesen, nicht die
Dateien daneben – darum zeigte die alte Vorschau nur Text ohne Bilder).

Aufruf: python3 scripts/vorschau-datei.py [--projekt PFAD] [--ohne-videos]
Videos sind drin – in einer kleinen Vorschaufassung (640×360, ~300 kbit/s), die das Skript mit ffmpeg selbst
nach _transport/vorschau-videos/ rechnet (einmalig, wird wiederverwendet). Grund: die Originale (720p) würden
die Datei auf 40 MB+ treiben, device_commit_files erlaubt 30 MB je Datei. Ohne ffmpeg oder mit --ohne-videos
bleiben nur die Standbilder, und der Abspielknopf meldet „Video folgt“. Nach jedem bauen.py erneut ausführen.
"""
import argparse
import base64
import mimetypes
import re
import shutil
import subprocess
import sys
from pathlib import Path

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("image/webp", ".webp")


def daten_uri(pfad: Path) -> str:
    typ = mimetypes.guess_type(pfad.name)[0] or "application/octet-stream"
    return f"data:{typ};base64," + base64.b64encode(pfad.read_bytes()).decode("ascii")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projekt", default=".")
    ap.add_argument("--ohne-videos", action="store_true", help="Videos nicht einbetten (nur Standbilder)")
    a = ap.parse_args()
    projekt = Path(a.projekt).resolve()
    web = projekt / "website"
    klein_ordner = projekt.parent / "_transport" / "vorschau-videos"
    ffmpeg = shutil.which("ffmpeg")
    if not a.ohne_videos and not ffmpeg:
        print("HINWEIS: ffmpeg fehlt – Vorschau ohne Videos")

    def video_klein(ziel: Path) -> Path | None:
        """Kleine Fassung für die Vorschau (einmal rechnen, dann wiederverwenden)."""
        if a.ohne_videos or not ffmpeg:
            return None
        klein_ordner.mkdir(parents=True, exist_ok=True)
        k = klein_ordner / ziel.name
        if not k.exists() or k.stat().st_mtime < ziel.stat().st_mtime:
            subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(ziel), "-vf", "scale=640:-2", "-c:v", "libx264",
                            "-preset", "slow", "-crf", "30", "-maxrate", "320k", "-bufsize", "640k", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "48k", "-ac", "1", "-movflags", "+faststart", str(k)], check=True)
        return k
    if not (web / "index.html").exists():
        sys.exit("FEHLER: website/index.html fehlt – erst bauen.py laufen lassen")

    seiten = ["index.html", "danke.html", "fehler.html"]
    seiten += sorted(p.relative_to(web).as_posix() for p in (web / "stellen").glob("*.html"))
    seiten += sorted(p.relative_to(web).as_posix() for p in (web / "rechtliches").glob("*.html"))

    cache: dict[str, str] = {}

    def einbetten(ziel: Path) -> str | None:
        if not ziel.exists() or not ziel.is_file():
            return None
        k = str(ziel)
        if k not in cache:
            if ziel.suffix == ".mp4":
                klein = video_klein(ziel)
                if klein is None:
                    return None
                cache[k] = daten_uri(klein)
                return cache[k]
            cache[k] = daten_uri(ziel)
        return cache[k]

    # CSS: ci.css + stil.css, url(...) auf Schriften/Bilder einbetten
    css = ""
    for name in ("ci.css", "stil.css"):
        p = web / "assets" / "css" / name
        if p.exists():
            t = p.read_text(encoding="utf-8")
            t = re.sub(r'url\(["\']?(\.\./[^"\')]+)["\']?\)',
                       lambda m: f'url("{einbetten((p.parent / m.group(1)).resolve()) or m.group(1)}")', t)
            css += f"\n/* {name} */\n" + t
    css += "\n.vs-seite{display:none}.vs-seite.aktiv{display:block}\n.vorschau-hinweis a{color:inherit}\n"

    js = (web / "assets" / "js" / "app.js").read_text(encoding="utf-8") if (web / "assets" / "js" / "app.js").exists() else ""

    bloecke = []
    for rel in seiten:
        quelle = web / rel
        html = quelle.read_text(encoding="utf-8")
        m = re.search(r"<body[^>]*>(.*)</body>", html, flags=re.S)
        body = m.group(1) if m else html
        # Skripte und Kommentare raus (app.js kommt einmal unten rein)
        body = re.sub(r"<script[^>]*src=[^>]*></script>", "", body)
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        basis = quelle.parent

        def ressource(mm):
            attr, wert = mm.group(1), mm.group(2)
            if wert.startswith(("http:", "https:", "mailto:", "tel:", "data:", "#", "javascript:")):
                return mm.group(0)
            pfad, _, anker = wert.partition("#")
            ziel = (basis / pfad).resolve() if pfad else quelle
            try:
                ziel_rel = ziel.relative_to(web).as_posix()
            except ValueError:
                return mm.group(0)
            if attr in ("href",) and ziel_rel in seiten:
                return f'href="#" data-seite="{ziel_rel}" data-anker="{anker}"'
            if attr == "href" and ziel.suffix == ".php":
                return 'href="#" data-seite="fehler.html"'
            if attr == "action":
                return 'action="#"'
            if attr == "srcset":
                teile = []
                for kand in wert.split(","):
                    url, _, desc = kand.strip().partition(" ")
                    d = einbetten((basis / url).resolve())
                    teile.append((d or url) + (" " + desc if desc else ""))
                return f'srcset="{", ".join(teile)}"'
            d = einbetten(ziel)
            if d is None and ziel.suffix == ".mp4":
                return f'{attr}=""'
            return f'{attr}="{d or wert}"'

        body = re.sub(r'\b(href|src|srcset|poster|action)="([^"]*)"', ressource, body)
        bloecke.append(f'<div class="vs-seite" id="vs-{re.sub(r"[^a-z0-9]+", "-", rel.lower())}" data-rel="{rel}">{body}</div>')

    titel = re.search(r"<title>(.*?)</title>", (web / "index.html").read_text(encoding="utf-8"), flags=re.S)
    titel = (titel.group(1).strip() if titel else "Vorschau") + " – Vorschau"
    steuerung = """
<script>
(function(){
  function zeige(rel, anker){
    document.querySelectorAll('.vs-seite').forEach(function(d){ d.classList.toggle('aktiv', d.dataset.rel===rel); });
    var akt=document.querySelector('.vs-seite.aktiv');
    if(anker){ var z=akt && akt.querySelector('#'+CSS.escape(anker)); if(z){ z.scrollIntoView(); return; } }
    window.scrollTo(0,0);
  }
  document.addEventListener('click', function(e){
    var a=e.target.closest('a[data-seite]');
    if(a){ e.preventDefault(); zeige(a.dataset.seite, a.dataset.anker||''); return; }
    var h=e.target.closest('a[href^="#"]'); if(!h) return;
    var id=h.getAttribute('href').slice(1); if(!id) return;
    var akt=document.querySelector('.vs-seite.aktiv'); var z=akt && akt.querySelector('#'+CSS.escape(id));
    if(z){ e.preventDefault(); z.scrollIntoView({behavior:'smooth'}); }
  });
  // Burger-Menü auf jeder eingebetteten Seite (app.js bindet nur das erste)
  document.querySelectorAll('.navi-schalter').forEach(function(s,i){ if(i===0) return;
    s.addEventListener('click', function(){ var n=s.parentElement.querySelector('.hauptnavi'); if(n){ var o=n.classList.toggle('offen'); s.setAttribute('aria-expanded', o?'true':'false'); } }); });
  document.addEventListener('submit', function(e){
    if(e.target.classList.contains('bewerbungsformular')){ e.preventDefault(); e.stopImmediatePropagation();
      var m=e.target.querySelector('.formular-meldung'); if(m){ m.textContent='Vorschau: Das Formular versendet erst auf dem echten Server.'; m.classList.add('erfolg'); } }
  }, true);
  zeige('index.html','');
})();
</script>"""
    hinweis = ('<div class="vorschau-hinweis">Lokale Vorschau – alles in einer Datei. Das Bewerbungsformular versendet erst auf dem echten Server. '
               '<a href="#" data-seite="index.html">Startseite</a></div>')
    aus = (f'<!doctype html>\n<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
           f'<title>{titel}</title><style>{css}</style></head><body>\n{hinweis}\n' + "\n".join(bloecke)
           + f'\n<script>{js}</script>{steuerung}\n</body></html>\n')
    ziel = projekt.parent / "Vorschau öffnen.html"
    ziel.write_text(aus, encoding="utf-8")
    mb = len(aus.encode()) / 1048576
    print(f"Geschrieben: {ziel} ({mb:.1f} MB, {len(seiten)} Seiten, {len(cache)} eingebettete Dateien)")
    if mb > 29:
        print("WARNUNG: über 29 MB – device_commit_files lehnt Dateien über 30 MB ab. Videos kürzen oder --ohne-videos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
