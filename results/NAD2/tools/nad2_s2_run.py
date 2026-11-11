#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s2_run.py — kolejka smoke S2 NADIR-II (PROMPT_NAD2_S2 §0.2, §R; ≤ 3 booty). Wzór
results/NADIR/tools/nadir_s4_campaign.py (nietknięty): strażniki stanowiska z kont_s2_campaign_g.py (zegar 60 s, sieroty po PID,
/dev/shm) — import READ-ONLY, ścieżki przestawione na results/NAD2/s2 w tym procesie; bramka zdrowia ANEKS_NADIR-4 §3.1 przyrządem A
(results/NADIR/tools/nadir_s4_bramka.przyrzad_a — import READ-ONLY, katalog wyjścia przestawiony na results/NAD2/s2/bramka): A, NO-GO
⇒ 3 min ⇒ C (z telemetrią), trzecie NO-GO z rzędu ⇒ STOP-NAD2-2-STANOWISKO, nic nie zużyte; telemetria §3.3 w tle bootu
(<boot>/host_telemetria.jsonl). Boot: results/NAD2/tools/nad2_boot.sh z trybami jawnie (BOOT_*). Bramka tempa w boocie 0.93 (rc 9 =
boot zużyty).
Kolejność (§R): P = passthrough (NADIR_MODE=0, KONT_MODE=0, NAD2_PASSTHROUGH=1, litera NADIR1, epizody 0–3 jak S3 B1); potem C =
cięcie c11_s02 (epizod 23, KONT_INJECT_T 30, NADIR_MODE=1, KONT_MODE=1, litera NAD2). C nie startuje, jeśli P nie jest bitowo zgodny
(passthrough_summary.json: ticki > 0 ∧ różnice = 0 ∧ rc = 0). Rezerwa: jeden boot (stanowisko albo powtórka po bramce tempa).
Budżet S2 ≤ 3 booty (księga results/NAD2/s2/kampania_ksiega.jsonl, wiersz per zużyty boot). Po C: wyciąg ULG (nad2_ulg), analizator
(nad2_analyze) i sprawdziany (nad2_s2_spr). timesyncd: zatrzymany na starcie, wznawiany na końcu (litera ANEKS_SKAN2-0b).
STOPy globalne verbatim: breach ⇒ STOP; REFUSE(POS) fałszywy ⇒ STOP; budżet ⇒ STOP.
Użycie: nad2_s2_run.py [--sucho]   (--sucho: plan i stan księgi, 0 bootów). Wyjście: kampania_s2.log, kampania_s2.json.
"""
import json
import os
import subprocess
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [os.path.join(ROOT, "results/KONT/tools"), os.path.join(ROOT, "results/NADIR/tools"), os.path.join(ROOT, "results/NAD2/tools"), ROOT]
import kont_s2_campaign_g as G                     # READ-ONLY
import nadir_s4_tel as TL                          # READ-ONLY (ANEKS_NADIR-4 §3.3)

S2 = os.path.join(ROOT, "results/NAD2/s2")
G.S2 = S2
G.LOG = os.path.join(S2, "kampania_s2.log")
G.SKRYPTY = G.SKRYPTY | {"kont_s4_flight", "nadir_s4_flight", "nad2_flight", "intruder_motion", "nadir_obs"}
log = G.log
BOOT = os.path.join(ROOT, "results/NAD2/tools/nad2_boot.sh")
KSIEGA = os.path.join(S2, "kampania_ksiega.jsonl")
BUDZET = 3
NOGA_PRZED = 0                                     # NADIR-II: pierwszy boot nogi (budżet nogi ≤ 22)
LOTY = {"P": {"nazwa": "p_passthrough", "epizody": "0,1,2,3", "inject": "-",
              "env": {"BOOT_NADIR_MODE": "0", "BOOT_KONT_MODE": "0", "BOOT_PASSTHROUGH": "1", "BOOT_LITERA": "NADIR1"}},
        "C": {"nazwa": "c11_s02", "epizody": "23", "inject": "30",
              "env": {"BOOT_NADIR_MODE": "1", "BOOT_KONT_MODE": "1", "BOOT_PASSTHROUGH": "0", "BOOT_LITERA": "NAD2"}}}


def ksiega():
    return [json.loads(l) for l in open(KSIEGA) if l.strip()] if os.path.exists(KSIEGA) else []


def wolna(nm):
    n = 1
    while True:
        c = nm if n == 1 else f"{nm}_r{n}"
        if not any(f == c or f.startswith(c + "_") or f.startswith(c + ".") for f in os.listdir(S2)):
            return c
        n += 1


def bramka_zdrowia(name):
    import nadir_s4_bramka as B
    B.OUT = os.path.join(S2, "bramka")
    proby = []
    for k in range(3):
        if k:
            time.sleep(180)
        B.zegar_ok()
        tag = f"{name}_g{k + 1}"
        try:
            r = B.przyrzad_a(tag, tel=bool(k))
        except Exception as ex:
            log(f"{name}: bramka zdrowia błąd {ex!r}")
            return None, proby
        p = {"tag": tag, "wariant": r["wariant"], "tempo": r["tempo"], "GO": r["GO"], "czolowka_operatora": r.get("czolowka_operatora"),
             "t": time.strftime("%F %T")}
        proby.append(p)
        with open(os.path.join(S2, "bramka_ksiega.jsonl"), "a") as f:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
        log(f"{name}: bramka zdrowia {tag} ({p['wariant']}) GO={p['GO']} tempo={p['tempo']}"
            + (f" — do zamknięcia: {p['czolowka_operatora']}" if p["czolowka_operatora"] else ""))
        if r["GO"]:
            return True, proby
    return False, proby


def boot(lot, bn):
    L = LOTY[lot]
    name = wolna(L["nazwa"])
    go, proby = bramka_zdrowia(name)
    if go is None:
        return "STOP-NAD2-2-BRAMKA", None
    if not go:
        return "STOP-NAD2-2-STANOWISKO", None
    ok, z = G.zegar(name)
    log(f"{name}: próbnik {z['skoki']} skoków ok={ok}")
    if not ok:
        return "STOP-NAD2-2-ZEGAR", None
    znal, zywe = G.sprzataj_sieroty()
    if zywe:
        return "STOP-NAD2-2-SIEROTY", None
    shm = G.shm_krok(name, False)
    env = {**os.environ, **L["env"], "PERC2_FASTDDS_PROFILE": G.PROFIL, "PYTHONDONTWRITEBYTECODE": "1"}
    tp = os.path.join(S2, f"{name}_host_telemetria.jsonl")
    tl = TL.Telemetria2(tp, 3600)
    t0 = time.time()
    try:
        for _ in range(4):
            r = subprocess.run(["bash", BOOT, str(bn), name, L["epizody"], L["inject"]], cwd=ROOT, env=env, capture_output=True, text=True)
            open(os.path.join(S2, f"{name}_driver.log"), "a").write(r.stdout + r.stderr)
            if r.returncode != 3:
                break
            log(f"{name}: env-block rc=3, nie boot, czekam 120 s"); time.sleep(120)
        else:
            return "STOP-NAD2-2-ENV", None
    finally:
        tl.close()
    if r.returncode in (4, 5, 6):
        log(f"{name}: guard rc={r.returncode}, stos nie ruszył, nie boot")
        return "STOP-NAD2-2-GUARD", None
    d = os.path.join(S2, name)
    if os.path.isdir(d):
        os.replace(tp, os.path.join(d, "host_telemetria.jsonl"))
    try:
        kt = json.load(open(os.path.join(d, "kont_tempo.json")))
    except (OSError, ValueError):
        kt = None
    ev = []
    if os.path.exists(os.path.join(d, "trace.jsonl")):
        ev = [json.loads(l) for l in open(os.path.join(d, "trace.jsonl")) if '"event"' in l]
    names = [e.get("ev") for e in ev]
    wpis = {"boot_s2": bn, "lot": lot, "nazwa": name, "rc": r.returncode, "czas_s": round(time.time() - t0, 1), "tempo": kt,
            "bramka_tempa": r.returncode == 9 or (kt is not None and not kt.get("ok")), "bramka_zdrowia": proby, "shm": shm,
            "breach": any(n in ("breach", "breach_gt") for n in names), "nad2_litera": next((e for e in ev if e.get("ev") == "nad2_litera"), None),
            "t": time.strftime("%F %T")}
    if lot == "P":
        try:
            ps = json.load(open(os.path.join(d, "passthrough_summary.json")))
        except (OSError, ValueError):
            ps = None
        wpis["passthrough"] = ps
        wpis["passthrough_ok"] = bool(ps) and ps["ticki"] > 0 and ps["roznice"] == 0 and r.returncode == 0
    with open(KSIEGA, "a") as f:
        f.write(json.dumps(wpis, ensure_ascii=False, default=str) + "\n")
    log(f"{name} rc={r.returncode} boot {bn}/{BUDZET} tempo={(kt or {}).get('dsim_dwall_settle')} breach={wpis['breach']} "
        + (f"passthrough={wpis.get('passthrough')}" if lot == "P" else f"litera={wpis['nad2_litera']}"))
    return None, wpis


def po_c(name):
    d = os.path.join(S2, name)
    import nad2_ulg, nad2_analyze, nad2_s2_spr
    w = nad2_ulg.wyciag(d)
    log(f"{name}: wyciąg ULG {w}")
    a = nad2_analyze.analyze(d)
    s = nad2_s2_spr.sprawdz(d)
    log(f"{name}: analizator bezpieczeństwo_ok={a.get('bezpieczenstwo_ok')}; sprawdziany {json.dumps({k: v.get('ok') for k, v in s.items() if isinstance(v, dict)})}")
    return a, s


def main():
    sucho = "--sucho" in sys.argv[1:]
    os.makedirs(S2, exist_ok=True)
    ks = ksiega()
    uzyte = len(ks)
    p_ok = any(w["lot"] == "P" and w.get("passthrough_ok") for w in ks)
    c_done = any(w["lot"] == "C" and not w["bramka_tempa"] for w in ks)
    plan = ([] if p_ok else ["P"]) + ([] if c_done else ["C"])
    log(f"=== NAD2 S2 {'(na sucho) ' if sucho else ''}start: księga {uzyte}/{BUDZET}, P ok={p_ok}, C zrobione={c_done}, plan {plan}")
    if sucho:
        print(json.dumps({"plan": plan, "uzyte": uzyte, "budzet": BUDZET, "loty": LOTY}, ensure_ascii=False))
        return
    subprocess.run(["sudo", "-n", "systemctl", "stop", "systemd-timesyncd"], check=True)
    stop, wyniki = None, {}
    try:
        while plan:
            if uzyte >= BUDZET:
                stop = "STOP-NAD2-2-BUDZET"; break
            lot = plan[0]
            st, w = boot(lot, NOGA_PRZED + uzyte + 1)
            if st:
                stop = st; break
            uzyte += 1
            wyniki[w["nazwa"]] = w
            if w["breach"]:
                stop = "STOP-NAD2-2-BREACH"; break
            if w["bramka_tempa"]:
                log(f"{w['nazwa']}: przerwany bramką tempa (boot zużyty) — powtórka z rezerwy, jeśli budżet pozwala")
                continue
            if lot == "P" and not w["passthrough_ok"]:
                stop = "STOP-NAD2-2-PASSTHROUGH"; log(f"ALARM {stop}: lot C nie startuje"); break
            plan.pop(0)
            if lot == "C":
                a, s = po_c(w["nazwa"])
                wyniki[w["nazwa"]]["analiza_bezpieczenstwo_ok"] = a.get("bezpieczenstwo_ok")
                wyniki[w["nazwa"]]["sprawdziany"] = {k: v.get("ok") for k, v in s.items() if isinstance(v, dict)}
    except Exception as ex:
        stop = "STOP-NAD2-2-WYJATEK"; log(f"ALARM {stop}: {ex!r}"); raise
    finally:
        subprocess.run(["sudo", "-n", "systemctl", "start", "systemd-timesyncd"])
        log(f"KONIEC booty={uzyte}/{BUDZET} stop={stop} pozostało={plan}")
        p = os.path.join(S2, "kampania_s2.json")
        prev = json.load(open(p)) if os.path.exists(p) else {"przebiegi": []}
        prev["przebiegi"].append({"booty": uzyte, "stop": stop, "wyniki": wyniki, "pozostalo": plan})
        json.dump(prev, open(p, "w"), ensure_ascii=False, indent=1, default=str)
    print("KONIEC", uzyte, stop)


if __name__ == "__main__":
    main()
