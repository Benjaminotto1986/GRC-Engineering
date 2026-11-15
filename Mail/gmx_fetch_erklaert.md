# `gmx_fetch.py` – Zeile für Zeile erklärt

> Lies diese Erklärung **neben** dem Skript (in VS Code: Rechtsklick auf die Datei → „Open to the Side“).
> Die Zeilennummern beziehen sich auf `gmx_fetch.py`. Am Ende jedes Abschnitts stehen Kontrollfragen –
> versuche sie zu beantworten, **bevor** du weiterliest.

---

## Zeilen 1–22: Docstring
```python
"""
gmx_fetch.py – E-Mails ...
"""
```
- Drei Anführungszeichen `"""` öffnen einen **mehrzeiligen String**. Steht er ganz oben in einer Datei,
  heißt er **Docstring** – die Beschreibung des Moduls. Python führt ihn nicht aus, aber
  `help(gmx_fetch)` zeigt ihn an. Gute Praxis: Zweck, Ablauf, Aufruf beschreiben.

---

## Zeilen 24–33: Imports
| Zeile | Code | Erklärung |
|---|---|---|
| 24 | `import argparse` | Lädt das Modul zum Auswerten von Kommandozeilen-Optionen wie `--von`. `#` leitet einen **Kommentar** ein – alles danach ignoriert Python. |
| 25 | `import email` | Modul, das das Mail-Rohformat (RFC822) in Header und Teile zerlegt. |
| 26 | `import getpass` | Fragt Passwörter ab, ohne sie anzuzeigen. |
| 27 | `import imaplib` | Der IMAP-**Client**: spricht das IMAP-Protokoll mit dem Server. |
| 28 | `import json` | Wandelt Python-Listen/Dicts in JSON-Text um (und zurück). |
| 29 | `import os` | Zugriff aufs Betriebssystem, hier: Umgebungsvariablen (`os.environ`). |
| 30 | `import re` | **Reguläre Ausdrücke** (Regex) – Textmuster suchen/ersetzen. |
| 31 | `import sys` | Systemfunktionen: Fehlerausgabe (`sys.stderr`), Programm beenden (`sys.exit`). |
| 32 | `from email.header import decode_header` | Holt **nur eine Funktion** aus einem Untermodul. Danach kann man `decode_header(...)` direkt schreiben statt `email.header.decode_header(...)`. |
| 33 | `from email.utils import parsedate_to_datetime` | Wandelt einen Datums-Text wie `Mon, 09 Nov 2026 08:15:00 +0100` in ein `datetime`-Objekt. |

Alle Module gehören zur **Standardbibliothek** – sie sind mit Python installiert, kein `pip install` nötig.

**Kontrollfragen:** Was ist der Unterschied zwischen `import email` und `from email.header import decode_header`?
Was passiert, wenn du Zeile 28 löschst?

---

## Zeilen 35–37: Konstanten
| Zeile | Code | Erklärung |
|---|---|---|
| 35 | `IMAP_HOST = "imap.gmx.net"` | Eine **Variable** mit einem **String** (Text). GROSSBUCHSTABEN sind eine Konvention für **Konstanten** – Werte, die sich nicht ändern sollen. Python erzwingt das nicht. |
| 36 | `IMAP_PORT = 993` | Ein **Integer** (Ganzzahl). 993 = IMAP über SSL/TLS (verschlüsselt). |
| 37 | `MAX_TEXT = 2000` | Wie viele Zeichen Mail-Text gespeichert werden. |

**Warum oben?** Wer das Skript für web.de anpassen will, ändert nur Zeile 35 – nicht irgendwo im Code.

---

## Zeilen 40–44: `connect()` – Verbindung + Login
| Zeile | Code | Erklärung |
|---|---|---|
| 40 | `def connect(user, password):` | `def` definiert eine **Funktion** namens `connect` mit zwei **Parametern**. Der Doppelpunkt leitet den **Block** ein; alles Eingerückte (4 Leerzeichen) gehört dazu. |
| 41 | `"""Verschlüsselte ..."""` | Docstring der Funktion. |
| 42 | `imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)` | Erzeugt ein **Objekt** der Klasse `IMAP4_SSL`. Dabei wird sofort die verschlüsselte TCP-Verbindung zu `imap.gmx.net:993` aufgebaut. Das Objekt merken wir uns in `imap`. |
| 43 | `imap.login(user, password)` | Ruft die **Methode** `login` des Objekts auf → sendet den IMAP-Befehl `LOGIN`. Bei falschen Daten **wirft** sie eine Ausnahme (`IMAP4.error`) – genau das war dein `authentication failed`. |
| 44 | `return imap` | Gibt das eingeloggte Objekt an den Aufrufer zurück. |

