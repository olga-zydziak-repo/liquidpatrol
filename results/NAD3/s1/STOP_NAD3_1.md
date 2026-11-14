# STOP-NAD3-1 — NADIR-III S1: zbudowane, FREEZE odtworzone co do cyfry, certy przechodzą, wierność 100% — żadna śmierć S1 nie zachodzi

14.11.2026 · wykonawca · PROMPT_NAD3_S1 (sha256 3c789f88 PASS z wklejki). **0 bootów.**

**Werdykt: S1 PASS.**
- P9_nad3 i P7_nad3 PROVED, P5_nad3 PASS na wszystkich trzech tabelach. Ostrość trzyma: każdy mutant tabeli odrzucony.
- W1 = 100% na 13/13 lotach NAD2.
- Obligacja wejścia przechodzi, a mutant z czystą ramą jest wykryty w 100% ticków utraty.
- Regresja bez nowego FAIL.
- Dotychczasowe manifesty odtwarzają się bit w bit (4/4).
- STOP-NAD3-1-FREEZE nie zaszedł: G unii = liczby CC z różnicą 0.0000 m w każdym polu.

## Bramka §0

- origin = HEAD = `300f0cd4`. Drzewo czyste poza zastanymi `?? results/DEMO_C`.
- sha256 promptu 3c789f88… i PRE_NAD3 56a1ac43… zgodne z sumami Olgi.
- Commit **[CO-NAD3-0] `87112eb0`** przed zmianą kodu:
  - `PRE_NAD3.md` verbatim w korzeniu (byte-check 56a1ac43);
  - KSIĘGA §8 i KIERUNKI §9 append-only verbatim (asercja prefiksu);
  - ratyfikacja zapisana jako „ratyfikuję PRE_NAD3".

## Budowa (diff w liniach)

| plik | zmiana | linie |
|---|---|---|
| `harness/nad3_degrad.py` | **nowy**, z narzędzia reconu. Sztywna siatka slotów (slot n = ⌊(t − t₀ + 1e-3)·f⌋, najwyżej jedna poprawka na slot). Bias radialny ±E·p̂_fix o stałym znaku, ziarno. Pole `nad3` = {E, slot, model, znak}. Env nieustawiony ⇒ `przetworz(fx) is fx`. „biały” i „wolny” zostają tylko dla replayu. | 137 |
| `harness/nadir_obs.py` | Wołanie degradacji między `Rama.obserwacja` a `_send`. Wiersz dostaje `fx_deg` tylko przy włączonej degradacji, meta `nad3` tylko przy włączonej. `nadir_fix.py` nietknięty. | +11 / −1 |
| `r03/nadir_shield.py` | Reżim „nad3” obok „nad2”: `nad3_tabela` (sha, stałe, próg całkowity, τ* = ostatnia krawędź), `przedzial_nad3`, `u_nad3` / `r_nad3`, `_nad3_barrier`, `_step_nad3` (kształt 1:1 z `_step_nad2`), `nad3_echo`. Odmowa startu `NadirStartError` z kodem 41–45. Kod nad2 i stałe nad2 bez zmiany. | +159 / −1 |
| `bench/scenarios.py` | RANGE0, DISK_R i próg zawracania (`PROG_ZAWRACANIA`, dotąd literał 14.0) jako argumenty `gen_episode` / `gen_manifest`. Domyślne bez zmian. | +20 / −10 |
| `r01/proofs/p9_nad3_verify.py` | **nowy**: P9/P7/P5_nad3. Lustro, siatka, fuzz i rdzenie z `p9_nad2_verify` (import read-only), parametryzowane tabelą. | 618 |
| `results/NAD3/tools/` | Kopie oznaczone „NAD3:”: `nad3_flight.py` (58 linii diff wobec `nad2_flight.py`), `nad3_krok.py` (7, tylko opis), `nad3_analyze.py` (75), `nad3_launch.sh` (9), `nad3_boot.sh` (48). Nowe: `nad3_freeze.py`, `nad3_manifest.py`, `nad3_w1.py`, `nad3_w2.py`, `nad3_certs_selfcheck.py`, `test_nad3_s1.py`, `nad3_regresja.sh`. | — |

