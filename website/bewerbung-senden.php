<?php
/**
 * bewerbung-senden.php – nimmt eine Bewerbung entgegen und verschickt zwei Mails:
 *   1. an die Empfänger der Stelle (aus bewerbung-konfiguration.php, NIE aus dem Formular):
 *      alle Angaben + PDF-Anhänge
 *   2. an den Bewerber: Eingangsbestätigung (ohne Anhänge)
 *
 * Speichert nichts auf dem Server. Antwortet mit JSON (für app.js) oder leitet
 * ohne JavaScript auf danke.html weiter.
 *
 * Schutz: Honigtopf-Feld "webseite" (muss leer bleiben), Zeitsperre 3 Sekunden,
 * Empfänger nur über die Stellen-Kennung, Anhänge nur PDF bis max_mb, Kopfzeilen bereinigt.
 *
 * Läuft auf All-Inkl mit PHP 8.1+. Auf GitHub Pages (Vorschau) läuft kein PHP – dort
 * schaltet app.js auf den E-Mail-Rückfallweg um.
 */
declare(strict_types=1);
mb_internal_encoding('UTF-8');

$konfig = require __DIR__ . '/bewerbung-konfiguration.php';
$istAjax = isset($_SERVER['HTTP_X_REQUESTED_WITH']) || (($_SERVER['HTTP_ACCEPT'] ?? '') && str_contains($_SERVER['HTTP_ACCEPT'], 'application/json'));

function antwort(bool $ok, string $meldung, int $status = 200): never {
    global $istAjax;
    http_response_code($status);
    if ($istAjax) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(['ok' => $ok, 'meldung' => $meldung], JSON_UNESCAPED_UNICODE);
    } else {
        header('Location: ' . ($ok ? 'danke.html' : 'fehler.html?grund=' . rawurlencode($meldung)));
    }
    exit;
}
function feld(string $name): string {
    $w = $_POST[$name] ?? '';
    return is_string($w) ? trim(str_replace(["\r", "\n"], ' ', $w)) : '';
}
function betreff(string $s): string { return '=?UTF-8?B?' . base64_encode($s) . '?='; }

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') antwort(false, 'Nur POST erlaubt.', 405);

// --- Schutz ---
if (feld('webseite') !== '') antwort(true, 'Danke.');                       // Roboter: still schlucken
$zeit = (int) feld('zeit');
if ($zeit > 0 && (time() * 1000 - $zeit) < 3000) antwort(false, 'Bitte nimm Dir einen Moment Zeit und sende das Formular erneut.', 429);

// --- Stelle und Empfänger ---
$kennung = feld('stelle');
if ($kennung === '' || !isset($konfig[$kennung]) || str_starts_with($kennung, '_')) antwort(false, 'Unbekannte Stelle.', 400);
$stelle = $konfig[$kennung];
$empfaenger = array_values(array_filter($stelle['empfaenger'], fn($e) => filter_var($e, FILTER_VALIDATE_EMAIL)));
if (!$empfaenger) antwort(false, 'Für diese Stelle ist keine Empfängeradresse hinterlegt.', 500);

// --- Pflichtfelder (dritte Prüfung nach Browser und app.js) ---
$name = feld('name'); $email = feld('email'); $telefon = feld('telefon');
if (mb_strlen($name) < 2) antwort(false, 'Bitte Deinen Namen angeben.', 422);
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) antwort(false, 'Bitte eine gültige E-Mail-Adresse angeben.', 422);
if (mb_strlen(preg_replace('/\D/', '', $telefon)) < 6) antwort(false, 'Bitte eine Telefonnummer angeben.', 422);
if (feld('datenschutz') !== 'ja') antwort(false, 'Bitte der Datenverarbeitung zustimmen.', 422);
$nachricht = trim((string) ($_POST['nachricht'] ?? ''));
$zusatz = [];
foreach ((array) ($_POST['zusatz'] ?? []) as $k => $v) {
    if (is_string($v) && trim($v) !== '') $zusatz[preg_replace('/[^a-z0-9_]/i', '', (string) $k)] = trim(str_replace(["\r", "\n"], ' ', $v));
}

// --- Anhänge: nur PDF, Größe begrenzt, Inhalt geprüft ---
$anhaenge = [];
$maxDateien = (int) ($konfig['_max_dateien'] ?? 3);
$maxBytes = (int) ($konfig['_max_mb'] ?? 10) * 1024 * 1024;
if (!empty($_FILES['unterlagen']['name'][0])) {
    $n = count($_FILES['unterlagen']['name']);
    if ($n > $maxDateien) antwort(false, "Bitte höchstens $maxDateien Dateien anhängen.", 422);
    $finfo = new finfo(FILEINFO_MIME_TYPE);
    for ($i = 0; $i < $n; $i++) {
        if ($_FILES['unterlagen']['error'][$i] === UPLOAD_ERR_NO_FILE) continue;
        if ($_FILES['unterlagen']['error'][$i] !== UPLOAD_ERR_OK) antwort(false, 'Eine Datei konnte nicht hochgeladen werden.', 422);
        $tmp = $_FILES['unterlagen']['tmp_name'][$i];
        if ($_FILES['unterlagen']['size'][$i] > $maxBytes) antwort(false, 'Eine Datei ist zu groß (max. ' . ($konfig['_max_mb'] ?? 10) . ' MB).', 422);
        if ($finfo->file($tmp) !== 'application/pdf') antwort(false, 'Bitte nur PDF-Dateien anhängen.', 422);
        $dateiname = preg_replace('/[^A-Za-z0-9._-]/', '_', basename((string) $_FILES['unterlagen']['name'][$i]));
        if (!str_ends_with(strtolower($dateiname), '.pdf')) $dateiname .= '.pdf';
        $anhaenge[] = ['name' => $dateiname, 'inhalt' => file_get_contents($tmp)];
    }
}

