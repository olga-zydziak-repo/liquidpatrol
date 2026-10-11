# RAPORT_AKW_S3 — KAMPANIA 12×{B, V2+skan} (ANEKS_AKW-2 §4) — STOP-AKW3

Wykonawca · 11.10.2026 · ARCH-1 = ANEKS_AKW-2.md VERBATIM w korzeniu (commit c9149e93,
pierwszy w sesji). Profil II FROZEN b94cdeae (ratyfikacja ANEKS_AKW-2 §2). Werdykt
liczbowy niżej zdaniem ZAMROŻONYM (progi PRE_2A §4 verbatim); interpretacja = ANEKS_AKW-3.

## §1. Wynik główny

**48/48 par w siatce, n_common = 48 (≥40 ✓). pass(B) = 46, pass(V2+skan) = 34,
Δ_new = 12.** Próg zamrożony: Δ_new ≥ 10 ⇒ **ŚMIERĆ-AKW — „skan nie wystarcza —
akwizycja nie była jedynym ogniwem"** (zdanie PRE_2A §4 / ANEKS_AKW-2 §4.6, cytowane
verbatim; strefa 5–9 nie zachodzi, Δ=12). ΔΔ = 34 − 12 = **22** — ZAWSZE
z kwalifikatorem dwóch kampanii (DET S4 vs AKW S3; różne sesje, ta sama siatka,
te same progi). Kwalifikatory cytowań: DET + „akwizycja skanem krokowym 40°/1.2 s".

S-BEZP: **breach 0 we wszystkich 25 bootach kampanii; REFUSE 0 / gałęzie puste w obu
ramionach; stop_now false wszędzie** (program utrzymuje breach 0 / REFUSE 0 we
wszystkim, co kiedykolwiek poleciało uzbrojone — +25 bootów).

**Bezpiecznik modu (ANEKS_AKW-2 §3): NIE ZADZIAŁAŁ — ryzyko otwarte §3 ZAMKNIĘTE
POMIAREM na pierwszym wolno-modowym boocie V2 (r1_V2)** i potwierdzone 10×: wolny mod
7.58 Hz z admisją 96.1–99.0% przy celu w FOV w epizodach ślepych (nigdy zero; patrz
§4 mod per boot). Profil II działa w OBU modach kadencji.

## §2. Reżim wykonania + odchylenia JAWNE

Driver `akwS3_boot.sh` (kopia akwS1_boot, sha b7ff3ebf; manifest niesie profil II),
orkiestrator `akwS3_campaign.sh` (kopia detS4_campaign + bezpiecznik modu, e3bae803),
parowanie `akw_pairs.py` (kopia detS4_pairs, zmiany wyłącznie ścieżkowe, 0f248ed0).
Booty 5–30, rundy r1…r12, rotacja naprzemienna, cooldown ≥300 s + proc_gate SUSTAINED
CLEAN 3×30 s per boot, REPO-2, manifesty 1. klasy (akw_scan_sha256 = b94cdeae na żywo
we wszystkich 25; feed_sha per ramię).

1. **Pad hosta między r7_B a r7_V2** (noc 10/11.10, ~01:43): proces kampanii zginął
   wraz z procesem sesji, r7_V2 przerwany w COOLDOWNIE przed startem bootu (katalog
   nie powstał, zero artefaktów, host po weryfikacji czysty — zero sierot). Wznowienie
   `akwS3_campaign.sh 7 12` per wznawialność drivera (r7_B pominięty po gotowym
   summary). Koszt: **1 launch stracony** (licznik zdążył się zwiększyć; launch bez
   bootu i bez lotu). To NIE było przerwanie decyzją — pad środowiska; granica rundy
   nienaruszona merytorycznie (żaden boot nie poleciał połowicznie).
2. **r12_B nieważny → powtórka r12_Br (zapas 1/3):** c08_s04 valid_V2p False
   (dsim_dwall 0.8874, 5 deep-stalli) — znana klasa ważności symulatora (jak c03
   bootu 3 S1); powtórka ważna 4/4, weszła do parowania jako pierwsza ważna próba.
