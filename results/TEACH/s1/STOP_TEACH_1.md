# STOP-TEACH-1 — TEACH S1: producent mapy w kodzie lotu odtwarza recon, FREEZE co do cyfry, certy przechodzą, K′ odrzucony — żadna śmierć S1 nie zachodzi

16.11.2026 · wykonawca · PROMPT_TEACH_S1 (sha256 1f16675c PASS z wklejki). **0 bootów.**

**Werdykt: S1 PASS.** Żaden STOP bez śmierci nie zachodzi.
- **Certy:** P9_teach i P7_teach PROVED, P5_teach PASS. Ostrość trzyma: każdy mutant tabeli odrzucony.
- **Wierność:**
  - W1 bez zmian: proces `nadir_obs` bez TEACH_MODE daje te same wiersze co `ad1e71fd`; NAD3 W1 100%.
  - W2: moduł lotu odtwarza recon M4 / SIFT na 39/39 parach (łata × lot) bez naprawy toru.
- **W3:** zamknięcie mapy max 97 ms przy wymogu 500 ms.
- **W4:** K′ odrzucony regułą PRE, w lotach zostaje dobór K z reconu.
- **W5:** 0 ticków e′ > U′, max e′/U′ 0.35.
- **Regresja:** bez nowego FAIL.
- **FREEZE:** różnica 0.0000 m w każdym polu.
- **Pliki z PRE §5 pkt 6:** bez zmiany bajtu.

## Bramka §0

- origin/master = HEAD = `ad1e71fd`. Drzewo czyste poza zastanymi `?? results/DEMO_C`.
- Sumy plików z wklejki zgodne z sumami Olgi:
  - PROMPT_TEACH_S1: 1f16675c…;
  - PRE_TEACH: ee1a4bb7…, byte-check pliku w korzeniu.
- Sygnał „ratyfikuję PRE_TEACH” przyszedł w drugiej wiadomości. Pierwsza wiadomość skończyła się na STOP-TEACH-1-§0.2.
- **[CO-TEACH-2] `99755112`:**
  - PRE_TEACH.md verbatim w korzeniu;
  - §8 do KSIĘGI (35 linii) i §9 do KIERUNKÓW (11 linii), append-only, verbatim (bloki wycięte z pliku PRE).

## Budowa

| plik | zmiana | linie |
|---|---|---|
| `harness/teach_map.py` | **nowy**, producent mapy (opis niżej) | 338 |
| `harness/nadir_obs.py` | gałąź `TEACH_MODE=1` (opis niżej) | +79 / −6 |
| `r01/proofs/p9_teach_verify.py` | **nowy**, kopia `p9_nad3_verify.py`, zmiany „TEACH:” | 701 (diff 315) |
| `results/TEACH/tools/teach_flight.py` | kopia `nad3_flight.py` | diff 72 |
| `results/TEACH/tools/teach_launch.sh` | kopia `nad3_launch.sh` | diff 40 |
| `results/TEACH/tools/teach_boot.sh` | kopia `nad3_boot.sh` | diff 70 |
| `results/TEACH/tools/teach_analyze.py` | kopia `nad3_analyze.py` | diff 142 |
| `results/TEACH/tools/teach_certs_selfcheck.py` | kopia `nad3_certs_selfcheck.py` | diff 45 |
| `results/TEACH/tools/` | nowe narzędzia (lista niżej) | — |
| `worlds/world_teach_{S,M,J}.sdf`, `results/TEACH/s1/zrodla/x500_teach_flow/` | wygenerowane | — |

**`harness/teach_map.py` — producent mapy.**
- Interfejs jak `Rama`: `obserwacja(t, obraz BGR, ekf_q, ekf_pos, gnss, t_flagi)` zwraca datagram, a `rejestr` trafia do wiersza.
- Tor odniesienia importowany READ-ONLY (sha teach2 sprawdzane przy starcie): `teach2`, `teach_r34`, `orto_r2`, `orto_r3`.
- Faza mapy:
  - wejście od −z_EKF ≥ 6 m, jak seria „przed” w reconie;
  - bufor jednej klatki;
  - dopasowania wiązań liczone z wyprzedzeniem.
