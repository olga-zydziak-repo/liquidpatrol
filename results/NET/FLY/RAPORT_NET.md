# RAPORT_NET — noga sieci, RAPORT KOŃCOWY lotów (pozycja 4) — STOP-F1

LiquidPatrol · CC 6.09.2026 · łańcuch: PRE_NET N6/N7 + ANEKS_NET-0/-1/-2/-3 · świat world_demo_A3 · FILM=0
frozen + FREEZE_NET + FREEZE_FLY bajt-identyczne · ZERO treningu w locie (SR-3) · commity F0/F1/diag/F2/F3 niepushowane (push=Olga)

## §1. D0 + FREEZE_FLY
Weryfikacja sha komplet (I0.4, `results/NET/FLY/D0.md`): frozen ławki, piny, FREEZE_NET (NCP 0337d5ea, MLP 1d190023), przyrząd lotu. Świeży zbiór s11-s13 zamrożony (a2dacee6). net_controller liczy weights_sha przy starcie → rozjazd = odmowa lotu (0 odmów w kampanii — wagi zgodne we wszystkich bootach). Fakt D0(b): mechanizm r = R-G GEOFENCE (bariera P2, shield.py:101-110).

## §2. Diag (STOP-F0, ratyf. ANEKS_NET-3)
boot-0n/0m: bramka techniczna PASS. Smoke: NCP 4/4, MLP 1/4 → znalezisko Z-F1 (luka model↔SITL) zarejestrowane.

## §3. Kampania kryterialna F2 (ziarna 1-4, 48+48, przeplot, kolejki osobne)

| ramię | D6 | p_net | Wilson 95% | próg ≥40/48 | **WERDYKT** |
|---|---|---|---|---|---|
| **NCP-20** | **45/48** | **0.9375** | [0.8316, 0.9785] | ✓ | **PASS** |
| tiny-MLP | 8/48 | 0.1667 | [0.087, 0.2958] | ✗ | **FAIL** |

- **0 breach, 0 REFUSE** w 96 epizodach kryterialnych (+36 fresh). Osłona nie musiała interweniować — MLP zawodził na jakości orbity (frac/sweep/entry), nie na naruszeniu koperty R_E.
- p_net(NCP)=0.9375 ≈ mianownik egzekutora 0.9167 — imitacja niemal dorównuje nauczycielowi w locie.

## §4. Pary (zgodne/niezgodne per scenariusz — ZERO języka istotności, N7)

| para | n | zgodne | niezgodne | kierunek |
|---|---|---|---|---|
| **NCP ↔ egzekutor** | 48 | **47** | 1 | NCP zaliczył 1 scenariusz oblany przez wyrocznię (a_only=1) |
| MLP ↔ egzekutor | 48 | 10 | 38 | egzekutor zaliczył 37, MLP nie (b_only=37) |
| **NCP ↔ MLP** | 48 | 9 | 39 | **netto +37 na korzyść NCP** (NCP-only 38, MLP-only 1) |

NCP odwzorowuje wzorzec D6 nauczyciela niemal 1:1 (47/48). MLP rozjeżdża się z oboma.

## §5. REFUSE-ledger osłony (sekcja tezy programu)

**NCP: 0 REFUSE · MLP: 0 REFUSE** w całej kampanii (F2+F3, 132 epizody). Teza „osłona zawiera zły kontroler" NIE została wystawiona na próbę przez REFUSE — bo nawet słaby MLP nie naruszał koperty R_E (jego porażki to jakość orbity: niedopełniony sweep/frac, d_min<4 wobec INTRUZA — a osłona chroni dom R_E=32, nie separację od intruza). To istotny wynik: **zła sieć degraduje MISJĘ (p_net niski), nie BEZPIECZEŃSTWO (0 breach/0 REFUSE)**. Osłona pozostała cicha, bo złość MLP była w domenie jakości, nie koperty. **Zawieranie tutaj = clip_v + geometria koperty (R_E) i dysku intruza — NIE aktywna interwencja osłony** (aktywna interwencja/REFUSE zmierzona w K1 pod denialem, nie tutaj; ledger PUSTY 0/132). Zakaz roszczenia „osłona zawierała złą sieć" (ANEKS_NET-4 §2).

