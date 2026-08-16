"""r01/authz.py — admisja + podpisane rekordy decyzji (port P4, HMAC-SHA256).

Każda komenda przechodzi przez `Authorizer.admit(command, age_s)`:
  parse (gramatyka) → spec → decyzja (ALLOW / REFUSE(COMMAND_INVALID|STALE_CMD)) → rekord PCDL
  podpisany HMAC-SHA256, wpięty w łańcuch (prev_hash) — odtwarzalny per misja.
Właściwości P4:
  (a) żadnego przejścia trybu bez admisji: `mode_of` odmawia gdy rekord ≠ ALLOW;
  (b) spec wykonany ≡ spec admitowany (tryb z REKORDU, nie re-parse);
  (c) poza gramatyką ⇒ REFUSE(COMMAND_INVALID); komenda przeterminowana ⇒ REFUSE(STALE_CMD);
  (d) rekord podpisany HMAC, łańcuch weryfikowalny i odtwarzalny (bez zegara ściennego).

Noga D / DEMO-B (§2 PROMPT_D_BUILD_1) — TOKEN operatora (authority gating, NIE „secure C2"):
  `issue_token(operator_id, nonce, admission_seq, locked, current_seq)` wydaje podpisany rekord
  `OBSERVE_GRANT` (gramatyka `grant observe`) rozszerzony o `operator_id`/`nonce`/`admission_seq`.
  Własności (kryte P4 + testami deterministycznymi, ANEKS_D1 §Semantyka):
    - default-deny: brak ważnego tokenu ⇒ `token_auth_ok(seq)` = False (osłona emituje NO_AUTH);
    - pre-autoryzacja zakazana: ¬locked ∨ admission_seq≠current_seq ⇒ REFUSE(PREAUTH), logowane;
    - nonce jednorazowy: reuse GRANTOWANEGO nonce ⇒ REFUSE(NONCE_REUSE);
    - per-admisja: token ważny tylko dla epizodu wydania; `consume_tokens(seq)` na EXPIRE.
  Cały rekord (łącznie z polami tokenu) jest w podpisie HMAC — `verify_chain` odtwarza payload jako
  rekord-bez-`sig`, więc tamper `operator_id`/`nonce`/`admission_seq` jest WYKRYWALNY.

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
        self._nonces_seen: set = set()     # DEMO-B: nonce jednorazowy (burn dopiero na GRANT)
        self._consumed: set = set()        # DEMO-B: indeksy tokenów skonsumowanych na EXPIRE

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

    # -- TOKEN operatora (DEMO-B) -------------------------------------------
    def issue_token(self, operator_id: str, nonce, admission_seq: int, *,
                    locked: bool, current_seq: int) -> dict:
        """Wydaje token `OBSERVE_GRANT` dla epizodu `admission_seq`. Default-deny:
        pre-autoryzacja (¬locked ∨ admission_seq≠current_seq) ⇒ REFUSE(PREAUTH), logowane w łańcuchu;
        reuse GRANTOWANEGO nonce ⇒ REFUSE(NONCE_REUSE). Nonce burnowany DOPIERO na GRANT (odrzucone
        próby nie palą nonce'a — pre-auth nic nie nadał)."""
        spec = parse("grant observe")                       # nowy element gramatyki (OBSERVE_GRANT)
        prev = self.chain[-1]["sig"] if self.chain else GENESIS
        if not locked or int(admission_seq) != int(current_seq):
            decision, reason, mode = "REFUSE", "PREAUTH", None
        elif nonce in self._nonces_seen:
            decision, reason, mode = "REFUSE", "NONCE_REUSE", None
        else:
            decision, reason, mode = "ALLOW", None, spec.mode()
            self._nonces_seen.add(nonce)
        payload = {"seq": len(self.chain), "prev_hash": prev, "command_raw": "grant observe",
                   "decision": decision, "reason": reason, "spec": spec.as_dict(), "mode": mode,
                   "operator_id": str(operator_id), "nonce": nonce, "admission_seq": int(admission_seq)}
        rec = dict(payload); rec["sig"] = sign(payload, self.key)
        self.chain.append(rec)
        return rec

    def token_auth_ok(self, current_seq: int) -> bool:
        """auth_ok dla osłony: istnieje ALLOW `OBSERVE_GRANT` związany z `current_seq`, niekonsumowany.
        (podpis ∧ nonce świeży ∧ epizod zgodny ∧ niekonsumowany — świeżość/nonce wymuszone przy wydaniu)."""
        for i, rec in enumerate(self.chain):
            if (rec.get("decision") == "ALLOW" and rec.get("spec", {}).get("action") == "OBSERVE_GRANT"
                    and rec.get("admission_seq") is not None
                    and int(rec["admission_seq"]) == int(current_seq) and i not in self._consumed):
                return True
        return False

    def consume_tokens(self, admission_seq: int) -> int:
        """EXPIRE epizodu: konsumuje wszystkie ALLOW tokeny `admission_seq` (re-admisja wymaga nowego)."""
        n = 0
        for i, rec in enumerate(self.chain):
            if (rec.get("decision") == "ALLOW" and rec.get("spec", {}).get("action") == "OBSERVE_GRANT"
                    and rec.get("admission_seq") is not None
                    and int(rec["admission_seq"]) == int(admission_seq) and i not in self._consumed):
                self._consumed.add(i); n += 1
        return n

    def verify_chain(self) -> bool:
        prev = GENESIS
        for rec in self.chain:
            # payload = rekord bez `sig` → tamper KAŻDEGO pola (w tym operator_id/nonce/admission_seq) wykryty
            payload = {k: v for k, v in rec.items() if k != "sig"}
            if rec["prev_hash"] != prev:
                return False
            if not hmac.compare_digest(rec["sig"], sign(payload, self.key)):
                return False
            prev = rec["sig"]
        return True
