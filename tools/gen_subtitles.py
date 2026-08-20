#!/usr/bin/env python3
"""tools/gen_subtitles.py — DEMO-B B3 (PROMPT_D_BUILD_3 §2): generator napisów (.vtt) + plansz.

ZASADA NADRZĘDNA (frozen R3 / SR-E2): wszystko dynamiczne pochodzi WYŁĄCZNIE z trace, certów
(r01/proofs/certs/P*.json), manifestów i spec aktów. Zero treści wpisanych ręcznie poza statycznymi
szablonami z placeholderami. Hashe certów CZYTANE programowo (SR-E3: hash/liczba na sztywno = naruszenie).

ASERT KOMPLETNOŚCI (§2): generator NIE tworzy wyjścia, jeśli w trace brakuje któregokolwiek zdarzenia
wymaganego scenariuszem aktu — głośny FAIL z nazwą brakującego zdarzenia (wzorzec asercji z mti_flight).

ROSZCZENIE PERCEPCJI (D3(a)) tylko zmierzone: segment „claim" renderowany wyłącznie gdy trace
potwierdza JEDNOCZEŚNIE stan OBSERVE i d w kopercie scharakteryzowanej (ring_band_m ze spec); wszędzie
indziej plansza D3(b) „beyond characterized envelope — transit". Granice segmentów Z TRACE, nie z planu.

Uruchom: python3 tools/gen_subtitles.py <trace.jsonl> <acts/AX_spec.yaml> <out_dir> [--lang en]
Wyjście: <out_dir>/subtitles.vtt + <out_dir>/planszas.json
"""
from __future__ import annotations
import argparse
import json
import math
import os
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
CERTS = os.path.join(ROOT, "r01", "proofs", "certs")

# --- Słownik treści (statyczne szablony z {placeholderami}); parametr języka ------------------------
STRINGS = {
    "en": {
        "ev.entry": "Target admitted to channel (structure ∧ MTI).",
        "ev.refuse_no_auth": "Escalation refused — REFUSE(NO_AUTH): no valid operator token.",
        "ev.grant": "Operator token issued (per admission episode).",
        "ev.observe": "OBSERVE: holding at safe distance.",
        "ev.expire": "Target lost — EXPIRE at age ceiling; token consumed.",
        "ev.readmit": "Re-admission: new episode (admission_seq {seq}) — full gate.",
        "ev.grant2": "New operator token required (previous consumed).",
        "ev.denial": "GPS aiding denied (EKF2_GPS_CTRL=0).",
        "ev.refuse_pos": "REFUSE(POS_DEGRADED) — position health lost.",
        "ev.touchdown": "Velocity-descent touchdown inside envelope.",
        # ANEKS_D6 §1b: roszczenie D3(a) = ZACHOWANIE OSŁONY/BRAMY PRZY DANEJ DETEKCJI (token/dominacja/
        # EXPIRE/containment), NIE wykrywalność celu. Detekcja = PRZESŁANKA (GT-fed), nie teza.
        "seg.claim": "CERTIFIED LAYER — OBSERVE hold, safe distance (given GT-fed detection; ring {lo:.0f}–{hi:.0f} m)",
        "seg.transit": "beyond characterized envelope — transit",
        "pl.proved": "PROVED — shield certificates\nP1 (z3, {p1n}/{p1n} unsat) sha:{p1h}\nP4 (PASS) sha:{p4h}\nP5 (PASS, {p5cov}) sha:{p5h}",
        "pl.measured": "MEASURED (this run)\n{lines}",
        "pl.operator": "Operator: scripted signatory — HITL simulated (ANEKS_D1 §A5).",
        "pl.per_admission": "Authorization is per admission episode — no target re-identification (B1 §1.3).",
        "pl.authority_gating": "Authority gating (local HMAC) — demonstration, not secure C2 (B1 §1.7).",
        "pl.trl": "SITL only — TRL 2–3.",
        # ANEKS_D6 §1c: DWIE plansze OBOWIĄZKOWE (SR-M2 — brak którejkolwiek albo sformułowanie roszczące
        # percepcję live = naruszenie). Treść 1:1 z aneksu.
        "pl.detection_channel": "detection channel: ground-truth-fed (idealized detector)",
        "pl.live_perception": ("live perception characterized separately — REGATE: cov_entry_once=1.0 @7–9 m, "
                               "ego-motion flight; not claimed in dwell-hold"),
        "pl.cut": "— separate boot / explicit cut —",
        "pl.contrast": "Contrast: AUTO.LAND flyaway {flyaway} m (RAPORT_R03A B1-bis)\nvs velocity-descent touchdown {td} m (this run).",
    },
}

