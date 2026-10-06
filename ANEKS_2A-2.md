# ANEKS_2A-2 — werdykt bramek po powtórce, errata B(i), decyzja: C-sonda bezpieczeństwa (2 booty)

CC · 05.10.2026 · łańcuch 2A (po STOP-2A2b, commity b22dbc6→5af1e54→ed5d084). Samowykonalny: §5.
Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-2A2b

Przyjęte: N1 zamknął znalezisko yaw pomiarem (sanity 4.66°/4.11° z kontrolą negatywną 75.16°
na starych danych — przyrząd rozróżnia), N2 działa wg spec, orbit-pokrycie 1.0000 ×2, dsw
i quat PASS, testy 6/6 + regresja 187. Atrybucja ogniwa limitującego jest TWARDA, z dowodami
rozłącznymi: projekcja oczyszczona (te same boxy przez dokładny quat ⇒ identyczny błąd),
czas oczyszczony (klatki 14.7 Hz, YOLO ~15 ms, latencja p95 0.052 s), geometria oczyszczona
(pokrycie 1.0) — zostaje DETEKTOR: top-1 poza intruzem w ~97%/~88–97% klatek orbity na tle
naziemnym, przy pinhole 0.65–0.80 m na klatkach z boxem na prawdziwym celu. Powtórka lekcji
r02 o kruchym separatorze: w S2 cel stał na tle nieba, po naprawie yaw kamera patrzy w teren.

## §2. Werdykty bramek (progi bez zmian)

- **A:** orbit PASS 1.0000 ×2 · approach FAIL ×2 (0.898/0.648) — mechanizm: przejściowy
  slew nosa na początku epizodu, zjadający stałe sekundy z krótkiej fazy. Wpis OPISOWY
  (fizyka sztywnej kamery + start epizodu nosem w bok); progu nie zmieniam, pre-aim/gimbal
  = jawna zmiana zakresu w ewentualnej przyszłej nodze percepcji, nie w tej.
- **B latencja:** PASS (0.052 s).
- **B błąd:** FAIL uczciwy (p95 40.9 m) ⇒ **wyjątek ekonomiczny OBOWIĄZUJE: etap C = sonda
  2 bootów, kampania 24-bootowa NIE leci.**
- **B kadencja — ERRATA, wpis do księgi błędów CC (klasa: metryka zmieniła znaczenie przez
  ratyfikowaną interwencję; MÓJ błąd):** próg „świeże ≥8 Hz" zamrożono w PRE, gdy REFRESH
  był bezwarunkowy; ratyfikując N2 (bramkowanie) nie przeliczyłem, że „świeżość" od tej
  chwili mierzy koniunkcję jakości∧czasu — brama odrzuca złe boxy, więc licznik świeżych
  spada z przyczyn JAKOŚCIOWYCH. Litera progu padła (7.58), ale zdanie śmierci, którego
  ten próg był nośnikiem („percepcja limituje CZASOWO"), jest zmierzone jako FAŁSZYWE
  (surowy tor: 14.7 Hz / 15 ms / 52 ms). **Śmierci czasowej NIE ogłaszam** — ogłoszenie jej
  z fałszywym mechanizmem byłoby gorsze niż errata. Pełna jawność: litera ✗, mechanizm
  przeciwny, decyzja tu, historia do RAPORT_2A §odchylenia.

**Werdykt merytoryczny etapu B (kanon przy zamknięciu):** „percepcja limituje DOKŁADNOŚCIĄ
— konkretnie: pretrained detektor open-vocabulary na tle naziemnym — w tej scenie; tor
czasowy, geometryczny i projekcyjny dowiedzione sprawne". Zmiana/doszkolenie detektora =
ŚWIADOMIE poza tą nogą (PRE D4: zero treningu); „detektor-v2" wpisuję do katalogu jako
osobną pozycję z triggerem, nie otwieram.

## §3. C-SONDA BEZPIECZEŃSTWA — 2 booty (pytanie przeformułowane do tego, co uczciwie mierzalne)

Skoro feed percepcyjny ma ZNANY, duży błąd (fantomy tła 29–67 m NED — częściowo POZA
klatką R_E=32), sonda nie mierzy „kosztu percepcji" (to wymagałoby zdrowego feedu), tylko
pytanie centralne programu w najostrzejszej dostępnej formie: **czy system pozostaje
bezpieczny, gdy percepcja aktywnie steruje ku fantomom poza kopertą?** Pierwszy pomiar
zawierania pod ZŁĄ PERCEPCJĄ — tanio, bo zepsuty feed już istnieje.

Konfiguracja: 2 booty, FEED=V (rejestr, zero edycji kodu), CONTROLLER=net (0337d5ea),
scenariusze c11_s01 + c08_s03, pełne uzbrojenie, reżim bootów jak S2. Pomiary:
- **S-BEZP (kryterialne):** breach R_E = 0 wymagane (breach ⇒ STOP natychmiast);
  REFUSE per gałąź = wpis (REFUSE(GEOFENCE) na pogoni za fantomem = wynik OCZEKIWANY
  i cenny, nie anomalia); REFUSE(POS) ⇒ STOP.
- **S-MISJA (opisowe, bez progów):** frakcja track_valid, frakcja hover-hold, czy orbit-entry
  zaszło, t_entry, z_max, trajektoria względem fantomów (maks. zbliżenie do R_E).
Ważność V2′; INVALID ⇒ 1 powtórka z puli.

## §4. Rozliczenia bieżące (formalnie przy zamknięciu)

P-2A-1 ✗ (przeszacowanie, klasa infra). P-2A-3 ✗ (błąd ≤3 m — padł z atrybucją). P-2A-2 —
rozstrzygnięcie przy zamknięciu z erratą §2 (latencja ✓, kadencja-litera ✗ z przyczyną
jakościową). P-2A-4/P-2A-5 — kampania C nie poleci: poza sumą (nietestowalne), zapis
z przyczyną. Budżet po sondzie: 6 bootów lotnych z ≤31.

## §5. Wykonanie (jedna sesja)

1. Bramka: origin/master zawiera ed5d084 (brak ⇒ STOP, prośba o push); ahead pusty;
   porcelain pełny; FROZEN wykonaniem (w tym bench_flight 05137098, feed_vision 0a975121
   = FREEZE_2A po N1/N2).
2. ARCH-1: ten plik → korzeń VERBATIM, pierwszy commit.
3. Sonda §3: 2 booty, zero edycji kodu; OUTDIR `results/2A/probeC/<boot>`.
4. STOP-2A3: commit (booty + `results/2A/RAPORT_2A_S3.md`: S-BEZP z gałęziami REFUSE,
   S-MISJA opisowo, trajektorie vs fantomy, porcelain). Push = Olga; „wypchnięte".
   Dalej: **ANEKS_2A-3** — zamknięcie nogi (werdykt całości, kanon, KSIĘGA, CO-2A;
   detektor-v2 do katalogu). STOP.
