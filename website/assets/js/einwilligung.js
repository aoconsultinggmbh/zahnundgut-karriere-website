/* ============================================================================
   EINWILLIGUNGSBANNER (Cookie-Banner)
   Wiederverwendbar für alle Websites von AO Consulting.

   RECHTLICHE GRUNDLINIE, bitte beim Anpassen nicht aufweichen:

   1. Kein Schalter für nicht notwendige Dienste ist vorbelegt. Eine vorbelegte
      Zustimmung ist nach dem Planet49-Urteil des EuGH (C-673/17) keine wirksame
      Einwilligung. "Alles erlauben" ist deshalb nur optisch hervorgehoben,
      nicht vorausgewählt.
   2. "Nur notwendige" steht auf derselben Ebene, ist genauso groß und genauso
      leicht zu treffen wie "Alles erlauben". Alles andere wäre ein Dark Pattern
      und nach der Orientierungshilfe der Datenschutzkonferenz unzulässig.
   3. Die Einwilligung lässt sich jederzeit über die Fußzeile widerrufen, mit
      demselben Aufwand wie die Erteilung.
   4. Vor der Entscheidung wird kein einwilligungspflichtiger Dienst geladen.
   5. Der Zustand liegt im localStorage, nicht in einem Cookie. Er dient dem
      Nachweis der Einwilligung, dafür greift § 25 Abs. 2 Nr. 2 TDDDG.

   ANPASSEN FÜR EINE ANDERE SEITE:
   Vor dem Einbinden dieser Datei ein Konfigurationsobjekt setzen, zum Beispiel

     <script>window.AO_EINWILLIGUNG = { kategorien: [...], datenschutz: '...' };</script>

   Ohne Konfiguration greift die Vorgabe weiter unten.
   ============================================================================ */