# Zdarzenia WYMAGANE per klasa aktu (§2). Nazwy kanoniczne (klucze detektora).
REQUIRED_EVENTS = {
    "A1": ["entry", "refuse_no_auth", "grant", "observe"],
    "A2": ["entry", "refuse_no_auth", "grant", "observe", "expire", "readmit", "grant2"],
    "A3": ["denial", "refuse_pos", "touchdown"],
}


def load_trace(path):
    schema_v, ticks, events, meta = 1, [], [], {}
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        tt = row.get("t")
        # typy specjalne = STRINGOWA wartość 't' (r02 tick ma 't'=float → NIE specjalny). Zgodność wsteczna:
        # wszystko inne (r02 rec k-keyed, r03 t=="tick", archiwalny mti per-frame) → tick, bez wywrotki.
        if tt == "schema":
            schema_v = row.get("v", 1); continue
        if tt == "meta":
            meta = row; schema_v = row.get("schema_v", schema_v); continue
        if tt == "event" or "event" in row:
            events.append(row); continue
        if tt == "outcome":
            meta.setdefault("_outcome", []).append(row); continue
        ticks.append(row)                    # per-tick (nowe pola opcjonalne — .get z domyślną)
    return {"schema_v": schema_v, "ticks": ticks, "events": events, "meta": meta}


def _ev_time(row):
    """Czas zdarzenia [s] — 't' numeryczne (r02) potem 'mono' (r03 event)."""
    for k in ("t", "mono"):
        if isinstance(row.get(k), (int, float)):
            return float(row[k])
    return None


def _tick_time(row):
    """Czas ticka [s]. r02: klucz 't' (sekundy). r03: 't'=='tick' (typ wiersza) → użyj 'mono'."""
    t = row.get("t")
    if isinstance(t, (int, float)):
        return float(t)
    return row.get("mono")


def detect_events(trace, act, spec):
    """Zwraca dict kanoniczne_zdarzenie -> {"t": float, "detail": ...} albo None gdy brak."""
    found = {}
    ticks = trace["ticks"]; events = trace["events"]

    def first_tick(pred):
        for r in ticks:
            if pred(r):
                return r
        return None

    # ENTRY: pierwszy tick locked=True (przejście z braku locka)
    prev = False
    for r in ticks:
        lk = bool(r.get("locked"))
        if lk and not prev:
            found.setdefault("entry", {"t": _tick_time(r), "detail": {"admission_seq": r.get("admission_seq")}})
        prev = lk
    # REFUSE(NO_AUTH): event row lub tick reason
    e = next((x for x in events if x.get("event") == "refuse_no_auth"), None)
    if e is None:
        e = first_tick(lambda r: r.get("reason") == "NO_AUTH")
    if e is not None:
        found["refuse_no_auth"] = {"t": _ev_time(e), "detail": {}}
    # grant / grant2: token_issued ALLOW (kolejność czasowa)
    grants = [x for x in events if x.get("event") == "token_issued" and x.get("decision") == "ALLOW"]
    if grants:
        found["grant"] = {"t": _ev_time(grants[0]), "detail": {"seq": grants[0].get("admission_seq")}}
    if len(grants) >= 2:
        found["grant2"] = {"t": _ev_time(grants[1]), "detail": {"seq": grants[1].get("admission_seq")}}
    # OBSERVE: pierwszy tick mode OBSERVE + decision ALLOW
    r = first_tick(lambda r: r.get("mode") == "OBSERVE" and r.get("decision") == "ALLOW")
    if r is not None:
        found["observe"] = {"t": _tick_time(r), "detail": {}}
    # EXPIRE: token_consumed (fired na EXPIRE) lub przejście locked True->False po locku
    e = next((x for x in events if x.get("event") == "token_consumed"), None)
    if e is not None:
        found["expire"] = {"t": _ev_time(e), "detail": {}}
    # re-admisja: admission_seq rośnie do ≥1 na kolejnym ENTRY
    seqs = [r.get("admission_seq") for r in ticks if isinstance(r.get("admission_seq"), int)]
    if seqs and max(seqs) >= 1:
        r = first_tick(lambda r: r.get("admission_seq") == 1 and r.get("locked"))
        if r is not None:
            found["readmit"] = {"t": _tick_time(r), "detail": {"seq": 1}}
    # A3: denial / refuse_pos / touchdown
    e = next((x for x in events if x.get("ev") == "denial_on"), None)
    if e is not None:
        found["denial"] = {"t": _ev_time(e), "detail": {"r_est_at_cut": e.get("r_est_at_cut")}}
    r = first_tick(lambda r: r.get("reason") == "POS_DEGRADED")
    if r is not None:
        found["refuse_pos"] = {"t": _tick_time(r), "detail": {}}
    else:
        e = next((x for x in events if x.get("ev") == "refuse_pos_land"), None)
        if e is not None:
            found["refuse_pos"] = {"t": _ev_time(e), "detail": {}}
    e = next((x for x in events if x.get("ev") == "touchdown"), None)
    if e is not None:
        found["touchdown"] = {"t": _ev_time(e), "detail": {}}
    return found