3. **Przyrząd kroków:** liczba PEŁNYCH kroków do pierwszego fresh/ENTRY liczona
   z FIZYCZNEGO yaw pokładowego (own_q rekordów percep_feed, czas sim — ta sama
   fizyka, którą niesie yaw_sanity_ulog, bez wyrównywania zegarów ulog↔sim; pola
   nominalne deg_skanu_* NIEUŻYTE zgodnie z ANEKS §4.4). Spójność z ulog: suma
   omiatanych stopni per boot zgodna z yaw_sanity (p50 segmentów rotacji 11.2–14.2
   °/s = sygnatura profilu II: kroki 60°/s z lagiem P + stare ~0).
4. Launches kampanii: **26/≤27** (24 booty parowe + 1 powtórka + 1 stracony padem);
   booty WYKONANE kampanii: 25; booty nogi łącznie: **29/≤32**.

## §3. Werdykt i dekompozycje (prereg ANEKS_AKW-2 §4.6)

| przekrój | n_common | pass(B) | pass(V2) | Δ |
|---|---|---|---|---|
| **PEŁNA SIATKA 48** | 48 | 46 | 34 | **12** |
| 46 sceno-świeże (bez c08_s03, c11_s01) | 46 | 44 | 34 | 10 |
| 2 sceno-w-TRAIN | 2 | 2 | 0 | 2 |
| bearing 0° | 12 | 12 | 9 | 3 |
| bearing 90° | 12 | 11 | 8 | 3 |
| bearing 180° | 12 | 12 | 9 | 3 |
| bearing 270° | 12 | 11 | 8 | 3 |
| v_intr 0.0 m/s (c00–c03) | 16 | 16 | 15 | 1 |
| v_intr 0.5 m/s (c04–c07) | 16 | 16 | 14 | 2 |
| v_intr 1.0 m/s (c08–c11) | 16 | 14 | 5 | **9** |
| split TRAIN (8 komórek) | 32 | 31 | 23 | 8 |
| split VAL (c02,c04) | 8 | 8 | 8 | 0 |
| split TEST (c06,c09) | 8 | 7 | 5 | 2 |

Mechanizm w liczbach (opisowo, bez zmiany zdania zamrożonego):
- **Δ po bearingach jest PŁASKA (3/3/3/3)** — w DET deficyt był w całości ślepy
  geometrycznie (bearing 0: 12/12 pass, reszta ~0). Skan krokowy ZRÓWNAŁ bearingi.
- **Cały rezydualny deficyt koncentruje się w celu SZYBKIM (v=1.0): Δ=9 z 12**;
  przy v=0 Δ=1, przy v=0.5 Δ=2. Porażki V2 (14): 11 w c08–c11. ENTRY zachodzi
  niemal wszędzie (klasy F1_cel, patrz §4) — pada budżet czasowy sędziego PO
  akwizycji (pościg za szybkim celem po koszcie skanu do ~13–22 s), a w c08
  (bearing 0, v=1.0; 3 porażki) cel UCIEKA ze stożka zanim dwell+MTI się domknie
  i wraca dopiero ze skanu — szybki cel zamienia nawet bearing-0 w pościg.
- **Per-para vs DET: z 35 porażek V2 DET (wszystkie ślepe) 24 przechodzi TERAZ**;
  nadal padają: c01_s01 (mechanizm locka-przed-epizodem na stagingu — jak c00 S1),
  c05_s02, c06_s04 oraz 8×c09–c11 (v=1.0). **3 porażki NOWE względem DET:
  c08_s02/s03/s04 (bearing 0, v=1.0)** — w DET bez skanu nos stał na północy i szybki
  cel bearing-0 był łapany natychmiast; pod skanem po utracie nos ODKRĘCA SIĘ od celu
  (skan od ψ_last) i reakwizycja kosztuje 7–13 pełnych kroków (fresh dopiero
  15.5–27.7 s) ⇒ budżet D6 pada. KOSZT SKANU ma więc drugą stronę: pomaga ślepym
  bearingom (24 domknięte), a szkodzi szybkiemu celowi tam, gdzie skan nie był
  potrzebny (3 regresje). Saldo per-para: +24 / −3.
- **Kontrola dryfu pass(B): 46/48 vs 47/48 DET** — B-FAIL: c09_s02, c11_s02 (obie
  v=1.0; w DET padła c09_s03 — ten sam pas trudności, dryf ≤1 pary). Obie pary
  B-FAIL to też V2-FAIL (porażki WSPÓLNE, nie koszt skanu).
- „V2 lepszy ≥3" NIE zachodzi.

## §4. Telemetria §4.4 (per boot V2 i per epizod)

