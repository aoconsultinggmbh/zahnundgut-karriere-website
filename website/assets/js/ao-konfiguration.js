/* ============================================================================
   KONFIGURATION für Einwilligungsbanner und Messung (AO-Standard), Karriereseite ZAHN & GUT.
   DIESE DATEI IST DIE EINZIGE, DIE PRO KUNDE ANGEPASST WIRD.

     ga4        Google Analytics: bei ZAHN & GUT bewusst leer (Awan 07.10.2026: Analytics fällt weg,
                Besucherzahlen kommen cookiefrei aus Matomo, siehe statistik.js)
     metaPixel  Pixel-ID aus dem Meta-Werbekonto (laut Awan 07.10.2026), misst Recruiting-Anzeigen

   Der Meta-Pixel lädt erst nach Zustimmung im Banner (messung.js). Wird hier etwas geändert,
   muss die Datenschutzerklärung mit (rechtliches/datenschutz.html, Abschnitt Meta-Pixel).
   ============================================================================ */
window.AO_MESSUNG = {
  ga4: '',
  metaPixel: '1382645662547987'
};

window.AO_EINWILLIGUNG = {
  datenschutz: '/rechtliches/datenschutz.html',
  impressum: '/rechtliches/impressum.html',
  hinweis: 'Damit messen wir, ob unsere Stellenanzeigen bei Facebook und Instagram zu Bewerbungen führen. Dabei werden Daten an Meta übertragen, deshalb fragen wir vorher.',
  hinweisFein: 'Ohne Zustimmung wird nichts von Meta geladen. ',
  kategorien: [
    {
      id: 'notwendig',
      name: 'Notwendig',
      kurz: 'Hält die Webseite funktionsfähig und speichert Ihre Entscheidung aus diesem Fenster.',
      pflicht: true,
      dienste: [{
        name: 'Einwilligungsspeicher',
        anbieter: 'Zahnarztpraxis ZAHN & GUT, Düsseldorfer Straße 81, 40667 Meerbusch',
        zweck: 'Speichert, welchen Diensten Sie zugestimmt haben.',
        art: 'Lokaler Speicher im Browser, kein Cookie',
        dauer: '12 Monate'
      }]
    }
  ]
};

/* Die Kategorie Marketing erscheint nur, wenn oben eine Pixel-ID steht.
   Solange beide Kennungen leer sind, erscheint gar kein Banner. */
(function () {
  var m = window.AO_MESSUNG || {};
  var k = window.AO_EINWILLIGUNG.kategorien;
  if (String(m.metaPixel || '').trim()) {
    k.push({
      id: 'marketing',
      name: 'Marketing',
      kurz: 'Misst, ob eine Stellenanzeige bei Facebook oder Instagram zu einer Bewerbung geführt hat. Erst mit Ihrer Zustimmung wird dafür der Meta-Pixel geladen.',
      dienste: [{
        name: 'Meta-Pixel (Facebook, Instagram)',
        anbieter: 'Meta Platforms Ireland Ltd., Merrion Road, Dublin 4, Irland',
        zweck: 'Erkennt, ob ein Besuch aus einer Anzeige kam, und misst Bewerbungen als Erfolg.',
        art: 'Cookies und Kennungen im Browser, Übermittlung an Meta, Verarbeitung auch in den USA möglich',
        dauer: 'Bis zu 24 Monate'
      }]
    });
  }
})();
