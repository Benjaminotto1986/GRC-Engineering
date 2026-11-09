"""
gmx_fetch.py – E-Mails aus einem GMX-Postfach abrufen, nach Absender filtern und als JSON speichern.

Konzept:
  GMX bietet keine REST-API, sondern das klassische Mail-Protokoll IMAP.
  IMAP ist ebenfalls eine Schnittstelle: Wir schicken Befehle an einen Server und bekommen Antworten.
  Der Ablauf ist immer gleich:
      1. Verbinden   – verschlüsselte Verbindung zu imap.gmx.net:993 (SSL)
      2. Login       – Benutzername + Passwort
      3. SELECT      – Ordner wählen (z. B. INBOX), hier nur lesend (readonly)
      4. SEARCH      – der SERVER filtert, z. B. FROM "absender@example.de" -> liefert Mail-Nummern
      5. FETCH       – zu jeder Nummer die komplette Mail (Rohformat RFC822) holen
      6. Parsen      – Rohformat mit dem Modul "email" in Absender, Betreff, Text zerlegen
      7. Speichern   – Liste von Dicts als JSON-Datei (dasselbe Format, das REST-APIs sprechen)

Nutzung:
  python gmx_fetch.py --von absender@example.de [--ordner INBOX] [--max 50] [--aus mails.json]
Zugangsdaten:
  Aus den Umgebungsvariablen GMX_USER und GMX_PASSWORD – fehlen sie, fragt das Skript nach.
  Das Passwort gehört NIE in den Code oder ins Repository.
Nur Python-Standardbibliothek, keine Installation nötig.
"""

import argparse  # Kommandozeilen-Optionen (--von, --max, ...) komfortabel einlesen
import email     # Rohe Mails (RFC822) in ihre Bestandteile zerlegen
import getpass   # Passwort abfragen, ohne dass es am Bildschirm erscheint
import imaplib   # IMAP-Client: die eigentliche "Schnittstelle" zum Mailserver
import json      # Ergebnis als JSON speichern
import os        # Umgebungsvariablen lesen
import re        # HTML-Tags grob entfernen, falls eine Mail nur HTML enthält
import sys       # Fehler-Ausgabe und Exit-Code
from email.header import decode_header           # kodierte Header wie "=?utf-8?q?Gr=C3=BC=C3=9Fe?=" lesbar machen
from email.utils import parsedate_to_datetime    # Datums-Header in ein datetime-Objekt umwandeln

IMAP_HOST = "imap.gmx.net"  # IMAP-Server von GMX (für gmx.de und gmx.net gleich)
IMAP_PORT = 993             # Standard-Port für IMAP über SSL
MAX_TEXT = 2000             # Mail-Text wird auf so viele Zeichen gekürzt, damit die JSON übersichtlich bleibt


def connect(user, password):
    """Verschlüsselte Verbindung zum GMX-Server aufbauen und einloggen. Gibt das IMAP-Objekt zurück."""
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    imap.login(user, password)  # wirft imaplib.IMAP4.error, wenn Login fehlschlägt
    return imap


def search_by_sender(imap, sender, folder="INBOX"):
    """
    Ordner lesend öffnen und den SERVER nach Mails eines Absenders suchen lassen.
    readonly=True: Mails werden durch das Abrufen NICHT als gelesen markiert.
    Rückgabe: Liste von Mail-Nummern (als Bytes, z. B. [b'12', b'15']).
    """
    status, _ = imap.select(folder, readonly=True)
    if status != "OK":
        raise RuntimeError(f"Ordner '{folder}' konnte nicht geöffnet werden.")
    # IMAP-Befehl: SEARCH FROM "absender". Anführungszeichen, damit auch Namen mit Leerzeichen gehen.
    # Teil-Treffer funktionieren: "@bsi.bund.de" findet alle Absender dieser Domain.
    status, data = imap.search(None, "FROM", f'"{sender}"')
    if status != "OK":
        raise RuntimeError("Suche auf dem Server fehlgeschlagen.")
    return data[0].split()  # data ist z. B. [b'12 15 20'] -> [b'12', b'15', b'20']


