# PRE_SKAN2 — prerejestracja nogi SKAN-II „admisja w rampie": nowy profil skanu (krok 68.3° / stare 0.4 s / dwell startowy 1.0 s) ma przyjąć najgorszy azymut przed zamknięciem pasa admisji — bez wiatru, na T6

CC · 1.11.2026 · po STOP-SKAN2R (4a319742), zweryfikowanym z repo wykonaniem.
Wymaga ratyfikacji Olgi; po niej PROMPT_SKAN2_S1 — na start DWA dokumenty.
**Ostatnia noga techniczna programu; każdy z werdyktów §3 zamyka pozycję
i wątek akwizycji.**

**Weryfikacja reconu (CC, z repo):** zakres czysty (16 nowych plików, zero
delecji, 0 bootów). Z surowych logów (percep_feed: own_q, fresh, trk_pos;
GT z gt_intruder przez `det_labels.BootGeo`; okna z trace) na PERC2 S2 i czterech
bootach bez wiatru WK/WK2 (24 epizody): **19 zdarzeń z fresh na celu, 15 bez
ani jednej klatki stare z celem w stożku przed admisją, 17 z |yaw_rate| ≥ 15°/s
w klatce admisji**; c10_s02 przyjęty przy 60.5°/s po 3 klatkach rampy, 8.74 s
(recon: 8.736 s, 60–75°/s). Latencja stożek→fresh p50 0.20 s; p90 psują dwa
zdarzenia: wk0_b1 c02_s01 (chybione pierwsze przejście, admisja 24.57 s) i c11_s04
(cel w strefie martwej, wyłączony z L przez recon). Uspokojenie yaw z 91 skoków:
T15_final p50 0.66 / p90 0.92 s (recon 0.79 / 0.86 — inna krawędź okna, ten
sam obraz: przestrzał ~8° i wahnięcie). Forma zamknięta odtworzona: 11.15 s
dla profilu FROZEN; tabela B-kal co do setnej (8.39 / 8.69 / 8.79 / 9.19 /
9.19 / 9.29 / 9.39; FROZEN 40/1.2/2.0 → 15.39). **Werdykt literą PROMPT_SKAN2_S0
(L = 1.384 s, 0 kombinacji) stoi i jest zapisany; ta prerejestracja
przeformułowuje hipotezę na podstawie danych, nie poluzowuje kryterium:**
hipoteza promptu celowała w stare, a dane mówią, że przy 14.7 Hz admisja
zachodzi w rampie (recon: ENTRY w rampie 22/36; CC: 15/19 bez stare).
Twierdzenie sufitu TRANSIT stoi w swoich przesłankach („w rampie admisja nie
istnieje" — prawda epoki 5 Hz, smoke AKW 0/235); ta noga testuje przesłankę.

## §1. Teza i pytania (FROZEN)

Teza Olgi: **mała sieć umie latać.** Dziś sieć nie dostaje szansy w 3/6 T6, bo
skan dociera do azymutu 270° po zamknięciu pasa admisji (11.15 s > 10.0 s).
Ta noga pyta, czy przegląd przeliczony na reżim 14.7 Hz oddaje sieci te trzy
epizody — **bez wiatru** (z wiatrem recon daje 0 kombinacji w każdym modelu;
kanon wiatru V-A3 nietknięty).

- **Q1 (c11, bearing 270°):** T6 c11_s02 / c11_s03 / c11_s04 — D6 ze świadkiem
  i t_acq ≤ 10.0 s. Model B-kal: najgorszy azymut przyjęty o 8.39 s (O_max
  1.64 s, zapas 1.11 s do 9.5 s); c11 przy θ = 226.6° oczekiwane 6.6–7.6 s.
- **Q2 (kontrole):** c08_s01 / c08_s02 (bearing 0, admisja w dwell) i c10_s02
  (180°, w PERC2 S2 8.78 s) — nowy profil nie może ich pogorszyć.
- **Q3 (koszt rampy):** fałszywe admisje przy większym udziale rampy
  (62–74 % cyklu zamiast 36 %) — ENTRY z błędem zasięgu > 5 m przy GT ≥ 5 m
  (dziś 0 na tle w 104 epizodach; 5 ENTRY z błędem 3.3–3.6 m na 15 m).

## §2. Projekt (FROZEN)

- **Wrapper NOWY** `r03/controllers/skan2_scan.py`, kontroler `net_skan2`,
  nad `FantomScan` (wzór net_akw/net_fantom; wpis rejestru additive
  w `r03/controllers/__init__.py`). Litera profilu w wrapperze: **krok 68.3°
  CCW, slew 60°/s, stare 0.4 s, dwell 1.0 s wyłącznie przy pierwszym hold
  epizodu (po `reset()`), 2.0 s po utracie** (okno odzysku REFRESH z PRE_AKW
  zostaje). W hold wrapper nadpisuje yaw własnym profilem w każdym ticku, z
  własnym ψ_last; poza hold pass-through cmd bez zmian (test bajtowy jak
  AkwScan/FantomScan); telemetria kwarantanny `q_*` nietknięta. **Nietykalne:**
  `akw_scan.py` b94cdeae, `fantom_scan.py` e435ed7e, `r02/*` (MTI, admisja,
  config), `harness/feed_vision*.py`, `percep_proc.py` 38a3a765, piny/profil
  OPS, sędzia 8ec0fcfb, bench_flight, manifest BENCH. Testy przed lotem: profil
  w czasie (krok/stare/slew/dwell z logu yaw na sucho), pass-through bajtowy,
  reset między epizodami.
- **Konfiguracja:** NCP net_fantom-równoważna (ncp 0337d5ea, rejestr
  additive), FEED=V2, INTRUDER=1, świat bez wiatru (ten sam co PERC2 S2),
  reżim OPS (profil a68a450b, sonda 8df528bb, pin 3354ae1e), higiena zegara
  (`wsl --shutdown` przed sesją, próbnik dwuzegarowy w manifeście), V2′ ≥ 0.90.
- **Siatka S1 = siatka PERC2 S2 1:1** (porównanie A/B z net_fantom w tym samym
  reżimie): boot 1 „bB_c1011" = epizody 22, 23, 35, 47 (c10_s02, c11_s02,
  c11_s03, c11_s04); boot 2 „bA_c08" = epizody 8, 20, 32, 44 (c08_s01…s04).
  Boot 1 pierwszy (tu jest pytanie). Linia bazowa net_fantom z RAPORT_PERC2_S2:
  c11 t_acq 12.23 / 12.31 / 24.97 s, D6 0/3; c10_s02 8.78 s PASS; c08 0.72 /
  0.27 / 0.31 / 0.10 s, PASS 4/4. Dolecenie epizodu nieważnego V2′
  jednorazowe, liczone do budżetu.
