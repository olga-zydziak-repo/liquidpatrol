"""r01/proofs/p4_verify.py — P4: admisja/gramatyka/HMAC (property-based, bez z3).

Port kształtu z liquidsight/proofs/p4_verify.py na zestaw komend R0.1 (§6):
  start patrol | hold | resume | return home | abort
Właściwości:
  (a) żaden tryb bez admisji: mode_of odmawia gdy rekord ≠ ALLOW;
  (b) tryb wykonany ≡ tryb admitowany (z rekordu, nie re-parse);
  (c) poza gramatyką ⇒ REFUSE(COMMAND_INVALID); przeterminowana ⇒ REFUSE(STALE_CMD);
      cel poza R_E ⇒ REFUSE(GEOFENCE);
  (d) rekord HMAC-SHA256, łańcuch weryfikowalny + odtwarzalny, sabotaż wykryty.
Uruchom: python3 -m r01.proofs.p4_verify
"""
from __future__ import annotations
import hashlib, json, os, sys, random

from r01.authz import Authorizer
from r01.language import parse, ACTIONS
from r01.config import STALE_CMD_S, R_E

_HERE = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(_HERE, "certs", "P4.json")

VALID = ["start patrol", "hold", "resume", "return home", "abort", "observe on", "observe off"]
# poza gramatyką: w tym near-miss dla OBSERVE (samo "observe", zły argument) — dalej COMMAND_INVALID
OUT = ["land", "fly to the red box", "patrol", "start", "hold now", "", "returnhome", "abort!",
       "observe", "observe maybe", "observe on now"]


def check():
    checks = {}
    # (c) wyczerpujące: 5 in-grammar, ~8 out-of-grammar
    a = Authorizer()
    checks["in_grammar_all_ALLOW"] = all(a.admit(c)["decision"] == "ALLOW" for c in VALID)
    a2 = Authorizer()
    checks["out_grammar_all_COMMAND_INVALID"] = all(
        a2.admit(c)["reason"] == "COMMAND_INVALID" for c in OUT)
    # (c) staleness + geofence
    a3 = Authorizer()
    checks["stale_REFUSE"] = a3.admit("hold", age_s=STALE_CMD_S + 0.1)["reason"] == "STALE_CMD"
    checks["fresh_ALLOW"] = a3.admit("hold", age_s=0.0)["decision"] == "ALLOW"
    checks["geofence_target_REFUSE"] = a3.admit("start patrol", target_xy=(R_E + 5, 0))["reason"] == "GEOFENCE"
    # (a)+(b): mode_of tylko dla ALLOW; tryb z rekordu
    a4 = Authorizer()
    rec = a4.admit("start patrol")
    checks["mode_from_record"] = a4.mode_of(rec) == "PATROL"
    # R0.2: observe on/off → tryb OBSERVE / PATROL (autorytet trybu OBSERVE, §2.4)
    checks["observe_on_mode_OBSERVE"] = a4.mode_of(a4.admit("observe on")) == "OBSERVE"
    checks["observe_off_mode_PATROL"] = a4.mode_of(a4.admit("observe off")) == "PATROL"
    try:
        a4.mode_of(a4.admit("land")); checks["mode_of_denies_non_allow"] = False
    except PermissionError:
        checks["mode_of_denies_non_allow"] = True
    # (d) łańcuch + tamper
    checks["chain_verifiable"] = a.verify_chain()
    a.chain[0]["command_raw"] = "abort"      # sabotaż
    checks["tamper_detected"] = not a.verify_chain()

    # --- DEMO-B: warstwa TOKENU operatora ("no OBSERVE without operator token") -------------
    at = Authorizer()
    checks["token_default_deny"] = (at.token_auth_ok(0) is False)          # brak tokenu ⇒ auth_ok False
    # anti-bypass: samo `admit("grant observe")` (bez nonce/epizodu) NIE jest ważnym tokenem
    at.admit("grant observe")
    checks["plain_grant_not_token"] = (at.token_auth_ok(0) is False)
    # pre-autoryzacja zakazana: ¬locked ⇒ REFUSE(PREAUTH), auth_ok dalej False
    r = at.issue_token("op1", "n_pa", 0, locked=False, current_seq=0)
    checks["preauth_not_locked"] = (r["decision"] == "REFUSE" and r["reason"] == "PREAUTH"
                                    and at.token_auth_ok(0) is False)
    # pre-autoryzacja zakazana: zły admission_seq ⇒ REFUSE(PREAUTH)
    r = at.issue_token("op1", "n_ep", 7, locked=True, current_seq=0)
    checks["preauth_wrong_episode"] = (r["reason"] == "PREAUTH" and at.token_auth_ok(0) is False)
    # ważny grant: ALLOW, mode OBSERVE, auth_ok True TYLKO dla epizodu wydania
    r = at.issue_token("op1", "n_ok", 0, locked=True, current_seq=0)
    checks["grant_allow_observe"] = (r["decision"] == "ALLOW" and r["mode"] == "OBSERVE")
    checks["token_binds_episode"] = (at.token_auth_ok(0) is True and at.token_auth_ok(1) is False)
    # nonce jednorazowy: reuse GRANTOWANEGO nonce ⇒ REFUSE(NONCE_REUSE)
    r = at.issue_token("op1", "n_ok", 0, locked=True, current_seq=0)
    checks["nonce_reuse_rejected"] = (r["reason"] == "NONCE_REUSE")
    # tamper pól tokenu wykrywany (podpis pokrywa nonce/admission_seq/operator_id)
    checks["token_chain_verifiable"] = at.verify_chain()
    saved = at.chain[-2]["nonce"]; at.chain[-2]["nonce"] = "forged"
    checks["token_tamper_detected"] = (not at.verify_chain())
    at.chain[-2]["nonce"] = saved
    # konsumpcja na EXPIRE: re-admisja wymaga NOWEGO tokenu
    checks["consume_on_expire"] = (at.consume_tokens(0) == 1 and at.token_auth_ok(0) is False)
    r = at.issue_token("op1", "n_ok2", 1, locked=True, current_seq=1)     # nowy epizod, nowy nonce
    checks["readmission_needs_new_token"] = (at.token_auth_ok(1) is True and at.verify_chain())

    # property-based tokeny: 1500 losowych sekwencji issue/consume — łańcuch ZAWSZE weryfikowalny,
    # auth_ok WYŁĄCZNIE gdy istnieje niekonsumowany ALLOW-grant bieżącego epizodu (default-deny inwariant)
    rngt = random.Random(4242)
    tok_ok = True
    for _ in range(1500):
        az = Authorizer(); seq = 0; granted_live = False
        for _ in range(rngt.randint(1, 8)):
            act = rngt.choice(["issue", "expire", "advance"])
            if act == "advance":                  # ENTRY: nowy epizod (konsumpcja poprzedniego)
                az.consume_tokens(seq); seq += 1; granted_live = False
            elif act == "expire":
                az.consume_tokens(seq); granted_live = False
            else:
                locked = rngt.random() < 0.8
                tseq = rngt.choice([seq, seq + 1, seq - 1])
                nonce = f"n{rngt.random()}"
                r = az.issue_token("op", nonce, tseq, locked=locked, current_seq=seq)
                if r["decision"] == "ALLOW":
                    granted_live = True
                elif locked and tseq == seq:      # locked ∧ epizod OK ∧ świeży nonce ⇒ MUSI ALLOW
                    tok_ok = False
            if az.token_auth_ok(seq) != granted_live:
                tok_ok = False
        if not az.verify_chain():
            tok_ok = False
    checks["token_property_1500"] = tok_ok

    # property-based: 2000 losowych sekwencji, łańcuch zawsze spójny, decyzje zgodne z parse
    rng = random.Random(1234)
    prop_ok = True
    for _ in range(2000):
        az = Authorizer()
        n = rng.randint(1, 6)
        for _ in range(n):
            cmd = rng.choice(VALID + OUT)
            age = rng.choice([None, 0.0, STALE_CMD_S + 1.0])
            rec = az.admit(cmd, age_s=age)
            spec = parse(cmd)
            if spec is None:
                if rec["decision"] != "REFUSE" or rec["reason"] != "COMMAND_INVALID":
                    prop_ok = False
            elif age is not None and age > STALE_CMD_S:
                if rec["reason"] != "STALE_CMD":
                    prop_ok = False
            else:
                if rec["decision"] != "ALLOW":
                    prop_ok = False
        if not az.verify_chain():
            prop_ok = False
    checks["property_2000_seqs"] = prop_ok
    return checks


