# RAPORT_NET_S1 — noga sieci, sesja 1 (trening offline + bramki N3) — STOP-N1

LiquidPatrol · pozycja 3 · CC 5.09.2026 · wejście: PRE_NET + ANEKS_NET-0 · wykonawca: Claude Code
ZERO bootów SITL · frozen nietknięty (piny + zestaw ławki, `git diff` pusty) · commity N-B0 `ae2a677` · N-B1 `2289080` · N-B2 `f8163a2` (niepushowane, push=Olga)

## §1. D0 — zbiór (szczegóły: `results/NET/D0_dataset.md`)

- 114 udanych demonstracji D6 (zgodne z oczekiwaniem; brak rozjazdu ⇒ brak STOP). Wiersze kept 161 380.
- Podział N2: TRAIN 81 ep / 114 705 w. (ziarna 1,3,5,6,7,9,10) · VAL 10 ep / 14 158 w. (ziarno 2) · TEST 23 ep / 32 517 w. (ziarna 4,8).
- Wykluczenia stall/reset = 0 (ZNALEZISKO §4: flaga stall niewpięta w loggerze ławki; zbiór czysty w czasie sim).
- Cechy = `bench/features.py` (sha 9adc1505, import); cel = `cmd_v_ned`; preprocessing = clip_age(≤1.0)+standaryzacja TRAIN (adapter wejścia, features.py nietknięte).

## §2. Wyniki per ramię

### NCP-20 (CfC, 1903 parametry)
- Krzywe: val_mse 1.194 → **0.1413** (epoka 199 = OSTATNIA, minimum na końcu — **val maleje monotonicznie do capu**).
- TEST RMS(v̂−v_nauczyciel) [DIAGNOSTYKA N3(ii)]: mediana **0.374**, IQR [0.367, 0.395].
- **Bramka N3(i): 1/12 (OBA ziarna TEST) · 5/12 (którekolwiek) · 6/24 epizody → FAIL pod każdą interpretacją.**
- Diagnoza: **UNDERFIT** — val wciąż opadał na zamrożonym capie 200 epok (SR-4: nie zmieniam hiperparametrów; to config z N-B1). Imitacja słaba (RMS 0.37), pętla zamknięta rozjeżdża się (frac<0.85 i d_min<4 w większości komórek).

### tiny-MLP (okno k=5, 2467 parametrów)
- Krzywe: val_mse 0.218 → **0.0308** (najlepsza epoka 78/80).
- TEST RMS [DIAGNOSTYKA]: mediana **0.179**, IQR [0.164, 0.208].
- **Bramka N3(i): 9/12 (OBA ziarna) / 12/12 (którekolwiek) / 21/24 epizody — WERDYKT ZALEŻNY OD REGUŁY AGREGACJI (patrz §4-O2).**
- Pod OBA: FAIL o 1 komórkę (padają c03[s4 frac 0.839], c07[s8 frac 0.824], c08[s4 frac 0.775] — wszystkie na frac, nie d_min; d_min≥5.46 wszędzie, bezpiecznie).

Tabele 12 komórek per ramię: `results/NET/{ncp,mlp}/eval.json`.

## §3. Predykcje (PRE_NET §3, prerejestrowane)

- **P-N1** (NCP przechodzi N3(i), p≈0.6): **CHYBIONA** — NCP FAIL 1/12 (underfit).
- **P-N2** (MLP przechodzi, p≈0.6): **ZALEŻNA OD REGUŁY** — FAIL(9/12) pod „oba ziarna", TRAFIONA(12/12) pod „którekolwiek". Do rozstrzygnięcia CC (§4-O2).
- **P-N5** (klasa porażek = c05/c07/c09 proximity): offline CZĘŚCIOWO — MLP pada na c03/c07/c08 (tylko c07 w zbiorze proximity; c03/c08 to nowe, frac-limited); NCP pada wszędzie (underfit maskuje klasę). Ocena właściwa dopiero w locie (pozycja 4).
- P-N3/P-N4/P-N6: dotyczą lotów (pozycja 4) — poza sesją 1.

## §4. Odchylenia i pytania do CC

**O1 — brak torch/jax/tf w środowisku.** NCP-20 (CfC) i tiny-MLP zaimplementowane w czystym numpy z ręcznym backprop (BPTT wsadowy dla CfC). Poprawność gradientów zweryfikowana numerycznie (gradcheck ~1e-10, w `net/tests_net.py`). Bez wpływu na kontrakt/architekturę; wpływ na wydajność (trening CPU: NCP ~69 s, MLP ~30 s).

**O2 — niejednoznaczność reguły agregacji bramki N3(i) [PYTANIE DO CC, W2].** PRE_NET N3(i)/PROMPT I2 mówią „analog-D6 w ≥10/12 KOMÓREK na ziarnach TEST", ale TEST = 2 ziarna (4,8) per komórka → redukcja 2 ziaren do werdyktu komórki jest NIEOKREŚLONA. Przyjąłem konserwatywnie **„komórka PASS ⇔ analog-D6 na OBU ziarnach"** (etos programu: K1-parowanie, V2′). Wpływ: **odwraca werdykt MLP** (9/12 FAIL vs 12/12 PASS „którekolwiek"; 21/24 epizody). Zgodnie z W2 („kryterium bez źródła nie istnieje; wątpliwość = pytanie do CC") NIE wybieram werdyktu cicho — proszę CC o regułę redukcji w ANEKS_NET-1. NCP FAIL pod każdą regułą (niewrażliwe).

**O3 — NCP underfit na zamrożonym capie.** val_mse malał monotonicznie do epoki 199/200; NCP nie zbiegł. SR-4 zabrania mi zmiany hiperparametrów po N-B1 — zgłaszam CC: czy sesja 2 to (a) więcej epok/inny lr dla NCP (zmiana hiperparametrów = decyzja CC per SR-4), (b) DAgger per N4, czy (c) NCP odpada. To NIE strojenie z mojej strony — czysta nota.

**O4 — stall/reset=0 w demo** (D0 §4): flaga stall niewpięta w loggerze ławki (frozen); deep-stalle tylko w rtf_stream (zegar ścienny). Metryki/cechy w czasie sim ⇒ zbiór czysty. Odchylenie łagodne odziedziczone z ławki, nie ruszam frozen.

## §5. STOP-N1

Sesja 1 domknięta: oba ramiona **nie przeszły** bramki N3(i) pod konserwatywną regułą (NCP 1/12 jednoznacznie; MLP 9/12, o 1 komórkę, werdykt zależny od O2). TEST dotknięty RAZ per ramię, żadnego powrotu do treningu (SR-3). Budżet: sesja 1 z 2 zużyta.

**Czeka na CC (ANEKS_NET-1):**
1. Reguła redukcji bramki N3(i) (O2) — „oba ziarna" vs „którekolwiek" vs próg epizodowy. Rozstrzyga werdykt MLP.
2. Plan sesji 2 (N4/N5): DAgger per ramię (trigger = FAIL sesji 1) i/lub decyzja o NCP underfit (O3). Weto Olgi „DAgger nie" wciąż otwarte do końca sesji 1.
3. Jeśli MLP uznane PASS (reguła „którekolwiek") — czy przechodzi do zamrożenia wag (FREEZE_NET) i pozycji 4, a NCP do contingency sesji 2.

Wykonawca po STOP: nic (SR-7). Olga: push {N-B0, N-B1, N-B2}.
