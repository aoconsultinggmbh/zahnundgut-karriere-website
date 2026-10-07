/* ============================================================================
   KONFIGURATION für das Einwilligungsbanner (AO-Standard), Karriereseite.
   Die Karriereseite lädt nichts, was eine Einwilligung braucht (keine Karten, keine Videos,
   Matomo cookiefrei). Deshalb gibt es nur „Notwendig“, und das Banner erscheint nicht
   (einwilligung.js blendet dann auch „Cookie-Einstellungen“ im Fuß aus).
   Kommt später etwas hinzu (z. B. Video von YouTube), hier eine Kategorie eintragen
   UND die Datenschutzerklärung anpassen.
   ============================================================================ */
window.AO_EINWILLIGUNG = {
  datenschutz: '/rechtliches/datenschutz.html',
  impressum: '/rechtliches/impressum.html',
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