(function () {
  'use strict';

  var SPEICHER = 'ao-einwilligung-v1';

  // ------------------------------------------------------------------------
  // Vorgabe-Konfiguration. Es werden nur Kategorien gezeigt, die die Seite
  // wirklich nutzt. Eine leere Kategorie aufzulisten wäre irreführend.
  // ------------------------------------------------------------------------
  var VORGABE = {
    datenschutz: 'datenschutz.html',
    impressum: 'impressum.html',
    kategorien: [
      {
        id: 'notwendig',
        name: 'Notwendig',
        kurz: 'Hält die Website funktionsfähig und speichert Ihre Entscheidung aus diesem Fenster. Ohne diese Funktionen lässt sich die Seite nicht sinnvoll anzeigen.',
        pflicht: true,
        dienste: [{
          name: 'Einwilligungsspeicher',
          anbieter: 'Puchmayr Dentaltechnik GmbH, Kelchstr. 23, 12169 Berlin',
          zweck: 'Speichert, welchen Diensten Sie zugestimmt haben, damit Sie nicht bei jedem Aufruf erneut gefragt werden.',
          art: 'Lokaler Speicher im Browser, kein Cookie',
          dauer: '12 Monate',
        }],
      },
      {
        id: 'medien',
        name: 'Karten und Videos',
        kurz: 'Lädt die Anfahrtskarte von Google Maps und das Video zum Berliner Inklusionspreis von YouTube. Erst dann wird Ihre IP-Adresse an Google übertragen.',
        dienste: [
          {
            name: 'Google Maps',
            anbieter: 'Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland',
            zweck: 'Zeigt die Anfahrt zum Labor auf einer interaktiven Karte.',
            art: 'Einbettung über iframe, Übertragung der IP-Adresse, Verarbeitung auch in den USA möglich',
            dauer: 'Siehe Datenschutzerklärung von Google',
          },
          {
            name: 'YouTube',
            anbieter: 'Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland',
            zweck: 'Spielt das Video zur Verleihung des Berliner Inklusionspreises ab.',
            art: 'Einbettung im Modus mit erweitertem Datenschutz über youtube-nocookie.com',
            dauer: 'Siehe Datenschutzerklärung von Google',
          },
        ],
      },
    ],
  };

  var konf = window.AO_EINWILLIGUNG || {};
  var KAT = konf.kategorien || VORGABE.kategorien;
  var LINK_DS = konf.datenschutz || VORGABE.datenschutz;
  var LINK_IMP = konf.impressum || VORGABE.impressum;

  // ------------------------------------------------------------------------
  // Zustand
  // ------------------------------------------------------------------------
  function leer() {
    var z = {};
    KAT.forEach(function (k) { z[k.id] = !!k.pflicht; });
    return z;
  }

  var zustand = null;   // null = noch keine Entscheidung getroffen
  var entschieden = false;

  // Gültigkeit der Einwilligung. Die Datenschutzerklärung nennt 12 Monate,
  // danach wird erneut gefragt. Ohne diese Prüfung wäre die Angabe unwahr.
  var GUELTIG_TAGE = 365;

  try {
    var roh = window.localStorage.getItem(SPEICHER);
    if (roh) {
      var d = JSON.parse(roh);
      var alter = d && d.zeit ? (Date.now() - new Date(d.zeit).getTime()) / 86400000 : Infinity;
      if (d && d.kategorien && alter <= GUELTIG_TAGE) {
        zustand = leer();
        KAT.forEach(function (k) {
          if (!k.pflicht && d.kategorien[k.id] === true) zustand[k.id] = true;
        });
        entschieden = true;
      } else {
        window.localStorage.removeItem(SPEICHER);
      }
    }
  } catch (e) { /* privater Modus oder gesperrter Speicher: Banner erscheint erneut */ }

  if (!zustand) zustand = leer();

  function sichern() {
    try {
      window.localStorage.setItem(SPEICHER, JSON.stringify({
        version: 1,
        zeit: new Date().toISOString(),
        kategorien: zustand,
      }));
    } catch (e) { /* nicht speicherbar, Entscheidung gilt für diese Sitzung */ }
  }

  function melden() {
    document.dispatchEvent(new CustomEvent('ao:einwilligung', { detail: { kategorien: zustand } }));
  }

  // ------------------------------------------------------------------------
  // Oberfläche
  // ------------------------------------------------------------------------
  var hinter = null, karte = null, sicht = 'kurz', zuletztFokus = null;

  function svgHaken() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>';
  }
  function svgSchild() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.6 4.5 5.6v6c0 4.6 3.2 8.8 7.5 9.9 4.3-1.1 7.5-5.3 7.5-9.9v-6L12 2.6Z"/><path d="M9.2 12.1 11.4 14.3l3.8-4"/></svg>';
  }

  function baue() {
    hinter = document.createElement('div');
    hinter.className = 'ein-hinter';
    hinter.setAttribute('data-offen', 'false');
    hinter.setAttribute('data-sicht', 'kurz');

    karte = document.createElement('div');
    karte.className = 'ein-karte';
    karte.setAttribute('role', 'dialog');
    karte.setAttribute('aria-modal', 'true');
    karte.setAttribute('aria-labelledby', 'ein-titel');
    karte.setAttribute('aria-describedby', 'ein-text');

    hinter.appendChild(karte);
    document.body.appendChild(hinter);

    // Klick auf die Abdunklung schließt nicht: es muss entschieden werden.
    // Nach einer Entscheidung ist das Fenster ein normaler Dialog und darf zu.
    hinter.addEventListener('click', function (e) {
      if (e.target === hinter && entschieden) schliesse();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && hinter.getAttribute('data-offen') === 'true' && entschieden) schliesse();
      if (e.key === 'Tab' && hinter.getAttribute('data-offen') === 'true') fokusFalle(e);
    });
  }

  function fokusFalle(e) {
    var ziele = karte.querySelectorAll('button:not([disabled]),a[href],[tabindex]:not([tabindex="-1"])');
    if (!ziele.length) return;
    var erste = ziele[0], letzte = ziele[ziele.length - 1];
    if (e.shiftKey && document.activeElement === erste) { e.preventDefault(); letzte.focus(); }
    else if (!e.shiftKey && document.activeElement === letzte) { e.preventDefault(); erste.focus(); }
  }

  function zeichne(fokussieren) {
    karte.innerHTML = sicht === 'kurz' ? htmlKurz() : htmlDetails();
    hinter.setAttribute('data-sicht', sicht);
    binde();
    if (fokussieren !== false) setzeFokus();
  }

  // Der Fokus darf erst gesetzt werden, wenn die Karte sichtbar ist.
  // Auf einem Element mit visibility:hidden bleibt focus() wirkungslos,
  // und dann greift auch die Fokusfalle nicht.
  function setzeFokus() {
    var ziel = karte.querySelector('.ein-knopf--alle, .ein-knopf--speichern') ||
               karte.querySelector('button');
    if (ziel) ziel.focus({ preventScroll: true });
  }

  // Der Rest der Seite wird für Tastatur und Screenreader stillgelegt,
  // solange der Dialog offen ist.
  function setzeInert(an) {
    Array.prototype.forEach.call(document.body.children, function (el) {
      if (el === hinter) return;
      if (an) { el.setAttribute('inert', ''); el.setAttribute('aria-hidden', 'true'); }
      else { el.removeAttribute('inert'); el.removeAttribute('aria-hidden'); }
    });
  }

  function htmlKurz() {
    // Namen unverändert übernehmen, sonst steht "karten und videos" im Satz
    var namen = KAT.filter(function (k) { return !k.pflicht; })
                   .map(function (k) { return k.name; }).join(' und ');
    return '' +
      '<div class="ein-koerper">' +
        '<span class="ein-kicker">Datenschutzeinstellungen</span>' +
        '<h2 id="ein-titel">Sie entscheiden, was geladen wird</h2>' +
        '<p id="ein-text">Diese Website nutzt nur, was für den Betrieb nötig ist. Zusätzlich können wir ' +
          (namen || 'externe Inhalte') + ' einbinden. Diese Inhalte stammen von Google. ' +
          'Beim Laden wird Ihre IP-Adresse an Google übertragen, deshalb fragen wir vorher.</p>' +
        '<p class="ein-fein">Ihre Wahl gilt 12 Monate und lässt sich jederzeit über ' +
          '„Cookie-Einstellungen" in der Fußzeile ändern. Es werden keine Werbe- oder ' +
          'Analysedienste eingesetzt. Mehr dazu in der ' +
          '<a href="' + LINK_DS + '">Datenschutzerklärung</a>.</p>' +
      '</div>' +
      '<div class="ein-fuss">' +
        '<span class="ein-empfehlung">Unsere Empfehlung</span>' +
        '<div class="ein-knoepfe">' +
          '<button type="button" class="ein-knopf ein-knopf--alle" data-tun="alle">' +
            svgHaken() + 'Alles erlauben</button>' +
          '<button type="button" class="ein-knopf ein-knopf--notwendig" data-tun="notwendig">' +
            'Nur notwendige</button>' +
        '</div>' +
        '<div class="ein-nebenlinks">' +
          '<button type="button" data-tun="details">Einzeln auswählen</button>' +
          '<a href="' + LINK_DS + '">Datenschutz</a>' +
          '<a href="' + LINK_IMP + '">Impressum</a>' +
        '</div>' +
      '</div>';
  }

  function htmlDetails() {
    var liste = KAT.map(function (k) {
      var an = zustand[k.id] === true;
      var dienste = (k.dienste || []).map(function (d) {
        return '<div class="ein-dienst"><span class="ein-dienst__name">' + d.name + '</span><dl>' +
          '<dt>Anbieter</dt><dd>' + d.anbieter + '</dd>' +
          '<dt>Zweck</dt><dd>' + d.zweck + '</dd>' +
          '<dt>Art</dt><dd>' + d.art + '</dd>' +
          '<dt>Dauer</dt><dd>' + d.dauer + '</dd>' +
          '</dl></div>';
      }).join('');
      return '' +
        '<div class="ein-gruppe">' +
          '<div class="ein-gruppe__kopf">' +
            '<span class="ein-gruppe__text">' +
              '<span class="ein-gruppe__name" id="ein-n-' + k.id + '">' + k.name + '</span>' +
              '<span class="ein-gruppe__kurz">' + k.kurz + '</span>' +
              (k.pflicht ? '<span class="ein-immer">Immer aktiv</span>' : '') +
            '</span>' +
            '<button type="button" class="ein-schalter" role="switch" data-kat="' + k.id + '" ' +
              'aria-checked="' + (k.pflicht ? 'true' : (an ? 'true' : 'false')) + '" ' +
              'aria-labelledby="ein-n-' + k.id + '"' + (k.pflicht ? ' disabled' : '') + '></button>' +
          '</div>' +
          (dienste ?
            '<button type="button" class="ein-mehr" aria-expanded="false" aria-controls="ein-d-' + k.id + '">' +
              (k.dienste.length === 1 ? '1 Dienst' : k.dienste.length + ' Dienste') + ' anzeigen</button>' +
            '<div class="ein-dienste" id="ein-d-' + k.id + '" hidden>' + dienste + '</div>'
            : '') +
        '</div>';
    }).join('');

    return '' +
      '<div class="ein-koerper">' +
        '<span class="ein-kicker">Datenschutzeinstellungen</span>' +
        '<h2 id="ein-titel">Einzeln auswählen</h2>' +
        '<p id="ein-text" class="ein-fein">Notwendige Funktionen lassen sich nicht abschalten, ohne sie ' +
          'funktioniert die Seite nicht. Alles andere ist aus, solange Sie es nicht einschalten. ' +
          'Details zu jedem Dienst stehen unter „Dienste anzeigen".</p>' +
        '<div class="ein-liste">' + liste + '</div>' +
      '</div>' +
      '<div class="ein-fuss">' +
        '<div class="ein-knoepfe">' +
          '<button type="button" class="ein-knopf ein-knopf--alle" data-tun="alle">' +
            svgHaken() + 'Alles erlauben</button>' +
          '<button type="button" class="ein-knopf ein-knopf--speichern" data-tun="speichern">' +
            'Auswahl speichern</button>' +
        '</div>' +
        '<div class="ein-nebenlinks">' +
          '<button type="button" data-tun="notwendig">Nur notwendige</button>' +
          '<button type="button" data-tun="kurz">Zurück</button>' +
          '<a href="' + LINK_DS + '">Datenschutz</a>' +
        '</div>' +
      '</div>';
  }

  function binde() {
    karte.querySelectorAll('[data-tun]').forEach(function (b) {
      b.addEventListener('click', function () {
        var tun = b.dataset.tun;
        if (tun === 'alle') { KAT.forEach(function (k) { zustand[k.id] = true; }); fertig(); }
        else if (tun === 'notwendig') { zustand = leer(); fertig(); }
        else if (tun === 'speichern') { fertig(); }
        else if (tun === 'details') { sicht = 'details'; zeichne(); }
        else if (tun === 'kurz') { sicht = 'kurz'; zeichne(); }
      });
    });

    karte.querySelectorAll('.ein-schalter:not([disabled])').forEach(function (s) {
      s.addEventListener('click', function () {
        var an = s.getAttribute('aria-checked') === 'true';
        s.setAttribute('aria-checked', an ? 'false' : 'true');
        zustand[s.dataset.kat] = !an;
      });
    });

    karte.querySelectorAll('.ein-mehr').forEach(function (m) {
      m.addEventListener('click', function () {
        var offen = m.getAttribute('aria-expanded') === 'true';
        var ziel = document.getElementById(m.getAttribute('aria-controls'));
        var anzahl = ziel ? ziel.querySelectorAll('.ein-dienst').length : 0;
        m.setAttribute('aria-expanded', offen ? 'false' : 'true');
        if (ziel) ziel.hidden = offen;
        m.textContent = (anzahl === 1 ? '1 Dienst' : anzahl + ' Dienste') +
                        (offen ? ' anzeigen' : ' ausblenden');
      });
    });
  }

  // ------------------------------------------------------------------------
  // Öffnen, schließen, speichern
  // ------------------------------------------------------------------------
  function oeffne(zielSicht) {
    if (!hinter) baue();
    sicht = zielSicht || 'kurz';
    zuletztFokus = document.activeElement;
    zeichne(false);
    document.documentElement.classList.add('ein-offen');
    setzeInert(true);
    hinter.setAttribute('data-offen', 'true');
    // erst im nächsten Frame ist die Karte sichtbar und fokussierbar
    requestAnimationFrame(setzeFokus);
  }

  function schliesse() {
    if (!hinter) return;
    hinter.setAttribute('data-offen', 'false');
    document.documentElement.classList.remove('ein-offen');
    setzeInert(false);
    if (zuletztFokus && zuletztFokus.focus) zuletztFokus.focus();
  }

  function fertig() {
    var vorher = {};
    try {
      var roh = window.localStorage.getItem(SPEICHER);
      if (roh) vorher = (JSON.parse(roh) || {}).kategorien || {};
    } catch (e) { /* egal */ }

    // Wird eine bereits erteilte Zustimmung zurückgenommen, muss die Seite neu
    // geladen werden. Ein schon eingebundener iframe lässt sich nicht sauber
    // zurücknehmen, nur entfernen.
    var widerruf = KAT.some(function (k) {
      return !k.pflicht && vorher[k.id] === true && zustand[k.id] !== true;
    });

    entschieden = true;
    sichern();
    melden();
    schliesse();
    if (widerruf) window.setTimeout(function () { window.location.reload(); }, 320);
  }

  // ------------------------------------------------------------------------
  // Öffentliche Schnittstelle
  // ------------------------------------------------------------------------
  window.aoEinwilligung = {
    erlaubt: function (kat) { return zustand[kat] === true; },
    entschieden: function () { return entschieden; },
    setze: function (kat, wert) {
      if (kat === 'notwendig') return;
      zustand[kat] = wert === true;
      entschieden = true;
      sichern();
      melden();
    },
    oeffnen: function () { oeffne('details'); },
    zuruecksetzen: function () {
      try { window.localStorage.removeItem(SPEICHER); } catch (e) { /* egal */ }
      window.location.reload();
    },
  };

  // ------------------------------------------------------------------------
  // Start
  // ------------------------------------------------------------------------
  // Gibt es keine einzige freiwillige Kategorie, waere ein Banner sinnlos und
  // nur laestig: dann wird nichts geladen, was einer Zustimmung beduerfte.
  // KEINE_FREIWILLIGE
  var hatFreiwillige = KAT.some(function (k) { return !k.pflicht; });

  function start() {
    // Ohne freiwillige Kategorie gibt es nichts einzustellen: Auslöser in der
    // Fußzeile ausblenden, damit kein Knopf dasteht, der nichts tut.
    if (!hatFreiwillige) {
      document.querySelectorAll('[data-einwilligung-oeffnen]').forEach(function (b) {
        var huelle = b.closest('[data-einwilligung-huelle], li');
        (huelle || b).style.display = 'none';
      });
      melden();
      return;
    }
    // Auslöser in der Fußzeile verkabeln
    document.querySelectorAll('[data-einwilligung-oeffnen]').forEach(function (b) {
      b.addEventListener('click', function (e) { e.preventDefault(); oeffne('details'); });
    });
    if (!entschieden) oeffne('kurz');
    else melden();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
