# RAPORT_K1 — osłona GPS-denied vs natywny failsafe PX4, prosta 5 punktów, parowana

LiquidPatrol · noga K1 · PRE_K1 (RATYF. 22.08.2026) · seria domknięta 2026-08-27
przez ANEKS_K1-15..18 (+ INFRA-1/2, MAG-1/2). Agregat: `results/K1/K1_aggregate.json`.

## Werdykt (skrót)

**(±) PRZEWAGA ILOŚCIOWA BEZ NARUSZENIA** (§4). Na 4 sparowanych punktach z 5
(D4 wymaga ≥4/5, 0.65 ∧ 0.8 muszą sparować — spełnione): **breach_N = 0/4 ∧
breach_S = 0/4** — zarówno natywny failsafe PX4 pod utratą GNSS, jak i osłona
**zawierają** promień R_E = 32 m w KAŻDYM zmierzonym punkcie. Osłona ogranicza
wychylenie poza punkt denialu o **medianę Δx_exc = 2.494 m** (IQR 1.47,
pooled_std 0.905; mediana > pooled_std ⇒ przewaga istotna względem rozrzutu).
Roszczenie „ucieczki" natywnego PX4 **nie stoi** w tej geometrii SITL — degraduje
się do ilościowego: osłona wychyla mniej, ale obie konfiguracje mieszczą się w R_E.

## §I. Tabela — 5 punktów × 2 ramiona (booty ważne; sekwencje nav_state)

x_exc = wychylenie poziome poza punkt denialu [m]; r_max = maks. promień od home [m];
R_E = 32 m; wszystkie breach = False. nav_state: znaczniki `STAN@t_rel_denial[s]`.

| pt | ramię | run (ważny) | x_exc | r_max | t_refuse | t_td | breach | hab | wd |
|-----|----|-------------------|------:|------:|------:|-----:|:---:|:---:|:--:|
| 0.20 | N | N/p0_2/boot4 | 5.808 | 18.082 | — | 7.156 | False | VALID | 0 |
| 0.20 | S | S/p0_2/boot7 | 2.502 | 17.018 | 0.10 | 4.040 | False | VALID | 1 |
| 0.35 | N | N/p0_35/boot1 | 4.520 | 15.132 | — | 8.836 | False | VALID | 1 |
| 0.35 | S | S/p0_35/boot2 | 2.719 | 15.106 | 0.08 | 4.000 | False | VALID | 1 |
| 0.50 | N | N/p0_5/boot2 | 5.108 | 14.752 | — | 8.856 | False | VALID | 1 |
| 0.50 | S | S/p0_5/boot1 | 5.212 | 13.338 | 0.10 | 3.340 | False | VALID | 0 |
| 0.65 | N | N/p0_65/boot2 | 5.047 | 16.656 | — | 8.672 | False | VALID | 1 |
| 0.65 | S | S/p0_65/boot3 | 3.470 | 15.448 | 0.10 | 3.680 | False | VALID | 0 |
| 0.80 | N | N/p0_8/boot1 | 5.990 | 18.207 | — | 8.244 | False | VALID | 0 |
| 0.80 | S | S/p0_8/boot1 | 2.802 | 17.575 | 0.10 | 4.120 | False | VALID | 1 |

Sekwencje nav_state (mechanizm — RÓŻNICA ramion):
- **N (natywny):** `AUTO_LOITER → AUTO_PRECLAND → OFFBOARD → AUTO_LAND@+0.0 →
  DESCEND@+4.0 → OFFBOARD` — komenda land natywna WCHODZI w chwili denialu
  (δ=0), potem DESCEND z koastingiem pędu poziomego (stąd większe x_exc, dłuższe t_td).
- **S (osłona):** `AUTO_LOITER → AUTO_PRECLAND → OFFBOARD → DESCEND@+4.1 → OFFBOARD` —
  BEZ AUTO_LAND; osłona REFUSE(POS_DEGRADED) @ t_refuse ≈ 0.10 s → ścieżka D5
  (schodzenie), krótsze t_td (~4 s vs ~8 s N), mniejsze x_exc.

Mechanizm zawierania różny (N: natywny land+koasting; S: REFUSE→D5), skutek w R_E
ten sam (oba < 32 m). Osłona odpowiada **szybciej** (t_refuse 0.10 s) i schodzi
**wcześniej** (t_td ~4 s), stąd systematycznie mniejsze x_exc.

## §II. Werdykt wg §4 — z liczbami i identyfikatorami

Kryterium (±) z PRE_K1 §4: `breach_N = 0 ∧ breach_S = 0 ∧ mediana(Δx_exc) > pooled_std`.
Zmierzone (agregat na parach WAŻNYCH, `k1_aggregate` frozen; `K1_aggregate.json`):

- **n_pairs = 4** (0.20, 0.35, 0.65, 0.80); **UNPAIRED = 0.50** (dz = 0.972 m > 0.5, R3).
- **breach_N = 0, breach_S = 0** (oba ramiona, 4/4 par).
- **Δx_exc (N−S):** 0.20 → 3.306; 0.35 → 1.801; 0.65 → 1.577; 0.80 → 3.188.
- **mediana(Δx_exc) = 2.494 m**, IQR = 1.472, **pooled_std = 0.905 m** ⇒ mediana > pooled_std.
- **WERDYKT = (±)**; `k1_executable = True` (D4: 4/5, 0.65 ∧ 0.80 sparowane).

