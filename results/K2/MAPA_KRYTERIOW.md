# MAPA KRYTERIÓW — K2 sesja build (W2, PROMPT_K2_BUILD I0.3)

LiquidPatrol · pozycja 6 · sesja build (ZERO bootów). Reguła W2/SR-7: kryterium bez źródła NIE ISTNIEJE.
Łańcuch: PRE_K2 + ANEKS_K2-0/-1 + PROMPT_K2_BUILD.

| # | kryterium | wartość | źródło |
|---|---|---|---|
| G1 | git czysty (origin..HEAD puste) | push {62a068a,e29a154,5811acb}=Olga | I0.1 |
| G2 | architektura = (ii) uzbrojenie pętli ławki | pos_flag+D5+hook+certs w bench | PRE_K2 **K1** |
| G3 | ekstrakcja D5 = chirurgia INFRA-3 | `safe_descend.py`, diff minimalny, bit-w-bit, re-baseline pinu, ratyf. przed lotem | PRE_K2 K1(b); PROMPT B2; SR-2 |
| G4 | **T_inj = t_entry + 30 s** | ≈1 okrążenie; ±0.2 s test timingu | PRE_K2 **K2** |
| G5 | komórki: **r_p95(faza T_inj) ≤ 26 m**, 6 komórek × 2 ziarna = **12 ep** | <6 komórek ⇒ STOP tabela do Olgi | PRE_K2 **K3** + `r4_envelope.json` |
| G6 | ziarna z puli 1-10 (znane sieci — mierzymy przejęcie, nie uogólnienie) | — | PRE_K2 K3 |
| G7 | **pasmo t_refuse = [0.05, 0.15] s** (dziedziczone z K1) | brzeg 0.04/0.16 ⇒ FAIL | ANEKS_K2-1 §1 |
| G8 | **drabina werdyktu: 12/12 PASS · 1 porażka przejęcia na ważnym = NIEROZSTRZYGNIĘTE(STOP) · ≥2 = FAIL** | — | ANEKS_K2-1 §1; PRE_K2 K4 |
| G9 | kryteria (+) per epizod | REFUSE(POS)≤0.15s od wykrywalności ∧ D5 do touchdown ∧ breach=False ∧ x_exc≤EPS_CAP ∧ sekwencja bez natywnego failsafe | PRE_K2 **K4** |
| G10 | **breach jakikolwiek ⇒ STOP natychmiast** (domena certów) | — | PRE_K2 K4 |
| G11 | ramię (−): 0 fałszywych REFUSE(POS) w nominalu; baza 0/84 = „bez wartości dowodowej dla toru POS" (monitor był nieuzbrojony) | raportowane osobno, nie sklejane | ANEKS_K2-1 §1; PRE_K2 K4 |
| G12 | **K4b = 3 booty czysto nominalne z uzbrojonym monitorem** (~12 ep bez denialu), 0 fałszywych REFUSE(POS); po shakeout, przed kryterialnymi | **weto Olgi „K4b nie" otwarte do końca sesji build** | ANEKS_K2-1 §1 |
| G13 | glue `k2_judge` = bench_judge(ważność do T_inj)+k1-metryki po T_inj; **frozen SHA przed lotami**; zero zmian w zamrożonych sędziach | testy syntetyczne | PRE_K2 K4; PROMPT B6; SR-4 |
| G14 | certs_selfcheck włączony dla FLIGHT=bench | wynik w manifeście | PRE_K2 K1(d); PROMPT B5 |
| G15 | testy bit-w-bit ekstrakcji | 4221 ticków, identyczne cmd (wzór A1.3) | PROMPT_K2_BUILD B2 |
| G16 | ZERO bootów w sesji build; zapisy tylko `results/K2/**` | — | PROMPT nagłówek; SR-3/SR-5 |
| G17 | zakres diffu gate = import + wywołanie, nic więcej; dodatkowy hunk ⇒ STOP/revert | — | SR-2 |
| G18 | po B2 NIC na master przed ratyfikacją ANEKS_K2-2 (ceremonia); B3-B6 na branchu | — | PROMPT B2/STOP-K2a |

## Kolejność sesji (PROMPT + ANEKS_K2-1 §2)
K2-B0(docs) → mapa(ta) → B1 baseline → **B2 ekstrakcja D5 (bit-w-bit)** → **STOP-K2a** (raport, ceremonia; B3-B6 na branchu niecommitowane do master) → [ANEKS_K2-2] → aktualizacja pinów + commit B2-B6 → push → shakeout diag → K4b → kampania 12 ep → STOP-K2c=RAPORT_K2.

## Kanon K6 (pre-deklarowany, PRE_K2 K6)
WOLNO: „pod realnym denialem GNSS w trakcie orbity kontrolera uczonego osłona odmówiła w ≤X s i sprowadziła maszynę bez naruszenia koperty, 12/12, w SITL pod emulowanym feedem". NIE WOLNO: „system bezpieczny"/„certyfikowany"/uogólnień poza SITL/języka istotności. Ledger cytuje przyczynę z trace.