**Mod kadencji per boot V2 (bezpiecznik egzekwowany na bieżąco):** WOLNY 7.58 Hz —
r1,r2,r3,r4,r5,r7,r8,r10,r11,r12 (10 bootów, admisja ślepe@FOV 96.1/98.4/98.3/99.0/
96.6/98.9/97.6/98.8/98.5/96.7%); SZYBKI 14.71 Hz — r6, r9 (99.1/98.0%). E2E p95 0.080–0.084 s wszędzie. ADMISJA NIGDY ZERO ⇒ bezpiecznik bez tripa; wolny mod
z admisjami >0 już w r1_V2 — wpis zamykający ryzyko §3 pomiarem (10 niezależnych
bootów wolnomodowych).

**Koszt skanu (akwizycje ze skanu, fizyczne kroki):** bearing 90° → t_fresh p50 5.0 s
(p50 1 krok), 180° → 9.5 s (4 kroki), 270° → 12.9 s (6 kroków) — deterministyczna
geometria kroków 40° (bearing/40 + dwell 2 s + doloty), zgodna w obu modach kadencji.
ENTRY klasy: **wszystkie zdarzenia ENTRY w oknach epizodów = F1_cel; F3 (kandydat
tła) = 0 w całej kampanii**; pojedyncze epizody bez zdarzenia ENTRY w oknie = lock
przeniesiony sprzed okna (F2 staging, mechanizm DET-4 §3; np. r3_V2 c09_s01 — D6 PASS).
err_fresh V2 (per-epizod, mediany): p50_med 0.287 / p95_med 0.516 — det_v2 nadal
DOKŁADNIEJSZY od wyroczni B (0.674/1.279), spójnie z DET. feed_expire V2: 18 łącznie.
d_min min: B 0.427 / V2 0.478; z_max ≤14.4; r_max ≤26.3; REFUSE 0 w 48×2 epizodach.

### Tabela per epizod V2 (boot, mod, ważność, D6, t_entry sędziego, t pierwszego fresh, pełne kroki do fresh / do ENTRY, pierwsze ENTRY+klasa)

