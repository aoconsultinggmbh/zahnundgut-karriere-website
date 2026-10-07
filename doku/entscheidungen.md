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
  Einwilligungsbanner schlafend, Google for Jobs, Indeed-Feed, Matomo). Abschnitte in der Reihenfolge der alten Seite,
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
- **Kein Foto** bei der Ansprechpartnerin: Welches Bild Dr. Katrin Becker zeigt, ist nicht bestätigt. Stattdessen ein Bild
  des Behandlungszimmers.

## Bilder (alte Karriereseite, Nummer = Zahn-und-Gut-Karriere-<Nr>.webp)

| Datei | Nr. | Verwendung |
|---|---|---|
| hero-team(-mobil), og-bild | 33 | Titelbild (Team klatscht ab), Vorschaubild |
| ueber-uns | 21 | Über uns |
| team | 62 | Team (Pausenraum) |
| leitsatz | 59 | Hintergrund Leitsatz |
| gruende-teamgeist / -qualitaet / -menschlichkeit | 35 / 44 / 56 | Drei Gründe |
| kontakt-praxis | 52 | Ansprechpartnerin (Behandlungszimmer, ohne Personen) |
| faq-empfang | 12 | FAQ |
| stelle-ausbildung / -zfa / -zmp / -zmv | 40 / 19 / 38 / 13 | Kopfbild der Stellenseiten |

Nicht verwendet: 1, 15, 25, 26, 27, 29, 31, 48, 50, 54.

## Offen vor dem Livegang

- [ ] **Google Analytics und Meta-Pixel:** Die alte Seite hat beides (laut Datenschutz). Wenn die Praxis oder AO damit
      Anzeigen misst (z. B. Recruiting-Kampagnen über Meta), Kennungen in `assets/js/ao-konfiguration.js` eintragen
      (dann erscheint das Einwilligungsbanner) und den Datenschutz ergänzen. Sonst entfällt beides ersatzlos.
- [ ] **Zapier:** Die alte Seite schickt Bewerbungen über Zapier weiter (laut Datenschutz). Klären, wohin (Bewerbertool, Tabelle?).
      Die neue Seite schickt nur eine Mail an dr.k.becker@zahnundgut.de.
- [ ] **Ausbildung 2026:** auf der alten Seite noch als „Neu, 2026“ geführt. Hat vermutlich schon begonnen, auf 2027 umstellen?
- [ ] **Hero-Überschrift** „… & Zahnarzt Jobs“ wie auf der alten Seite, es gibt aber keine Zahnarzt-Stelle.
- [ ] Postfach **jobs@karriere-zahnundgut.de** als Absender anlegen (oder Absender in kunde.json ändern).
- [ ] Domain karriere-zahnundgut.de: Wo liegt sie, wo liegen die Postfächer (MX)? Alte Seite liegt bei Raidboxes.
- [ ] Datenschutz von der Praxis freigeben lassen (neu geschrieben, weil Hoster und Dienste wechseln).
- [ ] Gehalt nur mit Freigabe der Praxis (Google zeigt Anzeigen mit Gehalt besser).
- [ ] Foto von Dr. Katrin Becker: Welches Bild? Dann `ansprechpartner.foto` in kunde.json setzen.
- [ ] Matomo-Eintrag anlegen, `matomo_id` in kunde.json eintragen.
- [ ] Wistia-Video: falls gewünscht, als MP4 lokal einbauen (wie bei Whiteblick), nicht als Einbettung.
