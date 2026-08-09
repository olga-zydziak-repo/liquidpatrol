# PRE_R02C — tor C: „detection uplift" (recon → PRE → STOP)

Data: 2026-08-09. Reżim: **recon nieinwazyjny → pre-rejestracja → STOP** (osobny cykl, dyscyplina A2).
Geneza: `RAPORT_R02.md` §II (live-fed OTWARTY, przyczyna źródłowa = kadrowanie kamery §3f) + §III-bis
(prowieniencja przyrządu). Cel: podnieść detekcję w locie do progu operacyjnego przy ε_FP=0, BEZ
strojenia zamrożonych kryteriów. **Wszystkie liczby czasowe z etykietą przyrządu** (`nav`/`mav`/`monotonic_local`).

Zasada nadrzędna: `θ_conf` **nigdy nie obniżany**. Charakteryzacja **wyłącznie w locie** (§III-bis:
statyczne sweepy tracą status źródła progów — attitude zmienia kadrowanie). Wynik negatywny = wynik (SR-5).

---

## 1. RECON (R1–R4) — wykonany, nieinwazyjny

### R1 — dźwignia 0 (celowanie kamery): 0a vs 0b vs szersze FOV
Fakty z gz (`PX4-Autopilot/Tools/simulation/gz/models`):
- **Kamera `mono_cam`:** sensor `imager`, `horizontal_fov=1.74 rad` (~99.7°), 640×480 → **V-FOV ~83°**
  (pinhole: `2·atan(0.75·tan(0.87))=1.453 rad`). Oś optyczna = **+X `camera_link`**.
- **Montaż `x500_mono_cam`:** include `mono_cam` @ pose `.12 .03 .242 0 0 0` (ZERO rotacji) + **`CameraJoint`
  type=fixed** → kamera **sztywno do kadłuba, forward-poziomo**. Wariant `x500_mono_cam_down` = ta sama
  kamera, include-pose `0 0 .10 0 1.5707 0` (pitch 90° w dół) → **oś optyczna = rotacja w include-pose**.
- **Gotowy `gimbal` (CGO3) + `x500_gimbal`:** 3 jointy revolute (yaw/roll/pitch) + `camera_imu` feedback +
  `horizontal_fov=2.0`, sterowane **`gz-sim-joint-position-controller-system`** (PID per joint, oś pitch
  `cgo3_camera_joint` limit −2.36..0.785 rad, cmd przez topic gz).

**Ocena dźwigni:**
| Wariant | Wykonalność | Koszt | Co koryguje |
|---|---|---|---|
| **0a** statyczny pitch-offset | **TRYWIALNA** — nowy model = zmiana rotacji w include-pose (jak `_down`) | zero runtime | BIAS pitchu (nie jitter) |
| **0b** gimbal attitude-comp | **ŚREDNIA** — użyć `x500_gimbal` + node stabilizujący `cmd_pitch=−body_pitch` (attitude 20 Hz) ~30 lin | node + joint PID + integracja sensora imager na gimbalu | BIAS **oraz** jitter (utrzymuje elewację niezależnie od pitchu) |
| **szersze V-FOV** | **TRYWIALNA** — `horizontal_fov` ↑ w `mono_cam` | **KOSZT: mniej pikseli/° = mniejszy cel = KRÓTSZY zasięg** (mierzalny) | poszerza okno kątowe, nie centruje |

**LUKA RECONU (krytyczna dla wyboru 0a/0b):** `exec_lib.att()` ekstrahuje **tylko yaw** (linia 159) —
**pitch/roll NIGDY nie logowane**. Atrybucja §3f szła z KADRU (intruz nieobecny), NIE z pomiaru pitchu.
Arytmetyka: przy V-FOV 83° (±41.6°) intruz elew +12–16° klipuje się z góry dopiero przy **pitch-down
> ~26°** — dużo jak na zawis. Więc albo (i) OBSERVE-motion daje duży pitch, albo (ii) geometria sondy
była inna. **Magnituda i JITTER pitchu = NIEZMIERZONE** → determinują 0a (bias) vs 0b (jitter). **Build
MUSI to zmierzyć PIERWSZE** (rozszerzenie att() o pitch/roll — dwuzadaniowe z R2).

### R2 — dźwignia 2 (MTI/ruch): separator ortogonalny do conf
- **Klatki:** `mono_cam update_rate=15 Hz` (surowy topic); detektor przetwarza @1 Hz. MTI potrzebuje par
  klatek 15 Hz (nie kadencji 1 Hz).
