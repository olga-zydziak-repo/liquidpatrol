"""r01/authz.py — admisja + podpisane rekordy decyzji (port P4, HMAC-SHA256).

Każda komenda przechodzi przez `Authorizer.admit(command, age_s)`:
  parse (gramatyka) → spec → decyzja (ALLOW / REFUSE(COMMAND_INVALID|STALE_CMD)) → rekord PCDL
  podpisany HMAC-SHA256, wpięty w łańcuch (prev_hash) — odtwarzalny per misja.
Właściwości P4:
  (a) żadnego przejścia trybu bez admisji: `mode_of` odmawia gdy rekord ≠ ALLOW;
  (b) spec wykonany ≡ spec admitowany (tryb z REKORDU, nie re-parse);
  (c) poza gramatyką ⇒ REFUSE(COMMAND_INVALID); komenda przeterminowana ⇒ REFUSE(STALE_CMD);
  (d) rekord podpisany HMAC, łańcuch weryfikowalny i odtwarzalny (bez zegara ściennego).

Klucz = config.HMAC_KEY (placeholder R0.1 — mechanizm i odtwarzalność, nie sekret produkcyjny).
Geo-limit współdzielony z osłoną przez config (A2: jedno źródło).
"""
from __future__ import annotations
import hashlib
import hmac
import json

from r01.language import parse
from r01.config import HMAC_KEY, R_E, STALE_CMD_S

GENESIS = "GENESIS"


def _canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sign(payload: dict, key: bytes = HMAC_KEY) -> str:
    return hmac.new(key, _canonical(payload).encode("utf-8"), hashlib.sha256).hexdigest()


class Authorizer:
    """Łańcuch podpisanych rekordów decyzji dla JEDNEJ misji (deterministyczny, bez zegara)."""

    def __init__(self, key: bytes = HMAC_KEY):
        self.key = key
        self.chain: list[dict] = []

    def admit(self, command: str, age_s: float | None = None, target_xy=None) -> dict:
        spec = parse(command)
        prev = self.chain[-1]["sig"] if self.chain else GENESIS
        if spec is None:                                   # (c) poza gramatyką
            decision, reason, specd, mode = "REFUSE", "COMMAND_INVALID", None, None
        elif age_s is not None and age_s > STALE_CMD_S:    # (c) przeterminowana
            decision, reason, specd, mode = "REFUSE", "STALE_CMD", spec.as_dict(), None
        elif target_xy is not None and \
                max(abs(float(target_xy[0])), abs(float(target_xy[1]))) > R_E:
            decision, reason, specd, mode = "REFUSE", "GEOFENCE", spec.as_dict(), None
        else:
            decision, reason, specd, mode = "ALLOW", None, spec.as_dict(), spec.mode()
        payload = {"seq": len(self.chain), "prev_hash": prev, "command_raw": command,
                   "decision": decision, "reason": reason, "spec": specd, "mode": mode}
        rec = dict(payload); rec["sig"] = sign(payload, self.key)
        self.chain.append(rec)
        return rec

    def mode_of(self, rec: dict) -> str:
        """(a)+(b): tylko admitowany ALLOW nadaje tryb; tryb = z REKORDU (nie re-parse)."""
        if rec["decision"] != "ALLOW":
            raise PermissionError(f"brak admisji: {rec['decision']}({rec['reason']})")
        return rec["mode"]

    def verify_chain(self) -> bool:
        prev = GENESIS
        for rec in self.chain:
            payload = {k: rec[k] for k in
                       ("seq", "prev_hash", "command_raw", "decision", "reason", "spec", "mode")}
            if rec["prev_hash"] != prev:
                return False
            if not hmac.compare_digest(rec["sig"], sign(payload, self.key)):
                return False
            prev = rec["sig"]
        return True
