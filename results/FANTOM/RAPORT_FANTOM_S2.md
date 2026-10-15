# RAPORT_FANTOM_S2 — KAMPANIA 12×{B, V2} pod net_fantom (ANEKS_FANTOM-1 §4) — STOP-FANTOM2

Wykonawca · 15.10.2026 · ARCH-1 = ANEKS_FANTOM-1.md VERBATIM w korzeniu (commit
6f955d59, pierwszy w sesji). Kwarantanna K1 FROZEN e435ed7e (oba ramiona
CONTROLLER=net_fantom). Liczby pod zdaniami ZAMROŻONYMI (PRE_FANTOM §5 — dwie
warstwy, bez mieszania); WERDYKT FORMALNY = ANEKS_FANTOM-2.

## §1. Wyniki główne (liczby; zdania zamrożone do aplikacji w ANEKS)

**WARSTWA POZYCJI (N6):** przechodzi **3/6** (c01_s01 ✓, c08_s02 ✓, c06_s04 ✓;
c05_s02 ✗, c08_s03 ✗, c08_s04 ✗) · **regresje = 1** (c10_s02 — para wspólnie
ważna, B ✓, V2 ✗, w AKW V2 ✓). Progi zamrożone: SUKCES (≥5/6 ∧ regresje ≤1) — NIE
zaszedł; ŚMIERĆ-FANTOM (≤2/6 ∨ regresje ≥3) — NIE zaszła ⇒ **STREFA OPISOWA
z obowiązkową dekompozycją per epizod i per regresja (§3)**.

**WARSTWA SIATKI:** 48/48 par w siatce, **n_common = 40 (dokładnie próg; STOP
n_common<40 NIE zaszedł)**, pass(B) = 38, pass(V2) = 31, **Δ_new2 = 7** — strefa
opisowa progów PRE_2A §4 (≤4 / ≥10 / 5–9); zgodna z przewidywaniem desku recon (~6)
i wnętrzem przedziału P-F-3 [5,8]. „V2 lepszy ≥3" nie zachodzi. 46 sceno-świeże:
n_common 39, Δ 6.

**S-BEZP: breach 0 we wszystkich 27 bootach kampanii; REFUSE 0 / gałęzie puste;
stop_now false wszędzie.** Bezpiecznik modu: bez tripa (admisje ślepych 96.3–98.9%
we wszystkich 14 bootach V2, nigdy zero). Budżet: launches **27/27** (co do sztuki),
booty nogi **28/≤30**.

## §2. Reżim wykonania + odchylenia JAWNE (środowiskowe — pełna chronologia)

Narzędzia-kopie (sha w FREEZE_FANTOM S2): driver `fantomS2_boot.sh` d77fbf40
(z poprawką kosmetycznego printu zleconą ANEKS §1b), orkiestrator
`fantomS2_campaign.sh` 27b97e44 (bezpiecznik modu verbatim), parowanie
`fantom_pairs.py` f236c136. Booty 2–28, rundy r1–r12, rotacja naprzemienna,
manifesty 1. klasy (blok fantom: fantom_scan_sha256 e435ed7e na żywo ×27, q_events).

1. **Degradacja środowiska (rundy 1–3):** dsim_dwall epizodów 0.876–0.927 wobec
   0.95–0.97 w AKW S3 — seria nieważności (r1_B 2/4, r1_Br 3/4, r1_V2 2/4,
   r1_V2r 2/4, r2_V2 3/4, r2_V2r 2/4, r3_B 2/4, r3_V2 3/4), zapasy wyczerpane 3/3.
   DIAGNOZA Z DANYCH (bez dotykania frozen metryki): fizyka symulacji szła 1.0
   (trace gt mono-vs-sim; przystoje ≤0.45 s jak w AKW), a spadek siedział
   w PRÓBNIKU RTF — pary sąsiednich próbek rtf_stream z wall +≈3 s przy sim +0.04 s
   (próbnik odstawiany od CPU skleja stary sim z nowym wall); sędzia liczy
   dsim_dwall z tych próbek. Przyczyna: host w aktywnym użyciu + stan hosta po
   porannym restarcie (turbo nieaktywne — benchmark 1-rdzeniowy 33 M/s). Działania:
   **3× PAUSE na granicach rund** (mechanizm drivera), sonda automatyczna (mediana
   dsim bootu <0.93 ⇒ PAUSE), **restart hosta przez Olgę** po rundzie 3.
