# MAPA KRYTERIÓW — noga sieci, sesja 2 (W2, pierwsza czynność sesji)

LiquidPatrol · pozycja 3 · sesja 2 (OSTATNIA poz.3) · trening offline, ZERO SITL.
Reguła W2: kryterium bez źródła NIE ISTNIEJE. Łańcuch: PRE_NET + ANEKS_NET-0 + **ANEKS_NET-1** + PROMPT_NET_S1 (dziedziczone I0/SR).

| # | kryterium | wartość | źródło |
|---|---|---|---|
| G1 | git czysty (origin..HEAD puste) | push {N-B0,N-B1,N-B2,raport}=Olga | ANEKS_NET-1 §7; PROMPT I0.1 |
| G2 | frozen nietknięty (piny + zestaw ławki) | bajt-identyczne | I0.2/SR-2; PRE_NET §4 |
| **G13′** | **BRAMKA N3(i) = PER ROLLOUT ≥ 20/24** | analog-D6 (wejście≤25s ∧ frac≥0.85 ∧ d_min≥4) w ≥20/24 rolloutów (komórka×ziarno TEST 4,8); widoki per-komórka (oba/którekolwiek) raportowane opisowo | **ANEKS_NET-1 §2** (zastępuje S1 „oba ziarna") |
| G-MLP | MLP PASS (21/24) → FREEZE, zero dalszej pracy | `FREEZE_NET.md` weights_sha + config | ANEKS_NET-1 §4 |
| G-NCP1 | N-B3 przed wznowieniem: cap epok ×5 (200→1000) + harmonogram lr; selekcja WYŁĄCZNIE VAL | naprawa przyrządu, nie strojenie TEST | ANEKS_NET-1 §3.1 |
| G-NCP2 | DAgger (jeśli): 1 runda, wyrocznia 840514361e, model punktowy FEED-B, TRAIN+DAgger, selekcja VAL | trigger = FAIL S1 (spełniony) | ANEKS_NET-1 §3.2; N4/ANEKS_NET-0 |
| G-TEST | TEST NCP dotykany DRUGI i OSTATNI raz (jedno dotknięcie: po retrainie ALBO po DAgger; jeśli DAgger → TEST po nim); krotność (2×) w raporcie; TRZECIEGO NIE BĘDZIE | decyzja DAgger na VAL, nie TEST | ANEKS_NET-1 §3.3; SR-3 |
| G-NCPfail | NCP FAIL po ścieżce 1–3 ⇒ ODPADA; poz.4 sam MLP; „liquid" zamknięte offline negatywnie (raportowalne) | — | ANEKS_NET-1 §3.4 |
| G-DAG | okno weta „DAgger nie" ZAMKNIĘTE (koniec S1 bez weta) ⇒ N4=TAK | — | ANEKS_NET-1 §5 |
| G-BUD | budżet: S2 = OSTATNIA sesja poz.3 (cap ≤2) | — | ANEKS_NET-1 §3; PRE_NET N5 |
| G-P5 | raport S2 podaje KOMÓRKI porażek rolloutu obu ramion (dziedziczenie c05/c07/c09?) | — | ANEKS_NET-1 §6 |
| G-SITL | ZERO bootów SITL, zero zmian harness/; drivery wersjonowane w repo | — | PROMPT nagłówek; ANEKS_NET-0 §2 |

## Kolejność sztywna S2 (ANEKS_NET-1 §7)
FREEZE MLP (§4) → N-B3 (config NCP) → retrain NCP (selekcja VAL) → decyzja DAgger NA VAL (nie TEST) → [DAgger 1 runda → retrain → VAL] → **TEST NCP raz (ostatni)** → bramka §2 → STOP-N2 (RAPORT_NET_S2: komórki porażek, krotność TEST, werdykty obu ramion, FREEZE_NET kompletny).

## Nota TEST-discipline (kluczowe)
Bramka §2 jest rolloutem na ziarnach TEST ⇒ JEST dotknięciem TEST. Decyzja o DAgger MUSI zapaść na VAL (ziarno 2, rollout-proxy), nie na TEST. TEST NCP wykonywany DOKŁADNIE RAZ w S2 (2. i ostatni łącznie). Krotność raportowana przy werdykcie.
