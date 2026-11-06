# ANEKS_KONT-1e — po STOP-KONT2-PRZESKOK: przeskoki liczone od startu (lot 5/8 ważny), trzy pozostałe loty wstrzymane, diagnoza D4 przy biurku rozstrzyga o Δ i o losie S2

CC · 6.11.2026 · łańcuch KONT, po STOP-KONT2-PRZESKOK (d5bf03a3 na origin).
Budżet bez zmian (S2′ 5/12, noga 21/45). Wklejany jako jedyny dokument.
Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- **D3 PASS przyjęty: hipoteza fazy/kolejności potwierdzona skutkiem.**
  3/3 bootów s2d wstało na rozgrzanym stanowisku (initial absolute time
  7.4–7.5 s, sensor_combined > 62 tys.), wobec 14/14 FAIL starym
  launcherem. Zastrzeżenie wykonawcy przyjęte: launcher zmienia naraz
  kolejność startu i fazę, więc próg 0.5 s nie jest zmierzony — do
  raportu, nie do kanonu. Launcher s2d obowiązuje do końca nogi.
- **c00_s02_r3, przeskok:** CC z `ulog_wyciag.jsonl` i `ekf_watchdog.json`:
  jeden reinit watchdoga (SLOW_bias>0.08_no_decrease_30s, sim 64.7 s,
  bias 0.128 → 0.0002), flagi estymatora padają 103.9 s przed odcięciem
  i wracają po ~2.5 s, start (nav_state 17) dopiero 60 s przed odcięciem,
  **w powietrzu 0 przeskoków**, GPS w oknie restartu zdrowy. To restart
  filtra przez nasz własny watchdog na ziemi, nie niestabilność flagi GNSS.
- **c08_s04_r3, Δ = 2.80:** CC z trace, xy: skok realny (0.30 → 3.05 m
  między +1 a +2 s zejścia), ale pozycja EKF jest w tym oknie **niespójna
  z własną prędkością** (y: +0.33 → −3.22 m przy raportowanym |v| ≤ 0.3
  m/s) — sygnatura resetów pozycji estymatora przy wejściu w zejście,
  nie płynnego dryfu. GT gładkie (88 próbek / 3 s). Zejście zaczęło się
  przy prędkości stycznej ~1.9 m/s: hamowanie do v_xy = 0 równocześnie
  z rozpędzaniem pionowym — dokładnie profil D5.
- Tabela ε raportu: zgodna z przeliczeniem wyrywkowym CC (c08_s02a_r2,
  c08_s04_r3). ε liczone w xy (`kont_eps.py:46`) — poprawnie, bo bariera
  pilnuje promienia poziomego.

## §2. Rozstrzygnięcia 1–2 z raportu

1. **STOP był po literze i słusznie wykonany.** Metryka na dalej:
   przeskoki flagi liczą się **od startu** (nav_state 17/14 w górę);
   zdarzenia na ziemi raportowane osobno jako „restart estymatora na
   ziemi" z przyczyną watchdoga. Uzasadnienie: R-5 chroni przed fałszywym
   wejściem w KONT w locie, a watchdog preflight wykonuje na ziemi swoją
   zaprojektowaną pracę. Zmiana po danych, nazwana; kierunek
   anty-korzystny (wprowadza do danych najgorszy lot, nie usuwa go).
2. **c00_s02_r3 = lot ważny 5/8.** Najgorsze ε (3.67–4.02 m przy
   60–70 s) zostaje w krzywej.

## §3. Diagnoza D4 przy biurku (0 bootów; ulogi 5 lotów z dysku)

