/* Matomo, cookiefrei (Standard der AO Consulting). matomo_id aus kunde.json eintragen; leer = keine Messung. */
(function () {
  var K = window.KARRIERE || {}; // schreibt bauen.py nach assets/js/konfiguration.js aus kunde.json → statistik
  var ID = K.matomoId || '';
  var URL = K.matomoUrl || 'https://statistik.ao-consult.de/';
  if (!ID || /vorschau\.ao-consult\.de$|localhost|github\.io$/.test(location.hostname)) return;
  var _paq = window._paq = window._paq || [];
  _paq.push(['disableCookies']); _paq.push(['setDoNotTrack', true]);
  _paq.push(['trackPageView']); _paq.push(['enableLinkTracking']);
  _paq.push(['setTrackerUrl', URL + 'matomo.php']); _paq.push(['setSiteId', ID]);
  var g = document.createElement('script'); g.async = true; g.src = URL + 'matomo.js';
  document.head.appendChild(g);
  // Bewerbung als Ziel zählen (ohne Inhalte)
  document.addEventListener('submit', function (e) { if (e.target.classList.contains('bewerbungsformular')) _paq.push(['trackEvent', 'Bewerbung', 'abgesendet', e.target.elements['stelle'] ? e.target.elements['stelle'].value : '']); });
})();
