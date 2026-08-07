"""r01/language.py — gramatyka ZAMKNIĘTA, parser DETERMINISTYCZNY (port P4).

Zero LLM w torze autoryzacji. Gramatyka R0.2 (§6 PRE_R01 + §2.4 PRE_R02):
    start patrol | hold | resume | return home | abort | observe on | observe off
Parser → Spec (kanoniczny) albo None (poza gramatyką → NO_MATCH → REFUSE(COMMAND_INVALID)).
Leksykon = nowy habitat (komendy patrolu); struktura parsera portowana z LiquidSight.

R0.2 (§2.4): `observe on/off` = AUTORYTET trybu OBSERVE (default on). OBSERVE jest auto-wyzwalany
kanałem (ENTRY detektora), ALE pozwolenie wchodzi do gramatyki (P4), by nie omijać admisji:
detektor daje ENTRY, gramatyka daje pozwolenie, osłona składa oba. `observe on`→tryb OBSERVE,
`observe off`→powrót do PATROL (cofnięcie autorytetu obserwacji).
"""
from __future__ import annotations
from dataclasses import dataclass

ACTIONS = ("START_PATROL", "HOLD", "RESUME", "RETURN_HOME", "ABORT", "OBSERVE_ON", "OBSERVE_OFF")

# mapowanie akcji → tryb osłony (r01.shield.M_*)
ACTION_TO_MODE = {
    "START_PATROL": "PATROL",
    "HOLD": "HOLD",
    "RESUME": "PATROL",
    "RETURN_HOME": "RETURN",
    "ABORT": "ABORT",
    "OBSERVE_ON": "OBSERVE",
    "OBSERVE_OFF": "PATROL",
}

_CANON = {"START_PATROL": "start patrol", "HOLD": "hold", "RESUME": "resume",
          "RETURN_HOME": "return home", "ABORT": "abort",
          "OBSERVE_ON": "observe on", "OBSERVE_OFF": "observe off"}
_TABLE = {"start patrol": "START_PATROL", "hold": "HOLD", "resume": "RESUME",
          "return home": "RETURN_HOME", "abort": "ABORT",
          "observe on": "OBSERVE_ON", "observe off": "OBSERVE_OFF"}


@dataclass(frozen=True)
class Spec:
    action: str

    def canonical_command(self) -> str:
        return _CANON[self.action]

    def mode(self) -> str:
        return ACTION_TO_MODE[self.action]

    def as_dict(self) -> dict:
        return {"action": self.action}


def normalize(command: str) -> str:
    return " ".join(command.strip().lower().split())


def parse(command: str) -> Spec | None:
    c = normalize(command)
    action = _TABLE.get(c)
    return Spec(action) if action else None


def in_grammar(command: str) -> bool:
    return parse(command) is not None