- **Sędzia:** bazowy 8ec0fcfb, werdykty ze świadkiem ERRATUM-DMIN i bez;
  bramki ze świadkiem; GT z manifestu. **t_acq** = semantyka F1_cel z
  `perc2_s2_analyze.py` 7ae917f4 (pierwszy wiersz demo.jsonl z track_valid ∧
  |trk − GT_manifest|_xy ≤ 3 m, od t0) — ta sama co w tabeli PERC2 S2, więc
  liczby są wprost porównywalne; pierwsza fresh na celu raportowana obok,
  opisowo.
- **Etykieta per epizod (FROZEN, z logów):** PIERWSZE PRZEJŚCIE (fresh w
  pierwszym przejściu stożka przez azymut celu) / CHYBIONE (fresh w drugim
  cyklu lub później) / BRAK; udział rampy vs stare do fresh; liczba ENTRY
  z |trk − GT| > 5 m przy GT ≥ 5 m; yaw_rate w klatce admisji.

## §3. Osłona, STOPy, werdykty

- Twarde STOPy verbatim: **breach ⇒ STOP; REFUSE(POS) ⇒ STOP; budżet ⇒ STOP.**
  Fałszywy REFUSE(GEOFENCE) ⇒ STOP. Test pass-through wrappera FAIL ⇒ nie
  startuje.
- **Ryzyko nazwane 1:** chybione pierwsze przejście (1/7 epizodów bez wiatru
  w reconie, 1/19 zdarzeń u CC) w nowym profilu kosztuje pełny obrót ~8.4 s
  i dla v=1.0 jest śmiertelne — dlatego kryterium Q1 to 2/3, nie 3/3.
