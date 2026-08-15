# RAPORT_MTI — brama ENTRY struktura ∧ MTI: instrument, potok, charakteryzacja, BRAMKA DWUSTRONNA

Data: 2026-08-15. PX4 **v1.16.2**, Gazebo Harmonic, ROS2 Jazzy, MAVSDK, YOLO-World (struktura).
Reżim: build wg `PROMPT_MTI_BUILD` po ratyfikacji `PRE_MTI` (ridery R-M1..M5); kryteria `PRE_R02C`
ZAMROŻONE przed pomiarem (≥7 m przy coverage ≥0.8 na bramie struktura∧MTI; ε_FP = 0 wg definicji R3);
`θ_conf` NIETYKALNY (zdefiniowany, przestał być bramą — ratyfikowana zmiana znaczenia); `DEADMAN_TICKS=6`;
ANEKS-H obowiązuje każdemu biegowi (bieg naruszający = jawnie nieważny); każda liczba z etykietą przyrządu;
księgowość trójwynikowa; **FAIL = FAIL, bez strojenia po fakcie**. GT (gz) — nigdy w decyzji; tu nie ma
sędziego GT bo brama nie używa GT (struktura∧MTI z sensorów pokładowych), GT tylko znakuje `gt_present`.

Łańcuch commitów: PRE_MTI recon (`587248f`) → PRE aneks R-M1..M5 + teren DEMA (`068bfaa`) →
B1-B3 instrument+potok+brama (`b6c30f6`) → **B4-B5 charakteryzacja+bramka (ten blok)** → B6 raport.
**Push = Olga.**

Habitat (ANEKS-H, H.4): `worlds/world_demo_v1.sdf` sha256 **a76a38c8** (84 statyczne teksturowane
bloki `tex_*` visual-only + `ground_plane`; nagłówek == default; koperta R_E/geofence NIETKNIĘTA; światło
jak default). Wersja v1.0 (359 bloków, `eb80135a`, commit `068bfaa`) ZASTĄPIONA v1.1 (84 bloki) — 359
bloków dawało kontencję renderu gz → EKF *High Gyro Bias* → odmowa arm (podpis kontencji ANEKS-H/E2);
84 bloki utrzymują realną paralaksę tekstury przy zbieżnym EKF. **Liczby percepcyjne między światami się
NIE przenoszą (R-M1)** — nic z default.sdf / B0-B3 / A1 nie jest priorem; cała charakteryzacja MTI w
`world_demo_v1`.

---

## (0) ANEKS-H — ważność habitatu per boot

| boot | HEADLESS | RTF start→end | time-jump (stack.log) pre/post | EKF health hits | arm | werdykt boot |
|---|---|---|---|---|---|---|
| **fix1** | GUI=brak ✓ | 0.99997 → 1.00010 | 0 / 0 | 6 (settle) | OK | **WAŻNY** |
| **fix2** | GUI=brak ✓ | 0.99853 → (teardown) | 0 / 0 | 1 (settle) | OK | **WAŻNY** |
| **fix3** | GUI=brak ✓ | 1.00005 → 1.00015 | 0 / 0 | 1 (settle) | OK | **WAŻNY** |
| fix2_envfail1 | GUI=brak ✓ | — | — | (settle) | **ARM FAIL (60 retry)** | NIEWAŻNY — env (kontencja) |

Env-failure `fix2_envfail1` (High Gyro Bias, kontencja renderu) — NIE bieg pomiarowy, artefakty
zachowane `results/R02/mti/B4/fix2_envfail1/`. Znana naprawa (SR-N7): świat 84 bloki, YOLO po arm,
settle 150 s, retry 60 — zastosowana, nie diagnozowana od zera. Kolejny boot (relaunch fix2) armed. Nie
osiągnięto 3 env-fail pod rząd (SR-N7 nie wyzwolone).

---

## (I) WYNIK BRAMKI DWUSTRONNEJ per kryterium — z liczbami

Kryteria ZAMROŻONE przed pomiarem (`PRE_R02C` / `PRE_MTI`), świeży boot per bieg.

