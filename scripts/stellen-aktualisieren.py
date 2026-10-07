#!/usr/bin/env python3
"""
stellen-aktualisieren.py – frischt die Datumsangaben aller sichtbaren Stellen auf.

Google for Jobs blendet Anzeigen aus, deren validThrough überschritten ist, und stuft
alte datePosted-Werte ab. Deshalb läuft dieses Skript monatlich (GitHub-Ablauf
stellen-aktualisieren.yml) und danach bauen.py.

Was es tut, je Stelle mit status aktiv oder initiativ:
  gueltig_bis     = heute + gueltigkeit_tage (kunde.json → google_for_jobs, Standard 45)
  veroeffentlicht = heute, wenn datum_monatlich_erneuern true ist (Standard) – sonst unverändert

Pausierte Stellen werden nicht angefasst.

Aufruf:  python3 scripts/stellen-aktualisieren.py [--projekt PFAD] [--nur-pruefen]
Gibt die Anzahl geänderter Dateien aus; --nur-pruefen schreibt nichts.
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projekt", default=".")
    ap.add_argument("--nur-pruefen", action="store_true")
    ap.add_argument("--datum", help="Stichtag JJJJ-MM-TT (Standard: heute, für Tests)")
    a = ap.parse_args()

    projekt = Path(a.projekt).resolve()
    kunde = json.loads((projekt / "kunde.json").read_text(encoding="utf-8"))
    g4j = kunde.get("google_for_jobs", {})
    tage = int(g4j.get("gueltigkeit_tage", 45))
    erneuern = bool(g4j.get("datum_monatlich_erneuern", True))
    heute = date.fromisoformat(a.datum) if a.datum else date.today()

    geaendert = 0
    for pfad in sorted((projekt / "stellen").glob("*.json")):
        if pfad.name.startswith("_"):
            continue
        roh = pfad.read_text(encoding="utf-8")
        s = json.loads(roh)
        if s.get("status") not in ("aktiv", "initiativ"):
            continue
        neu = dict(s)
        neu["gueltig_bis"] = (heute + timedelta(days=tage)).isoformat()
        if erneuern:
            neu["veroeffentlicht"] = heute.isoformat()
        if neu != s:
            geaendert += 1
            print(f"{pfad.name}: veroeffentlicht {s.get('veroeffentlicht')} → {neu['veroeffentlicht']}, "
                  f"gueltig_bis {s.get('gueltig_bis')} → {neu['gueltig_bis']}")
            if not a.nur_pruefen:
                # Schlüsselreihenfolge und Einrückung erhalten, damit Diffs klein bleiben
                pfad.write_text(json.dumps(neu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{geaendert} Stellen aktualisiert" + (" (nur geprüft)" if a.nur_pruefen else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