- **Ryzyko nazwane 2:** dłuższa rampa (1.14 s zamiast 0.7 s) — koincydencja
  MTI przy 4°/klatkę zmierzona (0.38–0.46), przy 7–12°/klatkę zero; profil
  60°/s @14.7 Hz = 4.1°/klatkę, przestrzał do ~84°/s = 5.7°/klatkę. Jeśli
  sonda OPS pada, rampa wypada z reżimu — OPS jest warunkiem wejścia.
- **Werdykty (prereg):**
  - **V-A** (c11 ≥ 2/3 D6 PASS ze świadkiem ∧ t_acq ≤ 10.0 s na tych
    ∧ kontrole: c08 t_acq ≤ 1.0 s i D6 PASS, c10_s02 t_acq ≤ 8.78 s i D6 PASS
    ∧ 0 ENTRY z |trk − GT| > 5 m przy GT ≥ 5 m ∧ breach 0): „Przegląd perymetru
    przeliczony na gwarantowaną kadencję — admisja w rampie, krok 68.3°,
    stare 0.4 s, dwell startowy 1.0 s — przyjmuje najgorszy azymut przed
    zamknięciem pasa admisji: T6 bez wiatru a/6 (c11 b/3, t_acq …), kontrole bez
    regresji, zero fałszywych admisji. Sufit profilu misji z TRANSIT był
    sufitem epoki 5 Hz." Zdanie dla tezy: sieć dostaje epizody, których
    dotąd nie dostawała; siatka T6 odnawia się w czystym reżimie.
  - **V-B** (c11 = 1/3 ∧ reszta jak V-A): „profil skraca przegląd, ale nie
    gwarantuje pierwszego przejścia: c11 1/3" + mechanizm z etykiet.
  - **V-C** (c11 = 0/3 albo regresja kontroli albo FP > 0): „admisja w rampie
    nie przenosi się na profil 68.3/0.4 — sufit TRANSIT stoi także przy 14.7 Hz"
    + mechanizm (κ przy dłuższej rampie / chybienia / FP).
  - Każdy werdykt zamyka nogę i wątek akwizycji; brak nowych pozycji katalogu.
- **Pomiary opisowe:** t_acq per epizod, etykieta przejścia, yaw_rate przy
  admisji, udział rampy, ENTRY z błędem zasięgu (lista), koincydencja per
  klatka vs °/klatkę w locie (κ), D6 pełny | świadek, sweep, d_min.

## §4. Predykcje CC (do KSIĘGI)

- **P-SK2-1 (0.55):** c11 ≥ 2/3 D6 PASS ze świadkiem.
- **P-SK2-2 (0.70):** w epizodach c11 przyjętych w pierwszym przejściu t_acq
  ≤ 8.0 s.
- **P-SK2-3 (0.65):** co najmniej jedno CHYBIONE pierwsze przejście w 8
  epizodach S1.
- **P-SK2-4 (0.80):** c08 (4 epizody) t_acq ≤ 1.0 s — dwell 1.0 s nie szkodzi.
- **P-SK2-5 (0.85):** 0 ENTRY z |trk − GT| > 5 m przy GT ≥ 5 m.
- **P-SK2-6 (0.90):** breach 0.
- **Kalibracja do rozliczenia już teraz (✗ CC):** hipoteza PROMPT_SKAN2_S0
  celowała w czas wpatrywania; właściwy człon to admisja w rampie. Zapis przy
  CO, niezależnie od wyniku lotów.

## §5. Budżet, higiena, cytowanie

**Budżet twardy: ≤ 8 bootów** (S1 2 + dolecenia/powtórki ≤ 6); oczekiwane 2–4.
1 sesja + CO. Env `SKAN2_*`, katalog `results/SKAN2/`, nowe pliki wyłącznie:
wrapper, wpis rejestru (additive), driver (kopia drivera PERC2 S2 z nowym
kontrolerem i katalogiem), narzędzia etykiet/κ. ZERO edycji istniejących
plików poza additive wpisem rejestru; REPO-1/REPO-2, proc_gate, cooldown.
Cytowanie zdaniami z §3 z literą profilu (68.3° / 60°/s / 0.4 s / dwell 1.0
start · 2.0 po utracie), „bez wiatru, reżim OPS 14.7 Hz, SITL". Nie wolno:
przenosić na wiatr (V-A3 bez zmian), mówić „sufit zniesiony" bez odnowionej
siatki, nic o realnym sprzęcie.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