- **(−) ε_FP = 0 wg definicji R3 (pusta scena ORAZ scena z ruchem tła):** **PASS.**
  Zero fałszywych ENTRY we WSZYSTKICH 3 biegach: fix1 (fp_empty 171 / fp_bg 456 tick, fg=50), fix2
  (fp_empty 171 / fp_bg fg=26), fix3 (fp_empty 171 / fp_bg 455 tick, fg=46). `false_entry = 0`,
  `eps_fp_per_min = 0.0` bez wyjątku, ×3 booty × 2 sceny (pusta + ruch tła). W fp_bg odnotowano
  `false_gate_frames` (fix1/2/3 = 50/26/46 — chwilowa jednoklatkowa admisja struktura∧MTI przy ruchu tła) ale
  **0 ENTRY** — filtr spójności czasowej + DEADMAN pochłania je zanim urosną w ENTRY. To jest sedno
  redefinicji R3: ε_FP liczy ENTRY, nie pojedyncze klatki bramy.

- **(+) zasięg ≥ 7 m przy coverage ≥ 0.8 na bramie struktura∧MTI, ≥3 świeże booty:** **FAIL (strict).**
  `coverage_gate` (klatkowa admisja struktura∧MTI) NIE osiąga 0.8 na ŻADNYM zasięgu w ŻADNYM boocie —
  najlepszy pojedynczy punkt to 7 m ≈ 0.70 (fix2). Mediana per zasięg (§II) poniżej progu z marginesem.
  Detekcja struktury jest kompletna (`coverage_seen = 1.0` wszędzie — YOLO widzi cel co klatkę), ale
  **człon MTI jest przerywany klatkowo** (cel w geometrii OBSERVE-motion daje ruch derotowany tylko w
  części klatek; między impulsami ruchu komponent MTI zanika) → iloczyn struktura∧MTI < 0.8/klatkę.
  > **[KOREKTA R-3, 2026-08-16 — sesja DIAG/REGATE]** Zdanie „człon MTI przerywany klatkowo" opierało
  > się na obserwacji **nie-utrwalonej**: `gate = box∧central∧mti_ok` był agregowany łącznie, a per-tick
  > `recs` porzucane (`RAPORT_MTI_DIAG` D0) — **dekompozycja koniunkcji jest niedostępna z agregatów**,
  > więc atrybucja spadku do członu MTI (vs `central`) była nieuprawniona. **Rozstrzyga trace re-bramki**
  > (REGATE, koniunkty logowane osobno — R-2). Ponadto (+) FAIL był artefaktem POMIARU: metryka
  > `coverage_gate` liczyła koniunkcję każdą klatkę, choć brama wymaga `mti_ok` tylko do admisji
  > (ENTRY-once, `ANEKS_MTI_2`) — patrz `RAPORT_MTI_REGATE.md`.

**Dźwignie (rozdzielczość → FOV → gimbal) POZOSTAJĄ ZAPARKOWANE** (SR-M4/R-M3). FAIL na (+) NIE
uruchamia żadnej „przy okazji" — zwrot dźwigni wyłącznie nową decyzją Olgi z nowym dowodem. STOP z
liczbami (poniżej).