| boot | mod | epizod | ważny | D6 | t_entry | t_fresh | kroki→fresh | kroki→ENTRY | ENTRY (t_rel, klasa) |
|---|---|---|---|---|---|---|---|---|---|
| r1_V2 | WOLNY | c00_s01 | ✓ | ✓ | 4.212 | 1.42 | 0 | 0 | 1.42 F1_cel |
| r1_V2 | WOLNY | c01_s01 | ✓ | ✗ | 26.052 | 0.032 | 0 | 11 | 23.328 F1_cel |
| r1_V2 | WOLNY | c02_s01 | ✓ | ✓ | 12.212 | 9.6 | 4 | 4 | 9.6 F1_cel |
| r1_V2 | WOLNY | c03_s01 | ✓ | ✓ | 17.208 | 14.576 | 7 | 7 | 14.576 F1_cel |
| r2_V2 | WOLNY | c04_s01 | ✓ | ✓ | 8.716 | 15.824 | 7 | 7 | 15.824 F1_cel |
| r2_V2 | WOLNY | c05_s01 | ✓ | ✓ | 10.02 | 8.228 | 3 | 3 | 8.228 F1_cel |
| r2_V2 | WOLNY | c06_s01 | ✓ | ✓ | 10.02 | 9.596 | 4 | 4 | 9.596 F1_cel |
| r2_V2 | WOLNY | c07_s01 | ✓ | ✓ | 0.0 | 0.048 | 0 | 6 | 14.236 F1_cel |
| r3_V2 | WOLNY | c08_s01 | ✓ | ✓ | 2.864 | 1.388 | 0 | 0 | 1.388 F1_cel |
| r3_V2 | WOLNY | c09_s01 | ✓ | ✓ | 3.048 | 1.6 | 0 | None | — (lock sprzed okna) |
| r3_V2 | WOLNY | c10_s01 | ✓ | ✗ | 0.0 | 8.86 | 4 | 4 | 8.86 F1_cel |
| r3_V2 | WOLNY | c11_s01 | ✓ | ✗ | 0.08 | 12.58 | 6 | 6 | 12.58 F1_cel |
| r4_V2 | WOLNY | c00_s02 | ✓ | ✓ | 4.292 | 1.504 | 0 | 0 | 1.504 F1_cel |
| r4_V2 | WOLNY | c01_s02 | ✓ | ✓ | 9.076 | 6.452 | 2 | 2 | 6.452 F1_cel |
| r4_V2 | WOLNY | c02_s02 | ✓ | ✓ | 11.868 | 9.372 | 4 | 4 | 9.372 F1_cel |
| r4_V2 | WOLNY | c03_s02 | ✓ | ✓ | 15.56 | 12.924 | 6 | 6 | 12.924 F1_cel |
| r5_V2 | WOLNY | c04_s02 | ✓ | ✓ | 3.572 | 1.512 | 0 | 0 | 1.512 F1_cel |
| r5_V2 | WOLNY | c05_s02 | ✓ | ✗ | 8.98 | 22.748 | 10 | 10 | 22.748 F1_cel |
| r5_V2 | WOLNY | c06_s02 | ✓ | ✓ | 9.524 | 9.42 | 4 | 4 | 9.42 F1_cel |
| r5_V2 | WOLNY | c07_s02 | ✓ | ✓ | 7.02 | 12.292 | 5 | 5 | 12.292 F1_cel |
| r6_V2 | SZYBKI | c08_s02 | ✓ | ✗ | 4.372 | 27.684 | 13 | 13 | 27.684 F1_cel |
| r6_V2 | SZYBKI | c09_s02 | ✓ | ✗ | 4.544 | 3.748 | 1 | 1 | 3.748 F1_cel |
| r6_V2 | SZYBKI | c10_s02 | ✓ | ✓ | 5.124 | 9.64 | 4 | 4 | 9.64 F1_cel |
| r6_V2 | SZYBKI | c11_s02 | ✓ | ✗ | 0.06 | 12.192 | 5 | 5 | 12.192 F1_cel |
| r7_V2 | WOLNY | c00_s03 | ✓ | ✓ | 4.912 | 2.084 | 0 | 0 | 2.084 F1_cel |
| r7_V2 | WOLNY | c01_s03 | ✓ | ✓ | 9.732 | 0.008 | 0 | 2 | 7.004 F1_cel |
| r7_V2 | WOLNY | c02_s03 | ✓ | ✓ | 12.112 | 9.488 | 4 | 4 | 9.488 F1_cel |
| r7_V2 | WOLNY | c03_s03 | ✓ | ✓ | 15.452 | 12.768 | 6 | 6 | 12.768 F1_cel |
| r8_V2 | WOLNY | c04_s03 | ✓ | ✓ | 9.288 | 16.004 | 6 | 6 | 16.004 F1_cel |
| r8_V2 | WOLNY | c05_s03 | ✓ | ✓ | 0.08 | 5.308 | 2 | 2 | 5.308 F1_cel |
| r8_V2 | WOLNY | c06_s03 | ✓ | ✓ | 9.192 | 11.384 | 5 | 5 | 11.384 F1_cel |
| r8_V2 | WOLNY | c07_s03 | ✓ | ✓ | 10.276 | 13.204 | 6 | 6 | 13.204 F1_cel |
| r9_V2 | SZYBKI | c08_s03 | ✓ | ✗ | 4.232 | 15.532 | 7 | 7 | 15.532 F1_cel |
| r9_V2 | SZYBKI | c09_s03 | ✓ | ✗ | 0.04 | 4.836 | 1 | 1 | 4.836 F1_cel |
| r9_V2 | SZYBKI | c10_s03 | ✓ | ✗ | 5.28 | 9.0 | 4 | 4 | 9.0 F1_cel |
| r9_V2 | SZYBKI | c11_s03 | ✓ | ✗ | 0.0 | 21.656 | 10 | 10 | 21.656 F1_cel |
| r10_V2 | WOLNY | c00_s04 | ✓ | ✓ | 4.496 | 1.704 | 0 | 0 | 1.704 F1_cel |
| r10_V2 | WOLNY | c01_s04 | ✓ | ✓ | 9.156 | 6.52 | 1 | 1 | 6.52 F1_cel |
| r10_V2 | WOLNY | c02_s04 | ✓ | ✓ | 12.132 | 9.372 | 4 | 4 | 9.372 F1_cel |
| r10_V2 | WOLNY | c03_s04 | ✓ | ✓ | 16.244 | 13.528 | 6 | 6 | 13.528 F1_cel |
| r11_V2 | WOLNY | c04_s04 | ✓ | ✓ | 3.432 | 1.276 | 0 | 0 | 1.276 F1_cel |
| r11_V2 | WOLNY | c05_s04 | ✓ | ✓ | 0.0 | 5.008 | 1 | 1 | 5.008 F1_cel |
| r11_V2 | WOLNY | c06_s04 | ✓ | ✗ | 11.364 | 0.024 | 0 | 4 | 10.52 F1_cel |
| r11_V2 | WOLNY | c07_s04 | ✓ | ✓ | 10.808 | 13.48 | 6 | 6 | 13.48 F1_cel |
| r12_V2 | WOLNY | c08_s04 | ✓ | ✗ | 4.26 | 21.448 | 10 | 10 | 21.448 F1_cel |
| r12_V2 | WOLNY | c09_s04 | ✓ | ✓ | 0.0 | 4.76 | 1 | 1 | 4.76 F1_cel |
| r12_V2 | WOLNY | c10_s04 | ✓ | ✓ | 7.992 | 10.132 | 4 | 4 | 10.132 F1_cel |
| r12_V2 | WOLNY | c11_s04 | ✓ | ✗ | 5.088 | 12.616 | 6 | 6 | 12.616 F1_cel |
## §5. Tabela 48 par (ramię = pierwsza ważna próba; para ważna ⇔ obie strony ważne)

