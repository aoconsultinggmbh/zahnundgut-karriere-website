# Entscheidungen und offene Punkte – Karriereseite ZAHN & GUT

Stand 07.10.2026, Awan Tofik mit Claude.

## Vorgaben von Awan (Chat 07.10.2026)

- Neue Karriereseite für https://karriere-zahnundgut.de/ als Vorschau auf GitHub, nach neuem AO-Standard („frische Karriereseite“).
- Alte Seite **nicht** technisch nachbauen (CI, Formulare usw.), nur **Schriften und Farben** übernehmen. Darf nicht zu stark abweichen.
- Aufbau wie whiteblick-karriere.de (Reihenfolge der Abschnitte).
- Bilder von der alten Karriereseite übernehmen.
- Bewerbungen an **dr.k.becker@zahnundgut.de** (wie auf der alten Seite).
- Projektname `zahnundgut-karriere-website`, Vorschau `zahnundgut-karriere.vorschau.ao-consult.de`.
- Livegang ohne vorherige Abstimmung mit der Praxis (Entscheidung AO Consulting).

## Umsetzung

- **Technik:** Kopie des AO-Standards aus `messerschmidt-karriere` (neuester Stand: bauen.py, Barrierefreiheits-Widget,
  Einwilligungsbanner für den Meta-Pixel, Google for Jobs, Indeed-Feed, Matomo). Abschnitte in der Reihenfolge der alten Seite,
  die der Whiteblick-Reihenfolge entspricht: Hero, Über uns, Team, Benefits, Stellen, Leitsatz, Drei Gründe, Ansprechpartnerin,
  Tipps, Bewerbungsprozess, FAQ.
- **Texte:** 1:1 von der alten Seite (Über uns, Team, Benefits, Stellen, Tipps, Prozess, FAQ, Impressum). Gedankenstriche
  durch Punkt oder Doppelpunkt ersetzt (AO-Stil). Neu formuliert, aber nur aus Aussagen der Praxis zusammengesetzt:
  „Drei gute Gründe“ (Teamgeist, Qualität, Menschlichkeit = Leitsatz der Praxis), Fakten-Leiste (aus den Stellenanzeigen),
  Lagebeschreibung (Kontaktseite zahnundgut.de).
- **Schrift:** Open Sans (Text) und Open Sans Condensed (Überschriften, Menü) wie auf zahnundgut.de. Lokal als eine variable
  Datei (`font-stretch: 75%` = Condensed), Lizenz OFL in `website/assets/fonts/LICENSE-OpenSans.txt`.
- **Farben:** Logo-Grün #95c11f, Knopf-Grün #97bf0d (alte Seite), Text #555555. Weiße Schrift auf diesem Grün hat nur
  2,2:1 Kontrast, deshalb Knöpfe mit dunkler Schrift und ein Text-Grün #5a7a14 (5,0:1) für Links und Dachzeilen.
- **Logo:** weißes SVG der alten Seite, nachgefärbt wie das PNG-Logo (`logo.svg`, `logo-weiss.svg`). Favicon = Kreis mit „&“.
- **Formular:** AO-Standard (`bewerbung-senden.php`, Mail an dr.k.becker@zahnundgut.de, Eingangsbestätigung, nichts gespeichert).
  Zusatzfragen wie im alten Initiativformular (ZMV: Wunschbereich, Berufserfahrung).
- **Status:** wie auf der alten Seite: Ausbildung und ZFA „Offen“, ZMP/ZMF/DH und ZMV „Initiativ“.
- **Nicht übernommen:** Wistia-Video im Abschnitt „Über uns“ (externer Dienst, AO-Standard lädt nichts von außen),
  Google Analytics, Meta-Pixel, Google reCAPTCHA, Zapier, Borlabs Cookie, Google Maps.
