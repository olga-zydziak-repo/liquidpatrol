# FREEZE_AKW — zamrożenie przyrządu nogi AKW (init przy S1, PRE_AKW §2 / PROMPT_AKW_S1 §1)

Wykonawca · 09.10.2026 · po ratyfikacji PRE_AKW (Olga, 09.10.2026) i PROMPT_AKW_S1;
ARCH-1 = commit b1f77856 (PRE_AKW.md VERBATIM, pierwszy commit sesji).

## Parametry profilu skanu — S2, ANEKS_AKW-1 §5 ŚCIEŻKA II (FROZEN — zmiana wartości = ANEKS, nie env)

Obowiązuje od S2 (edycja profilu per reguła prerejestrowana §5: desk S2a κ₉₀ kandydaci
0.0/0.0/2.1 ⇒ ω_safe = 0.85·2.1·7.58 = 13.53 < 14 ⇒ ścieżka II, zastosowana mechanicznie).

| parametr | wartość |
|---|---|
| tryb skanu | **step-and-stare**, jednokierunkowy CCW (yaw atan2 ROSNĄCY) |
| krok | **40°** rampą **60 °/s** (0.667 s) |
| stare | **1.2 s** nosa nieruchomego po każdym kroku (ω·dt=0) |
| pełny przegląd | 9 kroków ≈ **16.8 s** (worst-case czekania) |
| dwell po wejściu w hold | **2.0 s** trzymania ψ_last (BEZ ZMIAN), potem cykl krok→stare od ψ_last |
| ψ_last / wrap / reset() / zegar | BEZ ZMIAN wobec S1 (tabela niżej); doszło domknięcie krawędzi wrapu: emisja dokładnie −π ⇒ +π (kontrakt (−π,π], krok 2/3 s vs siatka ticków) |
| env | `AKW_DWELL_S` wyłącznie diagnostyczny; parametry kroku/stare BEZ env (zmiana = ANEKS); driver bramkowy nadal ODMAWIA przy env AKW_* |
| t_A (bramka A′ re-smoke, wzór §5) | **23 s** = min(23, ⌈(16.8+3)·1.25⌉) |

Sha wrappera: **przed** (S1, ciągły 30°/s) `2237cc7c…` → **po** (S2, ścieżka II)
`b94cdeaef311c46067724eb095eb7ce32c08c9929c15cfa2cc4614619063d375`.
Test przedlotowy: przed `6ee42fd5…` → po
`5549d9345cab75b480711ca822010e8793e8a8f22cc2b517d4693408dc50c7c9`
(§3.1 pass-through BEZ ZMIAN merytorycznych — jedyna zmiana to lista importowanych
stałych; §3.2 profil przepisany na ścieżkę II z wzorcem niezależnym od implementacji;
§3.3 asserty stałych profilu zaktualizowane). 12/12 PASS po edycji.
NOTA JAWNA: driver `akwS1_boot.sh` (FROZEN, poza listą edycji ANEKS §5) wstrzykuje do
manifestu opisowe pole `scan_dps_frozen: 30.0` — od S2 pole HISTORYCZNE/nieaktualne;
prawdę o profilu niesie `akw_scan_sha256` (liczony na żywo) + ta tabela.
Narzędzie desku S2a: `results/AKW/tools/akw_s2a_cliff.py` (NOWE)
`9b014b5758e38ff609da92d95d17b10a584bd3b593ac68d9d09148bf8a76c66a`.

## Parametry profilu skanu — S1, HISTORYCZNE (ciągły 30°/s; FAIL bramki A smoke ⇒ ANEKS_AKW-1)

| parametr | wartość |
|---|---|
| ω skanu | **30.0 °/s**, ciągły, jednokierunkowy CCW (konwencja kodu: yaw atan2 ROSNĄCY, jak orbit_executor CCW) |
| ψ_last (doprecyzowanie wiążące PROMPT §1) | ostatnio WYEMITOWANY yaw z każdego ticku (track: atan2 delegata; skan: własna rampa) |
| dwell po wejściu w hold | **2.0 s** trzymania ψ_last, potem rampa ψ(t)=ψ_last+ω·t_skanu |
| rampa | liczona wewnętrznie UNWRAPPED; **emisja wrapowana do (−π, π]** (granica MAVSDK w benchu bez zmian) |
| reset() | zeruje stan skanu i **ψ_last = 0.0** (pierwszy hold epizodu ⇒ dwell na 0.0, rampa od 0) |
| zegar profilu | now_s pętli (ten sam co w step delegata) |
| env `AKW_SCAN_DPS`/`AKW_DWELL_S` | WYŁĄCZNIE odczyt diagnostyczny; loty NA WARTOŚCIACH Z KODU — driver bramkowy ODMAWIA przy ustawionych |