- **Ego-motion:** yaw @20 Hz jest; **roll/pitch wymagają rozszerzenia att()** (dane już płyną w
  `attitude_euler`, trywialne). Kompensacja: warp klatki[t−1]→[t] z delty attitude (homografia rotacyjna;
  translacja/paralaksa trudniejsza), różnica, próg residuum = regiony ruchome.
- **Koszt:** warp+diff per klatka @15 Hz (tani CPU/numpy), nowy węzeł/stopień.
- **ε_FP:** MTI flaguje KAŻDE residuum (niedokompensowana paralaksa nad teksturą gruntu, trawa, cienie) →
  **z założenia PODNOSI ε_FP**. Więc MTI = **AND-gate z kandydatem** (conf/strukturalny ∧ ruch-spójny),
  NIE samodzielny. Wartość ∝ (ruch względny intruza) / (residuum kompensacji): **hover intruz → słaby MTI**;
  **OBSERVE-motion drona → duże ego-motion → duże residuum**. Separator ortogonalny do conf — ratuje gdy
  sygnał≤szum, ale tylko dla ruchomego celu przy dobrej kompensacji.

### R3 — re-derywacja N dead-mana: rozkład stalli pętli live-fed [POMIAR]
`gate_run_r02._pub` instrumentowany; G1 live-fed (detektor W PĘTLI), **kanał `monotonic_local`**, N=3088:
- **p50=0.0506, p95=0.0512, p99=0.0515, MAX=0.0529 s = 1.06 ticka @20 Hz**.
- **stalli >4 ticków (0.20 s): 0; >6 ticków (0.30 s): 0.**

**WNIOSEK (obala wcześniejsze założenie):** pętla decyzyjna jest **twardo związana ~1 tickiem** — NIE
stalluje pod kontencją, bo **detektor to OSOBNY proces ROS2**, a pętla tylko czyta kanał (subskrypcja).
Założenie „pętla stalluje ~1 s" było NIEZMIERZONE i BŁĘDNE. **N re-derywowalne: N ≥ margines × max_stall.
Przy max 1.06 ticka: N=3 (0.15 s) daje ~3× margines; N=4 (0.20 s) ~4×.** Wtedy budżet zombie =
COM_OF_LOSS_T (~1.30 s `nav`) + N·tick → **N=3 ⇒ ~1.45 s ∈ okno 0.9–1.5**. ZASTRZEŻENIE: pomiar pod
patrolem; **re-potwierdzić pod OBSERVE-motion** (inna dynamika) przed zamrożeniem N.

### R4 — re-derywacja θ_conf z chmur w locie [protokół + baseline]
- **Baseline w locie (bieżący, PRZED fixem):** szum G1 live-fed `noise_max=0.0544` (n=554) ≪ θ_conf 0.1635;
  **sygnał w locie 0.045–0.081** (G2, §3f) — **PONIŻEJ szumu → conf-floor ZAPADŁ SIĘ w locie**.
- **Protokół post-fix (build):** po fixie kadrowania (R1) — re-charakteryzacja OBU chmur **wyłącznie w
  locie**, na zasięgu operacyjnym: (a) szum (pusta scena, lot), (b) sygnał (intruz w kopercie, lot).
  θ_conf' = środek przerwy JEŚLI istnieje. **Jeśli sygnał ≤ szum nawet po fixie → conf-floor PADA, ENTRY
  staje na separatorze RUCHU (R2) — DOPUSZCZALNY wynik, nie porażka** (decyzja Olgi).

---

## 2. DŹWIGNIE — kolejność (z reconu)

1. **0b (gimbal attitude-comp)** — czoło, JEŚLI build potwierdzi JITTER pitchu; **0a (statyczny offset)**
   jeśli build pokaże tylko BIAS (tańsze). Decyzja gated pomiarem pitchu (R1 luka).
2. **Szersze V-FOV** — wariant pomocniczy z **mierzonym kosztem zasięgu** (nie zamiast celowania).
3. **MTI (R2)** — separator ortogonalny, AND-gate; wchodzi gdy conf sam nie domyka (sygnał≤szum po fixie).
4. **R2-alt (detektor jednoklasowy) — OSTATNIA**, projekt anty-cyrkularny (§5).

---

## 3. KRYTERIUM DWUSTRONNE — ZAMROŻONE PRZED POMIAREM