> **ERRATUM #3 (ANEKS_K2-0 §2 E1, doc-only):** Recon K2 (R1) ustalił, że `bench_flight.py:326` woła `shield.step(..., pos_flag=None)` **na sztywno** ⇒ monitor POS_DEGRADED był **nieuzbrojony przez całą nogę sieci**; ławka to WŁASNA pętla (nie gate), a `certs_selfcheck` w niej nie biegł (`run_boot.sh:72` tylko gate_r03). Fakt „0 REFUSE / 0 breach w 84 ep" **pozostaje bez zmian**, ale interpretacja jest ZAWĘŻONA: REFUSE **pozycyjny** (POS_DEGRADED) był z konstrukcji NIEMOŻLIWY (flaga nieuzbrojona); uzbrojone były wyłącznie gałęzie wg D0(b) — **verbatim z D0.md: „aktywna bramka r = reguła R-G GEOFENCE (bariera P2-analog), `_geofence_violation` (r01/shield.py:101–110)… cel poza R_E LUB pozycja+hamowanie poza R_E LUB pion poza V_E"**. Zdania kanonu §2 NIE padają: zawieranie było przypisane clip_v + geometrii koperty — to zdanie okazuje się DOKŁADNIEJSZE, niż wiedzieliśmy, pisząc je (osłona nie miała uzbrojonej ścieżki pozycyjnej, więc „nie musiała interweniować" jest tym mocniejsze). Reguła trwała (E3): każdy przyszły materiał nazywa pętlę po imieniu (gate vs bench-loop) i przy „pod osłoną" wymienia UZBROJONE gałęzie.

## §6. Świeże ziarna s11-s13 (luka uogólnienia, raport-only, tylko NCP-PASS)

NCP fresh: **32/36 = 0.8889** [0.7468, 0.9559]. Luka: 0.9375 (trening) → 0.8889 (świeże), **Δ≈0.05 — mała**. Porażki fresh: c07_s11 (proximity, znana), **c10_s11/c10_s12/c10_s13** (c10 pada na WSZYSTKICH 3 świeżych ziarnach, a przechodził na treningowych → wąska słabość uogólnienia komórki c10 na nowych trajektoriach; frac-limited, nie proximity). MLP FAIL nie latał świeżych (N6).

## §7. Przyrząd bramki oceniony lotem (ANEKS_NET-3 §3 / Z-F1 — OBOWIĄZKOWE)

| ramię | offline rollout N3(i) | lot F2 | zgodność instrumentu |
|---|---|---|---|
| NCP | 24/24 PASS | 45/48 PASS | **ZGODNE** |
| MLP | 21/24 PASS | 8/48 **FAIL** | **ROZJAZD** |

**Model punktowy FEED-B jest OPTYMISTYCZNY dla MLP.** Rollout offline dał MLP 21/24 PASS, lot 8/48 FAIL — instrument nie oddał dynamiki PX4 (EKF/offboard/opóźnienia/RTF), na którą okno k=5 MLP jest wrażliwsze niż stan ciągły NCP. Rozkład komórek: NCP porażki lotu = c07/c09 (proximity, pokrywają się z granicą nauczyciela); MLP porażki = niemal wszędzie (nie klasa proximity — załamanie ogólne).
**Wniosek dla przyszłych nóg: bramka rolloutowa na modelu punktowym waliduje NCP wiernie, ale NIE jest wiarygodna dla architektur okiennych — dla nich potrzebny lot albo model z dynamiką.** To walidacja instrumentu N3(i), prerejestrowana Z-F1.

## §8. Predykcje — rozliczenie

| pred | treść | wynik |
|---|---|---|
| P-N3 | NCP↔MLP niezgodne ≤3 netto (pamięć bez różnicy) | **✗** (netto +37) |
| P-N4 | NCP ≥40/48 (p≈0.55) | **✓** (45/48) |
| P-N5-lot | porażki sieci = komórki proximity c05/c07/c09 | **✓ (NCP)** — c07_s02/c09_s02/c09_s03, dokładnie granica nauczyciela |
| P-N6 | REFUSE 0-2 w kampanii | **✓** (0) |
| P-N7 [post-diag] | MLP <40/48 (p≈0.55) | **✓** (8/48) |
| P-N8 [post-diag] | NCP↔MLP niezgodne ≥5 netto na korzyść NCP | **✓** (+37) — w napięciu z P-N3, P-N8 wygrała |