- Zamknięcie: zbiór wiązań wg definicji reconu i M4, rozwiązane raz.
- Lokalizacja: łańcuch `a12_geo0_g1.5`, wariant K / K′.

**`harness/nadir_obs.py` — gałąź `TEACH_MODE=1` (z `NADIR_MODE=1`).**
- Wejścia: obraz RGB zamieniany na BGR; flaga i jej chwila z `/fmu/out/estimator_status_flags`.
- Detektor znaczników liczy dalej (wiersz: `n`, `det`).
- Wiersz dostaje `fx`, `teach`, `gnss`, `t_flagi`. Meta dostaje `litera: "TEACH"` i blok `teach` (echo, tor, sumy, interpreter).
- Kody odmowy: 47 = TEACH + `NAD3_DEGRAD`; 48 = cień bez `TEACH_T_CIEN` albo nieczytelna maska.
- Cień `TEACH_CIEN=1`: flaga = sim < `TEACH_T_CIEN`, bez wysyłki. Maska `TEACH_MASKA` opcjonalna.

**Kopie narzędzi NAD3 (zmiany oznaczone „TEACH:”).**
- **Driver `teach_flight.py`:**
  - wymaga `TEACH_MODE=1` i tabeli punktu TEACH (inaczej kod 8);
  - zgodność producenta (datagram `zrodlo=teach`, meta TEACH, suma toru = `tor.json`, cień zgodny z env, brak `nad3`), inaczej kod 9;
  - osłonę woła przez nietknięty `nad3_krok.krok`;
  - selfcheck certów TEACH, meta `teach`.
- **Launcher `teach_launch.sh`:** `FLIGHT=teach`, model `gz_x500_teach_flow`, świat domyślny `world_teach_S`.
- **Boot `teach_boot.sh`:**
  - zmienne `BOOT_LATA` S/M/J, `BOOT_CIEN` / `BOOT_T_CIEN`, `BOOT_MASKA`;
  - tabela TEACH z sumą na sztywno, suma `tor.json` w strażniku;
  - bez degradacji, katalog `results/TEACH/<s2|s3>`.
- **Analizator `teach_analyze.py`:**
  - B1–B5 jak NAD3 na tabeli TEACH z meta lotu;
  - błąd poprawki |p_fix − GT(t_fix)|;
  - przerwy z pokryciem prawdziwym przez klatki kluczowe;
  - opóźnienie pierwszej poprawki, skok |Δ| przy pierwszej;
  - liczba klatek kluczowych i wiązań, czasy producenta;
  - ważność lotu (zero detekcji znaczników, mapa bez kadrów po fladze, georeferencja raz);
  - wyjście `wyniki_teach.json`.

**Nowe narzędzia w `results/TEACH/tools/`:** `teach_freeze.py`, `teach_swiaty.py`, `teach_w1_obs.py`, `teach_w2.py`, `teach_w3.py`, `teach_w4.py`, `teach_w5.py`, `teach_strumien.py`, `test_teach_s1.py`.

**Analizator na sucho** (`--tabela freeze_U_TEACH.json`) na p01_p1_c05_zew NAD3:
- B1–B4 OK, max e′/U′ 0.48, D1 dostępne;
- lot nieważny z powodem „brak producenta TEACH”, zgodnie z oczekiwaniem (3932 detekcje znaczników).
- Część źródłowa (`zrodlo_teach`) sprawdzona testem na syntetycznym `nadir_obs.jsonl` z producenta.

**Światy i model** (`teach_swiaty.py` ⇒ `swiaty.json`):
- Pliki źródłowe bez zmiany bajtu: `world_nadir2_A3.sdf` 7f2bbe13…, `x500_nadir2_flow` 1fa0c57d….
- Model `x500_teach_flow`: model.sdf 656ccc9b…, config f653e8a7…. Diff wobec źródła to wyłącznie nazwa i 4 maski:

  | czujnik | maska |
  |---|---|
  | nadir | 8 |
  | imager | 4294967285 |
  | flow_camera | 4294967283 |
  | lidar (w `<ray>`) | 4294967287 |

