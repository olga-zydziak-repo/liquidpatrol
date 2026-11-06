# ANEKS_KONT-1 — przyjęcie STOP-KONT1 (S1 PASS) i trzy rozstrzygnięcia przed S2: przyrząd nominalny, przesunięcie pionowe, kandydat na mechanizm dryfu

CC · 6.11.2026 · łańcuch KONT, po STOP-KONT1 (4bfb538c na origin).
Wklejany razem z PROMPT_KONT_S2. Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- Zakres: 113 plików, +42576/−0, same dodania. PRE_KONT w korzeniu,
  sha 57d899f2 zgodne.
- **(i) Identyczność:** przeliczona własnym kodem z PNG w
  `results/KONT/s1/frames/` (40 plików, 8 póz × R1/R2/T/N/flow):
  T vs R1 max |Δ| = 0 i 0 pikseli różnych w 8/8; R1 vs R2 = 0. Kontrola
  N (bez maski) 93–99. Test jest czuły, maska działa.
- **(ii)/(iii):** z `ulog_wyciag_bootB.jsonl`, przejścia względem odcięcia:
  xy_valid i v_xy_valid = 1 od −146.05 s do końca, dead_reckoning = 0 od
  −146.05 s, nav_state 14 do +85.94 s (przyziemienie GT +85.92 s), failsafe
  bez zmian, cs_gnss_pos → 0 przy +0.02 s, cs_opt_flow = 1 od −145.78 s bez
  przerwy. Zgodne z raportem.
- **(iv):** kadencja 14.71 Hz z raportu; V2′ 0.9105, blisko progu —
  druga kamera kosztuje, do pilnowania w S2.
- S1 **PASS**, budżet 2/3. P-KONT-1 ✓, P-KONT-2 ✓.

## §2. Rozstrzygnięcia przed S2

**R-1. Bramka przyrządu (gt_judge p95 0.119 > 0.10).** Próg 0.10 m z R0.3a
mierzył szum przyrządu w reżimie z samym GNSS. Tu nominał ma fuzję
przepływu (O8), więc część z 0.119 to błąd estymatora, nie przyrządu.
Progu nie luzuję. Zamiast niego: (a) przyrząd waliduje się testem
jednostkowym na syntetyce (swap + skew, jak R-2 w R0.3a), PASS warunkiem
ważności; (b) zmierzone p95 nominału per lot **wchodzi do ε** jako
składnik ε(0⁺) i tak samo do reguły ε_b. Błąd nominalny staje się częścią
tego, co bariera musi pokryć, zamiast być filtrem ważności.

**R-2. Przesunięcie pionowe 1.8 m.** CC sprawdził trace bootB: pierwsza
estymata EKF na ziemi ma z = +1.835 m (NED), GT z ≈ 0. W locie h_EKF ≈ 12.0
przy GT 13.78 i dalmierzu 13.95, a różnica jest stała. To przesunięcie
originu pionowego EKF przy starcie, nie błąd wysokości nad gruntem.
Skutek: dron w reżimie KONT lata ~1.8 m wyżej niż kanon, a geometria
kamery do intruza się zmienia. **Decyzja:** driver KONT mierzy
przesunięcie na ziemi przed uzbrojeniem (EKF z − GT z, okno ≥ 5 s)
i kompensuje komendę wysokości tak, żeby wysokość nad gruntem była jak
w kanonie. Wartość w manifeście. Mechanizm przesunięcia (inicjalizacja
z dalmierzem przy EKF2_RNG_CTRL=1?) zostaje opisowy, bez strojenia
parametrów. Ta sama kompensacja w S2 i S4.

