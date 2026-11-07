# RAPORT_KONT_S3 — osłona i certy nogi 2d: nakładka KONT, P9/P1/P7/P5_kont PROVED/PASS, T0–T4 PASS, 0 bootów

Wykonawca · 7.11.2026 · łańcuch KONT. Podstawa: PROMPT_KONT_S3 + ANEKS_KONT-3 (sha 80e87dac, CO-S2 `94ff9851`)
+ ANEKS_KONT-3b (sha 9e755cc4, `08d28da5`). Budowa: `4be66620`. Sygnał na końcu: **STOP-KONT3**.

## §0. Bramka i zakres

- Bramka §0.1: origin/master == HEAD == `94ff9851` (CO-S2), `origin/master..HEAD` puste, porcelain czysty poza
  `??` results/DEMO_C. Przed kodem STOP z pięcioma pytaniami o literę; rozstrzygnął je ANEKS_KONT-3b
  (commit `08d28da5`, byte-check OK).
- FROZEN sha8 na starcie i na końcu (bez zmian): `r01/shield.py` 1c584964, `r03/controllers/safe_descend.py`
  e3c1040b, `r03/config.py` 4c440e42, `results/KONT/s2/s2_freeze_bf.json` ae19f66c; zbiorczo po plikach
  śledzonych: `r01/proofs` 2592346a (23 pliki kanonu; nowe pliki obok), `bench` e40bcace, `harness` 7d8304b0,
  `r02` 7861730d. `git diff HEAD~1 HEAD` = same dodania (16 plików, +10021), zero edycji istniejących.
- Bootów w S3: **0**. Budżet nogi bez zmian: **24/45**, S2′ 8/12.

## §1. Co zbudowano (same nowe pliki)

| plik | rola |
|---|---|
| `r03/kont_shield.py` | `KontShield(PatrolShield)` — nakładka przez import i podklasę; KONT_MODE z env albo argumentu, echo `kont_echo()`; KONT_MODE=0 ⇒ wyłącznie metody bazowe |
| `r03/kont_gate.py` | warstwa komend: `KontCommand.descend` (D5 + trzymanie yaw z chwili decyzji; KONT_MODE=0 ⇒ yaw 0), `patrol` (R-G-NOM rzutuje v_ned) |
| `r01/proofs/p9_kont_verify.py` | prover czterech certów + lustro nakładki + rekonstrukcja fikstur (3b §1.5, §1.6) |
| `r01/proofs/certs/{P1,P5,P7,P9}_kont.json` | nowe certy; kanoniczne P1…P8 nietknięte obok |
| `results/KONT/s3/tools/` | `test_kont_s3.py` (T0–T4), `kont_mutants.py`, `kont_certs_selfcheck.py`, `kont_regresja.sh` |
| `results/KONT/s3/` | `p5_kont_grid.json` (siatka prereg), `provery_all.log`, `selfcheck.log`, `mutanty.json`, regresja przed/po |

Semantyka (litera 3 §2 + 3b §1):
- Flaga utraty = ¬`cs_gnss_pos`; debounce i histereza = `self.pos_debounce_ticks` / `self.pos_hyst_ticks`
  instancji (shield.py:72-74), czyli 2 ticki i 100 ticków (5 s); kształt monitora 1:1 z `_pos_monitor`.