// --- Mail 1: an die Praxis / das Unternehmen ---
$absender = $konfig['_absender'] ?: ('bewerbung@' . ($_SERVER['SERVER_NAME'] ?? 'localhost'));
$absenderName = $konfig['_absender_name'] ?: $konfig['_firma'];
$zeilen = [
    "Neue Bewerbung über die Karriereseite",
    "",
    "Stelle:    {$stelle['titel']}",
    "Standort:  {$stelle['standort']}",
    "Eingang:   " . date('d.m.Y H:i') . " Uhr",
    "",
    "Name:      $name",
    "E-Mail:    $email",
    "Telefon:   $telefon",
];
foreach ($zusatz as $k => $v) $zeilen[] = str_pad(ucfirst(str_replace('_', ' ', $k)) . ':', 11) . $v;
$zeilen[] = "";
$zeilen[] = "Nachricht:";
$zeilen[] = $nachricht !== '' ? $nachricht : "(keine)";
$zeilen[] = "";
$zeilen[] = $anhaenge ? "Anhänge: " . implode(', ', array_column($anhaenge, 'name')) : "Anhänge: keine";
$zeilen[] = "";
$zeilen[] = "Antworten geht direkt an den Bewerber (Antwort-Adresse ist gesetzt).";
$zeilen[] = "Hinweis: Bewerberdaten nach Abschluss des Verfahrens spätestens nach " . ($konfig['_loeschfrist_monate'] ?? 6) . " Monaten löschen.";
$text = implode("\r\n", $zeilen);

$grenze = 'grenze_' . bin2hex(random_bytes(12));
$kopf = "From: " . betreff($absenderName) . " <$absender>\r\n"
      . "Reply-To: " . betreff($name) . " <$email>\r\n"
      . "MIME-Version: 1.0\r\n"
      . "X-Mailer: Karriereseite\r\n";
if ($anhaenge) {
    $kopf .= "Content-Type: multipart/mixed; boundary=\"$grenze\"\r\n";
    $body = "--$grenze\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit\r\n\r\n$text\r\n";
    foreach ($anhaenge as $a) {
        $body .= "--$grenze\r\nContent-Type: application/pdf; name=\"{$a['name']}\"\r\n"
               . "Content-Disposition: attachment; filename=\"{$a['name']}\"\r\nContent-Transfer-Encoding: base64\r\n\r\n"
               . chunk_split(base64_encode($a['inhalt'])) . "\r\n";
    }
    $body .= "--$grenze--\r\n";
} else {
    $kopf .= "Content-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit\r\n";
    $body = $text;
}
$ok1 = mail(implode(', ', $empfaenger), betreff("Bewerbung: {$stelle['titel']}, $name"), $body, $kopf, "-f$absender");

// --- Mail 2: Eingangsbestätigung an den Bewerber ---
$bestaetigung = "Hallo $name,\r\n\r\n"
    . "vielen Dank für Deine Bewerbung als {$stelle['titel']} ({$stelle['standort']}). Sie ist bei uns eingegangen.\r\n\r\n"
    . ($konfig['_antwortzeit'] ? $konfig['_antwortzeit'] . "\r\n\r\n" : "")
    . "Deine Angaben:\r\nName: $name\r\nE-Mail: $email\r\nTelefon: $telefon\r\n"
    . ($anhaenge ? "Anhänge: " . implode(', ', array_column($anhaenge, 'name')) . "\r\n" : "")
    . "\r\nViele Grüße\r\n{$konfig['_firma']}\r\n";
$kopf2 = "From: " . betreff($absenderName) . " <$absender>\r\n"
       . "Reply-To: " . $empfaenger[0] . "\r\n"
       . "MIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit\r\n";
$ok2 = mail($email, betreff("Deine Bewerbung bei {$konfig['_firma']} ist eingegangen"), $bestaetigung, $kopf2, "-f$absender");

if (!$ok1) antwort(false, 'Der Versand hat nicht geklappt. Bitte schick Deine Bewerbung direkt per E-Mail an ' . $empfaenger[0] . '.', 500);
antwort(true, 'Danke! Deine Bewerbung ist angekommen' . ($ok2 ? '. Eine Bestätigung ist unterwegs an ' . $email . '.' : '.'));
