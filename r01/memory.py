"""r01/memory.py — pamięć korekt (port akt A4). OPCJONALNA w R0.1.

Korekta operatora = mapowanie ALIASU na słowo ZNANE gramatyce (np. halt→hold), zapisana jako
podpisany rekord (HMAC, jak authz) i aktywna od następnej komendy. Alias rozwiązywany PRZED
parserem — autoryzacja zawsze widzi kanoniczny spec.

ZAKAZY (niezmienniki §5): zero zmian progów osłony, zero zmian gramatyki (alias nie może nadpisać
słowa gramatyki; cel aliasu MUSI być słowem gramatyki). Moduł nie importuje osłony.
"""
from __future__ import annotations

from r01.language import normalize
from r01.authz import sign, GENESIS
from r01.config import HMAC_KEY

GRAMMAR_WORDS = {"start", "patrol", "hold", "resume", "return", "home", "abort"}


class SemanticMemory:
    def __init__(self, key: bytes = HMAC_KEY):
        self.key = key
        self.aliases: dict[str, str] = {}
        self.records: list[dict] = []

    def learn(self, alias: str, canonical: str) -> dict:
        alias = normalize(alias); canonical = normalize(canonical)
        if canonical not in GRAMMAR_WORDS:
            raise ValueError(f"cel aliasu '{canonical}' poza słowami gramatyki")
        if alias in GRAMMAR_WORDS:
            raise ValueError(f"alias '{alias}' jest słowem gramatyki — zakaz nadpisania (§5)")
        if " " in alias:
            raise ValueError("alias musi być pojedynczym tokenem")
        prev = self.records[-1]["sig"] if self.records else GENESIS
        payload = {"seq": len(self.records), "prev_hash": prev,
                   "kind": "alias", "alias": alias, "canonical": canonical}
        rec = dict(payload); rec["sig"] = sign(payload, self.key)
        self.records.append(rec)
        self.aliases[alias] = canonical
        return rec

    def resolve(self, command: str) -> str:
        return " ".join(self.aliases.get(t, t) for t in normalize(command).split())

    def verify_chain(self) -> bool:
        import hmac
        prev = GENESIS
        for rec in self.records:
            payload = {k: rec[k] for k in ("seq", "prev_hash", "kind", "alias", "canonical")}
            if rec["prev_hash"] != prev or not hmac.compare_digest(rec["sig"], sign(payload, self.key)):
                return False
            prev = rec["sig"]
        return True