Brzmienie roszczenia (zastępuje wariant „ucieczki" z planszy CONTRAST): *„Pod czystą
utratą GNSS (EKF2_GPS_CTRL=0), na 4 sparowanych punktach prostej, zarówno natywny
failsafe PX4, jak i osłona P2-ε zawierają dron w R_E = 32 m (0 naruszeń na oba ramiona).
Osłona ogranicza wychylenie poza punkt denialu o medianę 2.494 m (IQR 1.47) względem
natywnego PX4, reagując w 0.10 s i schodząc o ~4 s wcześniej."* Plansza CONTRAST traci
etykietę „natywny ucieka" — zostaje różnica wychylenia z jawną adnotacją, że OBIE
konfiguracje zawierają.

## §III. Erratum „42 m" (odsyłacz PRE_K1 §0)

Asercja „AUTO.LAND ucieka na 42 m" (RAPORT_K1_AUDIT.md, 2bd76d9) NIE potwierdziła się
pomiarem: w 4/4 sparowanych punktach natywne ramię N zawiera w R_E = 32 m (max
r_max_N = 18.207 m @ 0.80), zero naruszeń. „42 m" pozostaje nieodtworzone (SR-K6:
brak trace/ulog źródła asercji) — raport zastępuje ją zmierzonym r_max_N ≤ 18.2 m.

## §IV. Zagrożenia wierności (PRE_K1 §5) + noty uczciwości

Zagrożenia z góry (§5):
- **Quasi-idealne IMU SITL:** w realu dryf większy ⇒ obie liczby rosną; kierunek ryzyka
  gorszy dla N (dłuższy pościg za gorszą estymatą), neutralny dla S (hamuje niezależnie
  od estymaty). Nie twierdzę „HIL potwierdzi" — podaję kierunek.
- **Koasting w DESCEND** zależy od modelu oporu gz x500 — liczba x_exc nieprzenośna,
  mechanizm (N koastinguje pęd, S schodzi wcześniej) przenośny.
- **δ = 0** najkorzystniejsze dla N (land wchodzi zanim xy_valid zgaśnie); δ = 10 s to
  osobny tryb (§V, poza kryterium).
- **Denial = EKF2_GPS_CTRL=0** ≡ utrata danych dla flag EKF (audyt §4b); scope = clean
  loss, nie spoofing.

Noty uczciwości serii (MAG-2 N4):
1. **Pary 0.20 i 0.35 przeleciały pod RÓŻNYMI, pełznącymi wartościami CAL_MAG** (higiena
   CAL wdrożona dopiero od wznowienia 0.65, commit 5c0120a) — sparowały jednak na
   ZMIERZONEJ kinematyce wstrzyknięcia (dr/dv/dh/dz w tolerancji P2), nie na stanie
   kalibracji; od wznowienia WSZYSTKIE booty lecą identyczny baseline CAL (YOFF −0.13694),
   co czyni pary 0.65/0.80 lepiej porównywalnymi wewnętrznie niż 0.20/0.35.
2. **COM_ARM_MAG_STR = 2 czyni check siły mag formalnie opcjonalnym**, a fail-booty 0.65
   współwystępowały z faultami gyro/height (MAG-1: mag 58× dominuje preflight, gyro 20×,
   height 6×) — NIE dowodzę więc, że creep CAL był JEDYNYM blokerem arm; dowodzę, że był
   korzeniem DOMINUJĄCEGO objawu („Strong magnetic interference"), zdejmowanym higieną
   (mag-fail = 0 w 5/5 bootach lotnych po wdrożeniu: S 0.65 b3, N 0.65 b1/b2, S/N 0.80 b1).

Nota `wd-asym` (H3): 3 z 4 par mają dokładnie jedno ramię z reinitem watchdoga EKF2
(0.20, 0.65, 0.80) — reinit jest PREFLIGHT-ONLY (przed arm, segment roszczenia
denial→touchdown wolny od przyrządu), NIE wchodzi do PAIR_TOL i NIE zmienia `paired`;
etykieta oznacza asymetrię stanu początkowego EKF, nie różnicę w locie.

## §V. Informacyjne (poza kryterium)

- **0.50 UNPAIRED** (slot D4): N boot2 × S boot1 ważne, ale dz = 0.972 m > 0.5 (R3) —
  wysokości wstrzyknięcia rozjechane; wykluczone z kryterium, x_exc obu ~5.1–5.2 m
  (gdyby sparowane, Δ ≈ −0.10, w kierunku NULL — ale niemierzalne bez pary). N boot3/4
  i S boot3 przy 0.50 = env-fail (habitat/mag), nie liczone.
- **Historia odblokowania (meta):** K1 był STOP na cap B1 (env-fail arm) → INFRA-1/2
  ustaliły zatrzask biasu gyro/fault pionu, mitygacja = watchdog EKF2 preflight-only;
  MAG-1/2 ustaliły creep CAL_MAG, mitygacja = higiena baseline przed bootem. Dopiero po
  obu seria 0.20→0.80 przeszła. Obie mitygacje są PRZED-lotowe; sędzia (`k1_judge.py`
  sha frozen), osłona (`r01/shield.py`) i piny (`r03/config.py`, `r03/gate_run_r03.py`)
  NIETKNIĘTE we wszystkich bootach (`git diff HEAD` pusty, shield_pins 3/3 MATCH).
- δ = 10 s (land po zgaśnięciu xy_valid) NIE wykonany — pozostaje jako opisany wariant §5.

## Prowieniencja

Agregat: `k1_aggregate` (frozen), `results/K1/K1_aggregate.json`. Booty ważne per §I.
Kryterium §4 dosłowne (D4 RATYF. 22.08). Sędzia `k1_judge.py` frozen. push = Olga.
