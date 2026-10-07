/* ============================================================================
   BARRIEREFREIHEITS-WIDGET
   Wiederverwendbar für alle Websites von AO Consulting.
   Baut Auslöser und Bedienpanel selbst, verändert das übrige HTML nicht.
   Einstellungen bleiben im Browser des Besuchers gespeichert.

   WICHTIG: Dieses Widget ist eine Hilfe für Besucher, kein Ersatz für
   barrierefreies Markup. Semantik, Kontraste, Fokus und Tastaturbedienung
   müssen in der Seite selbst stimmen.
   ============================================================================ */
(function () {
  'use strict';

  var SPEICHER = 'ao-barrierefreiheit-v1';
  var wurzel = document.documentElement;

  /* ---------- Zustand ---------- */
  var standard = {
    kontrast: '',        // '', 'bf-kontrast', 'bf-invertiert', 'bf-graustufen'
    schrift: 0,          // 0 bis 4  entspricht 100 bis 160 Prozent
    zeile: 0,            // 0 bis 3
    buchstabe: 0,        // 0 bis 3
    linksHervor: false,
    titelHervor: false,
    legasthenie: false,
    cursor: false,
    ruhe: false,
    lesehilfe: '',       // '', 'bf-lesehilfe', 'bf-lesemaske'
    seite: 'rechts'
  };
  var zustand = laden();

  function laden() {
    try {
      var g = JSON.parse(localStorage.getItem(SPEICHER) || '{}');
      var z = {};
      for (var k in standard) z[k] = (k in g) ? g[k] : standard[k];
      return z;
    } catch (e) { return JSON.parse(JSON.stringify(standard)); }
  }
  function speichern() {
    try { localStorage.setItem(SPEICHER, JSON.stringify(zustand)); } catch (e) {}
  }

  /* ---------- Symbole ---------- */
  var S = {
    mensch: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="3.6" r="2.3"/><path d="M20.4 7.3c.2-.7-.2-1.4-.9-1.6-.2 0-.4 0-.6 0L12 7.1 5.1 5.7c-.7-.2-1.4.3-1.6 1-.1.7.3 1.4 1 1.5l4.9 1v2.2l-2 7.9c-.2.8.3 1.6 1.1 1.8.8.2 1.6-.3 1.8-1.1l1.7-6.3 1.7 6.3c.2.8 1 1.3 1.8 1.1.8-.2 1.3-1 1.1-1.8l-2-7.9V9.2l4.9-1c.5-.1.8-.4.9-.9Z"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    kontrast: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 3v18a9 9 0 0 0 0-18Z" fill="currentColor"/></svg>',
    invert: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 3v18M12 3a9 9 0 0 1 0 18"/><circle cx="12" cy="12" r="9"/></svg>',
    grau: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="9" cy="9" r="5.5"/><circle cx="15" cy="15" r="5.5"/></svg>',
    normal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9.5"/></svg>',
    link: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.8 1.7"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7L12.3 19"/></svg>',
    titel: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><path d="M5 5v14M13 5v14M5 12h8M17 9v10M17 9h4"/></svg>',
    legasthenie: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 19V7a3 3 0 0 1 3-3h11v15M7 19h11M7 19a3 3 0 0 1 0-6h11"/></svg>',
    cursor: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 3l14 8-6 1.6L11 20z"/></svg>',
    ruhe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>',
    linie: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><path d="M3 9h18M3 15h18"/></svg>',
    maske: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>',
    seite: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" aria-hidden="true"><path d="M9 6l-6 6 6 6M15 6l6 6-6 6"/></svg>'
  };

  /* ---------- Oberfläche bauen ---------- */
  var knopf = document.createElement('button');
  knopf.className = 'bf-knopf';
  knopf.type = 'button';
  knopf.setAttribute('aria-label', 'Barrierefreiheit: Einstellungen öffnen');
  knopf.setAttribute('aria-expanded', 'false');
  knopf.setAttribute('aria-controls', 'bf-panel');
  knopf.innerHTML = S.mensch;

  var panel = document.createElement('div');
  panel.className = 'bf-panel';
  panel.id = 'bf-panel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-modal', 'false');
  panel.setAttribute('aria-label', 'Einstellungen zur Barrierefreiheit');
  panel.dataset.offen = 'false';

  function schalter(id, symbol, text) {
    return '<button type="button" class="bf-schalter" data-bf="' + id + '" aria-pressed="false">' +
           symbol + '<span>' + text + '</span></button>';
  }
  function stufe(id, name) {
    return '<div class="bf-stufe"><span class="bf-stufe__name">' + name + '</span>' +
      '<span class="bf-stufe__steuer">' +
      '<button type="button" data-bf-minus="' + id + '" aria-label="' + name + ' verkleinern">&minus;</button>' +
      '<span class="bf-stufe__wert" data-bf-wert="' + id + '" aria-live="polite">100 %</span>' +
      '<button type="button" data-bf-plus="' + id + '" aria-label="' + name + ' vergrößern">+</button>' +
      '</span></div>';
  }

  panel.innerHTML =
    '<div class="bf-kopf">' +
      '<h2>Barrierefreiheit</h2>' +
      '<button type="button" class="bf-zu" aria-label="Einstellungen schließen">' + S.x + '</button>' +
    '</div>' +
    '<div class="bf-koerper">' +

      '<div class="bf-gruppe"><h3>Farben und Kontrast</h3><div class="bf-raster">' +
        schalter('bf-kontrast', S.kontrast, 'Hoher Kontrast') +
        schalter('bf-invertiert', S.invert, 'Farben umkehren') +
        schalter('bf-graustufen', S.grau, 'Graustufen') +
        schalter('reset-kontrast', S.normal, 'Originalfarben') +
      '</div></div>' +

      '<div class="bf-gruppe"><h3>Text</h3>' +
        stufe('schrift', 'Schriftgröße') +
        stufe('zeile', 'Zeilenabstand') +
        stufe('buchstabe', 'Buchstabenabstand') +
        '<div class="bf-raster" style="margin-top:9px">' +
          schalter('bf-legasthenie', S.legasthenie, 'Gut lesbare Schrift') +
          schalter('bf-titel-hervor', S.titel, 'Überschriften zeigen') +
        '</div>' +
      '</div>' +

      '<div class="bf-gruppe"><h3>Orientierung</h3><div class="bf-raster">' +
        schalter('bf-links-hervor', S.link, 'Links hervorheben') +
        schalter('bf-lesehilfe', S.linie, 'Leselinie') +
        schalter('bf-lesemaske', S.maske, 'Lesemaske') +
        schalter('bf-cursor', S.cursor, 'Großer Zeiger') +
      '</div></div>' +

      '<div class="bf-gruppe"><h3>Bewegung</h3><div class="bf-raster">' +
        schalter('bf-ruhe', S.ruhe, 'Animationen anhalten') +
        schalter('seite', S.seite, 'Seite wechseln') +
      '</div></div>' +

    '</div>' +
    '<div class="bf-fuss">' +
      '<button type="button" class="bf-reset">Alle Einstellungen zurücksetzen</button>' +
      '<p class="bf-hinweis">Ihre Auswahl wird nur in diesem Browser gespeichert und nicht übertragen.</p>' +
    '</div>';

  var leselinie = document.createElement('div');
  leselinie.className = 'bf-leselinie';
  var maske = document.createElement('div');
  maske.className = 'bf-maske';
  maske.innerHTML = '<div class="bf-maske-oben"></div><div class="bf-maske-unten"></div>';

  document.body.appendChild(knopf);
  document.body.appendChild(panel);
  document.body.appendChild(leselinie);
  document.body.appendChild(maske);

  /* ---------- Anwenden ---------- */
  var SCHRIFT = [1, 1.15, 1.3, 1.45, 1.6];
  var ZEILE = [1, 1.15, 1.35, 1.6];
  var BUCHSTABE = ['0em', '.045em', '.09em', '.14em'];

  function anwenden() {
    ['bf-kontrast', 'bf-invertiert', 'bf-graustufen'].forEach(function (c) {
      wurzel.classList.toggle(c, zustand.kontrast === c);
    });
    ['bf-lesehilfe', 'bf-lesemaske'].forEach(function (c) {
      wurzel.classList.toggle(c, zustand.lesehilfe === c);
    });
    wurzel.classList.toggle('bf-links-hervor', zustand.linksHervor);
    wurzel.classList.toggle('bf-titel-hervor', zustand.titelHervor);
    wurzel.classList.toggle('bf-legasthenie', zustand.legasthenie);
    wurzel.classList.toggle('bf-cursor', zustand.cursor);
    wurzel.classList.toggle('bf-ruhe', zustand.ruhe);
    wurzel.classList.toggle('bf-links', zustand.seite === 'links');

    wurzel.style.setProperty('--bf-schrift', SCHRIFT[zustand.schrift]);
    wurzel.style.setProperty('--bf-zeile', ZEILE[zustand.zeile]);
    wurzel.style.setProperty('--bf-buchstabe', BUCHSTABE[zustand.buchstabe]);
    wurzel.classList.toggle('bf-schrift-aktiv', zustand.schrift > 0);
    wurzel.classList.toggle('bf-zeile-aktiv', zustand.zeile > 0);
    wurzel.classList.toggle('bf-buchstabe-aktiv', zustand.buchstabe > 0);

    // Schalterzustände spiegeln
    panel.querySelectorAll('[data-bf]').forEach(function (b) {
      var id = b.dataset.bf, an = false;
      if (id === 'bf-kontrast' || id === 'bf-invertiert' || id === 'bf-graustufen') an = zustand.kontrast === id;
      else if (id === 'reset-kontrast') an = zustand.kontrast === '';
      else if (id === 'bf-lesehilfe' || id === 'bf-lesemaske') an = zustand.lesehilfe === id;
      else if (id === 'bf-links-hervor') an = zustand.linksHervor;
      else if (id === 'bf-titel-hervor') an = zustand.titelHervor;
      else if (id === 'bf-legasthenie') an = zustand.legasthenie;
      else if (id === 'bf-cursor') an = zustand.cursor;
      else if (id === 'bf-ruhe') an = zustand.ruhe;
      else if (id === 'seite') an = zustand.seite === 'links';
      b.setAttribute('aria-pressed', an ? 'true' : 'false');
    });

    // Stufenanzeigen
    setzeWert('schrift', Math.round(SCHRIFT[zustand.schrift] * 100) + ' %', zustand.schrift, SCHRIFT.length);
    setzeWert('zeile', ['normal', 'weit', 'weiter', 'max'][zustand.zeile], zustand.zeile, ZEILE.length);
    setzeWert('buchstabe', ['normal', 'weit', 'weiter', 'max'][zustand.buchstabe], zustand.buchstabe, BUCHSTABE.length);

    speichern();
  }

  function setzeWert(id, text, stufeJetzt, anzahl) {
    var w = panel.querySelector('[data-bf-wert="' + id + '"]');
    if (w) w.textContent = text;
    var minus = panel.querySelector('[data-bf-minus="' + id + '"]');
    var plus = panel.querySelector('[data-bf-plus="' + id + '"]');
    if (minus) minus.disabled = stufeJetzt <= 0;
    if (plus) plus.disabled = stufeJetzt >= anzahl - 1;
  }

  /* ---------- Bedienung ---------- */
  function oeffnen(auf) {
    panel.dataset.offen = auf ? 'true' : 'false';
    knopf.setAttribute('aria-expanded', auf ? 'true' : 'false');
    knopf.setAttribute('aria-label', auf ? 'Barrierefreiheit: Einstellungen schließen'
                                          : 'Barrierefreiheit: Einstellungen öffnen');
    if (auf) panel.querySelector('.bf-schalter').focus();
    else knopf.focus();
  }

  knopf.addEventListener('click', function () { oeffnen(panel.dataset.offen !== 'true'); });
  panel.querySelector('.bf-zu').addEventListener('click', function () { oeffnen(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && panel.dataset.offen === 'true') oeffnen(false);
  });

  panel.addEventListener('click', function (e) {
    var s = e.target.closest('[data-bf]');
    if (s) {
      var id = s.dataset.bf;
      if (id === 'bf-kontrast' || id === 'bf-invertiert' || id === 'bf-graustufen') {
        zustand.kontrast = (zustand.kontrast === id) ? '' : id;
      } else if (id === 'reset-kontrast') {
        zustand.kontrast = '';
      } else if (id === 'bf-lesehilfe' || id === 'bf-lesemaske') {
        zustand.lesehilfe = (zustand.lesehilfe === id) ? '' : id;
      } else if (id === 'bf-links-hervor') { zustand.linksHervor = !zustand.linksHervor; }
      else if (id === 'bf-titel-hervor') { zustand.titelHervor = !zustand.titelHervor; }
      else if (id === 'bf-legasthenie') { zustand.legasthenie = !zustand.legasthenie; }
      else if (id === 'bf-cursor') { zustand.cursor = !zustand.cursor; }
      else if (id === 'bf-ruhe') { zustand.ruhe = !zustand.ruhe; }
      else if (id === 'seite') { zustand.seite = zustand.seite === 'links' ? 'rechts' : 'links'; }
      anwenden();
      return;
    }
    var p = e.target.closest('[data-bf-plus]'), m = e.target.closest('[data-bf-minus]');
    var grenzen = { schrift: SCHRIFT.length, zeile: ZEILE.length, buchstabe: BUCHSTABE.length };
    if (p) { var k = p.dataset.bfPlus; if (zustand[k] < grenzen[k] - 1) { zustand[k]++; anwenden(); } }
    if (m) { var k2 = m.dataset.bfMinus; if (zustand[k2] > 0) { zustand[k2]--; anwenden(); } }
  });

  panel.querySelector('.bf-reset').addEventListener('click', function () {
    zustand = JSON.parse(JSON.stringify(standard));
    anwenden();
  });

  /* ---------- Leselinie und Lesemaske folgen dem Zeiger ---------- */
  var letzteY = window.innerHeight / 2;
  function zeichne(y) {
    letzteY = y;
    var h = 58;
    leselinie.style.top = Math.max(0, y - h / 2) + 'px';
    var oben = maske.firstElementChild, unten = maske.lastElementChild;
    oben.style.top = '0';
    oben.style.height = Math.max(0, y - h / 2) + 'px';
    unten.style.top = (y + h / 2) + 'px';
    unten.style.bottom = '0';
  }
  window.addEventListener('mousemove', function (e) {
    if (zustand.lesehilfe) zeichne(e.clientY);
  }, { passive: true });
  window.addEventListener('touchmove', function (e) {
    if (zustand.lesehilfe && e.touches[0]) zeichne(e.touches[0].clientY);
  }, { passive: true });
  zeichne(letzteY);

  anwenden();
})();
