# PRE_FANTOM — prerejestracja nogi FANTOM (czysty start epizodu: kwarantanna tracków sprzed startu)

CC · 12.10.2026 · po STOP-FANTOMR (15c31143, zweryfikowany z repo: R2 przeliczone
niezależnie z surowych wierszy — 18/17/15+2, szóstka alive-FAIL co do sida, 9 żywych-
PASS, pass 34; R3 zgodny z krzyżowym dowodem DET; plik:linie bencha potwierdzone,
w tym reset() per epizod :312 i yaw=0 w resecie :305). Wymaga ratyfikacji Olgi.
Po ratyfikacji CC dostarcza PROMPT_FANTOM_S1 — na start nogi wklejasz DWA dokumenty
(PRE + PROMPT); ratyfikacja sama nie uruchamia niczego.

## §1. Teza i dźwignia (FROZEN)

Jedno ogniwo niesie 6 z 12 porażek Δ kampanii AKW: **lock percepcji sprzed startu
epizodu** (3× parking świata przy pierwszym epizodzie bootu, 3× stary intruz
śledzony przez fazę resetu) → zero freshów po t0 → expire ~1 s → skan od ψ fantomu
→ ślepota 9.5–26.8 s. Dźwignia: **KWARANTANNA KONSUMENTA** — nowy wrapper
`net_fantom` (rejestr +1 linia additive) deleguje AkwScan (profil II FROZEN
b94cdeae nietknięty) i po `reset()` traktuje feed jako niewidoczny dla delegata
(hold → dwell → skan od ψ_last=0), dopóki nie zajdzie dowód admisji WEWNĄTRZ
epizodu. Wyjście jednorazowe per epizod; po wyjściu pass-through verbatim.
GRANICA UCZCIWOŚCI: wrapper decyduje wyłącznie, co sam konsumuje; percepcja,
admisja, telemetria percepcji, choreografia bencha i profil II — NIETKNIĘTE;
fantom zostaje w logach. Delegat w kwarantannie dostaje fd nieodróżnialny od
„brak tracku" wg istniejącego kontraktu (kopia/podmiana, zero mutacji współdzielonych
obiektów). Zdarzenia kwarantanny (wejście/wyjście, powód, t) idą do extra cmd
i manifestów 1. klasy.

## §2. Predykat wyjścia — kandydaci + reguła wyboru (desk, mechaniczna)

- **K2 (preferowany): fresh-po-starcie.** Wyjście, gdy fd niesie odświeżenie
  stemplowane po t_ref+ε (wykrywalne jako age < now − t_ref − ε), ε=0.5 s
  (ogon kolejki klatek fantomu: +0.02…+0.03 s « ε; realne admisje ≥ okna stare).
  t_ref = pierwszy step() po reset(). Fallback twardy: T_q=3.0 s (ochrona przed
  osobliwościami age; lock-real@start c05_s04 i ramię B wychodzą freshem ≤~0.6 s).
- **K1 (zapasowy, z recon):** pierwsze z: (A) przejście invalid→valid,
  (B) przeskok trk_pos >5 m vs migawka z t_ref, (C) T_q=3.0 s. Koszt nazwany:
  na ramieniu B i lock-real wychodzi dopiero przez (C) — +3 s na każdym epizodzie B.
- **Reguła wyboru (prereg):** desk-replay na artefaktach kampanii AKW: (i) 6/6
  fantomów trzymanych do realnej admisji epizodu; (ii) wyjście ≤1.0 s na 48 śladach B,
  na c05_s04 i na 30 czystych V2 (zero zwłoki ponad dzisiejsze zachowanie);
  (iii) na 9 żywych-PASS wyjście ≤ moment realnej admisji, przewidywana akwizycja
  ≤ obserwowana+1 s dla ≥8/9 (c09_s01 dopuszczony do +4 s). **K2 spełnia wszystko
  ⇒ K2 FROZEN; inaczej K1 z (ii) złagodzonym do ≤T_q i kosztem B nazwanym w raporcie;
  oba padają ⇒ STOP-ANEKS (śmierć pozycji na desku, zero lotów).** Parametry po
  wyborze (ε/T_q/D_jump) wchodzą do FREEZE_FANTOM — zdarzeniowe, nie per-klatka
  (brak sprzężenia z kadencją; reguła jednostek z ANEKS_AKW-1 nie ma tu zastosowania
  i to też jest decyzja jawna).

## §3. Sesja S1 — budowa + desk + smoke (1 sesja lotna, 1+1 boot)

1. Budowa `net_fantom` (delegacja AkwScan) + rejestr +1 linia + test T1:
   **tożsamość delegacji poza kwarantanną** — komendy bit-w-bit vs net_akw na
   sekwencjach odtworzeniowych (wzór 12/12 z AKW §3.1), obie gałęzie (track/hold).
2. Test T2: desk-replay §2 z regułą wyboru; wynik per epizod do raportu (tabela:
   6 fantomów + c05_s04 + 9 żywych-PASS + 4 ślady B); FREEZE_FANTOM (sha wrappera,
   rejestru, parametry, marker=reset() bez env).