- `t_KONT` od pierwszego ticka biegu flagi, który dał wejście (3b §1.3); koszyk = ⌊t_KONT⌋.
- Priorytet: latch > R-POS > **R-KONT** > R-G > **R-G-NOM** > abort > hold > return > {OBSERVE | R-AUTH} > patrol.
  R-KONT umieściłem w klasie R-POS (to „istniejące REFUSE(POS)", PRE_KONT §2.6; uzasadnienie jak shield.py:154).
  Tego miejsca 3b nie nazywa wprost — decyzja wykonawcy, dowiedziona w P1m, do potwierdzenia przez CC.
- R-KONT zatrzaśnięty do powrotu NOMINAL (flaga zdrowa ≥ M), potem odwracalny jak POS_DEGRADED; drugi epizod
  liczony (`n_kont_enter`). Stary monitor POS uzbrojony we wszystkich trybach (3b §1.4).
- R-G-NOM: REFUSE(GEOFENCE, rule R-G-NOM), bez zatrzasku, stan bez zmian, applied = cel bez składowej radialnej
  na zewnątrz; R_nom = **27.30** (3b §1.7).
- Tablica ε_b (koszyki 0…21) wkompilowana z sha nośnika; T3 i P9 sprawdzają zgodność z JSON.

## §2. Certy (z3 5.0.0 z `.certdeps`)

Jeden bieg `p9_kont_verify all`: **130.6 s** (`provery_all.log`); P9 ≈ 0.1 s, P1 ≈ 0.1 s, P7 0.8 s, P5 120 s.

**P9_kont — PROVED.** Per koszyk k = 0…21 cztery obligacje: `main` unsat 22/22, `sharp_eps` (ε_b(k)+δ),
`sharp_R` (R(k)+δ), `sharp_delta` (Δ_D5+δ) sat 22/22 każda (δ = 1/1000). Twierdzenie: 0 ≤ r_est ≤ R(k) ∧ ε ≤ ε_b(k)
∧ Δ ≤ 1.524 ∧ s ≤ d_stop ∧ |r_c − r_est| ≤ ε ∧ r_d ≤ r_est + ε + s + Δ ⇒ r_c ≤ 32 ∧ r_d ≤ 32.
R(0) = 27.303, R(10…20) = 24.148, R(21) = 23.888. Asercje arytmetyczne 7/7: reguła T* (k ≤ 21 ≤ 5.79,
koszyk 22: 4.325 + 1.524 = 5.849 > 5.79 — reguła m_p50, nie kontrprzykład twierdzenia), R_nom 27.30 ≤ R(0),
R(k) nierosnąca, dt = 1/20, ⌊wiek·dt⌋ ≤ 21 dla wieku < 440 ticków, tablica kont_shield ≡ JSON (sha ae19f66c).
Stałe wczytane z JSON z asercją sha; R_nom jedyną liczbą spoza nośnika (3b §1.7).

**P1_kont — PROVED (1-indukcja).** 17/17 unsat: base, inv_step, P1a–P1h (kanon z przesłankami KONT),
P1i (REFUSE z KONT = POS_DEGRADED, nieterminalny), P1j (KONT_REFUSE trwa do wyjścia monitora), P1k (powrót do
NOMINAL tylko przez monitor), P1l (R-G-NOM bez zatrzasku, stan bez zmian), P1m (kolejność latch > R-POS > R-G,
R-KONT ponad R-G, R-G ponad R-G-NOM — 3b §1.1), P1n (ALLOW w KONT ⇒ ¬naruszenie ∧ faza ≠ KONT_REFUSE),
nom_applied (NRA: applied R-G-NOM bez składowej na zewnątrz, składowa styczna zachowana).

**P7_kont — PROVED.** Wyczerpujący graf monitora GNSS + licznika t_KONT przy stałych produkcji (debounce 2,
hyst 100, T* = 440 ticków): **78 877 stanów, 315 508 krawędzi**. Sprawdzenia 11/11: wejście tylko po 2 tickach
utraty z zegarem cofniętym o 1 tick; brak ALLOW w KONT przy wieku ≥ 440 (max 439); REFUSE z czasu dokładnie przy
wieku 440; wyjście tylko po 100 zdrowych tickach i czyści KONT_REFUSE; KONT_REFUSE trwa do wyjścia; min cykl
ponownego wejścia 102 = hyst + debounce (drugi epizod); REFUSE z bariery osiągalny w każdym wieku 1…439;
iloczyn z monitorem POS = iloczyn kartezjański (pełna enumeracja na instancji zredukowanej 2/3/6: 216 stanów).
z3-duplikat kroku 5/5 unsat.
Iloczyn obu monitorów przy stałych produkcji (≈ 103 × 78 877 stanów) nie był enumerowany — zastąpiony
argumentem braku wspólnych zmiennych i wejść, sprawdzonym na instancji zredukowanej.

**P5_kont — PASS.** Lustro ≡ produkcja (decyzja, powód, reguła, stan, applied, detail, akcja, faza, t_KONT,
przyczyna, licznik epizodów) i tau_kont ≡ produkcja (decyzja, powód, stan, terminal, faza), **0 rozbieżności**:
siatka prereg 37 epizodów / 382 ticki; fuzz **100 000 epizodów / 4 042 863 ticki** (ziarno 0); fikstura S2
8 lotów / 17 725 ticków; tau_kont związany na 82 681 tickach (siatka + 2000 epizodów fuzz). Pokrycie 11/11 liści
+ obie przyczyny (T*, bariera) + drugi epizod. Mutanty lustra: **21/21 wykryte** (`mutanty.json`).

**Selfcheck ×2 z oczekiwaną niezgodnością** (`selfcheck.log`): bieg 1 PASS 13/13 (9 kanon + 4 KONT); bieg
kontrolny z kopią provera z dopiskiem — FAIL dokładnie 4 certów KONT, kanon 9/9, rc = 1 (oczekiwane); bieg 2
PASS 13/13; kanoniczny `r01.proofs.certs_selfcheck` PASS 9/9.

## §3. Certy nietknięte i punkt yaw (PROMPT §2, obowiązkowy)

**Brak yaw w obligacjach kanonu — cytat wykonaniem:**

```
grep -n -i -E "yaw|heading|\bpsi\b|ψ|odchyl" r01/proofs/{verify,geofence,p4_verify,conformance,eps_verify,
  d5_verify,posmon_verify,geo_cont_verify}.py r01/proofs/certs/{P1,P2,P2_eps,P2_vmax3p1,P4,P5,P6_d5,
  P7_posmon,P8_geo_cont}.json | wc -l
0
```

Zero trafień w 8 proverach i 9 certach (zgodnie z grepem CC). Yaw = 0 żyje wyłącznie w egzekutorach
(`r03/gate_run_r03.py:284`, `bench/bench_flight.py:389` — `VelocityNedYaw(0, 0, vdesc, 0)`), poza TCB i poza
obligacjami. Trzymanie yaw w KONT dodaje warstwa komend, a `safe_descend_step` bez zmian.

- **P6_d5** — twierdzenie z certu: „(a) vdesc=vf⇔el<dfd, vl⇔el≥dfd …; (b) 0≤vdesc nierosnąca ⇒ wysokość zadana
  monotonicznie nierosnąca; (c) touchdown⇔el≥dtot …; (d) 0≤vdesc≤vf". Mówi wyłącznie o składowej pionowej komendy
  (`d5_verify.py:9,16`); trzymanie yaw nie zmienia `safe_descend_step` ani vdesc, więc cert obowiązuje bez zmian.
- **P2 / P2_vmax3p1** — „p + v²/(2·a_brake) ≤ R_E ⇒ p ≤ R_E": własność bariery hamowania, niezależna od stanu KONT.
- **P2-ε** — „(r_est ≤ R_route′) ∧ ε ≤ ε_cap ⇒ r_true + d_stop ≤ R_E": prawdziwe w swoim reżimie (zliczanie,
  A-episode); reżim przepływu pokrywa P9_kont obok.
