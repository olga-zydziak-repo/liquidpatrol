# ANEKS_KONT-0 — przyjęcie STOP-KONTR: errata kanonu K2/R0.3a (natywny failsafe, „touchdown", przesłanka P2-ε), ścieżka B zamknięta, ścieżka A do PRE przez sondę

CC · 5.11.2026 · łańcuch KONT, po STOP-KONTR (a606c115 na origin).
Aneks samowykonalny (§6): sesja CO deskowa, zero bootów. Errata idą do
przodu, raporty K2, R0.3a i FV zostają bez edycji. Sygnały bez numeru
odrzucasz.

## §1. Weryfikacja CC z repo

- Zakres czysty: 11 nowych plików, +14228/−0, wyłącznie `results/KONT_RECON/**`.
- `kont_r3_eps.py` i `kont_r4_margin.py` uruchomione u CC na a606c115:
  `r3_eps.json` i `r4_margin.json` identyczne bajtowo z commitem. Przy 4 s
  ruch poleceniem p50 1.02 / max 8.45 m, K2 p50 0.47 / max 0.69 m.
- Niezależnie, własnym kodem z trace i px4.log:
  - **Natywny failsafe 12/12 K2.** Konsola PX4 każdego bootu k2c_b1…b12 ma
    `mc_pos_control: Failsafe: blind land` i `failsafe: Failsafe activated`,
    po nich `Landing detected`. Chwila 4.0 s pochodzi z ulogów, których repo
    nie ma (.ulg poza gitem). Przyjmuję ją z pomiaru wykonawcy, nazwane.
  - **„Touchdown” to nie przyziemienie.** Zdarzenie `touchdown` wypada
    +9.80–9.84 s od denialu, a GT z drona ma wtedy 1.15–3.77 m (wyjątek b11:
    0.0 m). GT z < 0.15 m osiąga +8.71–14.89 s.
  - **Przesłanka P2-ε łamana w locie.** r(GT) w chwili denialu: 3/12 ponad
    R_route′ 19.90 (b6 23.35, b7 20.41, b11 20.28). Po scenariuszach siatki
    sieci (64 epizody, 48 scenariuszy, FANTOM S2 + PERC2 S2 + SKAN2 S1):
    r_max > 19.90 w **44/48**, zakres 14.75–26.16 m. Zgodne z R4/R6 reconu.
  - **R0.3a też:** `results/R03/gate/S4/boot1/px4.log` ma `Failsafe
    activated` i `Landing detected` po denialu. S3 (z powrotem GNSS) go nie
    ma. Log S2 w repo to tylko `S2_run.jsonl`, bez konsoli, więc stan S2
    jest niesprawdzalny.

## §2. Errata kanonu (forward)

**E1 — K2, kto sprowadza drona.** Kanon K2 (ANEKS_K2-6 §2): „zejście
współdzielone do przyziemienia 12/12”. Poprawnie: osłona wykryła
degradację i odmówiła w 0.104–0.116 s, przez ~4 s prowadziła zejście
komendami D5, potem PX4 odebrał offboard (brak ważnej pozycji poziomej)
i natywny failsafe dokończył zejście w trybie blind land, prędkością
pionową bez kontroli poziomej. Zero naruszeń R_E w 12/12 (GT) stoi.
`PRE_K2:40` „sekwencja bez natywnego failsafe” jest fałszywe. Przyrząd
sprawdzał listę zdarzeń trace, a ta nie widzi nav_state.

**E2 — K2, czas przyziemienia.** „t_td ≈ 9.8 s” to koniec profilu
komend D5, nie przyziemienie. Przyziemienie (GT) następuje po 8.7–14.9 s.

**E3 — przesłanka P2-ε nie jest niezmiennikiem systemu.** P2-ε dowodzi
zawierania przy r_est ≤ R_route′ (19.90) ∧ ε ≤ ε_cap (9.25). Osłona nie
egzekwuje r_est ≤ 19.90 dla sieci w nominale, a sieć goniąca intruza
regularnie tę granicę przekracza. W K2 3/12 denialów zaczęło się poza
przesłanką. Zawieranie trzymało, bo zmierzone ε ≤ 3.37 m było dużo
mniejsze od capa. **Kanon:** dla lotów sieci pod utratą GNSS zawieranie
jest **zmierzone** (12/12, GT), nie dowiedzione. Twierdzenie pokrywa 9/12
przypadków K2 i trasę patrolu R0.3a, którą osłona prowadzi sama.

**E4 — R0.3a.** W S4 boot1 też działał natywny failsafe. Kanon R0.3a
„touchdown w R_E” zostaje prawdziwy według GT, ale zejście było częściowo
natywne. P6_d5 to dowód o komendach D5, nie o ruchu pojazdu. Od dziś pisać
to jawnie przy każdym cytowaniu.

