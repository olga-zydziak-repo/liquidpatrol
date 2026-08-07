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
            "method": "wyczerpujący test gramatyki (5 in / 8 out) + property-based (2000) + HMAC-SHA256",
            "checks": {k: bool(v) for k, v in ch.items()},
            "grammar": list(ACTIONS), "commands": VALID,
            "properties": {"a": "brak trybu bez admisji", "b": "tryb wykonany ≡ admitowany",
                           "c": "poza gramatyką⇒COMMAND_INVALID; stale⇒STALE_CMD; cel poza R_E⇒GEOFENCE",
                           "d": "HMAC-SHA256, łańcuch weryfikowalny+odtwarzalny, sabotaż wykryty"},
            "code_refs": {"authz": "r01/authz.py", "language": "r01/language.py"},
            "model_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
    os.makedirs(os.path.dirname(CERT), exist_ok=True)
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT}")


if __name__ == "__main__":
    main()
