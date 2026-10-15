# ANEKS_FANTOM-1 — przyjęcie S1 (K1 FROZEN, smoke PASS), ZWOLNIENIE KAMPANII (S2)

CC · 15.10.2026 · łańcuch FANTOM (po STOP-FANTOM1, commity a7f3073c→017421ed na
origin). Samowykonalny: §4 (kampania 24+3). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-FANTOM1

Przyjęte po weryfikacji CC z repo wykonaniem: ARCH-1 bajt-w-bajt (b1edc4c1…,
pierwszy commit); zakres czysty (jedyna edycja istniejącego pliku = rejestr
4f58d204→87203d29, 2 linie additive — precedens net_akw); kod fantom_scan.py
**e435ed7e** przeczytany przeciw kontraktowi PRE §1/§2 — zgodny co do litery
(podmiana NOWYM dictem wyłącznie dla fd ważnego, wyjście jednorazowe, pass-through
verbatim, stałe FROZEN bez env, QLOG czysto diagnostyczny); **T2 odtworzone
z surowych wierszy t2_desk.json**: K2 pada dokładnie na ii_lock_real (c05_s04:
age 0.14→3.18, zero odświeżeń 3 s — założenie PRE obalone pomiarem) i ii_czyste
(c04_s03: admisja przedstartowa daleka od GT, real_adm 16.06), K1 spełnia komplet
ze złagodzonym (ii) i kosztem nazwanym **12/48 C-exitów na B** (przeliczone: 12 C /
24 B-skok / 12 A); **smoke odtworzony z qlogu i summary**: B@0.884 / C@3.0 / C@3.0,
t_entry 2.51 / 8.60 / 5.09, ważność 3/3, refuse 0, breach 0, admisja 98.0%.

**Odchylenia przyjęte:** (a) „+1 linia" = 2 linie fizyczne — zgodne z precedensem;
(b) kosmetyczny print „controller=net_akw" w driverze — poprawka ZLECONA w kopii
kampanijnej (§4.3); (c) kadencja B opisowa — zgodnie z ANEKS_AKW-1 §2; (d) T1
w dwóch formach dosłownych przy delegacie rekurencyjnym — przyjęte jako poprawna
interpretacja litery, wpis do rejestru dobrych praktyk (uczciwe nazwanie, czemu
bit-w-bit wprost nie może zajść w kwarantannie); (e) flaka środowiskowa testu
DET-tools — odnotowana, poza zakresem nogi.

## §2. Werdykty (formalnie)

- **Budowa + T1 12/12 + T2 + smoke: PASS.** Predykat **K1 FROZEN** (A/B/C;
  T_q=3.0 s, D_JUMP=5.0 m; ε=0.5 s zapisany jako kandydacki-nieużyty).
