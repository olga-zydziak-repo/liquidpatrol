# RAPORT_FV — raport końcowy nogi FV (weryfikacja formalna jądra osłony, poz.1b)

CC · 11.09.2026 · noga FV wg PRE_FV (ratyf. ANEKS_FV-0). Sesje S1 (lustro + różnicówka + O1),
S2 (M-krok + O2), S3 (O3 + O4 + ten raport). Zero bootów/GPU/treningu/instalacji; z3 (`.certdeps`) +
stdlib + numpy z repo. **Zakaz języka (PRE_FV §5):** nie orzekam „formally verified system"; wyliczam
wyłącznie dowiedzione własności z ich założeniami i domenami.

## §1. Werdykt bramki nogi (PRE_FV §5)

Definicja: **PASS** = O1 ∧ O2 dowiedzione (certy P6/P7 + provery + wpisy w mapie `certs_selfcheck`) ∧
różnicówka §4 czysta (0 rozbieżności na commitowanej siatce + fuzz + fikstury). Stan po S1+S2+S3:

- **O1 (D5 `safe_descend_step`) — PROVED.** Cert `r01/proofs/certs/P6_d5.json` (verdict PROVED),
  prover `r01/proofs/d5_verify.py`, 10/10 obligacji z3 unsat, N*=194 kroków, t_touchdown=9.700 s.
  Twierdzenia (a) brzeg faz na H_SWITCH wg `<`, (b) vdesc nieujemna nierosnąca ⇒ wysokość zadana
  monotonicznie nierosnąca, (c) touchdown w N*=⌈desc_total/Δ⌉, (d) 0≤vdesc≤v_desc_fast. Źródło lustra
  `r01/proofs/fv_mirror.py:safe_descend_step_mirror` ← `r03/controllers/safe_descend.py:20-49`.
  Commit C2 dde0a7e.
- **O2 (histereza `_pos_monitor`) — PROVED.** Cert `r01/proofs/certs/P7_posmon.json` (verdict PROVED),
  prover `r01/proofs/posmon_verify.py`. Enumeracja osiągalnego grafu FSM (BFS): n_stanów=103,
  n_krawędzi=206 (≪10⁶). (a) min bieg True do REFUSE(POS) = 2 = debounce; (b) min bieg False do wyjścia
  = 100 = hyst; (c) min cykl re-enter = 102 = hyst+debounce; z3-duplikat step-inwariantów (a-step,b-step)
  oba unsat. Źródło lustra `fv_mirror.py:pos_monitor_step` ← `r01/shield.py:76-94`. Commit CO2 7aa879c.
- **Różnicówka lustro↔produkcja — CZYSTA (0 rozbieżności).** `r01/proofs/tests_fv_diff.py`: siatka
  prerejestrowana 54 punkty (`fv_diff_grid.json`, commit C1 729a44c) + fuzz 4×10⁵/funkcja ziarna {0..4}
  + fikstura D5 4221/1791 ticków (z K1/S). Rejestr `results/FV/REJESTR_ROZBIEZNOSCI.md` pusty. Lustro
  1:1 za pierwszym biegiem, zero poprawek kodu produkcji.
- **M-krok (adekwatność przyrządu) — 27/27 = 100% wykrytych.** `r01/proofs/tests_fv_mutants.py`
  (katalog `results/FV/MUTANTY.md`, 27 mutantów, 4 klasy × 4 funkcje); 0 przeżywających ⇒ `fv_diff_grid2.json`
  NIEPOTRZEBNA (0 iteracji). Sanity IDENTITY = 0 rozbieżności. Commity CM1 4a84f20, CM2 5856a92.

**WERDYKT BRAMKI = PASS.** O1 ∧ O2 dowiedzione ∧ różnicówka czysta ∧ przyrząd adekwatny. ŚMIERĆ nogi
nie zachodzi (lustro zbudowane bez reifikacji produkcji). TRIPWIRE niewyzwolony (0 kontrprzykładów
realnych na kodzie produkcyjnym w całej nodze).

## §2. O3 — zawieranie `_geofence_violation` ↔ Inv_P2 (niebramkujące) — DOWIEDZIONE