2. **Po restarcie hosta (rundy 4–12): środowisko ZDROWE** — dsim 1.012–1.046
   wszędzie, nieważności epizodów ZERO. Nowa obserwacja narzędziowa: **trzecia moda
   kadencji percepcji 5.10 Hz** (dt p50 0.196; 5 bootów V2) obok znanych 7.58/14.71
   — bez szkody (admisje 96.3–98.3%, E2E p95 ≤0.104; kadencja = telemetria opisowa
   per ANEKS_AKW-1 §2; bezpiecznik modu działa na admisjach, nie na Hz).
3. **Infra-pad r4_B:** spawn intruza „Service call timed out" (pierwszy boot B po
   restarcie hosta) ⇒ rc=3, zero epizodów, model_in_state=False — klasa narzędziowa,
   nie lotna; bez zapasów ⇒ strata 4 par rundy 4.
4. **Pary stracone: 8/8 limitu** — 4 środowiskowe przed restartem (c03_s01,
   c08_s01, c09_s01, c11_s01 — nieważność obu prób strony) + 4 z infra-padu r4_B
   (c00_s02…c03_s02). Finalne n_common = 40 = dokładnie próg twardego STOPu —
   kampania rozstrzygnięta NA STYK, bez naruszenia żadnego twardego STOPu.
5. Wszystkie przerwania wyłącznie na granicach rund (3× PAUSE + 1 pad sesji hosta
   przy restarcie — wznowienia per wznawialność, zero bootów połowicznych); raporty
   częściowe prowadzone bez interpretacji Δ (liczniki).

## §3. Dekompozycje prereg (ANEKS_FANTOM-1 §3/§4.6 — obowiązkowe)

### N6 per epizod, per PODKLASA i per WARIANT fantomu@t0

| epizod N6 | boot | podklasa (recon) | fantom@t0 W TEJ KAMPANII | q_exit | akwizycja t_entry [s] | D6 | ślepota AKW (odniesienie) |
|---|---|---|---|---|---|---|---|
| c01_s01 | r1_V2 | poprzedni-epizod | **ŻYWY** (d=20.7, age 0.13) | C@3.04 (trzymany) | 8.08 | **✓** | 22.3 s, FAIL |
| c05_s02 | r5_V2 | poprzedni-epizod | **ŻYWY** (d=18.4, age 0.55) | C@3.04 (trzymany) | 6.60 | ✗ | 21.9 s, FAIL |
| c06_s04 | r11_V2 | poprzedni-epizod | **ŻYWY** (d=27.1, age 0.38) | C@3.02 (trzymany) | 9.88 | **✓** | 9.5 s, FAIL |
| c08_s02 | r6_V2 | parking-świata | **brak** (lock nie zaszedł) | A@2.33 | 3.45 | **✓** | 26.8 s, FAIL |
| c08_s03 | r9_V2 | parking-świata | **brak** | C@3.01 | 5.01 | ✗ | 14.7 s, FAIL |
| c08_s04 | r12_V2 | parking-świata | **brak** | C@3.04 | 5.16 | ✗ | 20.5 s, FAIL |