**Wyprowadzenie X (z reconu):** koperta operacyjna OBSERVE — `D_safe=5.32` poziomo, **3D-mid = 7 m**
(środek koperty A7, ZAMROŻONE w `config_r02`). Detekcja musi działać do dystansu standoff, by pozyskać i
śledzić intruza. Statyczny zasięg efektywny ~10 m (sweep) daje zapas; w locie ≤ statyczny — **lot jest testem**.

> **KRYTERIUM (zamrożone):**
> - **(+) Zasięg skuteczny w locie ≥ X = 7 m**: intruz w kopercie na 3D ≤7 m → **coverage ≥ 0.8** klatek z
>   detekcją przechodzącą admisję ENTRY (conf≥θ_conf ∧ central ∧ k=3) **LUB** separator ruchu (R2), w locie.
> - **(−) ε_FP = 0**: pusta scena w locie → 0 fałszywych ENTRY (≤ `EPS_FP_PER_MIN`=0).
> - Oba **W LOCIE** (nie statycznie). Liczby czasowe etykietowane przyrządem.

Zamrożone przed pomiarem build. Rewizja X **tylko** nazwaną eskalacją (nie strojeniem pod pozytyw).
`θ_conf` bez zmian; jeśli sygnał≤szum → ENTRY na R2 (dopuszczalne), nie obniżanie θ_conf.

---

## 4. PLAN BUILD (po ratyfikacji PRE; kolejność)

1. **Pomiar attitude (domknięcie luki R1):** rozszerz `att()` o pitch/roll (dane płyną). Zmierz rozkład
   pitchu w **zawisie ORAZ OBSERVE-motion**, skoreluj z pozycją intruza w kadrze → **potwierdź mechanizm
   §3f ilościowo** i rozstrzygnij **0a (bias) vs 0b (jitter)**. (Dwuzadaniowe: te same pitch/roll zasilają R2.)
2. **Fix kadrowania** (0a lub 0b wg kroku 1). Wariant szersze-FOV z mierzonym kosztem zasięgu jeśli potrzebny.
3. **Re-char θ_conf w locie (R4):** obie chmury, zasięg operacyjny, wyłącznie lot.
4. **MTI (R2)** jeśli krok 3 pokaże sygnał≤szum: warp+diff @15 Hz z kompensacją pitch/roll/yaw, AND-gate.
5. **Re-derywacja N dead-mana (R3):** re-potwierdź rozkład stalli pod OBSERVE-motion → zamroź N (kandydat
   3–4 ticki), zaktualizuj budżet zombie i P1/P2 (założenie żywotności, [A4]→zmierzone).
6. **Bramka dwustronna** (§3) w locie; **R2-alt tylko jeśli 1–5 nie domkną** (§5).

---

## 5. R2-alt (detektor jednoklasowy) — OSTATNIA dźwignia, anty-cyrkularna

Uruchamiana tylko po wyczerpaniu 0b/0a/FOV/MTI. Projekt **anty-cyrkularny**: trening na **INNEJ scenie i
teksturach** niż bramka (inny świat gz / inne tło / inny render), walidacja na scenie bramki — by uniknąć
uczenia się artefaktów konkretnej sceny. Jednoklasowy („drone"), charakteryzacja w locie. Osobny PRE.

---

## 6. RYZYKA / ESKALACJE (nazwane)

- **Pitch mały (bias, nie jitter)** → 0a wystarcza; jeśli §3f nie odtworzy się ilościowo (intruz jednak w
  kadrze przy zmierzonym pitchu) → re-atrybucja przyczyny (nie brnięcie w gimbal). **Nazwany trigger: krok 1.**
- **Sygnał≤szum po fixie** → conf-floor pada, ENTRY na MTI (R2). Jeśli MTI też słaby (hover intruz) →
  R2-alt. Dopuszczalny łańcuch, nie porażka.
- **MTI podnosi ε_FP** ponad 0 → AND-gate ostrzejszy / MTI tylko jako potwierdzenie kandydata, nie źródło.
- **N pod OBSERVE-motion gorszy niż patrol** → N konserwatywne; jeśli budżet zombie wyjdzie z okna →
  raportować osobno (jak §III), nie poszerzać okna.

---

## STOP

Recon domknięty (R1–R4), kryterium dwustronne zamrożone, plan build i eskalacje nazwane. **STOP na
ratyfikacji PRE przez Olgę** (dyscyplina recon→PRE→STOP). Push i decyzja o wejściu w build = Olga.
Dowody reconu: `results/R02/gate_live/R3_STALL_G1.jsonl`, modele gz (ścieżki w §1).
