# MAPA KRYTERIÓW — K2 kampania kryterialna (W2)

Łańcuch: PRE_K2 + ANEKS_K2-0…-5. Reguła W2/SR-7: kryterium bez źródła nie istnieje.

| # | kryterium | wartość | źródło |
|---|---|---|---|
| G1 | git czysty | push {a5b15d3,k4b,2cd218d}=Olga (origin=2cd218d) | I0.1 |
| G2 | frozen+piny 5/5 | SHIELD FROZEN=True | SR-2 |
| G3 | 12 ep denialowych = 6 komórek × 2 ziarna | c00,c03,c05,c07,c09,c11 × s01,s02 | PRE_K2 K3 |
| G4 | komórki r_p95(T_inj)≤26m | wszystkie 6 (r4_envelope r@1orb_p95: 23.1/13.0/11.9/13.6/17.9/25.4) | PRE_K2 K3 + r4_envelope.json |
| G5 | **T_inj = t_entry+30s** | ±0.2s | PRE_K2 K2 |
| G6 | **1 denial-ep/boot** (denial kończy boot) | — | PRE_K2 K1 |
| G7 | budżet **K5′ ≤15 bootów lotnych / ≤2 sesje** | 12 ep + zapas ponowień | ANEKS_K2-5 |
| G8 | **pasmo t_refuse [0.05,0.15]s** | brzeg 0.04/0.16 FAIL | ANEKS_K2-1 |
| G9 | kryteria (+) epizodu | REFUSE(POS)≤0.15s od wykrywalności ∧ D5 do touchdown ∧ breach=False ∧ x_exc≤eps_cap ∧ bez natywnego failsafe | PRE_K2 K4 |
| G10 | **eps_cap = C.EPS_CAP = 9.25m (37/4) TRIPWIRE** | x_exc>9.25 ∧ breach=False ⇒ STOP diagnostyczny (nie zwykły FAIL) | ANEKS_K2-4 §3 + r03.config |
| G11 | **drabina: 12/12 PASS · 1 porażka przejęcia na ważnym = NIEROZSTRZYGNIĘTE(STOP) · ≥2 = FAIL** | — | ANEKS_K2-1 |
| G12 | **breach jakikolwiek ⇒ STOP natychmiast** (domena certów) | — | PRE_K2 K4 |
| G13 | kolejka cap attempt≤3; env-invalid re-append | — | PRE_K2 K4; C8 |
| G14 | ramię (−): faza nominalna (t_entry+30, monitor uzbrojony) 0 fałszywych REFUSE(POS), OSOBNO od K4b | K2_ARM_MONITOR=1 | ANEKS_K2-5 §1; ANEKS_K2-1 |
| G15 | raport per epizod denialowy = **sekwencja zdarzeń verbatim z trace** (ledger, przyczyna) | — | ANEKS_K2-4 §4 |
| G16 | czysty host, sustained-clean, cooldowny, driver w repo, zapisy results/K2/** | — | PROMPT; SR-5 |
