# ANEKS_AKW-2 — re-smoke PASS, profil II ratyfikowany, ZWOLNIENIE KAMPANII (S3)

CC · 10.10.2026 · łańcuch AKW (po STOP-AKW2, commity 80484a5c→157f1a3d na origin).
Samowykonalny: §4 (sesje S3 — kampania 24+3). Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-AKW2

Przyjęte po weryfikacji CC z repo wykonaniem: ARCH-1 bajt-w-bajt (33f0c1ab…); zakres
commitów = korzeń + akw_scan.py + results/AKW/**; bramki przeliczone z artefaktów
(t_entry 8.972/11.616/15.784 ≤ 23; C: breaches puste, refuse puste, stop_now false;
ważność 4/4, dsim 0.975–0.983); kadencja 14.71 Hz potwierdzona z surowych percep_feed;
blok walidacji desku odtwarza liczby S1 CO DO SZTUKI (1925/1823/1799/24 i 235/0);
κ-odczyty 0.0/0.0/2.1 → ω_safe 13.53 < 14 → ścieżka II zastosowana mechanicznie;
sha profilu b94cdeae w manifeście bootu i FREEZE_AKW.

**Odchylenia/doprecyzowania przyjęte z uznaniem:** (a) ODMOWA decymacji rekordów bez
klatek, nazwana wprost fałszerstwem — wzorcowa uczciwość przyrządowa, wpis do rejestru
dobrych praktyk; (b) rozbicie locked/unlocked wymuszone danymi — przyjęte jako
DOPRECYZOWANIE mechanizmu: klif S1 był klifem AKWIZYCJI (persystencja MTI nie składa
się nad celem transitującym kadr; fail_mti 70–95%, central 4–24%, k=3 nigdy), nie
śledzenia (to toleruje ≥4.5°/kl przy boxie stacjonarnym); (c) nota o nominalnych
polach deg_skanu_do_* analyzera FROZEN — przyjęta (prawda fizyczna = yaw_sanity_ulog);
(d) pole scan_dps_frozen w manifestach drivera od S2 historyczne — przyjęte (prawda =
akw_scan_sha256 na żywo).

## §2. Werdykty (formalnie) + ratyfikacja profilu II

- **A′: PASS 3/3** (wszystkie t_entry także ≤ 20 s starej bramki i ≤ 25 s sędziego;
  D6 3/3 ślepych — pierwszy raz w nodze). **C: PASS** (program: breach 0 / REFUSE 0
  we wszystkim, co kiedykolwiek poleciało uzbrojone — +1 boot). **B opisowa** —
  tożsama bootowi 2 S1 (14.71 Hz / 0.084 s).
- **Profil II RATYFIKOWANY jako FROZEN nogi:** akw_scan.py **b94cdeae** — step-and-stare
  40° @ 60°/s → stare 1.2 s, dwell 2.0 s, ψ_last, wrap z domkniętą krawędzią −π→+π;
  parametry BEZ env; pełny przegląd 16.8 s. Admisja w ślepych 98.4% (vs 94.7%
  ciągłego w tym samym modzie) — okna stare działają zgodnie z mechanizmem §1b.
- Mechanizm c00 (lock na fantomie stagingu + cel statyczny ⇒ MTI ślepy, reakwizycja
  33.4 s, poza D6) — bez zmiany klasy, poza bramkami nogi (ślepe = c01–c03); pozostaje
  w rejestrze jako nazwany kandydat katalogowy (wejście epizodu, nie misja). NIE
  otwieram.
- Predykcje: P-AKW-1 ✗ (S1); P-AKW-2/4/5 żyją; rozliczenie przy zamknięciu.

## §3. Ryzyko otwarte i jego pokrycie (prereg, egzekwowalne)

Profil II w WOLNYM modzie kadencji nielatany (lag P≈2.8 zjada ~0.5 s stare ⇒ ~5 cichych
klatek @7.58 Hz na warmup MTI Δ=3 + k=3 — rachunek ciasny, nie pomiar). Pokrycie —
**BEZPIECZNIK MODU kampanii:** pierwszy wolno-modowy boot V2 (dt p50 percep_feed
≥ 0.1 s po ≥300 rekordach, sprawdzane na bieżąco) z **ZEREM admisji przy celu w FOV
w epizodach ślepych** ⇒ przerwanie kampanii NA GRANICY RUNDY + STOP-ANEKS. Raport
kampanii niesie mod kadencji per boot V2. Pierwszy wolno-modowy boot z admisjami > 0
zamyka ryzyko pomiarem — odnotować wprost.

## §4. ZWOLNIENIE KAMPANII — S3 (24 booty + zapas 3; 1–2 sesje lotne)

1. **Bramka:** origin/master zawiera 157f1a3d; ahead pusty; porcelain pełny; FROZEN
   wykonaniem (akw_scan **b94cdeae**, rejestr 4f58d204, FREEZE_DET w całości, piny 5/5,
   certy 9/9, ncp 0337d5ea).
2. **ARCH-1:** ten plik → korzeń VERBATIM, pierwszy commit.
3. **Konfiguracja (PRE_AKW §5 VERBATIM):** 12 rund × 2 booty **{B, V2+skan}**,
   **OBA ramiona CONTROLLER=net_akw** (pass-through dowiedziony testem §3.1 — 12/12
   na profilu II); siatka 48 i przydział rund JAK DET S4 (r1 c00–c03×s01 … r12
   c08–c11×s04), rotacja ramion naprzemienna; driver kampanijny = NOWA kopia
   akwS1_boot dla rund (stare narzędzia nietknięte); reżim bootów, ważności
   (V2′ + żywość w V2), manifesty 1. klasy (akw_scan_sha256 na żywo, feed_sha per
   ramię) — wszystko wzorem DET S4/S1-AKW.
4. **Telemetria per epizod (DET S4 +):** t_entry, czas od startu skanu do ENTRY,
   liczba PEŁNYCH kroków do pierwszego boxu/ENTRY (z yaw_sanity_ulog, nie z pól
   nominalnych), admisja przy celu w FOV, klasy ENTRY F1/F2/F3, mod kadencji bootu;
   kontrola dryfu: pass(B)_new vs 47/48 DET.
5. **Bezpiecznik modu §3 — obowiązuje przez całą kampanię.** Pozostałe twarde STOPy
   VERBATIM: breach ⇒ STOP; REFUSE(POS) ⇒ STOP; n_common<40 ⇒ STOP; budżet ⇒ STOP.
   Przerwanie planowe wyłącznie na granicy rundy; STOP-AKW3a = raport częściowy BEZ
   interpretacji Δ; żadnych decyzji na cząstkowych licznikach.
6. **Werdykt (progi VERBATIM PRE_2A §4, zdanie zamrożone):** Δ_new = pass(B) −
   pass(V2+skan) na 48 parach wspólnie ważnych: **Δ_new ≤ 4 ⇒ „system przeżywa
   zejście z wyroczni — luka akwizycji domknięta zachowaniem"; Δ_new ≥ 10 ⇒
   ŚMIERĆ-AKW („skan nie wystarcza — akwizycja nie była jedynym ogniwem");**
   5–9 strefa opisowa; V2 lepszy ≥3 ⇒ zdanie jawne + podejrzliwość przyrządu.
   Prereg: ΔΔ = 34 − Δ_new zawsze z kwalifikatorem dwóch kampanii; dekompozycje
   per bearing / split / sceno-świeżość; per-para zestawienie z 29 ślepymi DET
   (ile przechodzi teraz). Kwalifikatory cytowań = DET + „akwizycja skanem krokowym
   40°/1.2 s". Zakazy PRE_2A §4 i kanonu DET bez zmian.
7. **STOP-AKW3:** commit (manifesty par, parowanie, `results/AKW/RAPORT_AKW_S3.md`:
   tabela 48 par, Δ_new, liczniki REFUSE per gałąź, telemetria §4, dekompozycje,
   mod per boot, porcelain). Push = Olga („wypchnięte"). Dalej: **ANEKS_AKW-3** —
   werdykt Δ_new, kanon nogi, KSIĘGA, CO-AKW (zamknięcie). STOP.

ZAKAZ w S3: jakichkolwiek edycji kodu/wag/progów/rejestrów (profil FROZEN b94cdeae;
jedyny nowy plik wykonawczy = driver-kopia kampanii + narzędzie parowania-kopia);
ewaluacji offline na TEST DET; lotów poza §4.

## §5. Budżet

Zużyte 4 + kampania 24 + zapas 3 = **31 z ≤32**. Sesje lotne nogi po S3: 3–4.
Przekroczenie ⇒ STOP.