Cert `r01/proofs/certs/P8_geo_cont.json` (verdict PROVED, `"gating": false`), prover
`r01/proofs/geo_cont_verify.py`, z3 NRA. Twierdzenie: ∀ (pos,vel,target) ∈ D: ¬`_geofence_violation`
⇒ pr + vn²/(2·a_brake) ≤ R_E (antecedent Inv_P2 z P2.json), pr=hypot(pos_x,pos_y), vn=hypot(vx,vy).

Domena D (verbatim z certu): |v|≤v_max (vn≤v_max, klamp min(·,v_max) na D nieaktywny ⇒ vh=vn);
pozycje pr ≤ R_env=37 (GF_MAX_HOR_DIST, r01/config.py:35); pion -V_E≤pos_z,target_z≤V_E, V_E=20
(r01/config.py:31). Stałe Inv wymierne wczytane z P2.json (v_max=3, R_E=32, a_brake=2 — nie przepisane).

Wynik trójwynikowo (czasy solvera; budżet O3c 60 min, zużyto 0.003 s łącznie):
- **G1 (bramkowa dla O3): unsat [0.3 ms] — DOWIEDZIONE.** Zawieranie zachodzi.
- **G2 (informacyjna, v_max=31/10, stałe P2_vmax3p1.json): unsat [0.2 ms].** Spójne z P2_vmax3p1.
- **G3 (kontrola niepustości D∧¬viol): sat [2.2 ms].** Domena nie pusta/trywialna ⇒ G1 unsat NIE
  jest próżny.