| scenariusz | split | wspólna | B_D6 | V2_D6 | d_min B | d_min V2 | boot B | boot V2 |
|---|---|---|---|---|---|---|---|---|
| c00_s01 | TRAIN | ✓ | ✓ | ✓ | 7.76 | 8.303 | r1_B | r1_V2 |
| c00_s02 | TRAIN | ✓ | ✓ | ✓ | 7.852 | 8.282 | r4_B | r4_V2 |
| c00_s03 | TRAIN | ✓ | ✓ | ✓ | 7.68 | 8.057 | r7_B | r7_V2 |
| c00_s04 | TRAIN | ✓ | ✓ | ✓ | 7.831 | 7.61 | r10_B | r10_V2 |
| c01_s01 | TRAIN | ✓ | ✓ | ✗ | 7.823 | 7.235 | r1_B | r1_V2 |
| c01_s02 | TRAIN | ✓ | ✓ | ✓ | 7.611 | 6.951 | r4_B | r4_V2 |
| c01_s03 | TRAIN | ✓ | ✓ | ✓ | 7.925 | 7.893 | r7_B | r7_V2 |
| c01_s04 | TRAIN | ✓ | ✓ | ✓ | 7.55 | 7.962 | r10_B | r10_V2 |
| c02_s01 | VAL | ✓ | ✓ | ✓ | 7.44 | 8.057 | r1_B | r1_V2 |
| c02_s02 | VAL | ✓ | ✓ | ✓ | 7.549 | 8.067 | r4_B | r4_V2 |
| c02_s03 | VAL | ✓ | ✓ | ✓ | 7.762 | 8.03 | r7_B | r7_V2 |
| c02_s04 | VAL | ✓ | ✓ | ✓ | 7.88 | 8.054 | r10_B | r10_V2 |
| c03_s01 | TRAIN | ✓ | ✓ | ✓ | 7.875 | 7.706 | r1_B | r1_V2 |
| c03_s02 | TRAIN | ✓ | ✓ | ✓ | 7.829 | 7.575 | r4_B | r4_V2 |
| c03_s03 | TRAIN | ✓ | ✓ | ✓ | 7.804 | 7.589 | r7_B | r7_V2 |
| c03_s04 | TRAIN | ✓ | ✓ | ✓ | 6.513 | 7.696 | r10_B | r10_V2 |
| c04_s01 | VAL | ✓ | ✓ | ✓ | 6.794 | 6.075 | r2_B | r2_V2 |
| c04_s02 | VAL | ✓ | ✓ | ✓ | 6.868 | 7.325 | r5_B | r5_V2 |
| c04_s03 | VAL | ✓ | ✓ | ✓ | 7.342 | 6.851 | r8_B | r8_V2 |
| c04_s04 | VAL | ✓ | ✓ | ✓ | 7.188 | 7.677 | r11_B | r11_V2 |
| c05_s01 | TRAIN | ✓ | ✓ | ✓ | 6.419 | 6.779 | r2_B | r2_V2 |
| c05_s02 | TRAIN | ✓ | ✓ | ✗ | 6.673 | 2.708 | r5_B | r5_V2 |
| c05_s03 | TRAIN | ✓ | ✓ | ✓ | 6.828 | 7.353 | r8_B | r8_V2 |
| c05_s04 | TRAIN | ✓ | ✓ | ✓ | 6.652 | 6.876 | r11_B | r11_V2 |
| c06_s01 | TEST | ✓ | ✓ | ✓ | 6.531 | 7.252 | r2_B | r2_V2 |
| c06_s02 | TEST | ✓ | ✓ | ✓ | 6.563 | 6.555 | r5_B | r5_V2 |
| c06_s03 | TEST | ✓ | ✓ | ✓ | 7.131 | 7.752 | r8_B | r8_V2 |
| c06_s04 | TEST | ✓ | ✓ | ✗ | 5.347 | 3.233 | r11_B | r11_V2 |
| c07_s01 | TRAIN | ✓ | ✓ | ✓ | 7.132 | 6.696 | r2_B | r2_V2 |
| c07_s02 | TRAIN | ✓ | ✓ | ✓ | 7.531 | 6.367 | r5_B | r5_V2 |
| c07_s03 | TRAIN | ✓ | ✓ | ✓ | 7.184 | 7.246 | r8_B | r8_V2 |
| c07_s04 | TRAIN | ✓ | ✓ | ✓ | 7.735 | 7.182 | r11_B | r11_V2 |
| c08_s01 | TRAIN | ✓ | ✓ | ✓ | 6.605 | 6.416 | r3_B | r3_V2 |
| c08_s02 | TRAIN | ✓ | ✓ | ✗ | 7.236 | 1.82 | r6_B | r6_V2 |
| c08_s03 | TRAIN | ✓ | ✓ | ✗ | 5.23 | 2.883 | r9_B | r9_V2 |
| c08_s04 | TRAIN | ✓ | ✓ | ✗ | 6.704 | 1.784 | r12_Br | r12_V2 |
| c09_s01 | TEST | ✓ | ✓ | ✓ | 6.568 | 7.133 | r3_B | r3_V2 |
| c09_s02 | TEST | ✓ | ✗ | ✗ | 1.089 | 1.299 | r6_B | r6_V2 |
| c09_s03 | TEST | ✓ | ✓ | ✗ | 7.304 | 2.517 | r9_B | r9_V2 |
| c09_s04 | TEST | ✓ | ✓ | ✓ | 4.466 | 6.794 | r12_B | r12_V2 |
| c10_s01 | TRAIN | ✓ | ✓ | ✗ | 5.975 | 5.425 | r3_B | r3_V2 |
| c10_s02 | TRAIN | ✓ | ✓ | ✓ | 6.87 | 4.486 | r6_B | r6_V2 |
| c10_s03 | TRAIN | ✓ | ✓ | ✗ | 5.653 | 3.882 | r9_B | r9_V2 |
| c10_s04 | TRAIN | ✓ | ✓ | ✓ | 5.664 | 5.609 | r12_B | r12_V2 |
| c11_s01 | TRAIN | ✓ | ✓ | ✗ | 6.911 | 1.184 | r3_B | r3_V2 |
| c11_s02 | TRAIN | ✓ | ✗ | ✗ | 0.427 | 2.322 | r6_B | r6_V2 |
| c11_s03 | TRAIN | ✓ | ✓ | ✗ | 5.329 | 0.478 | r9_B | r9_V2 |
| c11_s04 | TRAIN | ✓ | ✓ | ✗ | 5.311 | 2.26 | r12_B | r12_V2 |
## §6. Budżet i rytm — STOP-AKW3

Booty nogi: **29/≤32** (S1 3 + re-smoke 1 + kampania 25); launches kampanii 26/≤27
(1 stracony padem hosta — §2.1); zapas powtórek zużyty 1/3. Sesje lotne nogi: 3.
Artefakty: `camp/r*_{B,V2}[r]/` (25 bootów: manifesty, akw_summary, percep_feed,
akw_mode_fuse dla V2), `camp/akw_pairs.json` + `pairs_after_r1..r12.txt`,
`camp/akwS3_telemetry.json` (kroki fizyczne per epizod), `campaign_state.json`,
`akwS3_monitor.log`. Porcelain po commicie: pusty. Push = Olga.

Dalej: **ANEKS_AKW-3** — werdykt Δ_new (zdanie zamrożone §1), kanon nogi, KSIĘGA,
CO-AKW. ŻADNYCH interpretacji ponad §1/§3 po stronie wykonawcy. STOP.