> **NOTA DEFINICYJNA (kluczowa dla werdyktu):** kryterium (+) mierzy `coverage_gate` = klatkowy iloczyn
> struktura∧MTI, bo tak brzmi zamrożone zdanie „coverage na bramie struktura∧MTI". Istnieje MIĘKSZA,
> operacyjna miara `coverage_locked` (kanał trzyma lock przez ZOH-age między detekcjami: mediana
> 0.93/0.912/0.86 na 5/7/9 m; post-ENTRY = 1.0 gdzie ENTRY zaszło) — ale to INNA definicja i podstawienie
> jej pod (+) byłoby przesunięciem bramki po pomiarze (zakazane). Co więcej `coverage_locked` sама bywa
> krucha: fix3 @ 5 m = 0.0 (bez ENTRY). Raportuję obie; werdykt wiąże `coverage_gate` (zamrożone zdanie
> „coverage na bramie struktura∧MTI").

---

## (II) CHARAKTERYZACJA per dystans — mediana + IQR (R-M2)

Profil OBSERVE-motion, dwell ≥30 s, siatka {5, 7, 9} m, ×3 świeże booty (fix1, fix2, fix3).
`coverage_seen`/`coverage_gate`/`coverage_locked` — definicje w §Aneks-def.

### coverage_gate (brama struktura∧MTI, klatkowa) — kryterium (+)

| zasięg | fix1 | fix2 | fix3 | **mediana** | rozstęp [min–max] |
|---|---|---|---|---|---|
| 5 m | 0.333 | 0.600 | 0.393 | **0.393** | 0.333–0.600 |
| 7 m | 0.632 | 0.702 | 0.596 | **0.632** | 0.596–0.702 |
| 9 m | 0.621 | 0.632 | 0.649 | **0.632** | 0.621–0.649 |

Mediana `coverage_gate` na KAŻDYM zasięgu poniżej 0.8 z marginesem (max pojedynczy punkt = 0.702 @ 7 m,
fix2). **5 m gorsze niż 7/9 m** (mediana 0.393) — bliższy cel = większa amplituda przepływu w kadrze →
derotacja zostawia większe residuum tła, mniej klatek z CZYSTYM ruchem celu ponad tłem. **fix3 @ 5 m:
`n_entry = 0`** — brama struktura∧MTI nie zebrała dość spójnych klatek by w ogóle wejść w ENTRY w dwell
30 s (kolejny dowód klatkowej przerywności członu MTI).

### coverage_seen (detekcja struktury, YOLO) / coverage_locked (operacyjny, ZOH-age)

| zasięg | seen (wszystkie booty) | locked fix1 | locked fix2 | locked fix3 | locked mediana |
|---|---|---|---|---|---|
| 5 m | 1.0 | 0.93 | 0.945 | **0.0** | 0.93 |
| 7 m | 1.0 | 0.825 | 0.947 | 0.912 | 0.912 |
| 9 m | 1.0 | 0.759 | 0.93 | 0.86 | 0.86 |

`coverage_locked_post_entry = 1.0` wszędzie GDZIE doszło do ENTRY — **po pierwszym ENTRY kanał trzyma lock
ciągle**. Wyjątek **fix3 @ 5 m: locked = 0.0** (bo `n_entry = 0` — bez ENTRY kanał NIGDY się nie zamknął):
przy 5 m nawet MIĘKKA miara operacyjna potrafi się załamać, gdy klatkowa brama nie zbierze dość by wejść.
To pokazuje że przewaga `coverage_locked` nad `coverage_gate` NIE jest gwarantowana — zależy od osiągnięcia
ENTRY, które przy 5 m bywa nietrafione.

### czas do ENTRY [przyrząd: mav/monotonic od startu fazy] / komponenty MTI/klatkę

| zasięg | t_entry fix1 | t_entry fix2 | t_entry fix3 | comps median (fix1/2/3) |
|---|---|---|---|---|
| 5 m | 2.73 s | 3.08 s | **brak ENTRY** | 21 / 26 / 23 |
| 7 m | 5.29 s | 1.66 s | 2.64 s | 23 / 25 / 25 |
| 9 m | 7.39 s | 2.18 s | 4.23 s | 22 / 23 / 25 |

(fp_bg `false_gate_frames`: fix1/2/3 = 50/26/46 — wszystkie z 0 ENTRY, ε_FP=0. Komponenty MTI/klatkę
median ~21–26 na cel: obfite, ale rozproszone — obfitość komponentów ≠ ciągłość admisji celu.)

ENTRY osiągane w kilka sekund w 8/9 przypadków (`false_entry = 0` zawsze) — **gdy zachodzi, wykrycie jest
szybkie**. Wyjątek fix3 @ 5 m (`n_entry = 0`): przy najbliższym zasięgu brama potrafi w ogóle nie wejść.
Deficyt jest w KLATKOWEJ CIĄGŁOŚCI członu MTI (nie w detekcji struktury: `coverage_seen = 1.0` wszędzie),
a przy 5 m przechodzi w ryzyko nie-osiągnięcia ENTRY.

### conf pasywny (telemetria, NIE brama — R-M2 mediana+IQR)

| zasięg | mediana conf | IQR | max (info) |
|---|---|---|---|
| 5 m (fix1) | 0.097 | 0.052–0.135 | 0.285 |
| 7 m (fix1) | 0.088 | 0.050–0.122 | 0.386 |
| 9 m (fix1) | 0.070 | 0.024–0.132 | 0.391 |

`conf` mediana ≪ `θ_conf = 0.1635` na każdym zasięgu — **potwierdza dlaczego conf-floor był martwy i
dlaczego brama musi być struktura∧MTI** (spójne z RAPORT_LIVEFED_CHAR / PRE_MTI). conf jest tu wyłącznie
logowany.

---

## (III) GRANICA ROSZCZENIA

Zmierzona zdolność dotyczy **`world_demo_v1` w SITL** (Gazebo Harmonic, teksturowany grunt, geometria
OBSERVE-motion, intruz `intruder_model.sdf`). **NIE jest to roszczenie polowe ani o innych światach.**
Liczby percepcyjne między światami się nie przenoszą (R-M1) — `world_demo_v1` ≠ default.sdf ≠ pole.
`coverage_seen = 1.0` mówi że detektor struktury działa w tym habitacie; `coverage_gate < 0.8` mówi że
klatkowa brama struktura∧MTI w tym habitacie nie sięga zamrożonego progu operacyjnego.

---

## (IV) R-M4 — wymiana bramy percepcji BEZ dotknięcia certów (demonstracja tezy programu)

Brama ENTRY została wymieniona z `conf ≥ θ_conf` na `struktura ∧ MTI` **w całości UPSTREAM kanału 5-dim**
(`r02/target_channel.py`, flaga `entry_require_mti`). `shield.step`, tau z3, kanał 5-dim (cx,cy,w,h,age),
provery P1/P5 — **NIETKNIĘTE**. Dowód prowieniencji: `certs_selfcheck` **6/6 PASS** po implementacji bramy
(P1←verify.py, P2/P2_vmax3p1←geofence.py, P4←p4_verify.py, P5←conformance.py, P2_eps←eps_verify.py — każdy
`model_sha256` zgodny z prover). **Zero re-certów.** To jest operacyjna demonstracja tezy programu:
**rdzeń bezpieczeństwa (zawieranie) jest dowiedziony NIEZALEŻNIE od warstwy percepcji** — można wymienić
całą bramę wykrywania i formalna gwarancja osłony pozostaje ważna bez ponownego dowodzenia. `conf`
zdegradowany do telemetrii pasywnej (symetria z `eph` z R0.3a: nigdy w admisji, tylko log).

---

## (V) REJESTR FP — zmierzone vs przewidziane (inwentarz R2) + rozbieżności

Wektory syntetyczne R-M5 (B2, PRZED pierwszym lotem) — każdy nazwany FP z inwentarza R2 = test PASS:

| FP (inwentarz R2) | wektor syntetyczny B2 | oczekiwane | test |
|---|---|---|---|
| paralaksa teksturowanego gruntu pod ruchem | `test_fp_ground_parallax` | odrzucone | PASS |
| cień własnego drona | `test_fp_own_shadow` | odrzucone | PASS |
| śmigła przy krawędzi kadru | `test_fp_props_frame_edge` | odrzucone (border-erode + edge-touch) | PASS |
| residuum derotacji przy szybkim yaw | `test_fp_derotation_residual_fast_yaw` | odrzucone | PASS |

Pomiar w locie vs przewidziane: **ε_FP = 0 potwierdzone empirycznie** (§I(−)). Jedyna zmierzona
rozbieżność wobec przewidywania — w fp_bg (ruch tła/tekstura) pojawia się `false_gate_frames` (fix1: 50
klatek jednoklatkowej admisji struktura∧MTI) których inwentarz R2 nie skwantyfikował co do LICZBY. **Nie
urosły w ENTRY** (filtr spójności czasowej `persist_m=3/persist_window=4` + DEADMAN je pochłania) → ε_FP
mimo to = 0. Wniosek: filtr klatkowy przepuszcza rzadkie pojedyncze klatki paralaksy, brama ENTRY (nie
klatka) je odrzuca. Zmiana projektowa Δ=1→3 / persist 2/3→3/4 z val1 była MECHANIZMOWA (baseline ruchu
celu 200 ms), nie strojeniem progu po fakcie.

### Prowieniencja parowania klatka↔attitude [A4]

`content_resid_median` per boot: fix1 **64.7 s**, fix2 **33.4 s**, fix3 **31.0 s** — RÓŻNE wartości, każda
STAŁA w obrębie boota. To STAŁY absolutny offset PER BOOT (O zamrożony w spokojnym oknie przed-YOLO, potem
reset timesync w fazie settle przesunął origin epoch↔sim o wielkość zależną od danego bootu). Zmienność
między-bootowa 31–65 s przy stałości WEWNĄTRZ-bootowej **potwierdza że to origin timesync danego bootu, nie
systematyczny błąd instrumentu**. **Nieszkodliwy dla instrumentu:** derotacja używa ROTACJI WZGLĘDNEJ Δq
między kolejnymi klatkami; obie klatki pobierają attitude z tym samym stałym biasem → Δq zachowane.
Potwierdzone przez ε_FP=0 (×3) i integralność coverage (gdyby parowanie było realnie 30–65 s krzywe,
derotacja byłaby śmieciem i MTI eksplodowałby FP — nie eksplodował na żadnym boocie). Dodatkowy dowód
zdrowia parowania w OKNIE FREEZE: init spread fix2 = 0.068 s, fix1 = ~0.07 s (ciasny) — freeze łapie parę
recv-bliską; dryf pojawia się DOPIERO po resecie timesync, już jako stały offset. [A4]: przemrożenie O po
settle (po ostatnim resecie timesync) wyzerowałoby rezyduum absolutne — odłożone, nie wpływa na werdykt.

---

## (Aneks-def) Definicje coverage (kod `mti_flight.py`)

- **coverage_seen** = frakcja ticków z boxem detektora struktury (YOLO). Detekcja klatkowa.
- **coverage_gate** = frakcja ticków gdzie `box ∧ central ∧ mti_ok` TA SAMA klatka. **Kryterium (+).**
- **coverage_locked** = frakcja ticków gdzie kanał trzyma lock (ZOH-age między detekcjami). Miara
  operacyjna, MIĘKSZA (mostkuje luki tolerancją wieku); NIE jest kryterium (+).
- **coverage_locked_post_entry** = locked liczone od pierwszego ENTRY. = 1.0 wszędzie.

---

## WERDYKT

**Bramka dwustronna: (−) PASS ε_FP=0 · (+) FAIL strict (coverage_gate < 0.8 na każdym zasięgu, ×3 booty).**

STOP z liczbami (SR-M4/SR-N4): dźwignie zaparkowane. Zdolność wykrycia jest szybka i pewna (ENTRY w
sekundach, `coverage_seen=1.0`, `coverage_locked_post_entry=1.0`), lecz KLATKOWA brama struktura∧MTI nie
osiąga zamrożonego progu 0.8 bo człon MTI jest przerywany w geometrii OBSERVE-motion. Rdzeń bezpieczeństwa
dowiedziony niezależnie od percepcji (R-M4, certy 6/6). Zwrot dźwigni (rozdzielczość → FOV → gimbal) lub
rewizja definicji (+) na `coverage_locked` — **wyłącznie decyzją Olgi**.

> **[KOREKTA R-3, 2026-08-16]** Rewizja definicji (+) **RATYFIKOWANA** przez Olgę jako `ANEKS_MTI_2`
> (ENTRY-once): (+) mierzone jako `coverage_entry_once` (LOCKED po admisji) ≥0.8, nie per-frame
> `coverage_gate`. „Człon MTI przerywany klatkowo" to atrybucja nieuprawniona z agregatów (koniunkcja
> logowana łącznie); rozstrzyga trace re-bramki. Wynik pomiaru: `RAPORT_MTI_REGATE.md`.