**Szczegóły kopii:**
- **Driver.** Odmowa startu osłony kończy proces jej kodem. Bez reżimu nad3 kod 8. Zgodność degradacji producenta z tabelą punktu sprawdza meta `nadir_obs` (bias_rad, f = 1, K = 0, E = E tabeli); niezgodność ⇒ kod 9. Brak degradacji jest dopuszczony tylko z `NAD3_BEZ_DEGRADACJI=1` (boot passthrough S2). Meta lotu dostaje `nad3` (echo i sha tabeli, sha drivera, kroku, degradacji, producenta, osłony).
- **Boot.** Jeden tryb (NM=1, KM=1, PT=0, LIT=NAD2). `BOOT_PUNKT` ∈ P1/P2/P3 z sumą tabeli na sztywno w strażniku. `BOOT_DEGRAD` ∈ na_zewnatrz / do_srodka / 0 — launcher wystawia **wyłącznie bias radialny**, E brane z tabeli. Manifest NAD3 z sumą w strażniku. `NAD3_ETAP` ∈ s2 / s3.
- **Analizator.**
  - Tabela punktu z meta lotu, sprawdzona przez osłonę.
  - B1 liczony na e′ = |p_corr zdegradowane − GT(t próbki EKF)| wobec U′.
  - B4 bierze τ* i R′ z tabeli.
  - Obserwable PRE §6 per epizod: τ w misji, skok Δ′, `n_pred_odrzut`, r_max GT po fladze, max e′/U′, REFUSE w misji.
- **Analizator na sucho:** c10_s01 z tabelą W1 daje B1–B4, D1, e_corr, zapas i τ identyczne jak `wyniki_nad2.json`. Obserwable zgodne z reconem (skok max 0.3964, r_max 23.794).

**Manifest NAD3.** Plik `results/NAD3/s1/scenario_manifest_nad3.json` ma sha256 `74da23de…`, a testy są w `nad3_manifest.json`.
- Komórki: c00–c03 s01 (intruz stoi na 10.0 m) oraz c05_s01 i c10_s01. Trajektorie 200 s, `orbit_dir` z wersji 110 s, `episode_id` jak w kanonie.
- **Promień:** max na torze zadawanym 10.99775 m (c05) i 11.000035 m (c10).
- **Ciągłość:** max skok 7.2e-5 m (c05) i 1.019e-4 m (c10).
- Odtworzenie bit w bit (`filecmp`) przy wartościach domyślnych: `results/BENCH/scenario_manifest.json`, `results/NADIR/s4/scenario_manifest_s4.json` (090af08b), `results/NAD2/s4/scenario_manifest_s4L.json` (967e6799) i `_poz1.json` (9e7d4ad3) — **4/4**.

## FREEZE (`nad3_freeze.py` ⇒ `freeze_G.json`, `freeze_U_P{1,2,3}.json`)

| | 0.35 | 0.55 | 0.75 | 0.95 | 1.15 s |
|---|---|---|---|---|---|
| G unii 25 lotów | 0.8573 | 1.2703 | 1.6614 | 2.0590 | 2.3471 |
| oczekiwane (CC) | 0.8573 | 1.2703 | 1.6614 | 2.0590 | 2.3471 |
| różnica | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Tabele punktów (τ* = 1.15 s, próg 21 ticków, dodatek 0.012 s, F_zn z `freeze_U.json`):

| punkt | E | sha256 tabeli | najniższa bariera | oczekiwane | wykonalne (u′ ≤ m(20 m)) |
|---|---|---|---|---|---|
| P1 | 1.00 | 806f5e90… | 21.9263 m | 21.93 | prawda |
| P2 | 1.75 | 28e193de… | 20.8013 m | 20.80 | prawda |
| P3 | 2.75 | 841e3ae4… | 19.3013 m | 19.30 | **fałsz** (zgodnie z PRE) |