**Mechanizm, który to porządkuje.** PX4 po utracie ważnej pozycji
poziomej robi blind land, czyli zejście sterowane samą prędkością pionową.
To ta sama klasa akcji co D5 (otwarto-pętlowa względem degradowanej
wielkości). Dlatego nie powtórzyła się ucieczka AUTO.LAND o 42 m: AUTO.LAND
trzyma pozycję, blind land nie trzyma niczego poziomo. Zasada z R0.3a
dostaje drugi przykład, tym razem po stronie PX4. Nie ratuje to jednak
zdania, że zejście do ziemi prowadziła osłona.

**Raport programu (poza repo, CC poprawi):** dwa zdania są za mocne.
„Osłona przejmuje i sprowadza go na ziemię”: poprawnie osłona przejmuje
i zaczyna zejście, a kończy je natywny failsafe. „Własność konstrukcji, a
nie statystyka z lotów”: dla lotów sieci pod odcięciem GPS zawieranie jest
statystyką z lotów (E3).

## §3. Decyzja projektowa wokół E3

Utrata może przyjść w dowolnej chwili, więc przesłanka P2-ε musi
obowiązywać w nominale, zanim cokolwiek się stanie. Opcje:

1. **Bariera nominalna dla sieci** (osłona ogranicza r_est ≤ R_route′
   przez cały lot). Daje dowód, ale zmienia zachowanie sieci w 44/48
   scenariuszy. Unieważniałoby porównywalność całego kanonu kampanii,
   a sieć goni intruza, którego bariera by jej zabrała.
2. **Twierdzenie z rzeczywistym r.** Przy r_max 26.16 m i d_stop 2.85
   zostaje ε ≤ 2.99 m. To mniej niż sam ogon zejścia w najgorszym
   zmierzonym przypadku. Nie domyka się.
3. **Kanon historyczny jako pomiar (E3) + bariera nominalna wyłącznie
   w nodze KONT**, jako jej część projektu i zmierzony koszt (ile
   scenariuszy i ile sekund zadania traci sieć przez rezerwę na utratę).

**Rozstrzygnięcie CC: opcja 3.** Historia nie jest przepisywana, kanon
mówi prawdę, a KONT musi i tak policzyć rezerwę, bo jej bariera
r_est ≤ R_E − d_stop − ε_b(t) − Δ_D5(t) zaczyna działać w chwili utraty,
więc w chwili utraty musi już być spełniona. Koszt nominalny (utracone
podejścia do intruza blisko krawędzi) staje się pomiarem nogi, nie
ukrytym założeniem.

## §4. Ścieżki 2d

- **B (samo IMU): CLOSED jako samodzielna ścieżka.** Budżet obcina ściana
  natywna 4.0 s (EKF2_NOAID_TOUT; do ~9 s przy maksimum metadanych,
  przewidywanie). ~21 bootów za ≤ ~9 s zadania przy orbicie 70 s.
  Lot f4 (błąd prędkości 2.5 m/s w ~2 s, bez mechanizmu) zostaje nazwany
  i nieścigany.
- **A (przepływ optyczny + dalmierz): idzie do PRE_KONT przez sondę.**
  Ustalenia na start:
  - **O0 flaga.** Pod A `dead_reckoning` zostaje False, więc dzisiejszy
    monitor POS nie odpali. Źródło utraty to stan GNSS w estymatorze
    (`cs_gnss_pos`), z własnym pomiarem A-flag w sondzie. Bez tego osłona
    pod A nie wie, że straciła satelity. To blocker, nie szczegół.
  - **Świat i pin.** Wcześniej odrzuciłem maskę widoczności. Zmieniam
    zdanie, z warunkiem. Pin chroni to, co kamera przednia **widzi**, nie
    bajty pliku dla nich samych. Opcja (c) jest dopuszczalna wtedy i tylko
    wtedy, gdy sonda pokaże **identyczność klatek** mono_cam: ta sama poza,
    world_demo_A3 vs A3 + dekal + maska, różnica pikseli = 0 (dopuszczalny
    wyłącznie szum renderu zmierzony w kontroli A3 vs A3). Brak identyczności
    ⇒ fallback (a), nowy świat z rewalidacją percepcji, osobną decyzją.
    Plik pinu nietknięty w każdym wariancie.
  - **Druga kamera 50 Hz a reżim OPS.** Sonda mierzy podłogę kadencji
    z drugą kamerą. Obniżenie częstotliwości flow w kopii modelu dozwolone.
  - **O8 nominał.** Czy `EKF2_OF_CTRL=1` zmienia EKF w nominale
    (z GNSS): sonda mierzy różnicę estymaty w locie nominalnym.
- Cenzura T_cont w R4 (48/48 przy f5) to dolne oszacowanie. Pod A nie
  obowiązuje: krzywą ε_b(t) da dopiero charakteryzacja pod orbitą.

## §5. KSIĘGA (treść do skopiowania, append-only)

Dopisek do `KIERUNKI_PO_PLANIE.md`:

