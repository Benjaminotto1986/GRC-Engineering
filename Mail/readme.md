# GMX-Mails per Python abrufen

`gmx_fetch.py` holt Mails eines bestimmten Absenders aus dem GMX-Postfach und speichert sie als JSON.
Nur Python-Standardbibliothek – keine Installation nötig.

## Einrichtung (einmalig)
1. GMX im Browser öffnen → **E-Mail → Einstellungen → POP3/IMAP Abruf** →
   „Zugriff auf dieses Postfach über externe Programme erlauben“ aktivieren.
2. Bei aktivierter Zwei-Faktor-Authentifizierung ein **anwendungsspezifisches Passwort** anlegen
   und dieses statt des normalen Passworts verwenden.

## Aufruf
```bash
python gmx_fetch.py --von newsletter@example.de
```
Optionen: `--ordner INBOX` · `--max 50` · `--aus mails.json`.
`--von` darf auch nur ein Teil sein, z. B. `--von @bsi.bund.de` für alle Absender dieser Domain.

Zugangsdaten werden abgefragt – oder vorab als Umgebungsvariablen gesetzt (z. B. in der PowerShell):
```powershell
$env:GMX_USER = "dein.name@gmx.de"
$env:GMX_PASSWORD = "..."
```
**Passwörter nie in den Code oder ins Repo schreiben.** Die erzeugten `*.json`-Dateien in diesem Ordner
sind per `.gitignore` ausgeschlossen, damit keine Mail-Inhalte versehentlich auf GitHub landen.

## Ergebnis (Beispiel)
```json
[
  {
    "datum": "2026-11-09T08:15:00+01:00",
    "von": "BSI Newsletter <newsletter@example.de>",
    "an": "dein.name@gmx.de",
    "betreff": "Sicherheitswarnung …",
    "text": "Erste 2000 Zeichen des Mail-Textes …"
  }
]
```

## Was lernt man hier?
- **IMAP vs. REST-API:** Beides sind Schnittstellen. IMAP ist ein älteres Protokoll mit eigenen Befehlen
  (`LOGIN`, `SELECT`, `SEARCH`, `FETCH`); REST-APIs sprechen HTTP und meist JSON. Das Prinzip ist gleich:
  Anfrage schicken → Antwort auswerten.
- **Server-seitiges Filtern:** `SEARCH FROM "…"` lässt den GMX-Server filtern – es werden nur die
  Treffer übertragen, nicht das ganze Postfach.
- **readonly:** Der Ordner wird nur lesend geöffnet, Mails bleiben also ungelesen.
- **JSON:** Das Ausgabeformat ist dasselbe, das REST-APIs verwenden.

## Nächste Lernschritte
- Weitere Filter ergänzen (`SINCE 01-Nov-2026`, `SUBJECT "…"`, `UNSEEN`) – mehrere Kriterien
  einfach hintereinander an `imap.search(...)` übergeben.
- Die JSON-Datei an eine echte REST-API schicken (`urllib.request` oder das Paket `requests`).