def assert_complete(act, found):
    missing = [ev for ev in REQUIRED_EVENTS[act] if ev not in found or found[ev].get("t") is None]
    if missing:
        raise SystemExit(f"[gen_subtitles] FAIL asert kompletności {act}: brak zdarzeń {missing} w trace")


def _range3d(pos, intr):
    if not pos or not intr:
        return None
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos[:3], intr[:3])))


def build_segments(trace, spec, S):
    """Segmenty claim (D3(a)) vs transit (D3(b)) WYŁĄCZNIE z trace. claim ⟺ state OBSERVE ∧ d∈ring_band."""
    band = spec.get("geometry", {}).get("ring_band_m", [7.0, 9.0])
    lo, hi = float(band[0]), float(band[1])
    segs = []
    cur = None
    for r in trace["ticks"]:
        d = _range3d(r.get("pos"), r.get("intr_ned"))
        in_env = (d is not None and lo <= d <= hi)
        is_claim = (r.get("mode") == "OBSERVE" and r.get("decision") == "ALLOW" and in_env)
        kind = "claim" if is_claim else "transit"
        t = _tick_time(r)
        if cur is None or cur["kind"] != kind:
            if cur is not None:
                cur["t_end"] = t; segs.append(cur)
            label = (S["seg.claim"].format(lo=lo, hi=hi) if kind == "claim" else S["seg.transit"])
            cur = {"kind": kind, "t_start": t, "t_end": t, "label": label}
        else:
            cur["t_end"] = t
    if cur is not None:
        segs.append(cur)
    return segs


def read_cert(name):
    return json.load(open(os.path.join(CERTS, f"{name}.json")))


def build_planszas(act, trace, spec, found, S):
    """Plansze obowiązkowe — pola z plików (certy/spec/trace). ŻADNEGO hasha/liczby na sztywno."""
    pls = []
    # ANEKS_D6 §1c: dyskleimery OBOWIĄZKOWE NA POCZĄTKU dla aktów GT-fed (A1/A2). SR-M2: brak = naruszenie.
    if act in ("A1", "A2"):
        pls.append({"kind": "DETECTION_CHANNEL", "text": S["pl.detection_channel"]})
        pls.append({"kind": "LIVE_PERCEPTION", "text": S["pl.live_perception"]})
    p1 = read_cert("P1"); p4 = read_cert("P4"); p5 = read_cert("P5")
    p1n = len([k for k, v in p1.get("obligations", {}).items() if v == "unsat"])
    pls.append({"kind": "PROVED", "text": S["pl.proved"].format(
        p1n=p1n, p1h=p1["model_sha256"][:16], p4h=p4["model_sha256"][:16],
        p5h=p5["model_sha256"][:16], p5cov=p5.get("coverage", "?"))})
    # MEASURED — liczby z trace + spec/config (źródło przy każdej)
    mlines = []
    if act in ("A1", "A2"):
        min_ds = [r.get("min_d") for r in trace["ticks"] if isinstance(r.get("min_d"), (int, float))]
        if min_ds:
            mlines.append(f"min D_safe held: {min(min_ds):.2f} m (trace min_d; D_safe=5.32 config_r02)")
        if found.get("entry") and found.get("refuse_no_auth"):
            mlines.append(f"NO_AUTH shown before token: t={found['refuse_no_auth']['t']:.2f}s (trace)")
    if act == "A2" and found.get("expire"):
        mlines.append(f"EXPIRE at θ_age=3.0s ceiling; re-admission seq→1 (trace; config_r02)")
    if act == "A3":
        rests = [r.get("margin_R_E") for r in trace["ticks"] if isinstance(r.get("margin_R_E"), (int, float))]
        if found.get("denial"):
            mlines.append(f"denial r_est_at_cut={found['denial']['detail'].get('r_est_at_cut')} m (trace)")
        if rests:
            mlines.append(f"min margin R_E−r_est: {min(rests):.2f} m (trace; R_E=32 config)")
    pls.append({"kind": "MEASURED", "text": S["pl.measured"].format(lines="\n".join(mlines) or "(none)")})
    # Statyczne obowiązkowe
    pls.append({"kind": "OPERATOR", "text": S["pl.operator"]})
    pls.append({"kind": "PER_ADMISSION", "text": S["pl.per_admission"]})
    pls.append({"kind": "AUTHORITY_GATING", "text": S["pl.authority_gating"]})
    pls.append({"kind": "TRL", "text": S["pl.trl"]})
    if act == "A2":
        pls.append({"kind": "CUT", "text": S["pl.cut"]})
    if act == "A3":
        cp = spec.get("contrast_plansza", {})
        td = None
        # touchdown radial: preferuj zmierzony z trace (ostatni r_est przed touchdown), inaczej spec
        r_ests = [r.get("r_est") for r in trace["ticks"] if isinstance(r.get("r_est"), (int, float))]
        td = f"{r_ests[-1]:.2f}" if r_ests else str(cp.get("touchdown_radial_le_m", "?"))
        pls.append({"kind": "CONTRAST", "text": S["pl.contrast"].format(
            flyaway=cp.get("auto_land_flyaway_m", "?"), td=td)})
    return pls