Nota semantyczna (F3, „norma pełna vs po klampie"): produkcja liczy min(hypot(vx,vy), v_max)
(shield.py:98); na D klamp nieaktywny ⇒ braking = vn²/(2·a_brake) = człon bariery Inv_P2. Klamp
odwzorowany 1:1 przez z3.If(vn≤v_max, vn, v_max); równość vh=vn wynika z ograniczenia domeny, nie z
ręcznego uproszczenia. Zawieranie zależy od r_e (config :30, =32) ≤ R_E (P2.json, =32) — nie jest
wektorowo trywialne. **KONTRPRZYKŁADÓW MODELOWYCH BRAK** (G1,G2 unsat) ⇒ sekcja STOP/TRIPWIRE
niepotrzebna. **V_env=6.0 POZA zakresem O3** (limit środowiska ≠ zadany) — odsyłacz do erratum #2
`ERRATUM_VMAX.md`; predykat NIE pokrywa V_env i nie udaje, że pokrywa.

## §3. O4 — złożenie osłona∘sieć (stretch (ii), niebramkujące) — ERRATA ANEKS_FV-1c

**[ERRATA ANEKS_FV-1c — błąd kategorii vel ≠ v_cmd]** Poprzednie zdanie kompozycyjne L2 (zachowane
niżej pod „[superseded]") instancjonowało O3 G1 na **v_cmd** (komenda), podczas gdy O3 kwantyfikuje po
**vel MIERZONYM**: `_braking_dist(vel)`/`_geofence_violation(pos,vel,target)` liczą po argumencie vel
(r01/shield.py:97-99, :101-112), a produkcja podaje vel=telemetria/EKF (gate_run_r03.py:232 `vel=(m.vx,
m.vy,0.0)`→:268; bench_flight.py:342 `vel=[m.vx,m.vy,m.vz]`→:363); v_cmd trafia do `set_velocity_ned`
dopiero po ALLOW. Podstawienie v_cmd za vel wprowadzało niejawną przesłankę A-TRACK (|vel|≤|v_cmd|) —
nigdzie niedowiedzioną i EMPIRYCZNIE FAŁSZYWĄ (K1/ANEKS_K1-8: komenda 3.00, EKF 3.74, GT 5.34 m/s
w narożniku; ERRATUM_VMAX.md; V_env=6.0). Poprawka rozdziela trzy twierdzenia (K1/K2/K3). **O1, O2, O3,
L1 oraz cert P8 (domena jawna, gating:false) NIETKNIĘTE**; pada wyłącznie zdanie kompozycyjne L2 i to,
co propozycja kanonu §6 z niego wywodziła. Werdykt bramki nogi (PRE §5: O1∧O2∧różnicówka) nie zależy
od L2. Prereg CO3 nienaruszony (błąd w interpretacji, nie w obligacjach). `geo_cont_verify.py` NIETYKALNY
(docstring z dawnym L2 pozostaje — zmiana provera = nowe sha = regeneracja certu, klasa self-hash P2.json).

### Treść po erracie (OBOWIĄZUJĄCA) — trzy rozdzielne twierdzenia

- **L1 — |y_net| ≤ v_max architektonicznie.** Głowa sieci `y = tanh(·)·V_MAX` (net/models.py:12 dla CfC,
  :57 dla tiny-MLP: `y = a3 * self.vmax`, a3=tanh). |tanh(·)| ≤ 1 ⇒ |y_net| ≤ V_MAX dla DOWOLNYCH wag
  i historii stanu ukrytego. Dowód jednozdaniowy, bez certu.
- **K1 — kanał komendy (twierdzenie o KONTROLERZE).** L1 ∧ L2 ⇒ |v_cmd| ≤ v_max niezależnie od wag,
  historii i stanu sieci. `clip_v(v,vmax)` (r03/controllers/common.py:10-16): gdy |v|≤vmax zwraca v,
  inaczej v·(vmax/|v|) o normie DOKŁADNIE vmax ⇒ |clip_v|≤vmax bezwarunkowo (nawet gdyby L1 zawiodło).
  Cytaty: net/models.py:12/:57, common.py:10-16.
- **K2 — zawieranie na D (twierdzenie o OSŁONIE).** O3 G1 ⇒ antecedent Inv_P2 ⇒ (P2) pr ≤ R_E; zmienna =
  **vel MIERZONE**, domena D = {|vel| ≤ 3.0, pr ≤ 37, |z| ≤ 20}. Cert P8 (gating:false).
- **K3 — pomost A-TRACK (ZAŁOŻENIE, nie wniosek z K1).** „|vel| ≤ v_max" jest ZAŁOŻENIEM, nie wnioskiem
  z K1 — kontroler ogranicza KOMENDĘ, nie prędkość mierzoną. Zmierzone naruszenia: RAPORT_K1/ANEKS_K1-8
  (cmd 3.00 / EKF 3.74 / GT 5.34 m/s w narożniku), ERRATUM_VMAX.md. Poza D pokrycie daje WYŁĄCZNIE
  empiryczna analiza obwiedni (C_margin = 32 − (20.654 + 10.2) = 1.146 m przy V_env=6.0) — nie dowód.
  **Zdanie „sieć nie może wyprowadzić drona poza R_E" NIE wynika z K1 ∧ K2.**
- **L3 — `results/FV/NOTA_UNROLL.md` (desk-note, status „częściowy").** Weryfikacja unroll-T wnętrza CfC:
  co by wymagała (rozwinięcie T kopii rekurencji, kodowanie tanh/σ przestępnych, związanie 1903 wag numpy,
  własność warta dowodu), klasy narzędzi z nazwy (dReal δ-zupełne; CROWN/auto_LiRPA propagacja granic;
  Verisig/NNV/POLAR/ReachNN osiągalność; Marabou/Reluplex MILP — statusy z dokumentacji, do weryfikacji),
  dlaczego poza budżetem (F6/F7/SR-FV-3). Własność |y|≤V_MAX zamknięta architektonicznie przez L1 bez unrollu.

**O4 po erracie:** K1 (kanał komendy kontrolera) ∧ K2 (zawieranie osłony na D) dowiedzione ROZŁĄCZNIE;
ich złożenie w gwarancję toru wymaga A-TRACK (K3) — niedowiedzione, empirycznie łamane. Niebramkujące
(PRE_FV §5). Wnętrze CfC częściowe (L3).

### [superseded — errata ANEKS_FV-1c] poprzednia treść §O4 (zachowana, nic nie kasujemy)

> Twierdzenia o KODZIE i MODELU, zero twierdzeń o rzeczywistości lotu (F6):
> - **L1 — |y_net| ≤ v_max architektonicznie.** Głowa sieci `y = tanh(·)·V_MAX` (net/models.py:12 dla CfC,
>   :57 dla tiny-MLP: `y = a3 * self.vmax`, a3=tanh). Ponieważ |tanh(·)| ≤ 1, to |y_net| ≤ V_MAX dla
>   DOWOLNYCH wag i historii stanu ukrytego. Dowód jednozdaniowy, bez certu.
> - **L2 — kompozycja.** `clip_v(v, vmax)` (r03/controllers/common.py:10-16): gdy |v|≤vmax zwraca v
>   (norma ≤vmax), inaczej v·(vmax/|v|) o normie DOKŁADNIE vmax ⇒ |clip_v(v,vmax)| ≤ vmax dla dowolnego v
>   (BEZWARUNKOWO, nawet gdyby L1 zawiodło). Kompozycja: |v_cmd| ≤ v_max (L2) ∧ ¬`_geofence_violation`
>   ⇒ (O3 G1, PROVED) pr + v_cmd_h²/(2·a_brake) ≤ R_E = antecedent Inv_P2 ⇒ (P2.json, PROVED) pr ≤ R_E.
>   Założenie jawne: lustro ≡ produkcja dla predykatu (różnicówka S1 + M-krok). Łańcuch dotyczy KODU
>   (głowa + klamp + predykat + bariera P2), nie dynamiki lotu.
> - **L3 — `results/FV/NOTA_UNROLL.md` (desk-note, status „częściowy").** [treść bez zmian — patrz L3 wyżej]
>
> **O4 = DOWIEDZIONE na złożeniu (L1+L2), wnętrze CfC częściowe (L3).** Niebramkujące (PRE_FV §5).
> ↑ BŁĄD: L2 podstawia v_cmd za vel w antecedencie O3 (A-TRACK). Zastąpione przez K1/K2/K3 wyżej.

## §4. Wiązanie model↔kod (rdzeń metody) — podsumowanie z liczbami

Lustro `r01/proofs/fv_mirror.py` = przepisanie 1:1 czterech elementów jądra (`_braking_dist`,
`_geofence_violation`+`_radial`, `_pos_monitor`, `safe_descend_step`) ze stanem zreifikowanym jako
jawny wektor. Wiązanie (import produkcji bez modyfikacji, PRE_FV §2):

- **Różnicówka (S1):** siatka prerejestrowana **54** punkty (brzegi progów) + fuzz **4×10⁵**/funkcja
  (ziarna {0..4}) + fikstura **4221/1791** ticków D5 → **0 rozbieżności** (`tests_fv_diff.py`).
- **M-krok (S2):** **27** mutantów lustra (4 klasy × 4 funkcje, `MUTANTY.md`) → **27/27 = 100%
  wykrytych**, 0 przeżywających, 0 iteracji grid2 (`tests_fv_mutants.py`). Wykrycie dominująco siatką
  (25/27), 2 swap-mutanty geofence przez fuzz.
- **M5 (S2):** finalny bieg pełnej różnicówki na niemutowanym lustrze = **0 rozbieżności** (spójność
  po M).

Wniosek metodologiczny: lustro wierne (0 rozbieżności) I różnicówka adekwatna (łapie 27/27 wstrzykniętych
błędów). Dowody O1/O2/O3 stoją na tym wiązaniu przez jawne assumption „lustro ≡ produkcja" w każdym
cercie.

## §5. Rozliczenie predykcji (PRE_FV §9 + ANEKS_FV-1 §6 + P-CC2-1)

- **P-FV-1** (O1 dowiedzione w ≤1 sesji dowodowej od startu S1; p≈0.75) — **✓**. O1 PROVED w S1
  (P6_d5, dde0a7e), pierwsza sesja dowodowa.
- **P-FV-2** (różnicówka znajdzie ≥1 rozbieżność wymagającą poprawki LUSTRA; p≈0.6) — **✗**
  (niezrealizowana). 0 rozbieżności w S1 i M5; lustro 1:1 za pierwszym biegiem. Kalibracja CC
  „chroniczne zaniżanie glue" nie zadziałała tu w drugą stronę — glue okazał się trywialny.
- **P-FV-3** (O4(a)+(b) domknięte w ≤1 sesji; p≈0.7) — **✓**. L1+L2 domknięte w S3 (ta sesja).
- **P-FV-4** (wszystkie mutanty wykryte bez potrzeby grid2; p≈0.5; ANEKS_FV-1 §6) — **✓**. 27/27
  wykrytych, grid2 niepotrzebna.
- **P-CC2-1 część FV** (część (ii) „własności samej sieci CfC narzędziem off-the-shelf" → wynik
  częściowy albo śmierć na pokryciu narzędzi; p≈0.7) — **✓ (częściowy)**. Złożenie dowiedzione
  (O4/L1+L2), wnętrze CfC pozostaje niedowiedzione — desk-note „częściowy" (NOTA_UNROLL). Przenoszona
  z OTWARTE do rozliczonych w KSIEGA_PREDYKCJI. **P-CC2-2 (SPRIND) zostaje OTWARTE.**

Suma FV (czyste ✓/✗): **3 ✓ / 1 ✗** (P-FV-1,3,4 ✓; P-FV-2 ✗) + P-CC2-1(FV) ✓-częściowy. Edycja
`results/KSIEGA_PREDYKCJI.md` (sekcja „NOGA FV") naniesiona w tej sesji.

## §6. PROPOZYCJA kanonu roszczeń FV (rama ANEKS_FV-1c §4; NIE obowiązujący — brzmienie finalne = ANEKS_FV-2)

> **WOLNO** — wyłącznie wyliczanie własności z domenami i założeniami:
> - D5 (`safe_descend_step`): własności (a)–(d) dowiedzione przy założeniu zegara niemalejącego;
>   N*=194, t_touchdown 9.700 s (cert P6_d5). Lustro 1:1 zwalidowane różnicówką i M-krokiem.
> - Histereza (`_pos_monitor`): (a) REFUSE(POS) po ≥2 kolejnych tickach, (b) wyjście po ≥100 czystych,
>   (c) min cykl 102 — dowiedzione na PEŁNYM osiągalnym grafie 103 stanów / 206 krawędzi (cert P7).
> - Predykat geofence implementacji ≡ model certu P2 na D = {|vel| ≤ 3.0, pr ≤ 37, |z| ≤ 20}
>   (spójność kształtu i stałych; zastępuje próbkową konformancję P5 dla tego predykatu; cert P8,
>   niebramkujący; zmienna = vel MIERZONE).
> - Kanał komendy kontrolera uczonego ograniczony architektonicznie: |v_cmd| ≤ v_max niezależnie od wag
>   (L1 głowa tanh·V_MAX + L2 clip_v). Twierdzenie o KONTROLERZE, rozłączne od zawierania osłony.
> - Wiązanie model↔kod: siatka 54 + fuzz 4×10⁵ + fikstura 4221/1791 ticków, 0 rozbieżności; 27/27
>   mutantów wykrytych (moc przyrządu zmierzona).
>
> **NIE WOLNO:**
> - „formally verified system" / „osłona zweryfikowana formalnie" bez wyliczenia własności i domen
>   (PRE_FV §5 — zdanie nie istnieje).
> - „sieć nie może wyprowadzić drona poza R_E" — wymaga pomostu A-TRACK (|vel|≤|v_cmd|), niedowiedzionego
>   i empirycznie łamanego (K1/ANEKS_K1-8, ERRATUM_VMAX); NIE wynika z K1 ∧ K2.
> - jakiejkolwiek gwarancji przy |vel| > 3.0 (erratum #2; poza D predykat z klampem ZANIŻA drogę
>   hamowania — sufit 3²/(2·2)=2.25 m niezależnie od rzeczywistej prędkości).
> - ekstrapolacji poza model/SITL; twierdzeń o wnętrzu CfC (NOTA_UNROLL: częściowy); pomijania założenia
>   „lustro ≡ produkcja" przy cytowaniu któregokolwiek certu FV.

## §7. Odchylenia sesji i nogi

- **SEQ-1 (przejście S2→S3, kontekst z ANEKS_FV-1b §1):** trzy poślizgi sekwencji z rzędu (raport S2
  niedostarczony do CC; ANEKS_FV-1 wklejony zamiast -1a; PROMPT_FV_S3 bez linii go) → informacja
  o PROCESIE (za dużo ruchomych części na tryb solo), nie o operatorze. Odpowiedź = redukcja kroków
  (ANEKS_FV-1b §2: odczyt C1a–C1d do W0 sesji, linia go zastąpiona obecnością aneksu), reżim
  niezluzowany. Podwójny STOP bramek S3 (brak linii go §0.1 + niepushowany 57d8f45 §0.2) zadziałał
  jak projektowano — żadna praca nie ruszyła przedwcześnie.
- **ARCH-1 ANEKS_FV-1a:** w S3 nieobecny w Downloads (C0' dbc4442 skomitował tylko `ANEKS_FV-1b.md`,
  sha 7a314ee0…). **DOMKNIĘTY w CO5 (13.09):** `ANEKS_FV-1a.md` (sha 2eafb824…) + `ANEKS_FV-1c.md`
  (sha 101e5ad5…) dostarczone do korzenia repo. Wcześniej ANEKS_FV-1.md domknięty commitem 57d8f45.
- **L2 — błąd kategorii zadany≠faktyczny (errata ANEKS_FV-1c, §O4 wyżej):** zdanie kompozycyjne L2
  instancjonowało O3 na v_cmd zamiast na vel MIERZONYM (A-TRACK). Złapane przez CC PRZED werdyktem
  (prereg P-CC2-3). Poprawka doc-only CO5: rozdzielenie K1/K2/K3; O1/O2/O3/L1/P8 i werdykt bramki
  nietknięte. Trzecia instancja klasy „limit zadany ≠ faktyczny" w programie (po 11.69 m i V_MAX w PRE).
- **Bugfix harnessu provera (CO3→bieg):** pierwszy bieg `geo_cont_verify.py` rzucił `TypeError`
  (dekoder wyniku z3 używał `CheckSatResult` jako klucza dict — nieha­szowalny). Fix = porównanie
  wprost `r == z3.unsat` (jak `d5_verify._holds`). Zmiana dotyczy WYŁĄCZNIE dekodera wyniku; obligacje
  G1/G2/G3, domena D i twierdzenia (prerejestrowane w CO3 f01e083) NIETKNIĘTE. Integralność prereg
  zachowana.
- **Reżim czysty:** zero bootów/GPU/treningu/instalacji; produkcja importowana, nieedytowana;
  `fv_diff_grid.json` nietykalna; jedyna edycja pinowanego obszaru = +1 linia mapy `certs_selfcheck.py`
  (P8, diff verbatim w §8). SR-FV-1..7 czyste.

## §8. Domknięcia SR (S3-E, SR-FV-7)

Diff mapy `certs_selfcheck.py` (verbatim):
```diff
@@ PROVER_OF = {
     "P7_posmon.json": "posmon_verify.py",  # FV/O2: histereza _pos_monitor (enumeracja grafu + z3)
+    "P8_geo_cont.json": "geo_cont_verify.py",  # FV/O3: zawieranie geofence↔P2 (z3 NRA, niebramkujące)
 }
```
`certs_selfcheck` = **PASS 9/9** (P1,P2,P2_eps,P2_vmax3p1,P4,P5,P6_d5,P7_posmon,P8_geo_cont). pytest
offline = patrz raport CC (bez regresji). Drzewo w zakresie `proofs/` czyste po CO4.

**STOP-FV2.** Push = Olga. Ratyfikacja: **ANEKS_FV-2** (werdykt nogi + finalizacja kanonu §6).
Commity nogi: S1 {C0 df58922, C1 729a44c, C2 dde0a7e}; S2 {CM1 4a84f20, CM2 5856a92, CO2 7aa879c};
ARCH-1 ANEKS_FV-1 57d8f45; S3 {C0' dbc4442, CO3 f01e083, CO4 (ten)}.