**Kontrollfrage:** Wo im Skript wird `connect` aufgerufen, und was passiert dort mit der Ausnahme?

---

## Zeilen 47–61: `search_by_sender()` – Server filtern lassen
| Zeile | Code | Erklärung |
|---|---|---|
| 47 | `def search_by_sender(imap, sender, folder="INBOX"):` | `folder="INBOX"` ist ein **Default-Wert**: Gibt der Aufrufer nichts an, gilt `"INBOX"`. |
| 48–52 | Docstring | – |
| 53 | `status, _ = imap.select(folder, readonly=True)` | IMAP-Befehl `SELECT` (bzw. `EXAMINE` bei readonly) öffnet den Ordner. Die Methode liefert **zwei Werte** (ein **Tupel**); wir **entpacken** sie in `status` und `_`. Der Unterstrich ist Konvention für „brauche ich nicht“. |
| 54 | `if status != "OK":` | **Bedingung**: `!=` heißt „ungleich“. IMAP antwortet mit `OK`, `NO` oder `BAD`. |
| 55 | `raise RuntimeError(...)` | **Wirft** selbst eine Ausnahme → das Programm bricht ab (wenn niemand sie abfängt). `f"...{folder}..."` ist ein **f-String**: `{folder}` wird durch den Variablenwert ersetzt. |
| 56–57 | Kommentare | – |
| 58 | `status, data = imap.search(None, "FROM", f'"{sender}"')` | IMAP-Befehl `SEARCH FROM "grcengineer.com"`. `None` = Zeichensatz-Angabe (keine). Der **Server** filtert, wir bekommen nur Treffernummern. Die inneren `"` gehören zum IMAP-Befehl, die äußeren `'` zum Python-String. |
| 59–60 | `if status != "OK": raise ...` | Wie oben. |
| 61 | `return data[0].split()` | `data` ist eine Liste mit einem Element, z. B. `[b'12 15']`. `data[0]` holt das erste Element (Index 0!). `b'...'` sind **Bytes** (Rohdaten, nicht Text). `.split()` teilt an Leerzeichen → `[b'12', b'15']`. |

**Kontrollfragen:** Was würde passieren, wenn du `readonly=True` weglässt?
Warum ist es besser, dass der Server filtert, statt alle Mails zu laden und in Python zu filtern?

---

## Zeilen 64–77: `decode()` – Header lesbar machen
| Zeile | Code | Erklärung |
|---|---|---|
| 64 | `def decode(value):` | – |
| 69–70 | `if value is None: return ""` | `None` = „kein Wert“ (z. B. Mail ohne Betreff). `is` prüft auf **Identität** – bei `None` immer `is` statt `==` verwenden. Wir geben einen leeren String zurück, damit später nichts abstürzt. |
| 71 | `parts = []` | Leere **Liste** zum Sammeln. |
| 72 | `for text, charset in decode_header(value):` | **Schleife**: `decode_header` liefert eine Liste von Paaren `(text, zeichensatz)`, z. B. `[(b'Gr\xc3\xbc\xc3\x9fe', 'utf-8')]`. Jedes Paar wird direkt in zwei Variablen entpackt. |
| 73 | `if isinstance(text, bytes):` | Prüft den **Datentyp**: Ist `text` Bytes (noch kodiert)? |
| 74 | `parts.append(text.decode(charset or "utf-8", errors="replace"))` | `.decode()` wandelt Bytes → String. `charset or "utf-8"`: ist `charset` leer/`None`, nimm `"utf-8"` (der `or`-Trick). `errors="replace"` ersetzt kaputte Zeichen durch `�` statt abzustürzen. `.append()` hängt an die Liste an. |
| 75–76 | `else: parts.append(text)` | War es schon ein String, unverändert übernehmen. |
| 77 | `return "".join(parts)` | Fügt alle Listenteile zu einem String zusammen (Trennzeichen: `""` = nichts). |

**Kontrollfrage:** Was gibt `"-".join(["a", "b", "c"])` zurück?

---