3. **Smoke 1 boot V2** (zapas 1): sekwencja epizodów wymuszająca obie podklasy —
   pierwszy epizod c08_s02-podobny (parking świata) + przejście z epizodu
   z intruzem (klasa „poprzedni epizod") + kontrola c09_s01. Bramki: epizod
   fantomowy ma akwizycję ≤ t_A=23 s i q_exit wg projektu; c09_s01 D6 albo
   mechanizm nazwany; admisja ślepych bez zmian (96–99%); C: breach 0, REFUSE 0.
   FAIL smoke ⇒ STOP-ANEKS (analiza, bez wejścia w kampanię).
4. STOP-FANTOM1 (commit: wrapper, test, narzędzia, RAPORT_FANTOM_S1). Push = Olga.

## §4. Sesja S2 — kampania (24+3 booty, 1–2 sesje lotne)

Konfiguracja VERBATIM PRE_2A/AKW S3: 12 rund × {B, V2}, **oba ramiona
CONTROLLER=net_fantom**, siatka 48 i przydział rund jak DET S4/AKW S3, rotacja
naprzemienna, driver = nowa kopia kampanijna, ważności i manifesty 1. klasy
(fantom_sha na żywo, q_exit per epizod), bezpiecznik modu z ANEKS_AKW-2 §3
obowiązuje. Twarde STOPy verbatim: breach ⇒ STOP; REFUSE(POS) ⇒ STOP;
n_common<40 ⇒ STOP; budżet ⇒ STOP; przerwanie planowe tylko na granicy rundy;
raport częściowy bez interpretacji Δ. Telemetria DET S4 + AKW + q_exit/t_exit.

## §5. Werdykty (zdania zamrożone — DWIE WARSTWY, bez mieszania)

- **Warstwa POZYCJI (per nazwany epizod — pierwsza prerejestracja epizodowa
  programu):** zbiór nazwany N6 = {c01_s01, c05_s02, c06_s04, c08_s02, c08_s03,
  c08_s04}. **SUKCES POZYCJI: ≥5/6 z N6 przechodzi ∧ regresje (nowe FAIL na parach
  PASS-w-AKW, wspólnie ważnych) ≤1** ⇒ „fantom-start domknięty zachowaniem
  konsumenta; rezyduum = pościg za celem szybkim". **ŚMIERĆ-FANTOM: ≤2/6 z N6
  przechodzi ∨ regresje ≥3** ⇒ „kwarantanna nie wystarcza — start epizodu nie był
  tym ogniwem". Pomiędzy: strefa opisowa z obowiązkową dekompozycją per epizod N6
  i per regresja.
- **Warstwa SIATKI (porównywalność, progi VERBATIM PRE_2A §4):** Δ_new2 =
  pass(B) − pass(V2) na parach wspólnie ważnych; ≤4 / ≥10 / 5–9 opisowa; V2 lepszy
  ≥3 ⇒ zdanie jawne + podejrzliwość przyrządu. Raportowana OBOK werdyktu pozycji;
  oczekiwany wynik desku to strefa opisowa (~6) i NIE unieważnia on sukcesu pozycji
  — rozdzielenie warstw jest prerejestrowane właśnie po to.
- Kontrola dryfu: pass(B)_new vs 46/48; ΔΔ zawsze z kwalifikatorem kampanii.

## §6. Predykcje CC (do KSIĘGI przy zamknięciu; dźwignia ZMIERZONA deskiem —
korekta głęboka nie ma tu zastosowania, co jest jawnym użyciem reguły z ANEKS_AKW-3 §5)

- **P-F-1 (0.65):** smoke przechodzi za pierwszym podejściem (epizod fantomowy
  skonwertowany w locie).
- **P-F-2 (0.60):** konwersja ≥5/6 zbioru N6 w kampanii.
- **P-F-3 (0.55):** Δ_new2 ∈ [5, 8] (strefa opisowa; zdanie ≤4 nie padnie, bo
  pościg zostaje).
- **P-F-4 (0.75):** pass(B)_new ≥ 45 (kwarantanna nie rusza wyroczni).
- **P-F-5 (0.85):** breach 0 / REFUSE 0 w całej nodze.
- **P-F-6 (0.60):** c09_s01 (jedyny nazwany kandydat regresji) mimo kwarantanny
  przechodzi.

## §7. Budżet, higiena, nietykalne

Budżet: S1 smoke 1+1, S2 kampania 24+3, rezerwa 1 ⇒ **sufit nogi ≤30 bootów**;
przekroczenie ⇒ STOP. Sesje lotne: 2–3. Nazwy: `net_fantom`, env `FANTOM_*`
(wyłącznie diagnostyka), `results/FANTOM/`. Dziedziczone verbatim: FREEZE_DET
i FREEZE_AKW w całości, piny 5/5, certy 9/9, bezpiecznik modu. **NIETYKALNE:**
percepcja (det_v2/FeedVision/MTI/progi admisji), osłona, sieć/wagi, rejestr feedów,
profil skanu II (b94cdeae), choreografia bench_flight (FROZEN 05137098) — zmiana
WYŁĄCZNIE w nowym wrapperze + teście + 1 linii rejestru kontrolerów + kopii drivera
kampanii. Raporty wstecz nietykalne; errata wyłącznie w przód.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
