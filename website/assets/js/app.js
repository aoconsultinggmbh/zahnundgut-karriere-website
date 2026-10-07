/* app.js Karriereseite ZAHN & GUT (AO-Standard): Menü, Kopf beim Scrollen, Einblenden, Leitsatz, Bewerbungsformular.
   Kein Framework, nichts von außen. */
(function () {
  'use strict';
  var d = document, b = d.body, wurzel = d.documentElement;
  wurzel.classList.add('js');
  d.querySelectorAll('[data-jahr]').forEach(function (el) { el.textContent = String(new Date().getFullYear()); });

  var ruhe = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var feinzeiger = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var istRuhig = function () { return ruhe || wurzel.classList.contains('bf-ruhe'); };

  // Menü auf dem Handy
  var schalter = d.querySelector('.navi-schalter'), navi = d.querySelector('.hauptnavi');
  if (schalter && navi) {
    schalter.addEventListener('click', function () {
      var offen = navi.classList.toggle('offen');
      b.classList.toggle('navi-offen', offen);
      schalter.setAttribute('aria-expanded', offen ? 'true' : 'false');
      schalter.setAttribute('aria-label', offen ? 'Menü schließen' : 'Menü öffnen');
    });
    navi.querySelectorAll('a[href*="#"]').forEach(function (a) {
      a.addEventListener('click', function () { navi.classList.remove('offen'); b.classList.remove('navi-offen'); schalter.setAttribute('aria-expanded', 'false'); });
    });
  }

  // Startseite: Kopf liegt durchsichtig über dem Foto und wird beim Scrollen weiß
  var kopf = d.querySelector('.kopf-transparent');
  if (kopf) {
    var pruefen = function () { kopf.classList.toggle('kopf-transparent', window.scrollY < 60); };
    window.addEventListener('scroll', pruefen, { passive: true }); pruefen();
  }

  // Sanftes Einblenden
  var ziele = d.querySelectorAll('.abschnitt .text-spalte, .bild-quer, .kachel, .abschnitt-kopf, .benefit, .grund, .stelle-zeile, .f-anim');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (e) {
      e.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add('sichtbar'); io.unobserve(x.target); } });
    }, { rootMargin: '0px 0px -8% 0px' });
    ziele.forEach(function (el) { el.classList.add('einblenden'); io.observe(el); });
  }

  // Hero: Überschrift Zeile für Zeile
  requestAnimationFrame(function () { b.classList.add('geladen'); });

  // Leitsatz: Wörter füllen sich beim Scrollen mit Farbe
  var aussage = d.querySelector('[data-woerter]'), woerter = null;
  if (aussage) {
    // Nur an normalen Leerzeichen trennen: geschützte Leerzeichen (&nbsp;) halten Namen wie „ZAHN & GUT“ zusammen
    aussage.innerHTML = aussage.textContent.trim().split(/[ \t\r\n]+/).map(function (w) { return '<span>' + w.replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</span>'; }).join(' ');
    woerter = aussage.querySelectorAll('span');
  }

  var parallax = ruhe ? [] : d.querySelectorAll('[data-parallax]');
  var kopfEl = d.querySelector('.kopf'), letzteY = window.scrollY, tick = false;
  var fortschritt = d.querySelector('.f-fortschritt'), tiefe = ruhe ? [] : d.querySelectorAll('[data-tiefe]');
  function beimScrollen() {
    var y = window.scrollY, h = window.innerHeight;
    if (woerter) {
      var r = aussage.getBoundingClientRect();
      var anteil = Math.min(Math.max((h * .85 - r.top) / (r.height + h * .45), 0), 1);
      var n = Math.round(anteil * woerter.length);
      woerter.forEach(function (w, i) { w.classList.toggle('an', i < n); });
    }
    if (!istRuhig()) parallax.forEach(function (el) {
      var r = el.parentElement.getBoundingClientRect();
      if (r.bottom < 0 || r.top > h) return;
      var v = (r.top + r.height / 2 - h / 2) * -0.12;
      el.style.transform = 'translate3d(0,' + v.toFixed(1) + 'px,0) scale(1.12)';
    });
    if (fortschritt) fortschritt.style.setProperty('--f-p', (y / Math.max(1, d.documentElement.scrollHeight - h)).toFixed(4));
    if (!istRuhig()) tiefe.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.bottom < -200 || r.top > h + 200) return;
      el.style.translate = '0 ' + ((r.top + r.height / 2 - h / 2) * parseFloat(el.getAttribute('data-tiefe'))).toFixed(1) + 'px';
    }); else tiefe.forEach(function (el) { el.style.translate = ''; });
    if (kopfEl) kopfEl.classList.toggle('kopf-klein', y > 20);
    if (kopfEl && !b.classList.contains('navi-offen')) kopfEl.classList.toggle('kopf-weg', y > letzteY && y > 400);
    letzteY = y; tick = false;
  }
  window.addEventListener('scroll', function () { if (!tick) { tick = true; requestAnimationFrame(beimScrollen); } }, { passive: true });
  beimScrollen();

  // Lichtkegel folgt der Maus, Knöpfe mit leichtem Magnet-Effekt
  if (feinzeiger && !ruhe) {
    d.querySelectorAll('.stelle-zeile, .benefit, .kachel, .f-kachel').forEach(function (k) {
      k.addEventListener('pointermove', function (e) {
        var r = k.getBoundingClientRect();
        k.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        k.style.setProperty('--my', (e.clientY - r.top) + 'px');
      });
    });
    d.querySelectorAll('.knopf').forEach(function (k) {
      k.addEventListener('pointermove', function (e) {
        if (istRuhig()) return;
        var r = k.getBoundingClientRect();
        k.style.transform = 'translate(' + ((e.clientX - r.left - r.width / 2) * .18).toFixed(1) + 'px,' + ((e.clientY - r.top - r.height / 2) * .25).toFixed(1) + 'px)';
      });
      k.addEventListener('pointerleave', function () { k.style.transform = ''; });
    });
  }

  // Zahlen zählen beim Einblenden hoch (bei „Bewegung reduzieren“ sofort der Endwert)
  var zahlen = d.querySelectorAll('[data-zahl]');
  if (zahlen.length && 'IntersectionObserver' in window && !istRuhig()) {
    var zio = new IntersectionObserver(function (e) {
      e.forEach(function (x) {
        if (!x.isIntersecting) return;
        zio.unobserve(x.target);
        var el = x.target, ziel = +el.getAttribute('data-zahl'), start = null, dauer = 1400;
        if (!ziel) return;
        el.textContent = '0';
        function schritt(t) {
          if (start === null) start = t;
          var a = Math.min((t - start) / dauer, 1), w = 1 - Math.pow(1 - a, 3);
          el.textContent = String(Math.round(ziel * w));
          if (a < 1) requestAnimationFrame(schritt);
        }
        requestAnimationFrame(schritt);
      });
    }, { threshold: .6 });
    zahlen.forEach(function (z) { zio.observe(z); });
  }

  // Video: eigener Abspielknopf, danach die normalen Bedienelemente
  d.querySelectorAll('.f-video').forEach(function (f) {
    var v = f.querySelector('video'), k = f.querySelector('.f-play');
    if (!v || !k) return;
    v.controls = false;
    k.addEventListener('click', function () { v.controls = true; f.classList.add('laeuft'); v.play(); });
  });

  // FAQ: immer nur ein Eintrag offen
  d.querySelectorAll('.faq-liste details').forEach(function (det) {
    det.addEventListener('toggle', function () {
      if (det.open) d.querySelectorAll('.faq-liste details[open]').forEach(function (o) { if (o !== det) o.open = false; });
    });
  });

  // Knopf, der das Barrierefreiheits-Widget öffnet
  d.querySelectorAll('[data-bf-oeffnen]').forEach(function (k) {
    k.addEventListener('click', function () { var bk = d.querySelector('.bf-knopf'); if (bk) bk.click(); });
  });

  // Bewerbungsformular
  var form = d.querySelector('.bewerbungsformular');
  if (!form) return;
  var meldung = form.querySelector('.formular-meldung');
  var knopf = form.querySelector('button[type="submit"]');
  var zeit = form.querySelector('input[name="zeit"]');
  if (zeit) zeit.value = String(Date.now());
  var maxMb = +(form.getAttribute('data-max-mb') || 10), maxDateien = +(form.getAttribute('data-max-dateien') || 3);

  function zeige(text, fehler) {
    meldung.textContent = text;
    meldung.classList.toggle('fehler', !!fehler);
    meldung.classList.toggle('erfolg', !fehler);
  }

  function mailRueckfall(grund) {
    // Kein PHP (Vorschau) oder Versand gescheitert: Mailprogramm öffnen, damit keine Bewerbung verloren geht.
    var link = form.querySelector('a[href^="mailto:"]');
    if (!link) return zeige(grund, true);
    var daten = new FormData(form);
    var body = ['Name: ' + daten.get('name'), 'E-Mail: ' + daten.get('email'), 'Telefon: ' + daten.get('telefon'), '', daten.get('nachricht') || ''].join('\n');
    var href = link.getAttribute('href').split('&body=')[0] + '&body=' + encodeURIComponent(body);
    zeige(grund + ' Dein Mailprogramm öffnet sich mit Deinen Angaben. Bitte dort noch den Lebenslauf anhängen.', true);
    window.location.href = href;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var pflicht = ['name', 'email', 'telefon'];
    for (var i = 0; i < pflicht.length; i++) {
      var f = form.elements[pflicht[i]];
      if (!f || !f.value.trim()) { if (f) f.focus(); return zeige('Bitte alle Pflichtfelder (*) ausfüllen.', true); }
    }
    var email = form.elements['email'].value;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { form.elements['email'].focus(); return zeige('Bitte eine gültige E-Mail-Adresse angeben.', true); }
    if (!form.elements['datenschutz'].checked) return zeige('Bitte der Datenverarbeitung zustimmen.', true);
    var dateien = form.elements['unterlagen[]'] ? form.elements['unterlagen[]'].files : [];
    if (dateien.length > maxDateien) return zeige('Bitte höchstens ' + maxDateien + ' Dateien anhängen.', true);
    for (var j = 0; j < dateien.length; j++) {
      if (!/\.pdf$/i.test(dateien[j].name)) return zeige('Bitte nur PDF-Dateien anhängen.', true);
      if (dateien[j].size > maxMb * 1024 * 1024) return zeige('Eine Datei ist größer als ' + maxMb + ' MB.', true);
    }

    knopf.disabled = true;
    zeige('Wird gesendet …', false);
    fetch(form.getAttribute('action'), {
      method: 'POST', body: new FormData(form),
      headers: { 'Accept': 'application/json', 'X-Requested-With': 'fetch' }
    }).then(function (r) {
      if ((r.headers.get('content-type') || '').indexOf('application/json') === -1) throw new Error('kein-php');
      return r.json();
    }).then(function (res) {
      if (res.ok) {
        zeige(res.meldung, false); form.reset();
        form.querySelectorAll('.feld, .feld-reihe, button, .klein').forEach(function (el) { el.hidden = true; });
        meldung.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else { zeige(res.meldung, true); knopf.disabled = false; }
    }).catch(function (err) {
      knopf.disabled = false;
      mailRueckfall(err.message === 'kein-php' ? 'Der Online-Versand ist in der Vorschau noch nicht aktiv.' : 'Der Online-Versand hat gerade nicht geklappt.');
    });
  });
})();
