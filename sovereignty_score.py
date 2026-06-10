#!/usr/bin/env python3
"""
Souveränitätsindex V2 - Scoring-Skript
=======================================

Berechnet je Organisation eine Souveränitäts-Endnote (Schulnote 1-6) aus dem
flachen JSON-Export des Scanners (organizations*.json).

Architektur (drei Stufen):
  1. Per-System-Score : gewichteter Mittelwert der 5 Per-System-Marker
  2. Rollen-Score     : Rolle = max(System-Note, Proxy-Note)   -> schwächstes Glied
  3. Org-Endnote      : 0,6 * gewichteter Mittelwert der Rollen
                        + 0,4 * schlechteste Rolle              -> verhindert Ausmitteln

Aufruf:
  python3 sovereignty_score.py "organizations (1).json"
  python3 sovereignty_score.py "organizations (1).json" --out scored.json

Skala bei allen Markern: 1 = sehr souverän ... 6 = nicht souverän.
"""

import json
import sys
import statistics
import argparse

# --------------------------------------------------------------------------
# Konfiguration (zentral, damit Gewichte/Regeln an einer Stelle stehen)
# --------------------------------------------------------------------------

# Per-System-Marker und ihre Gewichte (werden intern auf Summe 1 normiert).
# Fehlt ein Marker (z.B. keine IPs), wird er weggelassen und der Rest
# proportional hochskaliert (n.b.-Regel).
SYS_MARKER_WEIGHTS = {
    "ip_country":      15,   # Dim 1 Geografie     - wo wird betrieben
    "ip_hoster":       15,   # Dim 2 Anbieter      - wer betreibt die IP
    "vendor_category": 10,   # Dim 2 Anbieter      - Anbieterklasse der Software
    "vendor_country":  10,   # Dim 3 Technologie   - Sitz des Herstellers
    "open_source":     10,   # Dim 3 Technologie   - offen vs. proprietaer
}

# Rollengewichte fuer die Org-Aggregation (nach Vertraulichkeits-Exposition).
ROLE_WEIGHTS = {
    "imap_pop3":  0.30,   # gesamtes Postfach (Daten at rest)
    "smtp_in":    0.25,   # eingehender Verkehr
    "smtp_out":   0.25,   # ausgehender Verkehr
    "webmailer":  0.20,   # Zugriffsschicht, Klartext + Credentials
}

# Org-Endnote: Anteil Mittelwert vs. schlechteste Rolle.
ORG_MEAN_SHARE  = 0.60
ORG_WORST_SHARE = 0.40

# Ab wie vielen nicht bewertbaren Per-System-Markern gilt eine Org als
# "nicht belastbar" (Status n.b. statt Endnote).
MAX_NB_MARKERS_PER_SYSTEM = 3


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------

def _weighted_mean(pairs):
    """pairs: Liste von (wert, gewicht); None-Werte werden ignoriert."""
    pairs = [(v, w) for v, w in pairs if v is not None]
    total_w = sum(w for _, w in pairs)
    if total_w == 0:
        return None, 0
    score = sum(v * w for v, w in pairs) / total_w
    return score, len(pairs)


def system_score(system):
    """Per-System-Score aus den 5 Markern. Gibt (score, n_marker) zurueck."""
    ips = system.get("ips") or []
    ip_country = statistics.mean([ip["country_rating"] for ip in ips]) if ips else None
    ip_hoster  = statistics.mean([ip["hoster_rating"]  for ip in ips]) if ips else None

    pairs = [
        (ip_country,                       SYS_MARKER_WEIGHTS["ip_country"]),
        (ip_hoster,                        SYS_MARKER_WEIGHTS["ip_hoster"]),
        (system.get("vendor_category_rating"), SYS_MARKER_WEIGHTS["vendor_category"]),
        (system.get("vendor_country_rating"),  SYS_MARKER_WEIGHTS["vendor_country"]),
        (system.get("open_source_rating"),     SYS_MARKER_WEIGHTS["open_source"]),
    ]
    return _weighted_mean(pairs)