- **Reguła wyboru zadziałała PRZECIW preferencji CC** — do rejestru kalibracji:
  założenie PRE („lock-real dostaje fresh ≤0.6 s") było fałszywe w danych; bez
  erratum, bo fallback był prerejestrowany i reguła wykonała go mechanicznie.
  Wniosek systemowy: założenia o danych w kryteriach prereg mają być mierzone
  w recon, nie zakładane w PRE — na szczęście tym razem łapał je desk przed lotem.
- **Smoke — uczciwe rozliczenie dowodu:** podklasa parking-świata skonwertowana
  W LOCIE na ŻYWYM fantomie (c08_s02: akwizycja 0.88 s przez przechwyt-B vs 26.8 s
  ślepoty i FAIL w kampanii AKW) — pierwszy lotny dowód dźwigni. Podklasa
  poprzedni-epizod zaszła w wariancie MARTWYM (c01_s01: konwersja 5.9 s zmierzona,
  ale przypisywalna czystemu startowi, nie kwarantannie). **Wariant ŻYWY podklasy
  poprzedni-epizod pozostaje dowiedziony wyłącznie deskiem (T2: 3/3 trzymane
  w replayu)** — ryzyko otwarte, nazwane; rozstrzyga kampania. c09_s01: 5.34 s vs
  przewidywanie desku 5.6 — model deskowy potwierdzony, zero regresji.
- P-F-1 rozstrzygnięty pozytywnie (smoke za pierwszym podejściem); formalne
  rozliczenie KSIĘGI przy zamknięciu nogi. Budżet: 1/≤30.

## §3. Ryzyko otwarte i pokrycie (prereg)

Jedyne nazwane: żywy fantom poprzedniego epizodu nielatany pod kwarantanną.
Pokrycie: w STOP-FANTOM2 **obowiązkowa dekompozycja N6 per podklasa** (parking vs
poprzedni-epizod) i per wariant fantomu@t0 (żywy/martwy/brak) — jeśli parking
konwertuje, a żywy-poprzedni nie, mechanizm się rozszczepia i werdykt to nazywa.
Dryf B: pass(B) vs 46/48 raportowany z jawną listą C-exitów (koszt +3 s na
12/48 wg desku) — regres B poniżej 44 ⇒ podejrzliwość wobec kwarantanny na
wyroczni PRZED interpretacją Δ_new2. Bezpiecznik modu ANEKS_AKW-2 §3 verbatim.

## §4. ZWOLNIENIE KAMPANII — S2 (24 booty + zapas 3; 1–2 sesje lotne)

1. **Bramka:** origin/master zawiera 017421ed; ahead pusty; porcelain pełny; FROZEN
   wykonaniem (fantom_scan **e435ed7e**, rejestr **87203d29**, akw_scan b94cdeae,
   FREEZE_DET w całości, piny 5/5, certy 9/9, ncp 0337d5ea).
2. **ARCH-1:** ten plik → korzeń VERBATIM, pierwszy commit.
3. **Konfiguracja (PRE_FANTOM §4 VERBATIM):** 12 rund × 2 booty **{B, V2}**, OBA
   ramiona CONTROLLER=net_fantom; siatka 48 i przydział rund jak DET S4/AKW S3
   (r1 c00–c03×s01 … r12 c08–c11×s04), rotacja naprzemienna; driver = NOWA kopia
   kampanijna fantomS1_boot (zmiany WYŁĄCZNIE: rundy/ścieżki + poprawka
   kosmetycznego printu z §1b; stare narzędzia nietknięte); reżim bootów, ważności
   (V2′+żywość w V2), manifesty 1. klasy (blok fantom: sha na żywo, q_events,
   feed_sha per ramię) — wzorem AKW S3.
4. **Telemetria per epizod (AKW S3 +):** q_exit_reason / q_exit_t; fantom@t0
   (żywy / martwy / brak, d_spawn, age@t0); podklasa (parking / poprzedni-epizod)
   dla locków; t_entry, kroki z yaw_ulog, admisja @FOV, klasy ENTRY, mod kadencji.
5. **Twarde STOPy VERBATIM:** breach ⇒ STOP; REFUSE(POS) ⇒ STOP; n_common<40 ⇒
   STOP; budżet ⇒ STOP; bezpiecznik modu przez całą kampanię; przerwanie planowe
   tylko na granicy rundy; raport częściowy bez interpretacji Δ i bez werdyktu N6.
6. **Werdykt (PRE_FANTOM §5 VERBATIM — dwie warstwy, bez mieszania):**
   POZYCJA: N6={c01_s01, c05_s02, c06_s04, c08_s02, c08_s03, c08_s04};
   **SUKCES: ≥5/6 przechodzi ∧ regresje ≤1** (nowe FAIL na parach PASS-w-AKW,
   wspólnie ważnych); **ŚMIERĆ-FANTOM: ≤2/6 ∨ regresje ≥3**; pomiędzy — strefa
   opisowa z dekompozycją per epizod. SIATKA: Δ_new2 progami PRE_2A §4 verbatim
   (≤4 / ≥10 / 5–9 opisowa; V2 lepszy ≥3 ⇒ zdanie jawne), raportowana OBOK.
   Prereg: dekompozycja per podklasa (§3), per bearing/split, pass(B) z listą
   C-exitów; ΔΔ zawsze z kwalifikatorem kampanii.
7. **STOP-FANTOM2:** commit (manifesty par, parowanie, `results/FANTOM/
   RAPORT_FANTOM_S2.md`: tabela 48 par, N6 per epizod z q_exit i podklasą,
   regresje, Δ_new2, dekompozycje, liczniki REFUSE, mod per boot, porcelain).
   Push = Olga („wypchnięte"). Dalej: **ANEKS_FANTOM-2** — werdykt dwuwarstwowy,
   KSIĘGA (P-F-1…6), CO-FANTOM. STOP.

ZAKAZ w S2: edycji kodu/wag/progów/rejestrów (fantom_scan FROZEN e435ed7e; jedyny
nowy plik wykonawczy = driver-kopia kampanii + narzędzie parowania-kopia);
ewaluacji offline na TEST DET; lotów poza §4.

## §5. Budżet

Zużyte 1 + kampania 24 + zapas 3 = **28 z ≤30** (rezerwa programowa 2). Sesje
lotne nogi po S2: 2–3. Przekroczenie ⇒ STOP.