- Światy: `world_teach_S` 38f1f4ac…, `world_teach_M` 4544aec9…, `world_teach_J` 1f97c0d0…. Różnią się od źródła nazwą świata, komentarzem i modelem `teren_teach`:
  - płaszczyzna 100 × 100 m, z 0.005 m, flagi 8;
  - tylko wizual, bez cienia własnego;
  - albedo = PNG łaty z `results/TEACH_RECON/dane`.
- `gz sdf -k` (parser, nie symulacja): Valid.

## FREEZE (`teach_freeze.py` ⇒ `freeze_G_TEACH.json`, `freeze_U_TEACH.json`)

| τ [s] | 0.35 | 0.55 | 0.75 | 0.95 | 1.15 | 1.35 | 1.55 | 1.75 | 1.95 | 2.15 |
|---|---|---|---|---|---|---|---|---|---|---|
| G unii 38 lotów | 0.8573 | 1.2703 | 1.6614 | 2.0590 | 2.3471 | 2.5715 | 2.7572 | 2.8929 | 3.1498 | 3.3315 |
| CC | 0.8573 | 1.2703 | 1.6614 | 2.0590 | 2.3471 | 2.5715 | 2.7572 | 2.8929 | 3.1498 | 3.3315 |
| różnica | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- 13 lotów NAD3 (12 cięć S3 + B4) nie podnosi żadnego pola (G z 25 lotów identyczne).
- **Tabela TEACH:** sha256_tabeli 7a56ba1b…, F = 0, E = 1.00 m, τ* = 2.15 s, próg 41 ticków.
- **Bariery:** 24.84 / 24.22 / 23.63 / 23.04 / 22.61 / 22.27 / 21.99 / 21.79 / 21.40 / 21.13 m.
- u′max 8.0213 m, wykonalne = prawda.
- E_d / E_s na τ*: 1.0515 / 1.7525 m. Przy τ ≤ 0.35 s: 2.536 / 4.2267 m.
- **Sprawdzian §2:** wszystkie różnice ≤ 0.01 m.
- Osłona (`r03/nadir_shield.py` bez zmiany bajtu) wczytuje tabelę w reżimie nad3 (punkt TEACH, 10 krawędzi, próg 41).

## Certy (`r01/proofs/p9_teach_verify.py`, model_sha256 1e4b7eca…)

- **P9_teach PROVED.**
  - 100 obligacji (10 przedziałów × 5 koszyków × 2 tryby): główna unsat, trzy obligacje ostrości sat.
  - Arytmetyka: próg 41 całkowity, τ* = ostatnia krawędź, R nierosnąca w i i k, pole braku poprawki najgorsze, `u_nad3` = wymierne.
  - Wykonalność prawda, zgodna z polem tabeli.
  - Ostrość:
    - τ* = 2.10 ⇒ osłona kod 45;
    - zamiana G[2] ↔ G[3] ⇒ UNPROVEN.
- **P7_teach PROVED.**
  - Graf monitora z progiem 41: 10 pól po 10 286 stanów i 82 116 krawędzi.
  - Instancja zredukowana OK; z3-duplikat 4 × unsat.
  - Ostrość: τ* = 2.12 i τ* = 2.20 przy progu 41 ⇒ kod 45.
- **P5_teach PASS** (1 min 45 s).
  - Liczba ticków:

    | siatka | fuzz | fikstura | tau_bind | passthrough |
    |---|---|---|---|---|
    | 830 | 1 383 996 | 139 884 | 41 489 | 164 896 |

  - Rozbieżności 0. Pokrycie 117 elementów: wszystkie reguły, przyczyny τ* i bariera, ramy, 100 pól, drugi epizod, utrata bez poprawki.
  - Fikstura: 13 lotów × 3 łaty ze strumieniem poprawek mapy.
  - Obligacja wejścia na `nad3_krok.krok`: r_est = |p_corr| w 112 644 / 112 644 tickach utraty (max |Δr| 0); w NOMINAL = |p_EKF| (27 240 ticków).
  - **Mutant bez poprawki** wykryty w 112 599 tickach (|Δr| do 17.5 m). Pozostałe 45 ticków to ticki sprzed pierwszej poprawki, gdzie Δ = 0.
  - Ostrość: krawędź 0.75 → 0.80 ⇒ rozbieżność konformancji.
