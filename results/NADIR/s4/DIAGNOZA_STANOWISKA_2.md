# DIAGNOZA_STANOWISKA_2 — ANEKS_NADIR-4 §3.5 i §3.4 (0 bootów)

10.11.2026 · wykonawca · po CO-N4 `8384c3c5`. Wszystkie pomiary przy
`systemd-timesyncd` = inactive (asercja w narzędziu, §3.2), profil OEM
„wydajny", zasilanie sieciowe. Przyrząd = A (`nadir_n1_ab.run`, rig A_5,
rozgrzewka 20 s + okno 120 s, rig sha zgodny z odniesieniem we wszystkich
przebiegach); telemetria §3.3 (`nadir_s4_tel.Telemetria2`) w wariancie C.
Dane: `results/NADIR/s4/bramka/`.

## 1. §3.5 — tempo zegara gościa wobec zegara Windows (`zegar_Z1.json`)

Trwały `powershell.exe` (Stopwatch QPC + DateTime.UtcNow), punkt = środek
najkrótszego round-trip z 15 pingów (RTT 0.25–0.78 ms), clocksource tsc.

| okno | Δ Windows QPC | Δ gość monotonic | gość / Windows |
|---|---|---|---|
| 120 s bezczynnie | 120.302 s | 120.974 s | **1.00558** (+0.56%) |
| pod rigiem A (156.5 s) | 156.525 s | 156.525 s | **1.00000** |

Tempo A w tym oknie 0.9037 w czasie gościa = 0.9037 w czasie Windows.

