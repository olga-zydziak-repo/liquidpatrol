# STOP-TEACH-2-SM — S2 zamknięty: smoke ważny, B1–B4 bez naruszeń, zero REFUSE w misji, max błąd poprawki 0.57 m; P-TEACH-11 ✓

17.11.2026 · wykonawca · PROMPT_TEACH_S2 (sha256 39de0cdf) z ANEKS_TEACH-2 (878fce80) i ANEKS_TEACH-3 (sha256 30abb4a4, „ratyfikuję TEACH-3”). **Booty nogi: 5 / 24** (S2: 5 / 7 — ST1, ST2, C1, C2, SM; dwie odmowy przyrządu przed bootem, niepoliczone).

**Werdykt: S2 PASS. STOP po S2 — dalej decyzja CC (aneks po S2 = ANEKS_TEACH-4).**

## §1 — bramka i kod (ANEKS_TEACH-3 §4)

| commit | treść |
|---|---|
| `bc7a1b40` [CO-TEACH-3] | ANEKS_TEACH-3 verbatim w korzeniu (byte-check 30abb4a4 PASS), §5 do KSIĘGI (26 linii, append-only); bramka origin = `8d80ab01` |
| `ab361d2b` [S2-FLAGA] | §3.2 w `harness/nadir_obs.py` i `harness/teach_map.py` (oznaczone „TEACH-3:”), testy, narzędzia, wyniki sprawdzianów w `results/TEACH/s2/flaga/` |
| `6f8c5313` [S2-SM-STRAZNIK] | strażnik SM w `teach_s2_run.py` (narzędzie, nie kod lotu) — odchylenie 1 |

**Zmiana kodu lotu (§3.2):**
- `nadir_obs`: w locie producent dostaje `(cs, t_flagi=None)`, czyli flagę jako stan przy klatce. Stempel wiadomości (epoka) trafia tylko do wiersza jako `ts_flagi`. Tryb cienia bez zmian.
- `teach_map`: bez podanej chwili flagi kadr z bufora nie wchodzi do mapy. Zamknięcie i τ liczą się od pierwszej klatki z flagą 0. Ścieżka z podaną chwilą bez zmian.
- Nowe sumy: `nadir_obs.py` db96a4a7…3ffff, `teach_map.py` 4eefedda…fcd7e.

**Sprawdziany §4.4 — wszystkie zielone:**

| sprawdzian | wynik |
|---|---|
| testy `test_teach_s2.py` (flaga jako stan) | 7 / 7: jedno zamknięcie, mapa niepusta, kadr z bufora odrzucony, τ = 0 przy klatce zamknięcia; 0→1→0→1→mapa→0 i zero przez cały czas; ścieżka z podaną chwilą bez zmian |
| W2 łata S (podana chwila) | 13 / 13 bez różnicy z reconem |
| W2-lot, 39 przebiegów | 39 / 39: mapa = recon − 1 kadr, 0 kadrów ≥ cięcie, ostatni kadr mapy 0.21–0.40 s przed cięciem; Δprzyjętych ∈ {−1, 0}; \|Δ max błąd\| ≤ 0.0044 m; Δθ_k ≤ 0.071°, Δt_k ≤ 0.0059 m (rachunek CC: 0.004 m / 0.07° / 0.006 m) |
| W2-wyścig, łata S, 13 | 13 / 13: kadry mapy = recon, θ_k i t_k ≤ 5·10⁻⁵, 0 kadrów ≥ cięcie; przyjętych −1 w każdym (pierwsza klatka po cięciu idzie do fazy mapy), max błąd bez zmian |
| próba na sucho ze stemplem epoki (p01, `on_flags` dosłownie z pliku, stempel sim + 1.79·10⁹ + 0.045·sim) | PASS: 1 zamknięcie przy klatce 173.8 (ULG 173.696), kadr 173.6 z bufora odrzucony, ostatni kadr mapy −0.296 s; okno [cięcie, koniec misji] 552 / 552 przyjęte; B1–B4 OK, lot ważny, max błąd 0.68 m |
| ostrość: to samo wejście na kodzie `34fd058b` (worktree) | chwila flagi producenta 1 790 000 181.5 s ⇒ **0 / 552 przyjętych** |
| W1-obs | bez zmiany (zgodne wszystkie tryby, kody 47/48) |

## §2 — SM (`sm_smoke_S_c05`, łata S, c05, cięcie 30 s po starcie epizodu)