def role_score(systems):
    """
    Rollen-Score. Pro System gilt: Rolle = max(System, Proxy) (schwaechstes Glied).
    Mehrere Systeme einer Rolle werden gemittelt.
    Gibt (score, n_systeme, n_nb_marker) zurueck.
    """
    notes = []
    nb_count = 0
    for s in systems:
        s_score, s_n = system_score(s)
        nb_count += (5 - s_n)  # fehlende Per-System-Marker zaehlen
        proxy = s.get("proxy")
        if proxy:
            p_score, _ = system_score(proxy)
            note = max(s_score, p_score)   # <-- harte Proxy-Regel
        else:
            note = s_score
        if note is not None:
            notes.append(note)
    if not notes:
        return None, len(systems), nb_count
    return statistics.mean(notes), len(systems), nb_count


def org_score(org):
    """Berechnet Endnote + Detailaufschluesselung fuer eine Organisation."""
    mail = org.get("mail_systems", {})
    roles = {}
    nb_total = 0
    for role, weight in ROLE_WEIGHTS.items():
        systems = mail.get(role) or []
        if not systems:
            roles[role] = None
            continue
        score, _, nb = role_score(systems)
        roles[role] = score
        nb_total += nb

    valid = {r: v for r, v in roles.items() if v is not None}
    if not valid:
        return {"roles": roles, "final": None, "note": "n.b.",
                "reason": "keine bewertbaren Mailsysteme"}

    # Datenqualitaets-Bremse
    if nb_total > MAX_NB_MARKERS_PER_SYSTEM * len(valid):
        return {"roles": roles, "final": None, "note": "n.b.",
                "reason": f"zu duenne Datenlage ({nb_total} fehlende Marker)"}

    # gewichteter Mittelwert ueber vorhandene Rollen (Gewichte renormiert)
    wsum = sum(ROLE_WEIGHTS[r] for r in valid)
    mean = sum(valid[r] * ROLE_WEIGHTS[r] for r in valid) / wsum
    worst = max(valid.values())
    final = ORG_MEAN_SHARE * mean + ORG_WORST_SHARE * worst

    return {
        "roles": roles,
        "mean": mean,
        "worst": worst,
        "final": final,
        "note": int(final + 0.5),   # kaufmaennisch auf Schulnote
    }


# --------------------------------------------------------------------------
# Ausgabe
# --------------------------------------------------------------------------

def print_report(org, result):
    print("=" * 74)
    prov = ", ".join(org.get("providers", [])) or "?"
    print(f"{org['org']}  ({prov})  -  {org.get('email_domain','?')}")
    print("-" * 74)
    mail = org.get("mail_systems", {})
    for role in ROLE_WEIGHTS:
        for s in mail.get(role) or []:
            ss, _ = system_score(s)
            px = s.get("proxy")
            if px:
                ps, _ = system_score(px)
                tag = f" | Proxy {px['software']} = {ps:.2f}  -> Rolle = max = {max(ss,ps):.2f}"
            else:
                tag = " | kein Proxy"
            print(f"  {role:10s} {s['software']:22s} System={ss:.2f}{tag}")
    if result["final"] is None:
        print(f"\n  ENDNOTE: {result['note']}  ({result['reason']})")
    else:
        rs = "  ".join(f"{r}={v:.2f}" for r, v in result["roles"].items() if v is not None)
        print(f"\n  Rollen: {rs}")
        print(f"  Mittelwert={result['mean']:.2f}  schlechteste Rolle={result['worst']:.2f}")
        print(f"  ENDNOTE = 0,6*{result['mean']:.2f} + 0,4*{result['worst']:.2f} "
              f"= {result['final']:.2f}  ->  Note {result['note']}")
    print()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Souveränitätsindex V2 scoring")
    ap.add_argument("input", help="Pfad zur organizations*.json")
    ap.add_argument("--out", help="optional: Pfad fuer JSON mit eingetragener Endnote")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    for org in data:
        result = org_score(org)
        print_report(org, result)
        # Endnote in die Org schreiben (numerisch, gerundet)
        org["sovereignty_index"] = result["final"]
        org["sovereignty_note"] = result["note"]

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"-> geschrieben: {args.out}")


if __name__ == "__main__":
    main()
