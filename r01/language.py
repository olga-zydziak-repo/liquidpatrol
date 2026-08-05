"""r01/language.py — gramatyka ZAMKNIĘTA, parser DETERMINISTYCZNY (port P4).

Zero LLM w torze autoryzacji. Gramatyka R0.1 (§6 PRE_R01):
    start patrol | hold | resume | return home | abort
Parser → Spec (kanoniczny) albo None (poza gramatyką → NO_MATCH → REFUSE(COMMAND_INVALID)).
Leksykon = nowy habitat (komendy patrolu); struktura parsera portowana z LiquidSight.
"""
from __future__ import annotations
from dataclasses import dataclass

ACTIONS = ("START_PATROL", "HOLD", "RESUME", "RETURN_HOME", "ABORT")

# mapowanie akcji → tryb osłony (r01.shield.M_*)
ACTION_TO_MODE = {
    "START_PATROL": "PATROL",
    "HOLD": "HOLD",
    "RESUME": "PATROL",
    "RETURN_HOME": "RETURN",
    "ABORT": "ABORT",
}


@dataclass(frozen=True)
class Spec:
    action: str

    def canonical_command(self) -> str:
        return {"START_PATROL": "start patrol", "HOLD": "hold", "RESUME": "resume",
                "RETURN_HOME": "return home", "ABORT": "abort"}[self.action]

    def mode(self) -> str:
        return ACTION_TO_MODE[self.action]

    def as_dict(self) -> dict:
        return {"action": self.action}


def normalize(command: str) -> str:
    return " ".join(command.strip().lower().split())


def parse(command: str) -> Spec | None:
    c = normalize(command)
    table = {"start patrol": "START_PATROL", "hold": "HOLD", "resume": "RESUME",
             "return home": "RETURN_HOME", "abort": "ABORT"}
    action = table.get(c)
    return Spec(action) if action else None


def in_grammar(command: str) -> bool:
    return parse(command) is not None