## Zeilen 80–104: `body_text()` – den Mail-Text finden
| Zeile | Code | Erklärung |
|---|---|---|
| 85 | `plain, html = None, None` | Zwei Variablen gleichzeitig setzen. Wir merken uns den ersten Text- und den ersten HTML-Teil. |
| 86 | `for part in msg.walk():` | Eine Mail ist ein **Baum** aus Teilen (Text, HTML, Anhänge, verschachtelt). `walk()` läuft alle Teile durch. |
| 87–88 | `if ... == "attachment": continue` | `continue` springt sofort zum **nächsten Schleifendurchlauf** – Anhänge überspringen. |
| 89 | `ctype = part.get_content_type()` | Der **MIME-Typ**, z. B. `"text/plain"`, `"text/html"`, `"image/png"`. |
| 90–91 | `if ctype not in (...): continue` | `not in` prüft, ob der Wert **nicht** in dem Tupel steht. Alles außer Text/HTML überspringen. |
| 92 | `payload = part.get_payload(decode=True)` | Holt den Inhalt als Bytes; `decode=True` entfernt die Transport-Kodierung (base64, quoted-printable). |
| 93–94 | `if payload is None: continue` | Leerer Teil → überspringen. |
| 95 | `text = payload.decode(...)` | Bytes → String, mit dem Zeichensatz, den der Teil angibt. |
| 96–97 | `if ctype == "text/plain" and plain is None: plain = text` | Nur den **ersten** Textteil merken (`and` = beide Bedingungen müssen wahr sein). |
| 98–99 | `elif ... html = text` | `elif` = „sonst, wenn“. Ersten HTML-Teil merken. |
| 100–101 | `if plain is not None: return plain.strip()` | Textversion bevorzugen. `.strip()` entfernt Leerzeichen/Zeilenumbrüche am Rand. |
| 102–103 | `return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()` | Von innen nach außen lesen: 1) `re.sub(r"<[^>]+>", " ", html)` ersetzt alles von `<` bis `>` (HTML-Tags) durch Leerzeichen. 2) `re.sub(r"\s+", " ", ...)` fasst mehrere Leerzeichen/Umbrüche zu einem zusammen. `r"..."` = **Raw-String**, damit `\s` nicht als Escape gedeutet wird. |
| 104 | `return ""` | Weder Text noch HTML gefunden. |

**Kontrollfrage:** Warum steht `plain is None` in der Bedingung von Zeile 96 – was würde ohne passieren?

---

## Zeilen 107–120: `parse()` – Rohmail → Dict
| Zeile | Code | Erklärung |
|---|---|---|
| 109 | `msg = email.message_from_bytes(raw)` | Zerlegt die Rohbytes in ein `Message`-Objekt, auf dessen Header man wie auf ein Dict zugreift: `msg["From"]`. |
| 110 | `try:` | Beginn eines **try-Blocks**: „Versuch das – wenn ein Fehler kommt, geh zu `except`.“ |
| 111 | `datum = parsedate_to_datetime(msg["Date"]).isoformat()` | Datum lesen und ins **ISO-8601-Format** bringen (`2026-11-09T08:15:00+01:00`) – sortierbar und international eindeutig. Zwei Aufrufe hintereinander (**Method Chaining**). |
| 112 | `except (TypeError, ValueError):` | Fängt genau diese zwei Fehlertypen ab (fehlendes oder kaputtes Datum). Nie pauschal `except:` ohne Typ – sonst versteckst du echte Fehler. |
| 113 | `datum = msg.get("Date", "")` | `.get(schlüssel, standard)`: liefert den Wert oder `""`, wenn er fehlt – stürzt nie ab. |
| 114–120 | `return { "datum": ..., ... }` | Ein **Dictionary** (Dict): Schlüssel → Wert. Genau diese Struktur landet später als JSON-Objekt in der Datei. `[:MAX_TEXT]` ist **Slicing**: die ersten 2000 Zeichen. |

**Kontrollfrage:** Was ist der Unterschied zwischen `msg["Date"]` und `msg.get("Date", "")`?

---

## Zeilen 123–133: `fetch()` – Mails holen
| Zeile | Code | Erklärung |
|---|---|---|
| 125 | `mails = []` | Ergebnisliste. |
| 126 | `for num in reversed(ids[-limit:]):` | `ids[-limit:]` = **die letzten `limit` Elemente** (negativer Index zählt von hinten). `reversed()` dreht die Reihenfolge um → neueste zuerst. |
| 127 | `status, data = imap.fetch(num, "(RFC822)")` | IMAP-Befehl `FETCH 12 (RFC822)`: „gib mir Mail 12 komplett im Rohformat“. |
| 128 | `if status != "OK" or not data or data[0] is None:` | Drei Fehlerfälle mit `or` verknüpft – trifft **einer** zu, gilt die Bedingung. `not data` ist wahr bei leerer Liste. |
| 129 | `print(..., file=sys.stderr)` | Ausgabe auf den **Fehlerkanal** statt die normale Ausgabe. `num.decode()` macht aus `b'12'` den Text `'12'`. |
| 130 | `continue` | Diese Mail überspringen, mit der nächsten weitermachen. |
| 131 | `raw = data[0][1]` | **Verschachtelter Index**: `data[0]` ist ein Tupel `(b'12 (RFC822 {4711}', b'...Mail...')`, davon `[1]` = die Mail-Bytes. |
| 132 | `mails.append(parse(raw))` | Parsen und das Dict an die Liste hängen. |
| 133 | `return mails` | Liste von Dicts zurückgeben. |

