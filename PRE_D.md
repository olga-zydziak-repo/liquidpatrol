# PRE_D — DEMO-B: recon (R1–R6) → akty zamrożone → TWARDY STOP

Data: 2026-08-16. Recon read-only (+ jedna sonda R2). HEAD `3cb48e2` (RE-BRAMKA ENTRY-once PASS
obustronnie; percepcja live domknięta w `world_demo_v1.1`). Reżim: kryteria/frozen/certy **nietykalne**;
prowieniencja per liczba; ANEKS-H obowiązuje; **nagranie ≠ pomiar** (fizyka realna, selekcja ograniczona
protokołem). **Ta sesja NIE nagrywa aktów i NIE buduje** — produkt = ten dokument do ratyfikacji Olgi.
Build + certy tokenu + nagrania + montaż = osobny prompt PO ratyfikacji (SR-D5).

---

## §0 — Cel i zasada uczciwości

DEMO-B pokazuje **wyłącznie zdolności po bramkach** złożone w jedną misję wieloetapową; wszystko poza
bramką ma **jawną planszę**. Trzy filary już po bramkach: (1) osłona P1/P2/P2-ε/P4/P5 (selfcheck 5/5);
> [KOREKTA A1, 2026-08-16, ratyfikowana] `certs_selfcheck` to **6/6**, nie 5/5: prowieniencja pokrywa
> P1, P2, P2_eps, P2_vmax3p1, P4, P5 (6 certów). Baseline B1 potwierdzony: PASS 6/6 na czystym HEAD `83c7e9c`.
(2) GPS-denied 4/4 (`RAPORT_R03A`: REFUSE 0.091 s, velocity-descent dwufazowy, touchdown w kopercie);
(3) percepcja live ENTRY-once (`RAPORT_MTI_REGATE`: (+) `coverage_entry_once`=1.0 @5/7/9 m, (−) 0
fałszywych ENTRY). Nowy element wchodzący do dema (koncepcyjnie ratyfikowany): **token operatora** —
`REFUSE(NO_AUTH)` jako stan domyślny, żadnej eskalacji (OBSERVE) bez decyzji człowieka.

**Zasada nagranie≠pomiar:** przebiegi fizycznie realne w SITL; selekcja ujęć ograniczona protokołem
antyselekcyjnym (§5). Plansza otwierająca: **„SITL only · TRL 2–3"**.

---

## §1 — Akty zamrożone (z trajektoriami z R5)

**AKT 1 — patrol, admisja, autoryzacja.** Dron patroluje trasę (`corner_waypoints_r03`, ±14.07 m);
intruz **wlatuje** (tranzyt → plansza R5-b) i **staje w strefie dwell 7–9 m** z charakteryzowaną
oscylacją (±1.5 m bok / ±0.6 m pion @0.3 Hz); dron w tej fazie wykonuje **profil OBSERVE-motion**
(reżim charakteryzacji — patrz R5). Overlay: koniunkty kanału `box/central/mti_ok`, stan
`CONFIRMING TARGET` przez okno admisji (**scenariusz daje ≥35 s** — zmierzone `t_entry` sięgało 28 s).
ENTRY → OBSERVE **zablokowane** `REFUSE(NO_AUTH)` → operator wydaje token → OBSERVE z trzymanym
`D_safe=5.32 m`, marginesy na żywo.

**AKT 2 — utrata i wygaśnięcie.** Cel znika (tranzyt → plansza R5-b); `age` rośnie na overlay'u;
sufit `θ_age=3.0 s` → **EXPIRE** → powrót do patrolu; cel wraca (tranzyt) → **re-admisja pełną bramą**
(box∧central∧mti_ok przez persist — semantyka ENTRY-once pokazana wprost, `ANEKS_MTI_2`); jeśli token
per-cel (§3) → drugi cel wymaga **nowego tokenu**.