Granice: E_d = 1.3705 m (PRE 1.37), E_s = 2.2842 m (PRE 2.28). **Sprawdzian §2: wszystkie różnice ≤ 0.01 m.**

## Certy (`r01/proofs/p9_nad3_verify.py`, model_sha256 1e37670e…)

- **P9_nad3 PROVED.**
  - 3 tabele × 50 pól: każde z obligacją główną unsat i trzema obligacjami ostrości sat (U′, R, Δ_D5).
  - Arytmetyka per tabela:
    - stałe tabeli = freeze;
    - krawędzie rosnące;
    - R nierosnąca w i oraz w k;
    - τ* = ostatnia krawędź;
    - próg (τ* − 2·dt)/dt = 21, całkowity i równy polu tabeli;
    - próg + 0.012 ≤ 1.15;
    - pole braku poprawki ma największe U′;
    - `u_nad3` produkcji = wartość wymierna do 1e-9.
  - Wykonalność jest zapisana (P1 i P2 prawda, P3 fałsz). Dowód przechodzi także dla P3.
  - **Ostrość:** mutant τ* = 1.10 odrzucony przez osłonę (kod 45); mutant z zamienionymi G[2] i G[3] odrzucony przez prover (R rośnie w i).
- **P7_nad3 PROVED.**
  - Graf monitora z progiem 21 ticków, wspólnym dla trzech tabel: 10 pól po 4946 stanów i 39 476 krawędzi, instancja zredukowana, z3-duplikat kroku 4 × unsat.
  - **Ostrość:** τ* = 1.12 (próg niecałkowity) i τ* = 1.20 przy progu 21 — oba odrzucone (kod 45).
- **P5_nad3 PASS** (4 min 10 s). Wynik per tabela:

  | | P1 | P2 | P3 |
  |---|---|---|---|
  | ticki fuzzu | 1 359 374 | 1 362 160 | 1 389 718 |
  | ticki fikstury | 103 720 | 51 860 | 51 860 |
  | ticki tau_bind (P1) | 40 747 | 40 032 | 40 631 |
  | ticki passthrough | 167 153 | 178 320 | 179 139 |

  - Na tabelę: siatka brzegów 500 ticków i 34 000 epizodów fuzzu.
  - Rozbieżności 0. Pokrycie pełne (67 elementów: wszystkie reguły, przyczyny τ* i bariera, ramy, 50 pól, drugi epizod, utrata bez poprawki).
  - **Obligacja wejścia** na `nad3_krok.krok`: r_est = |p_corr′| w 100% ticków utraty (P1 83 708; P2 i P3 po 41 854) i = |p_EKF| w NOMINAL.
  - **Mutant z czystą ramą** wykryty w 100% ticków utraty, |Δr| do 2.48 / 3.21 / 3.74 m.
  - Przejścia ramy OK. Passthrough `NadirShield(nadir=0, nad3)` ≡ `KontShield` pełnym dictem.
  - **Ostrość:** produkcja z krawędzią 0.75 → 0.80 (sha przeliczona) wobec lustra FREEZE ⇒ rozbieżność wykryta.
- **Certy NAD2 po zmianie osłony:** P9 / P1 / P7_nad2 PROVED i P5_nad2 PASS (pełny fuzz 100 000). Pliki certów bajtowo bez zmian.
- **Selfchecki:**
  - `nad3_certs_selfcheck` PASS 20/20 (kanon + nad2 + nad3 + tabela NAD2 + 3 tabele NAD3);
  - `nad2_certs_selfcheck` PASS 18/18.

## W1 — wierność (`nad3_w1.py` ⇒ `w1_wiernosc.json`)

Tabela testowa `tabela_W1_nad2.json` (nie FREEZE): krawędzie i G z `freeze_U.json`, E = 0, τ* = 1.05, próg 19.