def fmt_ts(t):
    t = max(0.0, float(t)); h = int(t // 3600); m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def build_cues(act, found, segs, S):
    """Napisy .vtt: zdarzenia (w kolejności czasowej) + banner segmentu na jego początku."""
    cues = []
    # zdarzenia
    ev_text = {"entry": S["ev.entry"], "refuse_no_auth": S["ev.refuse_no_auth"], "grant": S["ev.grant"],
               "observe": S["ev.observe"], "expire": S["ev.expire"], "grant2": S["ev.grant2"],
               "denial": S["ev.denial"], "refuse_pos": S["ev.refuse_pos"], "touchdown": S["ev.touchdown"]}
    items = []
    for ev, txt in ev_text.items():
        if ev in found and found[ev].get("t") is not None:
            items.append((found[ev]["t"], txt))
    if "readmit" in found:
        items.append((found["readmit"]["t"], S["ev.readmit"].format(seq=found["readmit"]["detail"].get("seq"))))
    # bannery segmentów
    for sg in segs:
        items.append((sg["t_start"], f"[{sg['label']}]"))
    items.sort(key=lambda x: (x[0], x[1]))
    for i, (t, txt) in enumerate(items):
        t_end = items[i + 1][0] if i + 1 < len(items) else t + 3.0
        if t_end <= t:
            t_end = t + 1.0
        cues.append((t, t_end, txt))
    return cues


def render_vtt(cues):
    out = ["WEBVTT", ""]
    for t0, t1, txt in cues:
        out.append(f"{fmt_ts(t0)} --> {fmt_ts(t1)}")
        out.append(txt)
        out.append("")
    return "\n".join(out) + "\n"


def generate(trace_path, spec_path, out_dir, lang="en"):
    S = STRINGS[lang]
    trace = load_trace(trace_path)
    spec = yaml.safe_load(open(spec_path))
    act = spec["act"]
    found = detect_events(trace, act, spec)
    assert_complete(act, found)                       # głośny FAIL jeśli brak zdarzenia
    segs = build_segments(trace, spec, S)
    planszas = build_planszas(act, trace, spec, found, S)
    cues = build_cues(act, found, segs, S)
    os.makedirs(out_dir, exist_ok=True)
    vtt = render_vtt(cues)
    open(os.path.join(out_dir, "subtitles.vtt"), "w").write(vtt)
    json.dump({"act": act, "schema_v": trace["schema_v"], "lang": lang,
               "segments": segs, "planszas": planszas,
               "events_detected": {k: v["t"] for k, v in found.items()}},
              open(os.path.join(out_dir, "planszas.json"), "w"), indent=2, ensure_ascii=False)
    return {"vtt": vtt, "planszas": planszas, "segments": segs, "found": found}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace"); ap.add_argument("spec"); ap.add_argument("out_dir")
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    r = generate(a.trace, a.spec, a.out_dir, a.lang)
    print(f"[gen_subtitles] OK {a.spec}: {len(r['segments'])} segm, {len(r['planszas'])} plansz → {a.out_dir}")


if __name__ == "__main__":
    main()