**Stanowisko:**
- bramka zdrowia A GO (tempo 0.916);
- próbnik zegara: 0 skoków;
- tempo w boocie 0.957 (próg 0.93);
- rc 0, breach brak, producent zgodny (meta TEACH, tor 0ffd62e3…, cień fałsz, datagram `teach`).

Rejestrator: 303 kadry na stanowisku, 6 w `kadry/`.

| | wynik |
|---|---|
| ważność (PRE §6) | **ważny**: 0 detekcji zgodnych z manifestem (surowa 1, ID 37, bok 5.0 px), brak mapy po fladze, georef raz |
| B1 / B2 / B3 / B4 | ✓ / ✓ / ✓ / ✓ — max e′/U′ 0.229, margines B2 16.6 m, REFUSE(POS) 0, failsafe 0 |
| D1 | kontynuacja 110.5 s od cięcia, track 100%, pasmo 100%, **REFUSE w misji 0** |
| błąd poprawki (n 584) | p50 0.317 / p95 0.503 / **max 0.567 m** |
| przerwy | max 0.2 s; > 1.15 s: 0; > 2.15 s: 0 |
| pierwsza poprawka | 0.132 s po fladze ULG; skok Δ 0.087 m |
| mapa | 174 kadry, 9 klatek kluczowych, 522 / 522 wiązań, zamknięcie 40.8 ms |

**Dodatkowo (ANEKS_TEACH-3 §4.5):**

| zdarzenie | czas sim [s] | wobec flagi ULG |
|---|---|---|
| flaga `cs_gnss_pos` 1 → 0 w ULG | 173.268 | 0 |
| wejście osłony w utratę (KONT) | 173.356 | +0.088 |
| klatka zamknięcia mapy (pierwsza z flagą 0) | 173.400 | +0.132 |
| kadr z bufora (odrzucony) | 173.200 | −0.068 |
| **ostatni kadr mapy** | **173.000** | **−0.268** |

- Kadr 173.2 ujęty 0.068 s przed flagą odrzucony zgodnie z regułą (kosztem jednego kadru).
- W wierszach `t_flagi` = None przez cały lot; `ts_flagi` (rejestr) w epoce, np. 1 794 926 048.8.
- Warunek ważności „żadna klatka kluczowa ani wiązanie po fladze” spełniony z zapasem 0.268 s.

**REFUSE:** 63 decyzje, wszystkie w zejściu planowym (292.1–295.1 s, `desc`), po końcu misji 283.73. Wzór jak NAD3 p01 (60 od 292.65).

**Predykcja P-TEACH-11 (0.70)** — SM ważny, B1–B4 bez naruszeń, zero REFUSE w misji, max błąd poprawki ≤ 1.00 m: **✓** (0.567 m).

## §3 — odchylenia

1. **Strażnik SM** (`teach_s2_run.py`): sprawdzał pole `bramka_obrazu` w księdze kampanii, którego nic nie zapisywało. Pierwsza próba SM skończyła się odmową przed czymkolwiek. Poprawka: strażnik czyta `<nazwa>/cien_s2.json` (C1 ok, C2 ok). Warunek ten sam, księga append-only nietknięta.
2. **Odmowa stanowiskowa:** `systemd-timesyncd` był aktywny (ANEKS_NADIR-4 §3.2), więc druga próba SM została odrzucona przed bootem. Zatrzymałem go na sesję (stop, nie disable — ANEKS_SKAN2-0b), próbnik 60 s pokazał 0 skoków. **Po sesji: `sudo systemctl start systemd-timesyncd` — akcja Olgi.**
3. **Mianownik 90% w próbie na sucho:** pierwsza wersja narzędzia liczyła od zamknięcia do końca nagrania, razem z zejściem i ziemią. Wychodziło 586 / 680 = 86.2%, a wszystkie 94 odrzucenia przypadają od 291 s (wysokość < 4 m, potem na ziemi). Poprawione na okno bramki obrazu z `teach_s2_cien` (cięcie → koniec misji, bez zejścia): 552 / 552. Próba 2A na starej ścieżce miała te same 586 przyjętych.
4. **Analizator a ostrość:** na kodzie `34fd058b` z zerem poprawek `teach_analyze` wywraca się przy zapisie JSON (numpy `bool_`). Narzędzie ostrości podmienia tylko serializację, analizator nietknięty. Dla analizatora to dług, poza zakresem.
5. **`test_teach_s1.py::test_analizator_zrodlo`** był czerwony już przed zmianą: stary klucz świadka sprzed TEACH-2A. Nienaprawiony, poza zakresem.