- **Siatka i fuzz:** kopie z NI = 10, czasy prób zatrzasku za progiem tabeli (odchylenie 7).
- **Certy NAD2 i NAD3:**
  - P9 / P7 nad3 i nad2 ponownie PROVED; pliki certów bajtowo bez zmian (`git status` czysty).
  - Selfchecki: `teach_certs_selfcheck` 24/24, `nad3_certs_selfcheck` 20/20, `nad2_certs_selfcheck` 18/18.

## W1 — regresja

**`teach_w1_obs.py` ⇒ `w1_obs.json`.**
- Bieżący `nadir_obs.py` wobec `ad1e71fd:harness/nadir_obs.py`, te same 240 klatek z p01 NAD3 (znaczniki narysowane w zapisanych narożnikach; 180 z detekcją).
- Tryby: NADIR_MODE=0 (także z TEACH_MODE=1 bez NADIR_MODE), NADIR_MODE=1 / NAD2, NADIR_MODE=1 / NAD2 / NAD3_DEGRAD.
- Wynik: 0 różnych wierszy, summary równe; 180 przyjętych poprawek Rama w trybach NADIR.
- Kody odmowy 47 i 48 działają.

**`nad3_w1.py` (istniejący, bez zmian):** W1 PASS (fx 21 993, ticki 51 860, decyzje i reguły 0 niezgodnych), pliki `results/NAD3/s1` bez zmiany bajtu.

**Pliki PRE §5 pkt 6** — sumy przed i po równe:
- `r01/shield.py`, `r03/nadir_shield.py`, `r03/kont_shield.py`, `r03/kont_gate.py`;
- `harness/nadir_fix.py`, `harness/nad3_degrad.py`;
- tabele NAD2 i NAD3 P1–P3, manifest NAD3 v2;
- `net/`, PX4 i kanon percepcji nietknięte (`git diff` pusty).

## W2 — wierność mapy (`teach_w2.py --wariant K` ⇒ `w2_K.json`, `czesci_K/`)

- Interpreter `/usr/bin/python3` 3.12.3, cv2 4.6.0 (systemowe, jak boot `nadir_obs` i recon).
- Zgodne 39/39 par:

  | łata | przyjęte | recon | Δ max błędu | max \|Δθ_k\| | max \|Δt_k\| | wiersze różne (k, zgodne, przyjęta) |
  |---|---|---|---|---|---|---|
  | S | 8545 | 8545 | 0.0000 m | 5e-5° | 5e-5 m | 0 |
  | M | 8576 | 8576 | 0.0000 m | 5e-5° | 5e-5 m | 0 |
  | J | 8584 | 8584 | 0.0000 m | 5e-5° | 5e-5 m | 0 |

- 366 klatek kluczowych, czasy równe reconowi.
- Δθ i Δt to zaokrąglenie zapisu reconu do 4 cyfr.

## W3 — czas (`teach_w3.py` ⇒ `w3_czas.json`)

Jeden proces na rdzeniu 3 (`taskset`), cv2 jednowątkowo, łata S, 13 lotów, wariant K.

| miara | wartość |
|---|---|
| od klatki flagi do gotowej georeferencji, max z 13 | **97 ms** (p50 82 ms), wymóg ≤ 500 ms |
| opóźnienie pierwszej przyjętej poprawki po fladze | 0.004–0.188 s sim |
| kadr fazy mapy (najgorszy lot) | p50 41 ms, p95 52 ms, max 162 ms |
| kadr fazy lokalizacji (najgorszy lot) | p50 33 ms, p95 40 ms, max 65 ms |

Przy 5 Hz kadr fazy mapy zajmuje p95 26% budżetu klatki, a lokalizacji 20%.