**R-3. Kandydat na mechanizm dryfu: błąd skali przepływu.** Wykonawca
podał stosunek drogi EKF/GT 1.136 w oknie (0.993 w nominale), a krzywa
ε(t) jest niemonotoniczna (2.19 → 0.53 m przy 20–30 s). Błąd skali na
orbicie daje dokładnie taki kształt: błąd rośnie z przemieszczeniem i
maleje, gdy dron wraca w okolice punktu odcięcia. Szybki test CC na
trace (model ε ≈ (s−1)·|p_GT(t) − p_GT(cięcie)|) dopasował s = 1.12
z rms 0.93 m i odtworzył spadek przy 30 s. Rzut wektorowy przemieszczeń
daje jednak p50 0.99, co jest sprzeczne z jednorodną skalą. **Mechanizm
nierozstrzygnięty.** Ma znaczenie, bo jeśli to skala z identyfikowalnym
źródłem (parametr kamery przepływu w kopii modelu, ogniskowa / hfov,
dystans do gruntu), to S2 bez poprawki charakteryzowałby błąd modelu,
nie przepływu. **Decyzja:** S2 zaczyna od diagnozy przy biurku z ulogu
bootB (0 bootów, §S2.0 promptu). Jeśli diagnoza wskaże źródło
naprawialne w kopii modelu albo w parametrze, STOP i dokument CC, bez
poprawek na własną rękę. Jeśli nie wskaże, S2 leci na obecnej
konfiguracji, a mechanizm zostaje nazwany jako otwarty.

**R-4. Nauczyciel na kamerze.** FeedB podaje intruza z GT, więc
pod dryfem orbita nauczyciela goni pozycję absolutną. Sieć w S4 widzi cel
kamerą, a tam dryf znosi się w wektorze względnym (R5 reconu). Żeby ε(t)
w S2 powstawało przy tym samym zachowaniu co w S4: **S2 leci z FEED=V2**
(kamera, reżim OPS). Akwizycja w S2 wychodzi wtedy jak w kanonie, a
odcięcie liczy się od t_entry + 30 s.

**R-5. Nominał ≥ 60 s w powietrzu dla przeskoków flagi.** W S1 było 54.4 s.
Wymóg spełniany łącznie w S2 (każdy boot ma ≥ 30 s nominału w powietrzu,
przeskoki sumowane). Jeden przeskok w nominale gdziekolwiek w S2 ⇒ STOP.

## §3. Uczciwa ocena przed S2

Z jednego lotu S1 i reguły §3 PRE: ε(70 s) = 6.50, Δ = 1.86. Przy 1.5×
z ośmiu lotów T* wypada raczej w przedziale 10–25 s niż ≥ 30 s, a próg
śmierci S2 to 10 s. Predykcja P-KONT-3 (T* ≥ 30 s, 0.55) zostaje taka,
jak jest zapisana — nie poprawia się predykcji po danych. Dziś
oceniałbym ją na ~0.3, chyba że diagnoza R-3 znajdzie naprawialną skalę.
To jest dziś najważniejsza dźwignia nogi. R_nom z tego samego lotu
(32 − 2.85 − 1.5·ε(0⁺) − 1.5·Δ) wychodzi okolice 26 m, czyli blisko
r_max 26.16: bariera nominalna może kosztować bardzo mało.

## §4. CO

Ten aneks verbatim do korzenia jako `ANEKS_KONT-1.md`, byte-check sha256
z wiadomości CC, w pierwszym commicie sesji S2 (PROMPT_KONT_S2 §0).
Do `results/KSIEGA_PREDYKCJI.md` (append-only) przy tym commicie:

```
## KONT S1 (ANEKS_KONT-1, 6.11.2026)
- P-KONT-1 (0.50) maska + identyczność klatek — ✓ (T=K=0, 8/8; kontrola N 93–99).
- P-KONT-2 (0.65) aiding ≥ 70 s bez nav 14→12 — ✓ (72.01 s; nav 14 do przyziemienia).
Uwaga CC (bez zmiany predykcji): po S1 P-KONT-3 (T* ≥ 30 s) oceniam niżej,
~0.3, zależnie od diagnozy skali przepływu (R-3).
```