- **Producent.** Rama NAD2 → `Degradacja(None)` (ten sam obiekt) na 21 993 klatkach: 0 niezgodności, max |Δd_ne| i |Δp_fix| = 0. Ścieżka `{model: zero}` daje to samo.
- **Osłona** w reżimie nad3 przez `nad3_krok` na 51 860 tickach 13 lotów: przedział, τ, R_k, faza i d_ne — 0 niezgodności. Także decyzja i reguła — 0.
- **Tick zatrzasku** zgodny w 13/13 (np. c10_s01 3051, lot długi 12 944). **W1 = 100%.**

## W2 — replay degradacji (`nad3_w2.py` ⇒ `w2_replay.json`)

13 lotów NAD2 × P1 / P2 / P3 × oba kierunki biasu, prawdziwa osłona nad3 na tabelach FREEZE, pętla otwarta.

| punkt / kierunek | ticki e′ > U′ | max e′/U′ | REFUSE w misji (12 cięć) | przyczyna | τ max w misji |
|---|---|---|---|---|---|
| P1 / na zewnątrz | 0 | 0.580 | 11 | bariera | 1.028 s |
| P1 / do środka | 0 | 0.467 | 10 | bariera | 1.028 s |
| P2 / na zewnątrz | 0 | 0.593 | 12 | bariera | 1.028 s |
| P2 / do środka | 0 | 0.506 | 10 | bariera | 1.028 s |
| P3 / na zewnątrz | 0 | 0.605 | 12 | bariera | 1.028 s |
| P3 / do środka | 0 | 0.548 | 10 | bariera | 1.028 s |

- Loty NAD2 latały na r_max 19.6–25.6 m, czyli powyżej r_zad = 20 m, więc odmowa w większości z nich jest oczekiwana.
- **Reprezentantem geometrii NAD3 jest c05_s01 (19.59 m)** i tam wynik układa się zgodnie z PRE:
  - P1: 0 REFUSE w misji w obu kierunkach;
  - P2 na zewnątrz: REFUSE(bariera) 10.5 s od flagi; P2 do środka: 0;
  - P3 na zewnątrz: REFUSE(bariera) 7.5 s od flagi; P3 do środka: 0 (pętla otwarta).
- REFUSE(τ*) w misji: 0. τ zrealizowane 1.028 s mieści się w przedziale (0.95, 1.15] z zapasem 0.11 s.

Wynik służy do porównania z lotami, nie do zmiany tabel.

## T — testy (`regresja_s1.tsv`)

- Te same 44 pliki co NAD2 S1 (ROS jazzy i `ros2_ws`), plus `test_nad3_s1.py` **10/10**.
  - Testy jednostkowe: decymator (jedna poprawka na slot, żadnej między slotami, także przy brakujących klatkach); passthrough `is` i bajty; bias i stan dostarczony; generator z wartościami domyślnymi bit w bit; kody odmowy 41–45; nad2 bez zmian; `u_nad3` z tabelą W1 ≡ `u_nad2` bitowo; tabele FREEZE; suma manifestu w boot.
- Wynik końcowy jest identyczny z bazą zmierzoną dziś przed zmianami. **Nowych FAIL brak.** Zastany: `r02/test_deadman.py` rc = 1.
- Dwie obserwacje stanowiskowe:
  - `results/DET/tools/test_aneks_det2.py` w bazie NAD2 S1 miał 1 FAIL, dziś przechodzi 4/4 w bazie i w biegu końcowym. W biegu równoległym z proverami miał raz 1 FAIL, a pojedynczo przechodzi 4/4 — niestabilny.
  - `tests_harness_infra3.py::test_proc_gate…` padł raz przy loadavg 2.22 (provery w tle; proc_gate progiem 1.5). W biegu końcowym na spokojnej maszynie przechodzi.

## Odchylenia od promptu (nazwane)