## W4 — dobór K′ (`teach_w4.py` ⇒ `w4_dobor.json`, `tor.json` sha e76187a4…)

| grupa | K: max błąd / max przerwa / # > 1.15 s | K′ |
|---|---|---|
| S 12 cięć | 0.732 / 1.4 / 1 | 0.799 / 0.2 / 0 |
| S lot długi | 0.846 / 2.4 / 6 | 0.846 / 5.6 / 2 |
| M 12 cięć | 0.753 / 0.2 / 0 | 0.824 / 0.2 / 0 |
| M lot długi | 0.946 / 2.2 / 3 | 0.933 / 5.2 / 2 |
| J 12 cięć | 0.708 / 0.2 / 0 | 0.780 / 0.2 / 0 |
| J lot długi | 0.902 / 2.2 / 3 | 0.902 / 5.4 / 2 |

**K′ odrzucony.** Usuwa przerwę p02 (1.4 → 0.2 s), ale łamie dwa warunki reguły:
- max błąd na 12 cięciach rośnie o 0.067–0.071 m przy dopuszczalnych 0.02 m;
- max przerwa w locie długim rośnie z 2.2–2.4 s do 5.2–5.6 s.

W lotach zostaje **K** (dobór z reconu).

## W5 — replay osłony (`teach_w5.py` ⇒ `w5_replay.json`)

13 lotów × łaty S, M, J, poprawki W2 / K, tabela TEACH, ścieżka `nad3_krok`, pętla otwarta.

| łata | ticki e′ > U′ | max e′/U′ | REFUSE w misji, 12 cięć | REFUSE w misji, lot długi | τ max w misji, 12 cięć / lot długi |
|---|---|---|---|---|---|
| S | 0 | 0.315 | 0 | τ*, 252.4 s po fladze | 1.388 / 2.392 s |
| M | 0 | 0.350 | 0 | τ*, 252.4 s po fladze | 0.232 / 2.196 s |
| J | 0 | 0.333 | 0 | τ*, 252.4 s po fladze | 0.232 / 2.196 s |

- Przekroczenia przesłanki: brak.
- REFUSE(τ*) w locie długim to przerwa poza mapą ≥ 2.05 s, czyli „ODMOWA-POZA-MAPĄ” zgodnie z PRE §3.2.
- W 12 cięciach REFUSE(τ*) pojawia się dopiero po końcu misji. To artefakt replayu: strumień poprawek reconu kończy się z misją.
- Odmowa z bariery: nie ma.

## T — testy (`regresja_s1.tsv`)

- 44 pliki z bazy NAD2 + `test_nad3_s1.py` (10/10) + `test_teach_s1.py` (10/10). Wynik identyczny z `results/NAD3/s1/regresja_s1.tsv`, poza dopisanym wierszem TEACH. **Nowych FAIL brak.** Zastany: `r02/test_deadman.py` rc = 1.
- `test_teach_s1.py` sprawdza:
  - brak poprawki przed flagą;
  - georeferencję dokładnie raz (także przy powrocie flagi);
  - mapę bez kadrów po fladze; bufor odrzuca kadr ≥ chwili flagi;
  - zamknięcie = recon;
  - K′ = K przy równych bokach;
  - **tryb cienia nic nie wysyła** (gniazdo UDS puste), a tryb lotu wysyła 24/24;
  - meta i detektor znaczników;
  - tabelę i mutant (kod 45);
  - część źródłową analizatora.

## Liczby do predykcji (bez rozliczenia)

- **P-TEACH-1** (moduł lotu odtwarza recon bez naprawy toru, georeferencja ≤ 0.5 s po fladze): W2 39/39 bez żadnej naprawy; zamknięcie max 97 ms.
- **P-TEACH-2** (K′ przyjęty wg reguły PRE §6): K′ odrzucony (błąd +0.07 m, przerwa lotu długiego do 5.6 s).

## Odchylenia od promptu (nazwane)