- **P4** — admisja, gramatyka komend i HMAC: nakładka nie zmienia admisji ani tokenu.
- **P8_geo_cont** — zawieranie predykatu `_geofence_violation` (FROZEN, wołany bez zmian przez R-G nakładki).
- P1, P5, P7_posmon kanoniczne zostają dla trybu legacy (KONT_MODE=0); ich odpowiedniki KONT to nowe pliki.

## §4. Testy (bez SITL)

`test_kont_s3.py`: **12/12 PASS**.
- **T0:** KONT_MODE=0 ⇒ trace bajtowo identyczny ze starą osłoną: fikstura S2 8 lotów / 17 725 ticków; fikstura
  FV 11 plików / 4221 ticków / 1791 zejścia (sha manifestu); FV dodatkowo vs decyzje zapisane w trace
  **4221/4221**. Wejścia zrekonstruowane (3b §1.5): S2 cel = pos + v·T_LOOKAHEAD (1.0 s, net_controller.py:34),
  pos/vel z `ekf`, flaga z `ulog_wyciag`; FV v = 0, cel = pos, pos_flag = dr. Domyślny KONT_MODE z env = 0.
- **T1:** wejście po debounce, zegar cofnięty (t_KONT = 0.05 s w ticku wejścia); REFUSE(T*) przy
  t_KONT ∈ [22.0, 22.05]; bariera w k ∈ {0, 9, 21}: R(k) − 0.001 i R(k) ALLOW, R(k) + 0.001 REFUSE(bariera);
  99 zdrowych ticków trzyma REFUSE, setny daje NOMINAL i ALLOW; drugi epizod (n = 2, zegar od zera); dr w KONT
  ⇒ R-POS (3b §1.4).