- **Foto Dr. Katrin Becker** = Bild 1 (von Awan per Screenshot der alten Seite bestätigt, 07.10.2026).
- **Meta-Pixel** 1382645662547987 (laut Awan): lädt erst nach Einwilligung (`messung.js`, Kategorie „Marketing“),
  meldet auf danke.html zusätzlich `SubmitApplication`. In der Vorschau und lokal wird Meta nie geladen, nur das Banner gezeigt.
  Banner-Text in `ao-konfiguration.js` (`hinweis`), einwilligung.js dafür um `hinweis`/`hinweisFein` erweitert.
- **Google Analytics** entfällt (Awan), Besucherzahlen über Matomo cookiefrei. **Zapier** war nie in Betrieb (Awan), entfällt.

## Überarbeitung Gestaltung (07.10.2026, Wunsch Awan: „zu stark von der CI abgewichen“)

Mischung aus alter Karriereseite und Hauptseite statt AO-Grundgestaltung: weißer Kopf mit farbigem Logo,
Menü in Open Sans Condensed (Versalien, gesperrt) wie zahnundgut.de, Überschriften Open Sans normal in Grün,
Teamfoto mit hellem Verlauf und grünem Textband, Foto neben grüner Textbox (Über uns, Team, Ansprechpartnerin),
Benefits auf grüner Fläche mit Logo-Schwüngen und weißen Karten, graue Stellenzeilen, eckige Formen,
Leitsatz vor der Steinwand mit dem Kupfer-Logo (Hintergrund der Hauptseite), heller Fuß mit grünem Logo-Band.
Neu: Siegel „Top-Arbeitgeber 2025 / 2026“ (Dr. Right) von zahnundgut.de. Laufband entfernt.
Weiße Schrift auf dem hellen Logo-Grün ist schlecht lesbar, deshalb Textboxen in #588010, Knöpfe in #6b9329
mit großer Schrift; das helle Grün #97bf0d nur für Flächen, Linien und Marken.

## Bilder (alte Karriereseite, Nummer = Zahn-und-Gut-Karriere-<Nr>.webp)

| Datei | Nr. | Verwendung |
|---|---|---|
| hero-team(-mobil), og-bild | 33 | Titelbild (Team klatscht ab), Vorschaubild |
| ueber-uns | 21 | Über uns |
| team | 62 | Team (Pausenraum) |
| wand-logo | Hauptseite | Hintergrund Leitsatz (back--zahnarztpraxis.jpg) |
| siegel-top-arbeitgeber-2025/2026 | Hauptseite | Siegel Dr. Right |
| gruende-teamgeist / -qualitaet / -menschlichkeit | 35 / 44 / 56 | Drei Gründe |
| ansprechpartner(-quer) | 1 | Dr. Katrin Becker (bestätigt) |
| faq-empfang | 12 | FAQ |
| stelle-ausbildung / -zfa / -zmp / -zmv | 40 / 19 / 38 / 13 | Kopfbild der Stellenseiten |

Nicht verwendet: 15, 59, 25, 26, 27, 29, 31, 48, 50, 52, 54.

- **Matomo:** Eintrag „ZAHN & GUT Karriere“ angelegt (ID 6, statistik.ao-consult.de, 07.10.2026).

## Offen vor dem Livegang

- [x] Ausbildung auf 2027 umgestellt (Awan 07.10.2026).
- [ ] **Hero-Überschrift** „… & Zahnarzt Jobs“ wie auf der alten Seite, es gibt aber keine Zahnarzt-Stelle.
- [ ] Postfach **jobs@karriere-zahnundgut.de** als Absender anlegen (oder Absender in kunde.json ändern).
- [ ] Domain karriere-zahnundgut.de: Wo liegt sie, wo liegen die Postfächer (MX)? Alte Seite liegt bei Raidboxes.
- [ ] Datenschutz von der Praxis freigeben lassen (neu geschrieben, weil Hoster und Dienste wechseln; Meta-Pixel jetzt mit Einwilligung).
- [ ] Gehalt nur mit Freigabe der Praxis (Google zeigt Anzeigen mit Gehalt besser).
- [ ] Wistia-Video: falls gewünscht, als MP4 lokal einbauen (wie bei Whiteblick), nicht als Einbettung.