1. **Producent importuje tor odniesienia** (READ-ONLY, sha teach2 07925633 sprawdzana przy starcie) zamiast kopii. Rozstrzyga W2.
2. **Bufor jednej klatki w fazie mapy.** Kadr wchodzi do mapy dopiero po nadejściu następnej klatki z flagą 1 albo przy zamknięciu, gdy jego czas < chwila flagi (timestamp wiadomości flagi). Dzięki temu spóźniona wiadomość flagi nie wpuszcza do mapy kadru sprzed niej. W replayu to bez znaczenia: W2 równe.
3. **Filtr −z_EKF ≥ 6 m w producencie** — definicja serii „przed” w reconie (`teach_r2.H_MIN`). Prompt go nie wymienia.
4. **Datagram:**
   - nowe pole `zrodlo = "teach"`;
   - przed pierwszą przyjętą poprawką `t_fix = None` (osłona liczy τ od wejścia w utratę, pole braku poprawki);
   - τ bramki przyjęcia producent liczy od chwili flagi, jak recon.
5. **`nadir_obs`:**
   - w gałęzi TEACH obiekt Rama nie powstaje;
   - meta `litera = "TEACH"`;
   - kody odmowy 47 / 48 (prompt mówi „z kodem” bez numeru).
6. **Tabela:**
   - `freeze_U_TEACH.json` ma poza polem `tabela` dodatkowe pola `bariery` i `sprawdzian_PRE_4` (osłona czyta tylko `tabela` i sumę);
   - G w osobnym `freeze_G_TEACH.json`.
7. **Prover:**
   - siatka brzegów i fuzz to kopie z NI = 10 (oryginały mają NI = 5 jako stałą modułu);
   - próby zatrzasku przesunięte z 1.2 s na próg + 0.15 s;
   - P1_teach nie powstał, jak w NAD3 (prompt wymienia P9 / P5 / P7).
8. **Krok osłony:** driver TEACH woła nietknięty `results/NAD3/tools/nad3_krok.py`, bez kopii (zero zmian do oznaczenia).
9. **Driver obsługuje cień** (`TEACH_CIEN`): nominały S3 i booty cienia S2 nie wysyłają datagramów.
   - Boot wymaga wtedy `BOOT_T_CIEN` (czas sim cięcia).
   - **Wyliczenie tej chwili z planu lotu nie jest zrobione** — zostaje dla S2.
10. **W1-obs:**
    - meta porównana przez odtworzenie z atrybutów modułu (`main()` wymaga ROS); gałąź meta poza TEACH ma ciało bez zmian;
    - wiersze i summary porównane z wyjścia.
11. **W2 — tolerancja θ / t:** recon zapisał θ i t do 4 cyfr, więc różnica 5e-5 to zaokrąglenie zapisu. Porównanie wiersz po wierszu dodane ponad litery promptu.
12. **W3 i obciążenie:** W3 biegł na rdzeniu 3 równolegle z P5_teach, W5 i W1-obs, przypiętymi do rdzeni 8–23.
13. **Strumień W5 / P5:**
    - Δ odtworzone z wierszy W2 (poprawka do 1e-4 m) i migawki EKF;
    - dostarczenie w miejscu seq datagramu lotu;
    - po końcu serii „po” brak poprawek, stąd REFUSE(τ*) poza misją.
14. **Model w repo jako źródło przypięte** `results/TEACH/s1/zrodla/x500_teach_flow` — launcher kopiuje go do PX4 przy boocie, wzór NADIR. PX4-Autopilot nietknięty.
15. **Części W2 obu wariantów w repo** (`czesci_K/`, `czesci_K2/`, po 0.9 MB) — wejście W4, W5, P5 i replikacji CC.
16. **Pamięć producenta:** cechy SIFT wszystkich kadrów mapy trzymane do zamknięcia (≈ 0.8 MB / kadr, ok. 180 kadrów ⇒ ~140 MB w procesie `nadir_obs`), po zamknięciu zwalniane poza klatkami kluczowymi.
17. **Analizator:** opcje `--tabela` / `--out` tylko do biegu na sucho.
18. **`gz sdf -k`** użyte jako parser poprawności świata (bez symulacji).

0 bootów. Sieć: żadna. Bez pushu.