**Wniosek:** pod obciążeniem zegar gościa chodzi z zegarem Windows co do
10⁻⁵ — tempo programu liczone zegarem gościa jest tempem w czasie Windows.
Założenie §3.5 („gość ok. 4% wolniej") nie potwierdza się względem zegara
Windows: bezczynnie gość jest o 0.56% *szybszy*, pod obciążeniem zgodny.
Rozjazd z NTP (skoki +1.35 s co ~33 s przy aktywnym timesyncd) pozostaje
niewyjaśniony tym pomiarem — różnica zegar Windows ↔ NTP nie była mierzona.
Propozycja dopisku do definicji tempa (decyzja CC): „tempo = dsim/dwall
w zegarze gościa przy zatrzymanym timesyncd; pod obciążeniem zgodne
z zegarem Windows do 10⁻⁵ (Z1)".

## 2. §3.4 — test remedium GPU

Stan przed: NVIDIA App → Grafika → Ustawienia globalne, **Tryb zarządzania
energią = Normalny** (zrzut Olgi, `nvidia_ustawienia_przed.json`; obok
„Zwiększenie wydajności baterii: Wł.", nietknięte). Panel sterowania NVIDIA
zainstalowany, ustawienie zmienione przez NVIDIA App (te same ustawienia
globalne).

| seria | godz. | tempo | mediana | P8 | P4 | SM med | moc med | flaga 0x4 |
|---|---|---|---|---|---|---|---|---|
| R0 bazowa, „Normalny" | 14:27–14:37 | 0.9101 / 0.9295 / 0.9211 / 0.9173 | **0.9192** | 0.185 / 0.067 / 0.092 / 0.117 | 0.34–0.45 | 277 MHz | 21.4–22.2 W | 0.61–0.78 |
| R1 „Preferuj maks. wydajność" | 15:56–16:06 | 0.8525 / 0.8522 / 0.8437 / 0.8438 | **0.8480** | 0.217 / 0.244 / 0.286 / 0.269 | 0.16–0.24 | 277 MHz | 22.9–23.3 W | 0.58–0.72 |

**Reguła przyjęcia:** udział P8 spada ✗ (0.115 → 0.254 średnio) ∧ mediana
tempa nie spada o > 0.01 ✗ (−0.071). **Werdykt: ODRZUCONE — ustawienie
cofnięte przez Olgę do „Normalny"** (sygnał „cofnięte", przed K1).
Ustawienie nie zmieniło stanu karty pod rigiem: zegar SM 277 MHz, P5/P8,
~22 W, flaga programowego limitu mocy jak w R0.

**Zakłócenie serii R1 (znalezisko):** telemetria GPU per proces pokazuje
w każdym oknie R1 **PredatorSense** z użyciem silników GPU ~33% (mediana,
24/24 próbek); w R0 na karcie tylko `vmwp` (WSL) i WindowsTerminal.
Spadku R1 nie można więc przypisać samemu ustawieniu.

### Kontrola po cofnięciu (poza literą §3.4, 0 bootów — do rozdzielenia zakłócenia)

| pomiar | godz. | tempo | P8 | konkurenci GPU (mediana użycia) |
|---|---|---|---|---|
| K1 (C) | 18:58 | 0.8872 | 0.125 | vmwp 28.5, dwm 5, chrome 4 (3 próbki) |
| K2_0 (C) | 19:01 | 0.8779 | 0.125 | vmwp 24, **chrome 17 (21/24)**, dwm 6 |
| K2_1 (C) | 19:03 | 0.8969 | 0.050 | vmwp 28, **chrome 19 (23/24)**, dwm 5 |

PredatorSense po zamknięciu okna nie używa GPU (procesy w tle zostają).
Tempo po cofnięciu 0.878–0.897 — powyżej R1, poniżej R0; w K2 na karcie
pracuje Chrome. Bramka 3.1 (≥ 0.90) dałaby w tym stanie NO-GO 3/3.

**Odczyt (opisowy, n mały):** we wszystkich trzech stanach karta stoi na
277 MHz; tempo spada, gdy na karcie jest drugi użytkownik Windows
(PredatorSense ~33% ⇒ 0.85; Chrome ~18% ⇒ 0.88–0.90; brak ⇒ 0.91–0.93).
Zgodne z H4′ (stos ograniczony kartą trzymaną na najniższych zegarach —
każdy konkurent zabiera z tej samej puli), ale nie potwierdza mechanizmu
dużego skoku −20…−25%. Udział P8 w tych 11 przebiegach nie tłumaczy tempa
lepiej niż obecność konkurenta. Nierozstrzygnięte: wpływ samego ustawienia
NVIDIA bez konkurenta (wymagałby powtórki R1 przy pustej karcie).

**Konsekwencja operacyjna (propozycja, decyzja CC):** przed kolejką i w jej
trakcie na komputerze nie działają aplikacje używające GPU (przeglądarka,
okno PredatorSense, NVIDIA App); telemetria gpuproc w bramce i w boocie
pozwala to sprawdzić post hoc.

## 3. Narzędzia (§3.2, §3.3)

- `results/NADIR/tools/nadir_s4_tel.py` — Telemetria2: nvidia-smi 1 Hz
  trwałym procesem (pstate, zegary, moc, util, temp,
  `clocks_event_reasons.active`); GPU per proces (CIM GPUEngine, czołówka 5);
  próbnik hosta z naprawioną kadencją (List zamiast konkatenacji tablic, sen
  do terminu, pole dur_s). Test 60 s: GPU n = 59, kadencja hosta 4.8 s,
  gpuproc 4.82 s; w 220-sekundowych oknach C kadencje stabilne (24 próbki
  gpuproc w oknie 120 s).
- `results/NADIR/tools/nadir_s4_bramka.py` — tryby `bramka <tag> [--tel]`
  (§3.1, kod 0 GO / 1 NO-GO / 2 błąd), `seria`, `zegar` (§3.5); każdy tryb
  odmawia przy timesyncd ≠ inactive.
- `results/NADIR/tools/nadir_stanowisko.py` — sonda B odmawia (kod 2) przy
  timesyncd ≠ inactive (§3.2).
- Uwaga wykonawcy: pierwsze wywołanie serii K2 nie zostawiło plików (wyjście
  zjedzone przez filtr grep); powtórzone, w tabeli tylko powtórka.

## 4. Stan

Ustawienia Windows/NVIDIA jak przed testem (Tryb zarządzania energią
„Normalny"). timesyncd zatrzymany. Bootów 0; S4 5/19, noga 16/30 bez zmian.
Czeka: „ratyfikuję N3" ⇒ commit 2 (budżet 24/35) + bramka 3.1 i telemetria
3.3 w kolejce.
