# MAPA KRYTERIÓW — pozycja 4, kampania kryterialna F2 (W2, pierwsza czynność sesji)

LiquidPatrol · loty sieci pod osłoną · reguła W2/SR-9: kryterium bez źródła NIE ISTNIEJE.
Łańcuch: PRE_NET N6/N7 + ANEKS_NET-0/-1/-2/-3 + PROMPT_NET_FLY.

| # | kryterium | wartość | źródło |
|---|---|---|---|
| G1 | git czysty (origin..HEAD puste) | push=Olga | I0.1; ANEKS_NET-3 §5 |
| G2 | frozen + FREEZE_NET + FREEZE_FLY nietykalne (wagi=pin, sha-refusal przy starcie) | bajt-identyczne | I0.2; SR-2 |
| G3 | **próg PASS ramienia = ≥ 40/48** (0.9×0.9167) na ziarnach 1-4 | ≥40/48 | PRE_NET **N7**; I0.3 |
| G4 | ważność V2′ + kolejka C8 + cap attempt≤3 + pierwsza ważna próba + INVALID_START→koniec bez inkr. | — | ławka/C8; I0.3 |
| G5 | **breach ⇒ STOP natychmiast**, raport, zero dalszych bootów | — | PRE_NET **N7**; SR-5 |
| G6 | REFUSE ⇒ FAIL epizodu ramienia + wpis do licznika osłony (czas, przyczyna z trace); BEZ limitu STOP | — | PRE_NET **N7** (pomiar tezy) |
| G7 | kolejki OSOBNE per ramię (queue_ncp/queue_mlp), booty PRZEPLATANE ncp/mlp | 48+48, 4 ep/boot | PROMPT F2; N6 |
| G8 | strażnik d_min międzysesyjny: dryf mediany W DÓŁ vs 7.7 ⇒ STOP | mediana/sesja | ANEKS_BENCH-2 R2; PROMPT F2 |
| G9 | warunki sesji: czysty host, pełny pytest z proc_gate, bramka procesowa, cooldowny, driver W REPO | — | PROMPT F2; ANEKS_BENCH-4 O1 |
| G10 | pary sieć↔egzekutor + NCP↔MLP (zgodne/niezgodne, ZERO języka istotności) | — | PRE_NET **N7**; N-F1b |
| G11 | komórki porażek (test dziedziczenia granicy c05/c07/c09 = P-N5-lot) | — | PRE_NET N8; ANEKS_NET-2 |
| G12 | świeże s11-s13 (36 ep/ramię PASS) = luka uogólnienia, RAPORT-ONLY (nie kryterium) | — | PRE_NET **N6**; F3 |
| G13 | zero treningu/DAggera/strojenia; zapisy tylko results/NET/FLY/** + kolejki | — | SR-3/SR-7 |
| G14 | env-block poza budżetem, zachowywany (*_void/); budżet ≤4 sesje/≤45 bootów lotnych | — | PROMPT nagłówek; SR |
| G15 | **§7 RAPORT_NET: „przyrząd bramki oceniony lotem"** (werdykt offline vs lot per ramię + rozkład komórek) | obowiązkowe | **ANEKS_NET-3 §3** (Z-F1) |

## Predykcje (rozliczane w RAPORT_NET §7)
- Prerejestrowane PRE §3: P-N3 (NCP↔MLP niezgodne ≤3 netto), P-N4 (NCP ≥40/48 p≈0.55), P-N5-lot (porażki proximity c05/c07/c09), P-N6 (REFUSE 0-2).
- **Post-diag (ANEKS_NET-3 §3, jawna etykieta):** P-N7 (MLP <40/48 p≈0.55), P-N8 (NCP↔MLP niezgodne ≥5 netto na korzyść NCP p≈0.5 — w napięciu z P-N3; loty rozstrzygną, jedna pada).

## Plan wykonania (przeplot)
Kolejki: queue_ncp/queue_mlp (48 każda). Booty F2: nieparzyste=ncp, parzyste=mlp (przeplot przeciw dryfowi). 12 bootów/ramię = 24 łącznie. Driver `net/run_fly_boot.sh crit <queue>`. Po każdym: judge+record+commit. Breach⇒STOP. Po 48+48: werdykty ≥40/48 → świeże s11-s13 dla PASS → STOP-F1.