## Sha zamrożone (sha256)

| plik | sha256 |
|---|---|
| `r03/controllers/akw_scan.py` (wrapper; S2 ścieżka II — historia: S1 `2237cc7c…`) | `b94cdeaef311c46067724eb095eb7ce32c08c9929c15cfa2cc4614619063d375` |
| `r03/controllers/__init__.py` (PO wpisie net_akw — 2 linie additive) | `4f58d204630b9cf8db3bfb9a98b480c7c24552c8c7632eee9373c18b7cbd656a` |
| `results/AKW/tools/akwS1_boot.sh` (driver, kopia detS4_boot; jedyna zmiana funkcjonalna: CONTROLLER=net_akw; dodatki niefunkcjonalne jawne: KIND=akw [etykieta finalize], guard ODMOWY przy env AKW_*, blok `akw` w manifeście, ścieżki results/AKW/camp) | `fcff9b30caed4345bc3bf032eddfd658028cc5c3e36c499390ffe7b629a711f3` |
| `results/AKW/tools/akw_analyze.py` (analiza, kopia detS4_analyze + blok akw/smoke_gates/yaw_sanity_ulog) | `e9b3bdfbfb44965671beb35ceb6502f0e7edfddd56231ee7d41d3fa86ff5377b` |
| `results/AKW/tools/test_pre_akw.py` (testy przedlotowe §2; S2 profil II — historia: S1 `6ee42fd5…`) | `5549d9345cab75b480711ca822010e8793e8a8f22cc2b517d4693408dc50c7c9` |
| `results/AKW/tools/akw_s2a_cliff.py` (desk S2a, NOWY) | `9b014b5758e38ff609da92d95d17b10a584bd3b593ac68d9d09148bf8a76c66a` |
| `results/AKW/tools/akw_s2_gates.py` (bramki A′/C re-smoke na wyjściu frozen analyzera, NOWY) | `ea30d9fb57025f453450251da35f7af488a8a8affa3bace850c9873b8b33b130` |

## Dziedziczone VERBATIM (bajty bez zmian — edycja = STOP)

FREEZE_DET w całości (results/DET/FREEZE_DET.md) · piny 5/5 (k1_shield_pins: shield
1c584964 · config 4c440e42 · gate_run 5647ae20 · base 7fc45cf2 · safe_descend e3c1040b)
· certy 9/9 · bench_flight `05137098` · bench_judge `8ec0fcfb` · feed_vision `acc81df7`
· det_v2.pt `775ead15` · det_v2.py `e801f7d5` · percep_proc `38a3a765` ·
feed_vision_proc `79633489` · feed_registry `ee1481f9` · ncp `0337d5ea` ·
net_controller `e8c1b658` (wrapper go IMPORTUJE, nie edytuje) · feed_sha_v2 `8015bd12`
(meta percep_feed, do manifestów V2).

Weryfikacja przy S1 (wykonaniem): piny 5/5 PASS, certy 9/9 PASS, sha 9/9 zgodne.
Testy przedlotowe: **12/12 PASS** (pass-through bajtowy: 5714 tików ramienia B +
3754 tików demo V2 + 411 ważnych tracków V2 wprost z percep_feed r1_V2; profil
[dwell/rampa 30°/s/wrap ±π/wznowienie od ψ_last/reakwizycja/reset]; rejestr +
regresja "net"). Istniejące pytest: **210 passed, 0 failed** (pełna lista suit
w RAPORT_AKW_S1; r01/brake_test.py i r02/test_deadman.py = skrypty zależne od rclpy,
nie kolekcjonują się gołym pythonem — stan habitatu sprzed nogi, bez zmian).
