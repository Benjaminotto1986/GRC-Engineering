"""
gspp_flatten.py – Grundschutz++-Katalog (OSCAL-JSON) in eine flache CSV-Tabelle umwandeln.

Konzept:
  Der BSI-Katalog ist ein verschachteltes OSCAL-Dokument:
      catalog -> groups (z. B. BER) -> groups (z. B. BER.5) -> controls (Practices) -> controls (Unter-Practices)
  Jede Practice hat
      props  = Metadaten (Sicherheitsniveau, Aufwand, Schutzziele, Gefährdungen, Tags)
      parts  = Inhalt: "statement" (die Anforderung) und "guidance" (Erläuterung)
      links  = Abhängigkeiten zu anderen Practices (required / related)
      params = Platzhalter im Text ({{ insert: param, ... }}), die DU als Anwender füllst
  Dieses Skript läuft einmal durch den ganzen Baum und schreibt pro Practice eine Zeile.

Nutzung:
  python gspp_flatten.py <Pfad zur resolved_catalog.json> <Ausgabe.csv>
Nur Python-Standardbibliothek, keine Installation nötig.
"""

import csv   # CSV schreiben (Excel-tauglich)
import json  # OSCAL liegt als JSON vor
import re    # Platzhalter im Text ersetzen
import sys   # Kommandozeilen-Argumente lesen


def prop(obj, name):
    """Wert einer OSCAL-Property per Name holen (props ist eine Liste von {name, value}). Leer, wenn nicht vorhanden."""
    return next((p["value"] for p in obj.get("props", []) if p["name"] == name), "")


def part(control, name):
    """Einen Teil (statement oder guidance) einer Practice holen."""
    return next((p for p in control.get("parts", []) if p["name"] == name), {})


def fill_params(text, control):
    """
    Platzhalter wie '{{ insert: param, ber.7.1-prm1 }}' lesbar machen.
    Hat der Parameter ein Label, wird es in [eckigen Klammern] eingesetzt – so siehst du, was DU festlegen musst.
    """
    labels = {p["id"]: p.get("label", p["id"]) for p in control.get("params", [])}
    return re.sub(r"\{\{\s*insert:\s*param,\s*([^\s}]+)\s*\}\}",
                  lambda m: f"[{labels.get(m.group(1), m.group(1))}]", text or "")


def walk(node, path, parent_id, rows):
    """
    Rekursiver Durchlauf durch den Baum.
    path      = Liste der Gruppen (Gruppe, Untergruppe), in denen wir gerade sind
    parent_id = ID der übergeordneten Practice (bei Unter-Practices wie BER.7.16.1)
    """
    for ctrl in node.get("controls", []):
        stm = part(ctrl, "statement")
        gdn = part(ctrl, "guidance")
        links = ctrl.get("links", [])
        rows.append({
            "ID": ctrl["id"],
            "Übergeordnet": parent_id,
            "Gruppe": " – ".join(path[:1]),
            "Untergruppe": " – ".join(path[1:2]),
            "Titel": ctrl.get("title", ""),
            "Anforderung": fill_params(stm.get("prose", ""), ctrl),
            "Modalverb": prop(stm, "modal_verb"),          # MUSS / SOLLTE / KANN
            "Aktionswort": prop(stm, "action_word"),        # was getan wird (aktivieren, verankern …)
            "Ergebnis": prop(stm, "result"),                # was am Ende da sein soll
            "Ergebnis-Spezifikation": prop(stm, "result_specification"),
            "Zielobjekt-Kategorien": prop(stm, "target_object_categories"),
            "Dokumentation": prop(stm, "documentation"),    # in welches Dokument das gehört
            "Sicherheitsniveau": prop(ctrl, "sec_level"),   # normal-SdT oder erhöht
            "Aufwand": prop(ctrl, "effort_level"),          # 0 = gering … höher = aufwendiger
            "Vertraulichkeit": prop(ctrl, "confidentiality"),
            "Integrität": prop(ctrl, "integrity"),
            "Verfügbarkeit": prop(ctrl, "availability"),
            "Authentizität": prop(ctrl, "authenticity"),
            "Gefährdungen": prop(ctrl, "threats"),          # elementare Gefährdungen G 0.x
            "Tags": prop(ctrl, "tags"),
            "Benötigt": ", ".join(l["href"].lstrip("#") for l in links if l.get("rel") == "required"),
            "Verwandt": ", ".join(l["href"].lstrip("#") for l in links if l.get("rel") == "related"),
            "Herkunft": ctrl.get("class", ""),              # Methodik (Prozess) oder Kernel (Technik)
            "Erläuterung": fill_params(gdn.get("prose", ""), ctrl),
        })
        walk(ctrl, path, ctrl["id"], rows)                  # Unter-Practices mitnehmen
    for grp in node.get("groups", []):
        walk(grp, path + [f'{grp["id"]} {grp["title"]}'], parent_id, rows)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        catalog = json.load(f)["catalog"]                   # Wurzelelement eines OSCAL-Katalogs
    rows = []
    walk(catalog, [], "", rows)
    # utf-8-sig + Semikolon: deutsches Excel öffnet die Datei per Doppelklick mit Umlauten richtig
    with open(dst, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)
    meta = catalog["metadata"]
    print(f'{len(rows)} Practices aus "{meta["title"]}" (Stand {meta["last-modified"][:10]}) nach {dst} geschrieben.')


if __name__ == "__main__":
    main()