```
## Dopisek stanu katalogu — 5.11.2026 (CO-KONT-0, ANEKS_KONT-0)

- **2d KONTYNUACJA PO UTRACIE GNSS** — OTWARTA (recon a606c115, 0 bootów).
  Ścieżka B (samo IMU) CLOSED: ściana natywna PX4 4.0 s (EKF2_NOAID_TOUT;
  xy_valid → offboard lost → blind land, 12/12 K2). Ścieżka A (przepływ
  optyczny + dalmierz, model x500_flow i plugin w buildzie, bez przebudowy)
  → PRE_KONT przez sondę: flaga cs_gnss_pos (O0), identyczność klatek
  mono_cam przy dekalu z maską (inaczej nowy świat), kadencja OPS z drugą
  kamerą, nominał OF_CTRL. Bariera nominalna r_est ≤ R_E − d_stop − ε_b −
  Δ_D5 częścią projektu KONT, jej koszt mierzony.
- **ERRATA K2/R0.3a (ANEKS_KONT-0 §2):** E1 zejście w K2: komendy D5 ~4 s,
  potem natywny failsafe blind land (12/12; R0.3a S4 boot1 też); E2 „t_td
  9.8 s" = koniec profilu komend, przyziemienie GT 8.7–14.9 s; E3 przesłanka
  P2-ε (r_est ≤ 19.90) nie jest niezmiennikiem dla sieci — r_max > 19.90
  w 44/48 scenariuszy, 3/12 denialów K2 poza przesłanką; zawieranie pod
  utratą GNSS w lotach sieci = POMIAR (12/12 GT), nie dowód; E4 P6_d5 =
  dowód o komendach, nie o ruchu pojazdu. Werdykty GT bez zmian.
- Stan: katalog 6 pozycji, 2d w toku. Breach 0 / REFUSE 0 programowo bez
  zmian.
```

Sekcja do `results/KSIEGA_PREDYKCJI.md`:

```
## KONT recon + errata K2 (ANEKS_KONT-0, 5.11.2026)
Recon bez PRE i bez predykcji numerowanych. Rozliczenia kalibracyjne CC:
- ✗ kalibracyjne (1): hipoteza „sekundy, nie minuty" wpisana do
  PROMPT_KONT_S0 jako skutek dryfu; budżet obcina ściana natywna PX4.
  Trafienie z niewłaściwego powodu liczę jako chybienie.
- ✗ kalibracyjne (2): PROMPT_KONT_S0 cytował ograniczenie renderu
  obalone w ENGINE-RECON (a610810).
- ✗ kalibracyjne (3): CC ratyfikował kanon K2 („zejście współdzielone do
  przyziemienia", t_td 9.8 s) bez sprawdzenia stanu pojazdu (nav_state);
  lista zdarzeń trace była jedynym przyrządem. Klasa „zadany ≠ faktyczny",
  czwarta instancja w programie.
- ✗ kalibracyjne (4): przy pisaniu kanonu K2 CC nie sprawdził, czy
  przesłanka P2-ε (r_est ≤ R_route′) jest niezmiennikiem lotów sieci.
  Nie była (44/48).

Lekcje: (1) każde zdarzenie „wykonano X" w trace sprawdzać z ulogu stanu
pojazdu, zanim trafi do kanonu; (2) przesłanka twierdzenia cytowanego dla
lotów sieci musi być zmierzona na tych lotach albo egzekwowana przez osłonę;
(3) .ulg poza gitem sprawił, że kluczowy pomiar (chwila ściany 4.0 s) jest
w repo niesprawdzalny dla recenzenta — do backlogu: wyciąg z ulogów
(nav_state, xy_valid, failsafe) commitowany jako jsonl przy każdym boocie
denialowym.
```

## §6. Zlecenie CO-KONT-0 (samowykonalne; jeden commit, zero bootów)

Bramka: `git fetch` → origin/master == **a606c115**; `origin/master..HEAD`
puste ⇒ dalej; inaczej STOP. Pliki (lista zamknięta): korzeń
**`ANEKS_KONT-0.md`** (ARCH-1, verbatim, byte-check sha256 z wiadomości
CC); **EDYCJA `KIERUNKI_PO_PLANIE.md`** — dopisek §5, append-only;
**EDYCJA `results/KSIEGA_PREDYKCJI.md`** — sekcja §5, append-only.
**NOWY `results/K2/ulog_wyciag_k2c.jsonl`**, tylko jeśli ulogi k2c_b1…b12
są na dysku: per boot t_denial, t_xy_invalid, t_offboard_lost, t_nav
14→12, failsafe, z narzędzia `kont_native_wall.py` bez zmian. ŻADNYCH edycji
RAPORT_K2, PRE_K2, RAPORT_R03A, certów ani kodu; żadnych bootów. Raport
płaski: diff-stat, porcelain. **Push = Olga.** Potem CC pisze PRE_KONT
(ścieżka A, sonda jako S1). STOP.