def decode(value):
    """
    Mail-Header lesbar machen. Header dürfen eigentlich nur ASCII enthalten,
    Umlaute werden deshalb kodiert (z. B. '=?utf-8?q?Gr=C3=BC=C3=9Fe?='). decode_header zerlegt das in Stücke.
    """
    if value is None:
        return ""
    parts = []
    for text, charset in decode_header(value):
        if isinstance(text, bytes):
            parts.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(text)
    return "".join(parts)


def body_text(msg):
    """
    Den Text einer Mail holen. Mails sind oft "multipart": mehrere Teile (Text, HTML, Anhänge).
    Bevorzugt wird der reine Text (text/plain); gibt es nur HTML, werden die Tags grob entfernt.
    """
    plain, html = None, None
    for part in msg.walk():  # walk() geht durch alle Teile, auch verschachtelte
        if part.get_content_disposition() == "attachment":
            continue  # Anhänge überspringen
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)  # decode=True löst base64 / quoted-printable auf
        if payload is None:
            continue
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if ctype == "text/plain" and plain is None:
            plain = text
        elif ctype == "text/html" and html is None:
            html = text
    if plain is not None:
        return plain.strip()
    if html is not None:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
    return ""


def parse(raw):
    """Eine rohe Mail (Bytes) in ein übersichtliches Dict umwandeln – eine 'Zeile' für die JSON-Datei."""
    msg = email.message_from_bytes(raw)
    try:
        datum = parsedate_to_datetime(msg["Date"]).isoformat()  # ISO-Format, z. B. 2026-11-09T08:15:00+01:00
    except (TypeError, ValueError):
        datum = msg.get("Date", "")
    return {
        "datum": datum,
        "von": decode(msg["From"]),
        "an": decode(msg["To"]),
        "betreff": decode(msg["Subject"]),
        "text": body_text(msg)[:MAX_TEXT],
    }


def fetch(imap, ids, limit):
    """Die neuesten 'limit' Mails aus der Trefferliste vollständig holen und parsen."""
    mails = []
    for num in reversed(ids[-limit:]):  # höchste Nummer = neueste Mail, also von hinten
        status, data = imap.fetch(num, "(RFC822)")
        if status != "OK" or not data or data[0] is None:
            print(f"Mail {num.decode()} konnte nicht geladen werden – übersprungen.", file=sys.stderr)
            continue
        raw = data[0][1]  # data[0] ist ein Tupel: (Befehlsinfo, Mail-Bytes)
        mails.append(parse(raw))
    return mails


def main():
    parser = argparse.ArgumentParser(description="GMX-Mails nach Absender filtern und als JSON speichern.")
    parser.add_argument("--von", required=True, help="Absender (ganz oder Teil, z. B. '@bsi.bund.de')")
    parser.add_argument("--ordner", default="INBOX", help="IMAP-Ordner (Standard: INBOX)")
    parser.add_argument("--max", type=int, default=50, help="Höchstens so viele (neueste) Mails holen (Standard: 50)")
    parser.add_argument("--aus", default="mails.json", help="Ausgabedatei (Standard: mails.json)")
    args = parser.parse_args()

    # Zugangsdaten: zuerst Umgebungsvariablen, sonst interaktiv abfragen.
    user = os.environ.get("GMX_USER") or input("GMX-Adresse: ")
    password = os.environ.get("GMX_PASSWORD") or getpass.getpass("GMX-Passwort: ")

    try:
        imap = connect(user, password)
    except imaplib.IMAP4.error as e:
        sys.exit(f"Login fehlgeschlagen ({e}). Ist IMAP in den GMX-Einstellungen aktiviert?")

    try:
        ids = search_by_sender(imap, args.von, args.ordner)
        print(f"{len(ids)} Mails von '{args.von}' gefunden, lade die neuesten {min(len(ids), args.max)} ...")
        mails = fetch(imap, ids, args.max)
    finally:
        imap.logout()  # Verbindung immer sauber schließen, auch bei Fehlern

    with open(args.aus, "w", encoding="utf-8") as f:
        # ensure_ascii=False: Umlaute bleiben lesbar statt ü; indent=2: hübsch eingerückt
        json.dump(mails, f, ensure_ascii=False, indent=2)
    print(f"{len(mails)} Mails gespeichert in {args.aus}")


if __name__ == "__main__":
    main()