- **Podklasa poprzedni-epizod: mechanizm ZASZEDŁ w wariancie ŻYWYM 3/3** — ryzyko
  otwarte ANEKS_FANTOM-1 §3 („żywy fantom poprzedniego epizodu nielatany")
  **ZAMKNIĘTE POMIAREM: kwarantanna trzyma żywe fantomy 3/3** (wyjścia C po
  predykacie, zero konsumpcji fantomu), akwizycje 6.6–9.9 s (vs 9.5–22.3 s ślepoty
  w AKW). Konwersja D6 2/3; porażka c05_s02 = pościg po akwizycji (6.6 s ≪ t_A).
- **Podklasa parking-świata: fantom NIE WYSTĄPIŁ w kampanii** (0/3 locków@t0
  w bootach z c08 jako pierwszym epizodem; w AKW występował — loteria 1–4 freshów
  przedstartowych nie zaszła w tych bootach po restartach hosta). Czysty start +
  kwarantanna dały akwizycje 3.4–5.2 s; D6 1/3 — obie porażki pościgowe (v=1.0).
  Mechanizm startowy w tej podklasie nie był więc testowany w locie kampanią;
  pozostaje dowód smoke S1 (c08_s02 ŻYWY parking → B@0.88 → D6 ✓).
- **Sygnatura wspólna 3 porażek N6: wczesna akwizycja (5.0–6.6 s) + przegrany
  POŚCIG za celem** — dokładnie rezyduum pościgowe v=1.0/0.5 znane z AKW
  (pozycja POŚCIG-V1 w katalogu), nie mechanizm startu.

### Regresje (nowe FAIL na parach PASS-w-AKW, wspólnie ważnych): **1**

| para | B | V2 | w AKW | mechanizm |
|---|---|---|---|---|
| c10_s02 | ✓ | ✗ | V2 ✓ | v=1.0, b180; akwizycja wczesna (t_entry 5.0), przegrany pościg — zmienność pościgu na granicznej komórce (c10 w AKW 2/4), nie koszt kwarantanny (q_exit C@3.0 = czysty start jak w AKW-przebiegu tej pary) |

### Siatka: bearing / prędkość / split / dryf B

- bearing (na parach wspólnych): Δ = 2/1/2/2 (b0/b90/b180/b270) — PŁASKA, geometria
  trzymana (wzór AKW).
- v_intr: **Δ = 0 / 1 / 6** (v=0: 11/11 vs 11/11; v=0.5: 16 vs 15; v=1.0: B 11/13,
  V2 5/13) — **całe rezyduum ponownie w celu szybkim**, spójnie z AKW (Δ=9/12
  w v=1.0) i z kanonem AKW („skan nie wystarcza na cel szybki").
- split: TRAIN/VAL/TEST bez anomalii (szczegół w fantom_pairs.json).
- **Dryf B:** pass(B) = 38/40 common (95.0%) vs AKW 46/48 (95.8%) — równoważny;
  B-FAILe: c09_s03, c11_s02 (obie v=1.0; w AKW padały c09_s02, c11_s02 — ten sam
  pas trudności). Lista C-exitów na B: kwarantanna wychodziła C (koszt +3 s)
  zgodnie z deskiem T2 — bez wpływu na wynik (pass(B) utrzymane); regres <44-ekwiw.
  nie zaszedł ⇒ podejrzliwość wobec kwarantanny na wyroczni NIE aktywowana.

### ΔΔ (zawsze z kwalifikatorem kampanii)

Δ_new2 = 7 vs Δ_new = 12 (AKW S3) vs Δ = 34 (DET S4) — trzy kampanie, ten sam
habitat/siatka/progi; porównania wyłącznie z kwalifikatorem (różne sesje, w tym
różne stany hosta; n_common 40 vs 48 vs 48).

## §4. Telemetria per boot V2 i per epizod

Mody kadencji (14 bootów V2): SZYBKI 14.71 Hz ×2 (r1_V2, r2_V2r), WOLNY 7.58 Hz ×7,
WOLNY **5.10 Hz ×5** (r4, r6, r8, r9, r10 — nowa moda po restarcie hosta; nota §2.2).
Admisje ślepych @FOV per boot: 96.3–98.9% — pasmo AKW utrzymane. Kompletna
telemetria per epizod (fantom@t0 żywy/martwy/brak/lock-real + d_spawn + age@t0,
q_exit powód/czas, t_entry, ważność): `camp/fantomS2_telemetry.json`; zdarzenia
kwarantanny per boot w manifestach (q_events) i `fantom_qlog.jsonl`.

### Tabela per epizod V2 (boot, mod, ważność, fantom@t0, q_exit, t_entry, D6)

| boot | mod | epizod | ważny | fantom@t0 | d_spawn | q_exit | t_entry | D6 |
|---|---|---|---|---|---|---|---|---|
| r1_V2 | SZYBKI (14.71 Hz) | c00_s01 | ✓ | brak | — | A@2.14 | 4.88 | ✓ |
| r1_V2 | SZYBKI (14.71 Hz) | c01_s01 | ✓ | żywy | 20.7 | C@3.04 | 8.08 | ✓ |
| r1_V2 | SZYBKI (14.71 Hz) | c02_s01 | ✗ | brak | — | C@3.04 | 12.556 | ✓ |
| r1_V2 | SZYBKI (14.71 Hz) | c03_s01 | ✗ | brak | — | C@3.05 | 15.564 | ✓ |
| r1_V2r | WOLNY (7.58 Hz) | c00_s01 | ✗ | żywy | 17.1 | B@0.97 | 3.628 | ✓ |
| r1_V2r | WOLNY (7.58 Hz) | c01_s01 | ✓ | żywy | 21.2 | C@3.0 | 8.176 | ✓ |
| r1_V2r | WOLNY (7.58 Hz) | c02_s01 | ✓ | brak | — | C@3.0 | 13.008 | ✓ |
| r1_V2r | WOLNY (7.58 Hz) | c03_s01 | ✗ | brak | — | C@3.0 | 17.176 | ✓ |
| r2_V2 | WOLNY (7.58 Hz) | c04_s01 | ✓ | brak | — | A@0.05 | 8.544 | ✓ |
| r2_V2 | WOLNY (7.58 Hz) | c05_s01 | ✓ | żywy | 23.6 | C@3.0 | 6.74 | ✓ |
| r2_V2 | WOLNY (7.58 Hz) | c06_s01 | ✗ | brak | — | C@3.05 | 10.052 | ✓ |
| r2_V2 | WOLNY (7.58 Hz) | c07_s01 | ✓ | żywy | 14.8 | C@3.04 | 9.476 | ✓ |
| r2_V2r | SZYBKI (14.71 Hz) | c04_s01 | ✓ | brak | — | A@0.08 | 9.256 | ✓ |
| r2_V2r | SZYBKI (14.71 Hz) | c05_s01 | ✗ | żywy | 23.6 | C@3.0 | 6.732 | ✓ |
| r2_V2r | SZYBKI (14.71 Hz) | c06_s01 | ✓ | brak | — | C@3.0 | 9.908 | ✓ |
| r2_V2r | SZYBKI (14.71 Hz) | c07_s01 | ✗ | żywy | 14.8 | C@3.05 | 0.0 | ✓ |
| r3_V2 | WOLNY (7.58 Hz) | c08_s01 | ✓ | brak | — | A@1.28 | 2.772 | ✓ |
| r3_V2 | WOLNY (7.58 Hz) | c09_s01 | ✗ | żywy | 13.8 | C@3.05 | 5.2 | ✓ |
| r3_V2 | WOLNY (7.58 Hz) | c10_s01 | ✓ | brak | — | C@3.0 | 5.056 | ✓ |
| r3_V2 | WOLNY (7.58 Hz) | c11_s01 | ✓ | żywy | 16.4 | C@3.0 | 5.072 | ✗ |
| r4_V2 | WOLNY (5.10 Hz) | c00_s02 | ✓ | brak | — | C@3.02 | 7.244 | ✓ |
| r4_V2 | WOLNY (5.10 Hz) | c01_s02 | ✓ | żywy | 21.3 | C@3.03 | 8.476 | ✓ |
| r4_V2 | WOLNY (5.10 Hz) | c02_s02 | ✓ | brak | — | C@3.04 | 13.42 | ✓ |
| r4_V2 | WOLNY (5.10 Hz) | c03_s02 | ✓ | brak | — | C@3.0 | 16.072 | ✓ |
| r5_V2 | WOLNY (7.58 Hz) | c04_s02 | ✓ | brak | — | A@2.65 | 4.436 | ✓ |
| r5_V2 | WOLNY (7.58 Hz) | c05_s02 | ✓ | żywy | 18.4 | C@3.04 | 6.6 | ✗ |
| r5_V2 | WOLNY (7.58 Hz) | c06_s02 | ✓ | brak | — | C@3.03 | 9.56 | ✓ |
| r5_V2 | WOLNY (7.58 Hz) | c07_s02 | ✓ | żywy | 18.1 | C@3.03 | 9.472 | ✓ |
| r6_V2 | WOLNY (5.10 Hz) | c08_s02 | ✓ | brak | — | A@2.33 | 3.448 | ✓ |
| r6_V2 | WOLNY (5.10 Hz) | c09_s02 | ✓ | brak | — | C@3.03 | 5.136 | ✗ |
| r6_V2 | WOLNY (5.10 Hz) | c10_s02 | ✓ | brak | — | C@3.04 | 5.008 | ✗ |
| r6_V2 | WOLNY (5.10 Hz) | c11_s02 | ✓ | brak | — | C@3.03 | 5.204 | ✗ |
| r7_V2 | WOLNY (7.58 Hz) | c00_s03 | ✓ | brak | — | C@3.05 | 7.436 | ✓ |
| r7_V2 | WOLNY (7.58 Hz) | c01_s03 | ✓ | żywy | 21.2 | C@3.04 | 9.016 | ✓ |
| r7_V2 | WOLNY (7.58 Hz) | c02_s03 | ✓ | brak | — | C@3.04 | 12.756 | ✓ |
| r7_V2 | WOLNY (7.58 Hz) | c03_s03 | ✓ | brak | — | C@3.01 | 16.056 | ✓ |
| r8_V2 | WOLNY (5.10 Hz) | c04_s03 | ✓ | żywy | 17.2 | B@1.4 | 3.452 | ✓ |
| r8_V2 | WOLNY (5.10 Hz) | c05_s03 | ✓ | brak | — | C@3.04 | 7.06 | ✓ |
| r8_V2 | WOLNY (5.10 Hz) | c06_s03 | ✓ | brak | — | C@3.04 | 9.628 | ✓ |
| r8_V2 | WOLNY (5.10 Hz) | c07_s03 | ✓ | brak | — | C@3.04 | 9.988 | ✓ |
| r9_V2 | WOLNY (5.10 Hz) | c08_s03 | ✓ | brak | — | C@3.01 | 5.008 | ✗ |
| r9_V2 | WOLNY (5.10 Hz) | c09_s03 | ✓ | żywy | 25.2 | C@3.05 | 0.04 | ✓ |
| r9_V2 | WOLNY (5.10 Hz) | c10_s03 | ✓ | brak | — | C@3.04 | 5.352 | ✗ |
| r9_V2 | WOLNY (5.10 Hz) | c11_s03 | ✓ | brak | — | C@3.01 | 4.908 | ✗ |
| r10_V2 | WOLNY (5.10 Hz) | c00_s04 | ✓ | brak | — | A@1.91 | 4.632 | ✓ |
| r10_V2 | WOLNY (5.10 Hz) | c01_s04 | ✓ | żywy | 21.5 | C@3.0 | 8.56 | ✓ |
| r10_V2 | WOLNY (5.10 Hz) | c02_s04 | ✓ | brak | — | C@3.04 | 12.016 | ✓ |
| r10_V2 | WOLNY (5.10 Hz) | c03_s04 | ✓ | brak | — | C@3.04 | 17.612 | ✓ |
| r11_V2 | WOLNY (7.58 Hz) | c04_s04 | ✓ | brak | — | C@3.04 | 10.02 | ✓ |
| r11_V2 | WOLNY (7.58 Hz) | c05_s04 | ✓ | brak | — | C@3.04 | 0.0 | ✓ |
| r11_V2 | WOLNY (7.58 Hz) | c06_s04 | ✓ | żywy | 27.1 | C@3.02 | 9.876 | ✓ |
| r11_V2 | WOLNY (7.58 Hz) | c07_s04 | ✓ | brak | — | C@3.03 | 10.3 | ✓ |
| r12_V2 | WOLNY (7.58 Hz) | c08_s04 | ✓ | brak | — | C@3.04 | 5.164 | ✗ |
| r12_V2 | WOLNY (7.58 Hz) | c09_s04 | ✓ | brak | — | C@3.02 | 5.108 | ✓ |
| r12_V2 | WOLNY (7.58 Hz) | c10_s04 | ✓ | żywy | 29.6 | C@3.04 | 5.112 | ✓ |
| r12_V2 | WOLNY (7.58 Hz) | c11_s04 | ✓ | brak | — | C@3.04 | 4.94 | ✗ |
## §5. Tabela 48 par (ramię = pierwsza ważna próba; para ważna ⇔ obie strony ważne)

| scenariusz | split | wspólna | B_D6 | V2_D6 | boot B | boot V2 |
|---|---|---|---|---|---|---|
| c00_s01 | TRAIN | ✓ | ✓ | ✓ | r1_Br | r1_V2 |
| c00_s02 | TRAIN | ✗ | — | ✓ | — | r4_V2 |
| c00_s03 | TRAIN | ✓ | ✓ | ✓ | r7_B | r7_V2 |
| c00_s04 | TRAIN | ✓ | ✓ | ✓ | r10_B | r10_V2 |
| c01_s01 | TRAIN | ✓ | ✓ | ✓ | r1_B | r1_V2 |
| c01_s02 | TRAIN | ✗ | — | ✓ | — | r4_V2 |
| c01_s03 | TRAIN | ✓ | ✓ | ✓ | r7_B | r7_V2 |
| c01_s04 | TRAIN | ✓ | ✓ | ✓ | r10_B | r10_V2 |
| c02_s01 | VAL | ✓ | ✓ | ✓ | r1_Br | r1_V2r |
| c02_s02 | VAL | ✗ | — | ✓ | — | r4_V2 |
| c02_s03 | VAL | ✓ | ✓ | ✓ | r7_B | r7_V2 |
| c02_s04 | VAL | ✓ | ✓ | ✓ | r10_B | r10_V2 |
| c03_s01 | TRAIN | ✗ | ✓ | — | r1_B | — |
| c03_s02 | TRAIN | ✗ | — | ✓ | — | r4_V2 |
| c03_s03 | TRAIN | ✓ | ✓ | ✓ | r7_B | r7_V2 |
| c03_s04 | TRAIN | ✓ | ✓ | ✓ | r10_B | r10_V2 |
| c04_s01 | VAL | ✓ | ✓ | ✓ | r2_B | r2_V2 |
| c04_s02 | VAL | ✓ | ✓ | ✓ | r5_B | r5_V2 |
| c04_s03 | VAL | ✓ | ✓ | ✓ | r8_B | r8_V2 |
| c04_s04 | VAL | ✓ | ✓ | ✓ | r11_B | r11_V2 |
| c05_s01 | TRAIN | ✓ | ✓ | ✓ | r2_B | r2_V2 |
| c05_s02 | TRAIN | ✓ | ✓ | ✗ | r5_B | r5_V2 |
| c05_s03 | TRAIN | ✓ | ✓ | ✓ | r8_B | r8_V2 |
| c05_s04 | TRAIN | ✓ | ✓ | ✓ | r11_B | r11_V2 |
| c06_s01 | TEST | ✓ | ✓ | ✓ | r2_B | r2_V2r |
| c06_s02 | TEST | ✓ | ✓ | ✓ | r5_B | r5_V2 |
| c06_s03 | TEST | ✓ | ✓ | ✓ | r8_B | r8_V2 |
| c06_s04 | TEST | ✓ | ✓ | ✓ | r11_B | r11_V2 |
| c07_s01 | TRAIN | ✓ | ✓ | ✓ | r2_B | r2_V2 |
| c07_s02 | TRAIN | ✓ | ✓ | ✓ | r5_B | r5_V2 |
| c07_s03 | TRAIN | ✓ | ✓ | ✓ | r8_B | r8_V2 |
| c07_s04 | TRAIN | ✓ | ✓ | ✓ | r11_B | r11_V2 |
| c08_s01 | TRAIN | ✗ | — | ✓ | — | r3_V2 |
| c08_s02 | TRAIN | ✓ | ✓ | ✓ | r6_B | r6_V2 |
| c08_s03 | TRAIN | ✓ | ✓ | ✗ | r9_B | r9_V2 |
| c08_s04 | TRAIN | ✓ | ✓ | ✗ | r12_B | r12_V2 |
| c09_s01 | TEST | ✗ | ✓ | — | r3_B | — |
| c09_s02 | TEST | ✓ | ✓ | ✗ | r6_B | r6_V2 |
| c09_s03 | TEST | ✓ | ✗ | ✓ | r9_B | r9_V2 |
| c09_s04 | TEST | ✓ | ✓ | ✓ | r12_B | r12_V2 |
| c10_s01 | TRAIN | ✓ | ✓ | ✓ | r3_B | r3_V2 |
| c10_s02 | TRAIN | ✓ | ✓ | ✗ | r6_B | r6_V2 |
| c10_s03 | TRAIN | ✓ | ✓ | ✗ | r9_B | r9_V2 |
| c10_s04 | TRAIN | ✓ | ✓ | ✓ | r12_B | r12_V2 |
| c11_s01 | TRAIN | ✗ | — | ✗ | — | r3_V2 |
| c11_s02 | TRAIN | ✓ | ✗ | ✗ | r6_B | r6_V2 |
| c11_s03 | TRAIN | ✓ | ✓ | ✗ | r9_B | r9_V2 |
| c11_s04 | TRAIN | ✓ | ✓ | ✗ | r12_B | r12_V2 |
## §6. Budżet i rytm — STOP-FANTOM2

Launches kampanii **27/27** (24 nominalne + 3 powtórki zapasu; w tym 1 infra-pad
r4_B bez epizodów), booty nogi **28/≤30** (S1 smoke 1 + kampania 27); rezerwa
programowa 2 nienaruszona (jej użycie = decyzja ANEKS). Sesje lotne nogi: 2.
Przerwania: 3× PAUSE (granice rund, diagnoza środowiska §2) + restart hosta —
wszystkie planowe/narzędziowe, zero bootów połowicznych. Artefakty:
`camp/r*_{B,V2}[r]/` (27 bootów), `camp/fantom_pairs.json`, `pairs_after_r1..r12`,
`camp/fantomS2_telemetry.json`, qlogi, monitor log, stan kampanii. Porcelain po
commicie: pusty. Push = Olga. Dalej: **ANEKS_FANTOM-2** — werdykt dwuwarstwowy
(strefa opisowa pozycji: 3/6 + regresje 1; siatka: Δ_new2=7 strefa opisowa),
KSIĘGA (P-F-1…6), CO-FANTOM. ŻADNYCH interpretacji ponad §1/§3 po stronie
wykonawcy. STOP.