**Kontrollfrage:** `ids = [b'1', b'2', b'3', b'4']`, `limit = 2` – welche Nummern holt die Schleife, in welcher Reihenfolge?

---

## Zeilen 136–171: `main()` – das Hauptprogramm
| Zeile | Code | Erklärung |
|---|---|---|
| 137 | `parser = argparse.ArgumentParser(description=...)` | Erzeugt den Kommandozeilen-Parser. `description` erscheint bei `--help`. |
| 138 | `parser.add_argument("--von", required=True, help=...)` | Definiert die Option `--von`, **Pflicht**. |
| 139 | `... "--ordner", default="INBOX"` | Optional, mit Standardwert. |
| 140 | `... "--max", type=int, default=50` | `type=int` wandelt die Eingabe (immer Text!) in eine Zahl um. |
| 141 | `... "--aus", default="mails.json"` | Ausgabedatei. |
| 142 | `args = parser.parse_args()` | Liest die echten Argumente. Danach: `args.von`, `args.max` usw. |
| 146 | `user = (os.environ.get("GMX_USER") or input("GMX-Adresse: ")).strip()` | `os.environ` ist ein Dict mit allen Umgebungsvariablen. Fehlt `GMX_USER`, liefert `.get` `None` → wegen `or` wird `input(...)` ausgeführt, das den Nutzer fragt. Danach `.strip()`. |
| 147 | `password = (... getpass.getpass(...)).strip()` | Gleiches Muster, Eingabe unsichtbar. |
| 148 | `quelle = "Umgebungsvariablen" if ... else "Eingabe"` | **Bedingter Ausdruck** (Ternary): `A if Bedingung else B` in einer Zeile. |
| 149 | `print(f"Login als {user!r} ...")` | `!r` zeigt die **repr**-Darstellung, also mit Anführungszeichen – so sieht man versteckte Leerzeichen. `len(password)` = Anzahl Zeichen (nie das Passwort selbst ausgeben!). |
| 151–152 | `try: imap = connect(user, password)` | Login versuchen. |
| 153–154 | `except UnicodeEncodeError: sys.exit(...)` | Sonderzeichen im Passwort. `sys.exit("Text")` gibt den Text aus und beendet mit Fehlercode 1. |
| 155–159 | `except imaplib.IMAP4.error as e: sys.exit(...)` | `as e` speichert die Ausnahme in `e`, damit wir die Server-Meldung anzeigen können. Mehrere Strings direkt hintereinander werden automatisch verbunden; `\n` = Zeilenumbruch. |
| 161–164 | `try: ids = ...; print(...); mails = fetch(...)` | Suchen und holen. `min(a, b)` = die kleinere Zahl. |
| 165–166 | `finally: imap.logout()` | `finally` läuft **immer** – auch wenn im try ein Fehler auftritt. So wird die Verbindung nie offen gelassen (sauberes Ressourcen-Management). |
| 168 | `with open(args.aus, "w", encoding="utf-8") as f:` | Datei zum **Schreiben** (`"w"`, überschreibt!) öffnen. `with` schließt die Datei automatisch am Blockende – auch bei Fehlern. |
| 170 | `json.dump(mails, f, ensure_ascii=False, indent=2)` | Liste von Dicts → JSON in die Datei. `ensure_ascii=False`: `ü` bleibt `ü`. `indent=2`: lesbar eingerückt. |
| 171 | `print(...)` | Erfolgsmeldung. |

---

## Zeilen 174–175: Einstiegspunkt
```python
if __name__ == "__main__":
    main()
```
- `__name__` ist eine spezielle Variable. Startest du die Datei direkt (`python gmx_fetch.py`), ist sie `"__main__"` → `main()` läuft.
- Importierst du die Datei in einem anderen Skript (`import gmx_fetch`), ist sie `"gmx_fetch"` → `main()` läuft **nicht**,
  aber du kannst die Funktionen (`parse`, `decode` …) wiederverwenden. So habe ich das Skript auch getestet.

---

## Gesamtbild
```
main()
 ├─ argparse            → Optionen lesen
 ├─ connect()           → TLS-Verbindung + LOGIN
 ├─ search_by_sender()  → SELECT (readonly) + SEARCH FROM
 ├─ fetch()             → FETCH je Nummer
 │    └─ parse()        → Header + Text
 │         ├─ decode()
 │         └─ body_text()
 ├─ logout()            (finally)
 └─ json.dump()         → mails.json
```