- **T2 (z R_nom 27.30 zamiast liczb promptu 27.50/27.52, unieważnionych przez 3b §1.7):** 27.29 i 27.30 ALLOW,
  27.31 i 27.50 na zewnątrz ⇒ REFUSE(R-G-NOM) bez zatrzasku; do środka ALLOW; składowa styczna zachowana;
  v_ned (2.0, 1.5) ⇒ (0.0, 1.5) w KONT_MODE=1, bez zmian w KONT_MODE=0.
- **T3:** sha nośnika, ε_b[0:22], Δ_D5, T*, k_ostatni = 21 zgodne; R_nom JSON 27.51 vs kod 27.30 (3b §1.7).
- **T4:** zejście z `safe_descend_step` niesie heading decyzji (76.58°) przez cały profil mimo zmian headingu;
  KONT_MODE=0 ⇒ yaw 0; po `release()` nowy epizod łapie nowy heading.

**Regresja** (`kont_regresja.sh`, każdy plik osobno, środowisko ROS jazzy jak harness):
- przed S3 (baza `08d28da5`, `regresja_baza_08d28da5.tsv`): 42 pliki, 242 testy passed, 3 skrypty rc = 0,
  **1 czerwony zastany: `r02/test_deadman.py` (skrypt rc = 1)**, opis w §6.6;
- po S3 (`regresja_po_s3.tsv`): 43 pliki (+ `test_kont_s3.py`, 12 passed), 254 passed; wyniki 42 starych plików
  **identyczne z bazą** (poza czasem trwania) — S3 nie wprowadza żadnej regresji; ten sam jeden czerwony.

## §5. Odstępstwa i poprawki w toku (nazwane)

1. **z3-duplikat P7 najpierw `sat`:** dziedzina kroku dopuszczała `g_bad = debounce` poza KONT (nieosiągalne).
   Zawęziłem ją do niezmiennika grafu i dodałem jego dowód indukcyjności (`z3_inv_step` unsat); obligacji nie
   osłabiłem. Ta edycja provera nastąpiła po zapisaniu P9/P1, więc wszystkie cztery certy przeliczono jednym
   biegiem `all` (selfcheck potwierdza jedną prowieniencję).
2. **Przyrząd mutantów:** pierwszy bieg dał 11/20, bo zmutowane funkcje pomocnicze nie były wołane przez
   `mirror_step` (przestrzeń nazw). Poprawione — 19/20, wada po mojej stronie.
3. **Luka siatki prereg:** mutant `>` → `≥` na barierze przeżył, bo siatka ma tylko R(k) ± 0.001, bez równości.
   Siatka zostaje nietknięta (P5 już na niej liczył); brzeg równości (r_est = R(k), r_est = R_nom) dodany do zbioru
   wejść mutantów i do T1/T2, plus mutant `n_rnom_ge` ⇒ 21/21.
4. **Regresja bazowa:** moja pierwsza pętla bez środowiska ROS dała fałszywe czerwone (`rclpy`); runner ładuje
   teraz ROS jak harness.

