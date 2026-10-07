/* ============================================================================
   MESSUNG — Google Analytics 4 und Meta-Pixel, aber erst nach Zustimmung.
   Wiederverwendbar für alle Websites von AO Consulting.

   EINBINDEN (nach einwilligung.js):
     <script>window.AO_MESSUNG = { ga4: '', metaPixel: '' };</script>
     <script src="assets/messung.js" defer></script>

   AUSFÜLLEN: Nur die beiden Werte oben. Solange sie leer sind, wird
   NICHTS geladen und NICHTS gemessen — genau das ist der Zustand für die
   Vorschau und für jede Seite, die noch nicht freigegeben ist.
     ga4        Messkennung aus Google Analytics, Form 'G-XXXXXXXXXX'
     metaPixel  Pixel-ID aus dem Meta-Werbekonto, nur Ziffern

   WIE ES ARBEITET
   1. Ganz zu Beginn wird Googles „Consent Mode v2" auf verweigert gesetzt.
      Das gilt auch dann, wenn später doch ein Google-Skript geladen wird.
   2. Erst wenn einwilligung.js meldet, dass die Kategorie „statistik"
      erlaubt ist, wird gtag.js nachgeladen. Vorher geht kein einziger
      Aufruf an Google hinaus.
   3. Dasselbe für „marketing" und den Meta-Pixel.
   4. Ein Widerruf lädt die Seite neu (das macht einwilligung.js), damit
      bereits geladene Fremdskripte wirklich verschwinden.

   WICHTIG: Dieser Baustein ersetzt keine Rechtsberatung. Vor dem Livegang
   müssen je Kunde vorliegen: eigenes Google-Konto, Auftragsverarbeitung mit
   Google, angepasste Datenschutzerklärung.
   ============================================================================ */
(function () {
  'use strict';

  var konf = window.AO_MESSUNG || {};
  var GA4 = String(konf.ga4 || '').trim();
  var PIXEL = String(konf.metaPixel || '').trim();
  var KAT_STATISTIK = konf.kategorieStatistik || 'statistik';
  var KAT_MARKETING = konf.kategorieMarketing || 'marketing';

  // Nichts konfiguriert: Baustein bleibt vollständig untätig.
  if (!GA4 && !PIXEL) return;

  /* ---------- Google: Zustimmung von vornherein verweigert ---------- */
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = window.gtag || gtag;

  if (GA4) {
    gtag('consent', 'default', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: 'denied',
      functionality_storage: 'granted',
      security_storage: 'granted',
      wait_for_update: 500
    });
  }

  var gaGeladen = false;
  var pixelGeladen = false;

  function ladeSkript(src, danach) {
    var s = document.createElement('script');
    s.async = true;
    s.src = src;
    if (danach) s.onload = danach;
    document.head.appendChild(s);
  }

  /* ---------- Google Analytics 4 ---------- */
  function starteGA() {
    if (gaGeladen || !GA4) return;
    gaGeladen = true;
    ladeSkript('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA4));
    gtag('js', new Date());
    gtag('config', GA4, {
      anonymize_ip: true,        // IP wird gekürzt
      allow_google_signals: false // keine geräteübergreifenden Werbemerkmale
    });
  }

  /* ---------- Meta-Pixel ---------- */
  // Vorschau (GitHub Pages) und lokaler Test: Banner erscheint zum Ansehen, Meta wird aber nie geladen,
  // damit keine Testbesuche im Werbekonto des Kunden landen.
  var NUR_TEST = /(^|\.)vorschau\.ao-consult\.de$|github\.io$|^localhost$|^127\.0\.0\.1$/.test(location.hostname);

  function startePixel() {
    if (pixelGeladen || !PIXEL) return;
    pixelGeladen = true;
    if (NUR_TEST) { if (window.console) console.info('Meta-Pixel: in der Vorschau nicht geladen'); return; }
    var f = window.fbq = function () {
      f.callMethod ? f.callMethod.apply(f, arguments) : f.queue.push(arguments);
    };
    f.push = f; f.loaded = true; f.version = '2.0'; f.queue = [];
    window._fbq = window._fbq || f;
    ladeSkript('https://connect.facebook.net/en_US/fbevents.js');
    f('init', PIXEL);
    f('track', 'PageView');
    // Danke-Seite nach dem Bewerbungsformular = erfolgreiche Bewerbung (Standard-Ereignis von Meta)
    if (/\/danke\.html$/.test(location.pathname)) f('track', 'SubmitApplication');
  }

  /* ---------- Auf die Entscheidung des Besuchers hören ---------- */
  function anwenden(kategorien) {
    var statistik = kategorien[KAT_STATISTIK] === true;
    var marketing = kategorien[KAT_MARKETING] === true;

    if (GA4) {
      gtag('consent', 'update', {
        analytics_storage: statistik ? 'granted' : 'denied',
        ad_storage: marketing ? 'granted' : 'denied',
        ad_user_data: marketing ? 'granted' : 'denied',
        ad_personalization: marketing ? 'granted' : 'denied'
      });
      if (statistik) starteGA();
    }
    if (PIXEL && marketing) startePixel();
  }

  document.addEventListener('ao:einwilligung', function (e) {
    anwenden((e.detail && e.detail.kategorien) || {});
  });

  // Falls die Entscheidung schon vorlag, hat einwilligung.js bereits gemeldet,
  // bevor diese Datei bereit war. Deshalb einmal aktiv nachfragen.
  function nachfragen() {
    var e = window.aoEinwilligung;
    if (!e) return;
    anwenden((function () {
      var z = {};
      z[KAT_STATISTIK] = e.erlaubt(KAT_STATISTIK);
      z[KAT_MARKETING] = e.erlaubt(KAT_MARKETING);
      return z;
    })());
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', nachfragen);
  } else {
    nachfragen();
  }
})();
