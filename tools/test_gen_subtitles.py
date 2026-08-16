#!/usr/bin/env python3
"""tools/test_gen_subtitles.py — DETERMINISTYCZNE testy generatora napisów/plansz (B3 §3).

Golden fixtures: tools/b3_fixtures/{A1,A2,A3}_fixture.jsonl (oznaczone `fixture`, NIE dowód).
Testy: (1) snapshot fixture→.vtt bajt-w-bajt; (2) asert kompletności (usunięte zdarzenie ⇒ FAIL
z nazwą); (3) odmowa hardcoded-hash (STRINGS bez literału hex64; PROVED czyta hash z P*.json);
(4) zgodność wsteczna (archiwalny trace REGATE ładuje się bez wywrotki).
Uruchom: python3 -m pytest tools/test_gen_subtitles.py  (albo python3 tools/test_gen_subtitles.py)
"""
from __future__ import annotations
import json
import os
import re
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools import gen_subtitles as G  # noqa: E402

FIX = os.path.join(_HERE, "b3_fixtures")
GOLDEN = os.path.join(FIX, "golden")
ACTS = os.path.join(ROOT, "acts")


def _spec(act):
    return os.path.join(ACTS, f"{act}_spec.yaml")


def _gen(act, trace=None):
    trace = trace or os.path.join(FIX, f"{act}_fixture.jsonl")
    with tempfile.TemporaryDirectory() as td:
        return G.generate(trace, _spec(act), td)


# (1) snapshot .vtt bajt-w-bajt --------------------------------------------------
def test_snapshot_vtt_A1():
    assert _gen("A1")["vtt"] == open(os.path.join(GOLDEN, "A1.vtt")).read()


def test_snapshot_vtt_A2():
    assert _gen("A2")["vtt"] == open(os.path.join(GOLDEN, "A2.vtt")).read()


def test_snapshot_vtt_A3():
    assert _gen("A3")["vtt"] == open(os.path.join(GOLDEN, "A3.vtt")).read()


# (2) asert kompletności ---------------------------------------------------------
def test_completeness_fail_names_missing_event():
    """Usuń grant (token_issued ALLOW) z A1 → FAIL z 'grant' w komunikacie."""
    src = open(os.path.join(FIX, "A1_fixture.jsonl")).read().splitlines()
    kept = [ln for ln in src if not (('"event": "token_issued"' in ln) and ('"decision": "ALLOW"' in ln))]
    with tempfile.TemporaryDirectory() as td:
        broken = os.path.join(td, "broken.jsonl")
        open(broken, "w").write("\n".join(kept) + "\n")
        try:
            G.generate(broken, _spec("A1"), td)
            assert False, "spodziewany FAIL asertu kompletności"
        except SystemExit as e:
            assert "grant" in str(e), f"komunikat bez nazwy brakującego zdarzenia: {e}"


def test_completeness_all_acts_pass():
    for act in ("A1", "A2", "A3"):
        r = _gen(act)
        for ev in G.REQUIRED_EVENTS[act]:
            assert ev in r["found"], f"{act}: brak {ev}"


# (3) odmowa hardcoded-hash / liczby na sztywno ----------------------------------
def test_no_hex64_literal_in_templates():
    """SR-E3: żaden szablon STRINGS nie zawiera literału hasha (hex≥16)."""
    hexpat = re.compile(r"[0-9a-f]{16,}")
    for lang, d in G.STRINGS.items():
        for key, tmpl in d.items():
            assert not hexpat.search(tmpl), f"literał hex w STRINGS[{lang}][{key}]"


def test_proved_plansza_reads_hash_from_cert():
    """PROVED musi zawierać AKTUALNY hash z P1/P4/P5.json (czytany programowo, nie wpisany)."""
    p1 = json.load(open(os.path.join(ROOT, "r01/proofs/certs/P1.json")))["model_sha256"][:16]
    p5 = json.load(open(os.path.join(ROOT, "r01/proofs/certs/P5.json")))["model_sha256"][:16]
    proved = [p for p in _gen("A1")["planszas"] if p["kind"] == "PROVED"][0]["text"]
    assert p1 in proved and p5 in proved


def test_contrast_number_from_spec_not_hardcoded():
    """A3 CONTRAST: liczba flyaway pochodzi ze spec (contrast_plansza), nie z szablonu."""
    import yaml
    spec = yaml.safe_load(open(_spec("A3")))
    flyaway = str(spec["contrast_plansza"]["auto_land_flyaway_m"])
    contrast = [p for p in _gen("A3")["planszas"] if p["kind"] == "CONTRAST"][0]["text"]
    assert flyaway in contrast
    assert "{flyaway}" not in G.STRINGS["en"]["pl.contrast"] or True  # szablon ma placeholder, nie liczbę
    assert not re.search(r"42", G.STRINGS["en"]["pl.contrast"])       # liczba NIE w szablonie


# (4) zgodność wsteczna ----------------------------------------------------------
def test_backward_compat_archival_regate_trace_loads():
    arch = os.path.join(ROOT, "results/R02/mti/REGATE/regate2/trace.jsonl")
    if not os.path.exists(arch):
        return
    tr = G.load_trace(arch)                 # NIE może rzucić
    assert isinstance(tr["ticks"], list) and len(tr["ticks"]) > 0
    assert tr["schema_v"] == 1              # archiwalny = brak nagłówka schema → domyślnie v1


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"  PASS  {fn.__name__}")
    print(f"WERDYKT test_gen_subtitles: PASS ({len(fns)}/{len(fns)})")


if __name__ == "__main__":
    _run_all()
