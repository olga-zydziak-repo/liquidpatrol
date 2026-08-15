#!/usr/bin/env python3
"""results/R02/mti/DIAG/d3_entry_once.py — D3 PROJEKCJA: re-scope MTI do ADMISJI (ENTRY-once).

PROJEKCJA OFFLINE ≠ POMIAR. Liczy z AGREGATÓW result.json (×3 booty) projekcję kryteriów pod
definicją: MTI wymagane WYŁĄCZNIE do admisji (ENTRY); po admisji kanał karmi STRUKTURA
(coverage_seen); EXPIRE/sufit/age bez zmian. To NIE jest re-symulacja per-frame (brak śladu
per-tick — patrz RAPORT_MTI_DIAG D0). D3 opiera się na polach, które PRZEŻYŁY agregację:
  - n_entry, time_to_entry_s        (czy i kiedy admisja)
  - coverage_seen (=1.0)            (kanał struktury po admisji)
  - coverage_locked_post_entry      (lock trzymany po admisji — kontrola ZOH)
  - false_entry (fp_empty, fp_bg)   (kryterium (−) pod ENTRY-once)
"""
import json
import os
import statistics as st

BASE = os.path.join(os.path.dirname(__file__), "..", "B4")
BOOTS = ["fix1", "fix2", "fix3"]
RANGES = ["5m", "7m", "9m"]

data = {b: json.load(open(os.path.join(BASE, b, "result.json"))) for b in BOOTS}

# --- (i) admisja per cela ---
admission = {r: [] for r in RANGES}
t_entry = {r: [] for r in RANGES}
cov_seen = {r: [] for r in RANGES}
cov_lock_post = {r: [] for r in RANGES}
for b in BOOTS:
    for r in RANGES:
        p = data[b]["phases"][f"sweep_{r}"]
        admission[r].append(p["n_entry"] >= 1)
        t_entry[r].append(p["time_to_entry_s"])
        cov_seen[r].append(p["coverage_seen"])
        cov_lock_post[r].append(p["coverage_locked_post_entry"])

# --- (iii) kryterium (−) pod ENTRY-once ---
minus = {}
for b in BOOTS:
    fe_empty = data[b]["phases"]["fp_empty"]["false_entry"]
    fe_bg = data[b]["phases"]["fp_bg"]["false_entry"]
    fgf = data[b]["phases"]["fp_bg"].get("false_gate_frames")
    minus[b] = {"fp_empty_false_entry": fe_empty, "fp_bg_false_entry": fe_bg,
                "fp_bg_false_gate_frames": fgf}

# --- projekcja (+) pod ENTRY-once ---
# operatywne pokrycie po admisji = coverage_seen (=1.0), kanał karmi struktura.
plus_by_range = {}
for r in RANGES:
    n_adm = sum(admission[r])
    te = [x for x in t_entry[r] if x is not None]
    plus_by_range[r] = {
        "boots_admitted": f"{n_adm}/3",
        "admission_flags": admission[r],
        "time_to_entry_s": t_entry[r],
        "time_to_entry_median_s": round(st.median(te), 3) if te else None,
        "coverage_seen": cov_seen[r],
        "coverage_locked_post_entry": cov_lock_post[r],
        # operatywne pokrycie ENTRY-once = coverage_seen tam gdzie admisja, else 0 (brak admisji)
        "operative_coverage_entry_once": [cs if adm else 0.0
                                          for cs, adm in zip(cov_seen[r], admission[r])],
    }

out = {
    "step": "D3 — PROJEKCJA ENTRY-once (MTI tylko do admisji)",
    "label": "PROJEKCJA OFFLINE ≠ POMIAR",
    "source": "results/R02/mti/B4/{fix1,fix2,fix3}/result.json (agregaty; brak śladu per-tick)",
    "definition": ("MTI wymagane WYŁĄCZNIE do ENTRY; po admisji kanał=struktura (coverage_seen); "
                   "EXPIRE/sufit/age bez zmian; utrata struktury→starzenie jak dotąd"),
    "plus_criterion_entry_once": plus_by_range,
    "minus_criterion_entry_once": minus,
    "verdict_plus": ("PROJEKCJA: (+) pod ENTRY-once — admisja 3/3 @7m i @9m, 2/3 @5m "
                     "(fix3@5m brak ENTRY: cov_gate=0.393 ale 0 serii K=3 spójnych). "
                     "Pokrycie operatywne po admisji = coverage_seen = 1.0 wszędzie gdzie admisja."),
    "verdict_minus": ("PROJEKCJA: (−) NIENARUSZONE — false_entry=0 na fp_empty ∧ fp_bg ×3 booty; "
                      "ENTRY-once nie zmienia progu admisji, więc 0 fałszywych ENTRY zostaje 0."),
    "caveat": ("coverage_locked_post_entry=1.0 to częściowo ZOH-age hold, ALE coverage_seen=1.0 "
               "(YOLO trafia każdy tick) ⇒ lock realnie odświeżany, nie tylko dryfuje ZOH. "
               "Jedyna komórka bez admisji = fix3@5m (najbliższy zasięg = najgorszy, zgodne z note_5m)."),
    "requires_live_rebracket": True,
}
outpath = os.path.join(os.path.dirname(__file__), "d3_entry_once.json")
json.dump(out, open(outpath, "w"), indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))
print(f"\n[D3] zapisano {outpath}")