**AKT 3 — GPS-denied.** Denial w patrolu (`EKF2_GPS_CTRL=0`); flaga → `REFUSE(POS_DEGRADED)`
(zmierzone **0.091 s** ≤ 0.15) → velocity-descent dwufazowy (1.5→0.7 m/s) → touchdown w kopercie
(zmierzone 14.84 m ≤ R_E 32). **Plansza kontrastu:** natywny `AUTO.LAND` w tym reżimie **ucieka 42 m
(zmierzone, `RAPORT_R03A` §II')**.

**Poza nogą D:** finał R0.4 (VIO) — osobny cykl. Dead-man/zombie — **plansza z liczbami R0.2**
(stream 1.383 s, zombie dead-man 1.589 s), nie akt live (recon nie kwalifikuje go jako taniego — wymaga
odsprzężonego streamera + reżimu śmierci osłony, ryzyko poza budżetem dema).

---

## §2 — Habitat aktów (ANEKS-H + kamera filmowa) — **SONDA R2 ROZSTRZYGNIĘTA**

Habitat = `world_demo_v1.1` sha256 **a76a38c8** (ANEKS-H: headless, RTF~1.0, time-jump 0/0, hash, zdrowie
EKF). **GUI w aktach ZAKAZANE na stałe (SR-D2)** — zmierzona kontencja GUI-klienta (>180% CPU, time-jumpy,
resety EKF, `run_stack.sh` komentarz) zabija to, co pokazujemy.

**Obraz dema = dodatkowy sensor kamery filmowej w świecie** (statyczna szeroka; opcjonalnie chase),
klatki zapisywane do plików per tick (montaż offline), **NIE streaming do GUI**.

**SONDA R2 (jedyna sonda tej sesji) — POMIAR PAROWANY** (baseline bez kamery vs probe z kamerą
1280×720@30 `always_on`, oba pod IDENTYCZNYM tłem — równoległy `fabryka/train_epoch1`; delta izoluje
koszt kamery; artefakty `results/demo/recon/`):

| bieg | RTF mediana | RTF min | time-jumpy | High Gyro Bias |
|---|---|---|---|---|
| baseline (bez kamery) | 0.9998 | 0.978 | 2 (tło) | 0 |
| **probe (kamera filmowa 720p)** | **0.9999** | 0.987 | 1 (tło) | 0 |
| **Δ (koszt kamery)** | **+0.0001** | — | — | — |

**WERDYKT R2: kamera filmowa TRZYMA lockstep.** Marginalny koszt renderu headless dodatkowego sensora
720p jest **pomijalny** (Δ RTF +0.0001, mediana ~1.0; time-jumpy z tła, nie z kamery; zero High Gyro
Bias). Problem kontencji dotyczył **GUI-klienta gz** (X11+render), nie headless sensora. **Habitat aktów =
ANEKS-H + kamera filmowa jest ważny.** Uwaga prowieniencji: sonda mierzona POD kontencją fabryki
(worst-case tła); w akcie fabryka NIE chodzi równolegle (§2 wymóg) → margines jeszcze większy.
Nowy hash świata (z kamerą) do zamrożenia w buildzie (ANEKS-H per akt).
*(Notatka instrumentu: nazwa `<world>` w SDF musi = nazwa bootowanego świata, inaczej topiki stats/kamery
się rozjeżdżają — bug sondy naprawiony.)*

---

## §3 — Token operatora: semantyka + zakres re-certów (R4)

**Znalezisko R4 (fundament):** łańcuch admisji **JUŻ istnieje** — `r01/authz.py` (`Authorizer.admit()`,
HMAC-SHA256 `sign()`, `mode_of()` **rzuca `PermissionError` gdy decyzja ≠ ALLOW** = „no mode without
admission", własność P4-a), `r01/language.py` (zamknięta gramatyka, `OBSERVE_ON/OFF`), łańcuch PCDL
(`seq`, `prev_hash`, `sig`, `verify_chain()`). W `r02/gate_run_r02.py:222-226` `admit_observe(on)` ustawia
**`observe_authority`** (domyślnie `False`, linia 187) przez `authz.admit`; eskalacja do OBSERVE zachodzi
w `tick()` linia **389**: `if locked and observe_authority and has_estimate → mode=M_OBSERVE`. **To jest
punkt-dławik.** ABSENT: `nonce`, tożsamość operatora, podpis operatora, jawny stan default-deny `NO_AUTH`.

**Proponowana semantyka MINIMALNA (do PRE):**
- **default-deny:** brak ważnego tokenu ⇒ `REFUSE(NO_AUTH)` (6. reason); OBSERVE nieosiągalne.
- **token = podpisana komenda operatora** przez ISTNIEJĄCY łańcuch `authz` (rozszerzony o pole
  tożsamości + nonce), wiążąca OBSERVE.
- **per-cel vs T_auth (rekomendacja: PER-CEL):**

| wariant | znaczenie | zaleta | wada |
|---|---|---|---|
| **per-cel** (rekom.) | token ważny dla TEJ admisji, konsumowany na EXPIRE; powrót celu → nowy token | najsilniejszy default-deny; każda intruzja = jawna decyzja człowieka; **spina AKT 2** (re-admisja→nowy token); zgodny z ENTRY-once (anti-clutter na każdym wejściu) | więcej promptów operatora w gęstym ruchu |
| T_auth (okno) | token ważny przez T; wielokrotne cele/re-wejścia w T bez pytania | mniej promptów | słabszy default-deny; nie pokazuje re-autoryzacji w AKT 2 |

**Rekomendacja: per-cel** (spina AKT 2, najczystsza narracja „człowiek decyduje o każdej eskalacji";
T_auth jako udokumentowana alternatywa dla operacji wielocelowych — poza demem).

- **kanał wydania:** komenda podpisana (HMAC + nonce), zapisana w trace (overlay czyta `REFUSE(NO_AUTH)`
  → `TOKEN ISSUED` → `OBSERVE`).

**Zakres certyfikacji (R4, do zamrożenia):**
- **`REFUSE(NO_AUTH)` jako 6. reason** (precedens ABORT/POS_DEGRADED): string w `r01/shield.py:35`, Int
  `NO_AUTH_R=6` + `domain(rsn)≤6` w `r01/proofs/verify.py`, `RSN_ID` w `conformance.py:28`.
- **P1 od nowa** (`verify.py`) — nowy guard = nowy liść w `tau`/`props` (obecnie 8 liści) + P-obligacja
  „token⇒OBSERVE, ¬token⇒¬OBSERVE"; **z A-auth jawnie**.
- **P5 konformancja od nowa (OBOWIĄZKOWO)** — `RSN_ID`, nowy liść w `LEAVES`/`leaf_of()`, wektory
  **celowane** (`gen_targeted`): brak tokenu ⇒ nigdy OBSERVE; token otwiera **wyłącznie** OBSERVE
  (nic innego); wygaśnięcie tokenu.
- **P4** (`p4_verify.py`) — admisja/token: własność „no OBSERVE-mode without operator token".
- **selfcheck ×2** (pierwszy krok + koniec).
- **P2/P2-ε/P4-geofence UZASADNIONE „nietknięte":** arytmetyka bariery geofence bez zmian; token nie
  dotyka `R_E`/`a_brake`/`v_max`. (P4 sam w sobie re-run bo to prover admisji.)
- **Testy deterministyczne automatu (bez SITL):** brak tokenu ⇒ nigdy OBSERVE; token nie otwiera niczego
  poza OBSERVE; wygaśnięcie per-cel na EXPIRE.

---

## §4 — Overlay/napisy z trace (R3) + braki do patcha

**SR-D4: napisy i plansze WYŁĄCZNIE z logu zdarzeń.** Znalezisko R3: **precedensu `subtitles.vtt` NIE MA**
(grep zero); istnieje natomiast wzorzec **asercji kompletności trace** (`mti_flight.py:428`
`assert len(TRACE)==n_ticks_total`) — to jest dyscyplina do przeniesienia na generator napisów
(log→napisy z asertem „każda plansza ma zdarzenie źródłowe"). Generator = **build od zera**.

**Najbogatsze źródło per-tick:** `results/R02/mti/**/trace.jsonl` (pola: `phase, t_mono, sim_t, has_box,
conf, cx, cy, w, h, central, mti_ok, n_comps, gate, entry, locked, age, lpos`). Shield trace
(`r01/shield.py:131`, in-mem) i R02 gate_live jsonl (`gate_run_r02.py:413`) oraz R03 jsonl
(`gate_run_r03.py`) uzupełniają.

**6 potrzeb overlayّa — analiza luk (R3):**

| # | potrzeba | status | patch |
|---|---|---|---|
| (a) | stan automatu + reason | PARTIAL — reason/rule/decision/mode w gate_live; `state` string tylko w shield in-mem | dodać `d["state"]` do rec `gate_run_r02.py:413` |
| (b) | koniunkty box/central/mti_ok | AVAILABLE w MTI trace; GAP w gate_live | dodać koniunkty do rec gate_live |
| (c) | age vs θ_age | **AVAILABLE** (`age` per-tick; θ_age stała) | — |
| (d) | margines D_safe (`min_d`) | **AVAILABLE** (`gate_run_r02.py:417`) | — (R03 `r_est`-margines: patch) |
| (e) | ε/budżet w GPS-denied | PARTIAL — meta raz + `denial_on`; brak per-tick `R_E−r_est` | dodać per-tick wiersz `r_est`/margines w `gate_run_r03.py` pętli denial |
| (f) | pozycje dron+intruz (minimapa) | dron AVAILABLE; **intruz GAP** (nigdzie nie logowany) | dodać `intr_ned` do rec (dostępne w zakresie) |

**Braki do patcha w buildzie:** (a) `state`, (b) koniunkty, (f) `intr_ned` → do rec gate_live; (e)
per-tick ε-margines w R03. (c)(d) pokryte. Generator napisów = nowy, z asertem kompletności.

---

## §5 — Protokół prób i ważności aktu (R6)

**Kryteria „aktu ważnego" — ZAMROŻONE PRZED nagraniami** (nie stroić po obejrzeniu ujęć):

- **AKT 1 ważny ⟺:** boot ANEKS-H ważny ∧ ENTRY osiągnięte w reżimie dwell 7–9 m ∧ `REFUSE(NO_AUTH)`
  pokazane PRZED tokenem ∧ po tokenie OBSERVE z **0 naruszeń D_safe** ∧ trace kompletny (assert).
- **AKT 2 ważny ⟺:** EXPIRE na `θ_age` ∧ powrót → re-ENTRY pełną koniunkcją ∧ (per-cel) nowy token
  wymagany ∧ trace kompletny.
- **AKT 3 ważny ⟺:** `REFUSE(POS_DEGRADED)` ≤ 0.15 s ∧ touchdown ≤ R_E ∧ trace kompletny.

**Protokół antyselekcyjny:** **≤3 próby/akt**; reguła wyboru **deterministyczna = PIERWSZA próba
spełniająca kryteria ważności**; **odrzucone próby ZACHOWANE i raportowane z powodem**. (Uwaga R6:
`ANEKS_DP1` jako plik NIE istnieje — wzorzec „pierwsza ważna próba" definiowany tu od nowa; dyscyplina
= asercja kompletności trace.)

**Struktura `results/demo/`:** `<akt>/<próba_N>/{trace.jsonl, frames/, manifest.json}`; `manifest.json`
= sha256 każdego artefaktu + hash commitu builda; `result.json` = werdykt ważności per kryteria wyżej.

**Montaż offline** (ffmpeg, poza SITL): plansze **PROVED** (hash certu) / **MEASURED** (wartość +
prowieniencja przyrządu); plansza otwierająca **„SITL only · TRL 2–3"**; długość celu **3–5 min**.

---

## §6 — Plansze prowieniencji per akt

- **AKT 1:** `PROVED` osłona P1/P4/P5 (selfcheck, hash certów); `MEASURED` ENTRY-once
  `coverage_entry_once`=1.0 @7/9 m, `t_entry` 1.6–28 s (REGATE, nav/monotonic); `PROVED` token
  P1/P4/P5 (po buildzie). Plansza reżimu: „percepcja charakteryzowana w dwell 7–9 m OBSERVE-motion".
- **AKT 2:** `MEASURED` θ_age=3.0 s deterministyczne (5 seedów sd=0, R0.2); semantyka ENTRY-once
  (`ANEKS_MTI_2`).
- **AKT 3:** `MEASURED` REFUSE 0.091 s, touchdown 14.84 m (RAPORT_R03A, S2); kontrast `MEASURED`
  AUTO.LAND flyaway 42 m. `PROVED` P2/P2-ε geofence.
- **Plansze R5-b** (poza kopertą) na KAŻDYM tranzycie intruza (patrz §7 R5).

---

## §7 — Uczciwość zasięgu percepcji (R5) — punkt krytyczny

Percepcja scharakteryzowana **wyłącznie w reżimie DWELL {5,7,9} m + dron OBSERVE-motion + intruz
oscylacja ±1.5 m/0.3 Hz** (REGATE). **NIE** scharakteryzowana: (i) intruz w ciągłym tranzycie
(wlot/ucieczka, cel przez zakresy); (ii) dron statyczny zawis (charakteryzacja wymagała ego-motion);
(iii) zakresy poza {5,7,9} m; (iv) dynamika celu poza oscylacją.

**Inwentarz R1 (wąskie gardło):** intruz to `gz set_pose` teleport — `mti_flight.replacer()` ma tryby
`track` (dwell na R z oscylacją = reżim) i `far` (60 m = wylot); **BRAK gładkiej trajektorii
wlot→dwell→wylot jako f(sim_t)** i BRAK dynamicznego pościgu.

**Rekomendacja wariantu (a) — trzymać reżim, gdzie się da:**
- AKT 1/2 **dwell hold** = reżim charakteryzowany → overlay ROSZCZĄCY pokrycie WYŁĄCZNIE tu.
- **wlot i wylot intruza = tranzyt** → dostają planszę **„beyond characterized envelope — transit"**;
  overlay NIE rości pokrycia percepcji w tranzycie.
- dron musi w oknie admisji wykonywać **OBSERVE-motion** (jak REGATE), inaczej zawis = poza reżimem →
  plansza.

**Gdzie (b) NIEUNIKNIONE:** każdy segment ruchu celu przez zakresy (wlot/wylot/powrót) i każdy zakres
poza {5,7,9} m. Uczciwa reguła: **roszczenie percepcji tylko w dwell-hold w reżimie; wszystko inne = plansza.**
Trajektoria do zbudowania: rozszerzyć `intruder_driver`/`replacer` o timeline `t→pozycja`
(wlot z far→9→7 m ~kilka s tranzytu, hold ≥35 s w 7–9 m z oscylacją, wylot→far) — **~1 sesja (R1)**.

---

## §8 — Rozbieżności

1. **HEAD niepushowany:** `origin/main`=`bce77d0`, HEAD lokalny=`3cb48e2` (REGATE + wcześniejsze).
   Prompt zakładał „HEAD po push". Recon oparty na lokalnym HEAD (kompletnym). **Zgłoszone, nie naprawiane**
   (push = Olga).
2. **`subtitles.vtt`/`ANEKS_DP1` — nie istnieją** (R3/R6): założony precedens jest w rzeczywistości
   wzorcem asercji-kompletności-trace, nie generatorem napisów. Generator napisów = build od zera.
3. **Sonda R2 pod kontencją fabryki:** pomiar RTF/lockstep mierzony gdy `fabryka/train_epoch1` chodził
   (7 GB GPU). Werdykt (kamera OK) tym MOCNIEJSZY (worst-case tła); akt wymaga fabryki wyłączonej (§2).
   Bug instrumentu (nazwa `<world>` vs boot-name) naprawiony; frozen świat NIETKNIĘTY (a76a38c8).
4. **px4 SITL auto-respawn** po teardown sondy (bez gz/GPU — nieszkodliwy; teardown builda wyczyści).

---

## DECYZJE DO RATYFIKACJI (Olga) — TWARDY STOP

1. **Kształt aktów** (§1): 3 akty jak wyżej, trajektorie R5-(a) + plansze R5-(b).
2. **Semantyka tokenu** (§3): **per-cel** (rekom.) vs T_auth.
3. **Trajektorie R5** (§7): wariant (a) dwell-hold-roszczenie + (b)-plansza w tranzycie.
4. **Habitat kamery filmowej** (§2): ANEKS-H + kamera 720p (sonda R2 PASS); nowy hash do zamrożenia.
5. **Długość i liczba aktów** (§5): 3 akty, 3–5 min, ≤3 próby/akt, pierwsza ważna.
6. **Zakres re-certów tokenu** (§3): P1+P4+P5 od nowa + selfcheck×2; P2/P2-ε nietknięte.

**Wycena builda (R1):** ~9–12 sesji (orkiestrator wieloaktowy ~2-3; token+NO_AUTH+re-admisja ~2-4;
patrol-podczas-detekcji ~2; choreografia intruza ~1; overlay+napisy+patche trace ~1-2; montaż ~1).
GPS-denied, OBSERVE+D_safe, kanał ENTRY/EXPIRE, dwell/wylot intruza — **już zaimplementowane**, wymagają
re-wiring.

Recon domknięty (R1–R6 + sonda R2). **Build DEMO-B = osobny prompt PO ratyfikacji** (SR-D5: token
z pełnym cyklem certów; frozen/kryteria nietykalne do buildu). **Push = Olga.**