**D4a — bias żyroskopu przy starcie s2d (pyt. 3 raportu):** z 5 ulogów
`estimator_sensor_bias` + pierwsze próbki `sensor_combined`: skąd bias
~0.10 na pierwszej próbce w 2/3 bootów s2d (hipoteza do sprawdzenia:
pierwsze próbki IMU z timestamp_sample 0 przy dołączeniu w 7.4 s);
**bias w chwili odcięcia** w każdym locie ≈ poziom bazowy — to jest
weryfikacja założenia 1c §3 („faza nie wpływa na mierzone wielkości")
w oknie pomiaru. Bias przy odcięciu podwyższony w którymkolwiek locie ⇒
nazwać wpływ na ε tego lotu.

**D4b — anatomia skoku Δ (pyt. 4 raportu):** z `vehicle_local_position`
(xy_reset_counter, delta_xy), innowacji i jakości przepływu, profilu vz
i attitude w oknie ±3 s od `descent_start`, **we wszystkich 5 lotach**:
czy skok to reset(y) pozycji; co je wyzwala (jakość flow przy
jednoczesnym hamowaniu i opadaniu?); korelacja Δ z prędkością styczną
w chwili wejścia w zejście (c08_s04_r3 miał ~1.9 m/s; pozostałe loty —
odczytać i zestawić z ich Δ 0.76–1.03).

**Werdykty prereg (jeden z trzech, mechanicznie z D4b):**
- **W-A: skok jest właściwością zejścia D5 pod przepływem** (resety
  realne, występują przy tym profilu niezależnie od prędkości stycznej
  albo bez wyraźnego dyskryminatora). Wtedy reguła PRE §3 stoi: Δ_D5 =
  1.5 × 2.80 = 4.20 m, T* ≈ 4 s < 10 s już przy n = 5, a dolatywanie
  lotów może T* tylko obniżyć (reguła bierze maksima — monotoniczność).
  **Śmierć S2 orzeczona nierównością, bez 3 pozostałych lotów.**
  ANEKS_KONT-2 zamyka nogę z liczbą.
- **W-B: artefakt przyrządu** (ulog nie pokazuje resetów ani wychylenia
  pozycji; trace rozjeżdża się z ulogiem). Wtedy korekta narzędzia
  dokumentem CC i przeliczenie; nic nie lata do tego czasu.
- **W-C: skok jest skutkiem hamowania równoczesnego z opadaniem**
  (resety tylko przy wysokiej prędkości stycznej; Δ pozostałych lotów
  koreluje z ich prędkością wejścia). Wtedy CC przedkłada Oldze poprawkę
  PRE §2.6 do ratyfikacji: akcja KONT „brake-first" — najpierw
  wyhamowanie poziome na wysokości (≤ 2 s), potem opadanie; pod
  przepływem zejście nie jest ślepe, więc argument R0.3a za
  równoczesnością (czas) traci przesłankę. Po ratyfikacji ≤ 2 loty
  próbne mierzą Δ_brake-first; stara Δ raportowana obok; dalsza kolejka
  i reguła Δ_D5 (z lotów nowym profilem) — osobnym dokumentem.

**Trzy pozostałe loty (c11_s04, c08_s02b, c02_s01) są wstrzymane do
werdyktu D4.** Ich jedyny wpływ na wynik to podniesienie maksimów.

## §4. CO

Aneks verbatim do korzenia jako `ANEKS_KONT-1e.md`, byte-check sha256
z wiadomości CC, commit 1: `KONT [ANEKS-1e]: przeskoki od startu, lot
5/8 ważny, loty wstrzymane, diagnoza D4`. Potem D4 (narzędzia nowe
w `results/KONT/tools/`, wyniki w `results/KONT/s2/d4/`), raport NOWY
`results/KONT/s2/RAPORT_KONT_S2e.md` z werdyktem W-A/W-B/W-C i dowodami
plik:linia, sygnał **STOP-KONT2e**. Zero bootów w tej sesji. Push =
Olga. Rozliczenia do KSIĘGI (w tym wada wykonawcy 1d §2.3, ✗ rachunkowe
CC 7≠8, korekta S2b §2 o `ekf2 missing data`) kumuluje ANEKS_KONT-2.