1. **Wybór reżimu osłony** to env `NADIR_OSLONA=nad3` (argument `nad3`), nie `NADIR_LITERA`. Ten env to litera producenta Rama i w NAD3 musi zostać NAD2, bo `nadir_fix.py` jest nietknięty i przyjmuje tylko NADIR1 / NAD2.
   - „Kombinacja nad2 + nad3” = argument `nad2=True` przy nad3 albo `NADIR_OSLONA=nad2` przy `nad3=True` ⇒ kod 43.
   - Przy nad3 reżim nad2 jest wyłączony mimo `NADIR_LITERA=NAD2`.
   - Pozostałe kody: 41 brak tabeli lub sumy, 42 sha, 44 nieznana wartość env, 45 stała tabeli niezgodna z osłoną.
2. **Tolerancje testów manifestu.**
   - Generator zaokrągla x0/y0 **i** t0/t1 do 4 cyfr. Ciągłość sprawdzana z tolerancją wyprowadzoną z rozdzielczości: 2·√2·5e-5 + v·2·5e-5 = 2.414e-4 m — nie ostrzej niż 1e-4 z promptu. Zmierzony max 1.019e-4 m (c10) przekracza 1e-4.
   - Promień: 11.0 + 1e-4 m. Zmierzony max 11.000035 m — początek odcinka zaokrąglony po wyjściu na brzeg dysku.
   - Zaraportowane jako obserwable, nie ukryte.
3. **W1 na osobnej tabeli testowej** `tabela_W1_nad2.json` (próg 19, τ* 1.05). Tabele FREEZE mają próg 21.
4. **P9_nad3:** wykonalność nie jest warunkiem dowodu. Zgodność wykonalności z polem tabeli i z oczekiwaniem §2 (T / T / F) jest jednak asercją certu.
5. **P1_nad3 nie powstał** — prompt wymienia P9 / P5 / P7. Reżim nad3 nie zmienia automatu (kviol abstrakcyjny). tau_kont ≡ produkcja jest sprawdzone w P5_nad3 (ok. 40 tys. ticków na tabelę), a P1_nad2 nadal PROVED.
6. **Mutanty ostrości** zapisywane przez `tempfile` w katalogu tymczasowym systemu, nie w repo.
7. **Driver nad3 niesprawdzony uruchomieniem `main()` z atrapą.** Sprawdzone: składnia, `bash -n` boota i launchera, analizator na sucho, osłona i krok przez W1, W2 i P5. Próba drivera na sucho należy do S2 przed pierwszym bootem (lekcja STOP-KONT4-DRIVER).
8. **Fikstura P5:**
   - P1 w obu kierunkach biasu, P2 na zewnątrz, P3 do środka;
   - dla każdego punktu mutant z ramą czystą liczony na tych samych lotach;
   - fuzz 34 000 epizodów na tabelę (łącznie 102 000).

## Reprodukcja

```
export PYTHONDONTWRITEBYTECODE=1
python3 results/NAD3/tools/nad3_freeze.py            # G unii (STOP przy |Δ| > 0.01), tabele P1–P3, sprawdzian §2
python3 results/NAD3/tools/nad3_manifest.py          # manifest NAD3 + testy na sucho
python3 results/NAD3/tools/nad3_w1.py                # W1 (kod 1 przy < 100%)
python3 results/NAD3/tools/nad3_w2.py                # W2
PYTHONPATH=.certdeps:. python3 -m r01.proofs.p9_nad3_verify all     # P9, P7, P5 (~4 min)
PYTHONPATH=.certdeps:. python3 results/NAD3/tools/nad3_certs_selfcheck.py
bash results/NAD3/tools/nad3_regresja.sh results/NAD3/tools/test_nad3_s1.py
```

**Sygnał: STOP-NAD3-1.** Push robi Olga. CC replikuje provery i FREEZE z repo i oddaje PROMPT_NAD3_S2 (geometria i smoke, ≤ 4 booty).