Napięcie P-N3↔P-N8 rozstrzygnięte przez loty na korzyść P-N8. Księga nogi (poz.3+4): P-N1✓(S2)/P-N2✓*/P-N3✗/P-N4✓/P-N5✓/P-N6✓/P-N7✓/P-N8✓/P-N5-offline✗.

## §9. Odchylenia
- O1 (numpy, brak torch) · O-F1 (scenarios.py pinowany → generator przez import, adjudykowane ANEKS_NET-3 §2) · Z-F1 (luka model↔SITL, §7). Driver `weights_sha` wstrzykiwany post-boot (net_controller odmawia lotu przy rozjeździe → przelot dowodzi zgodności). Zero SITL poza kampanią; drivery wersjonowane w repo.
- Budżet: 2 diag + 24 F2 + 9 F3 = **35 bootów lotnych** (≤45 ✓), env-blocki poza budżetem (auto-defer, zero strat).

## §10. WERDYKT NOGI SIECI + STOP-F1

**Slot lecący = NCP-20 (CfC).** p_net 0.9375 ≥ próg 0.825, near-teacher, 0 breach/REFUSE, granica dziedziczona = proximity nauczyciela (c07/c09), luka uogólnienia mała (0.089 fresh). **MLP odpada** (0.167 ≪ próg). **Teza „liquid" ROZSTRZYGNIĘTA POZYTYWNIE w locie: pamięć ciągła (CfC) transferuje do SITL, okno k=5 nie** — mimo że offline NULL (oba przeszły rollout). To główny wynik nogi.

**Los slotu (ratyf. ANEKS_NET-4 §1): slot lecący = NCP-20** (wagi 0337d5ea, nietykalne); **egzekutor skryptowy = kotwica na stałe**; MLP odchodzi z pełnymi danymi jako najcenniejszy negatyw programu. NCP 45/48 vs egzekutor 44/48, 1 para niezgodna = szum — **ZAKAZ roszczenia „sieć lepsza od egzekutora"** (ANEKS_NET-4 §2, klasa K1, brak języka istotności). Materiał do pozycji 5 (re-render/demo v2). Olga: push wszystkiego F0-F3 + raport.

## §11. Kanon roszczeń (ANEKS_NET-4 §2 — obowiązuje tu, w pozycji 5 i każdym materiale zewnętrznym)

**WOLNO twierdzić:**
- „20-neuronowa sieć CfC (~1.9k parametrów), wytrenowana czystą imitacją na 114 demonstracjach, osiąga w locie SITL skuteczność nauczyciela (45/48 vs 44/48; 47/48 par zgodnych na identycznych scenariuszach) i przechodzi prerejestrowany próg 0.9·p_exec; pod emulowanym track-feedem (10 Hz, 0.2 s, σ 0.5 m)".
- „Pamięć-przez-dynamikę transferuje przez lukę model-punktowy → SITL, której pamięć-przez-okno 0.25 s nie przeżywa (8/48) — przy TYM zadaniu, feedzie i czystej imitacji".
- „Wymiana kontrolera (skrypt → sieć) pod niezmienionymi certami i pinami, z tożsamością wag weryfikowaną przy każdym starcie".

**NIE WOLNO twierdzić:**
- „sieć lepsza od egzekutora" — 1 para niezgodna = szum; zakaz języka istotności (klasa K1).
- „liquid > MLP w ogólności" — k = 5 to jeden punkt przestrzeni okien; kontrola GRU nieodpalona (nota z triggerem, ANEKS_NET-4 §3).
- „osłona zawierała złą sieć" — ledger REFUSE PUSTY (0/132); zawieranie = clip_v + geometria koperty i dysku intruza; aktywna interwencja osłony zmierzona w K1 pod denialem, NIE tutaj. MLP degradował MISJĘ, nie bezpieczeństwo (§5).

Odsyłacz: ANEKS_NET-4 (CC 6.09.2026), §2 kanon roszczeń, §1 werdykty, §3 Z-F1 + trigger kontroli GRU.