## §6. Do rozstrzygnięcia przez CC

1. **Wiek flagi a t_KONT (A-flag szerzej niż 3b §1.3).** Na fiksturze S2 REFUSE(T*) zapada przy t_KONT
   22.000–22.048 s, ale przy prawdziwym wieku flagi z ulogu **22.044–22.092 s**: zegar startuje od pierwszego
   ticka pętli, który zobaczył flagę, a ten jest do jednego ticka (0.040–0.052 s) po zmianie w ulogu, plus
   kwantyzacja decyzji ≤ 1 tick. Ostatnie ≤ 0.1 s KONT leży więc w koszyku 22 pomiaru (ε_b 4.325 + 1.524 = 5.849 >
   5.79). P9_kont tego nie łamie (twierdzenie jest warunkowe na A-kont z koszykiem ⌊t_KONT⌋), ale A-flag w 3b
   obejmuje tylko odcięcie→flaga 0.004–0.016 s. Możliwości: (a) rozszerzyć A-flag o próbkowanie ≤ 2 ticki;
   (b) REFUSE przy t_KONT ≥ T* − 2·dt (zmiana reguły — dokument CC). Bez decyzji nic nie zmieniam.
2. **R-G-NOM ponad abort/hold/return (litera 3b §1.2).** Przy r_est > R_nom i celu na zewnątrz R-G-NOM wygrywa
   także w trybach HOLD/RETURN/ABORT: ABORT zatrzaskuje się dopiero, gdy cel przestanie wskazywać na zewnątrz,
   a HOLD dostaje przycięty cel zamiast punktu zawisu (`prio_nom_over_abort` w siatce). Tor wykonawczy przy
   R-G-NOM wysyła rzutowane v_ned, więc skutek w locie zależy od okablowania S4 — do potwierdzenia przed S4.
3. **Miejsce R-KONT w priorytecie** (§1): w klasie R-POS, ponad R-G — do potwierdzenia.
4. **Okablowanie egzekutora** (KontShield + KontCommand w torze S4, `cs_gnss_pos` z DDS) poza zakresem S3;
   moduły gotowe, wpięcie należy do S4.
5. **Kontynuacja skrócona barierą** (3b §2, potwierdzone offline na fiksturze): c02_s01_r4 — REFUSE(bariera)
   przy t_KONT 10.416 s (r_est 24.162 > R(10) 24.148); pozostałe 7/8 lotów REFUSE(T*) przy 22.00–22.05 s.
   R-G-NOM i R-POS z dr: 0 aktywacji w 8/8 lotach; wejście w KONT 0.080–0.100 s po zmianie flagi w ulogu.
6. **Regresja zastana:** `r02/test_deadman.py` jest czerwony od `fa5dc242` (20.08): atrapa w teście nie ma pola
   `_sp_yaw` dodanego wtedy do `r02/gate_run_r02.py` (`AttributeError`, DEAD-MAN PROPERTY: FAIL). Czerwony także
   na bazie `08d28da5` przed S3; `r02/**` FROZEN — nie ruszałem. Litera §3 „pełny zestaw PASS" nie jest spełniona
   z tego jednego powodu; S3 nie dodaje żadnej nowej porażki.

KSIĘGA (✗ CC z 3b §1.1, §1.6, §1.7) — dopisuje dokument zamykający, nie ten raport.

## §7. Stan repo

- Commity S3: `08d28da5` (ANEKS-3b), `4be66620` (S3-build), raport (ten plik + regresja po S3).
- `origin/master` = `94ff9851`; przed origin: 3 commity, niewypchnięte. **Push = Olga.**
- Porcelain po commicie raportu: czysty poza `??` results/DEMO_C.

**STOP-KONT3.** CC replikuje provery u siebie (`PYTHONPATH=.certdeps python3 -m r01.proofs.p9_kont_verify all`,
`python3 results/KONT/s3/tools/kont_certs_selfcheck.py`); ANEKS_KONT-4 otwiera S4.