def main():
    ch = check()
    ok = all(ch.values())
    print("=== P4 admisja/gramatyka/HMAC ===")
    for k, v in ch.items():
        print(f"  {k}: {'✓' if v else '✗ FAIL'}")
    print(f"WERDYKT P4: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)
    cert = {"property": "P4", "verdict": "PASS",
            "method": "wyczerpujący test gramatyki (7 in / 11 out) + property-based (2000 admisji + "
                      "1500 tokenów) + HMAC-SHA256; DEMO-B: warstwa tokenu operatora (OBSERVE_GRANT)",
            "checks": {k: bool(v) for k, v in ch.items()},
            "grammar": list(ACTIONS), "commands": VALID,
            "properties": {"a": "brak trybu bez admisji", "b": "tryb wykonany ≡ admitowany",
                           "c": "poza gramatyką⇒COMMAND_INVALID; stale⇒STALE_CMD; cel poza R_E⇒GEOFENCE",
                           "d": "HMAC-SHA256, łańcuch weryfikowalny+odtwarzalny, sabotaż wykryty",
                           "token": "DEMO-B: default-deny (brak tokenu⇒auth_ok False); 'no OBSERVE without "
                                    "operator token'; pre-autoryzacja zakazana (¬locked ∨ zły epizod⇒PREAUTH); "
                                    "nonce jednorazowy (reuse⇒NONCE_REUSE); per-admisja (token wiąże epizod, "
                                    "konsumpcja na EXPIRE, re-admisja wymaga nowego); tamper pól tokenu "
                                    "(nonce/admission_seq/operator_id) wykryty przez podpis. authority gating, "
                                    "NIE 'secure C2' (ANEKS_D1 §7)"},
            "code_refs": {"authz": "r01/authz.py (issue_token/token_auth_ok/consume_tokens)",
                          "language": "r01/language.py (OBSERVE_GRANT)"},
            "model_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
    os.makedirs(os.path.dirname(CERT), exist_ok=True)
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT}")


if __name__ == "__main__":
    main()
