# ANEKS_NADIR-4 — po STOP-NADIR4-DIAGNOZA: stanowisko dziś zdrowe (zaniżał zegar), bramka zdrowia przechodzi na przyrząd A przy zatrzymanym timesyncd; nowy trop wiodący — stan zasilania karty graficznej (277 MHz, P5/P8, programowy limit mocy); telemetria GPU 1 Hz w każdym boocie i test remedium przy 0 bootach

CC · 10.11.2026 · łańcuch NADIR, po STOP-NADIR4-DIAGNOZA (61be5d6d na
origin). Zmienia §3.4 i §3.5 ANEKS_NADIR-3; budżet z ANEKS_NADIR-3
§4.4 nadal czeka na „ratyfikuję N3". Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem)

1. **ANEKS_NADIR-3 na origin: byte-check PASS** (sha256 9588df13…c2e6,
   identyczny z plikiem CC — „sha ok"); pierwszy blok KSIĘGI verbatim,
   wiersza N3 nie ma — zgodnie z literą.
2. **Skoki zegara potwierdzone niezależnie** z surowych `rtf_*.jsonl`:
   +1.2…+1.56 s co ~33.6 s w każdym przebiegu. Po ich wycięciu
   własnym kodem CC: A 0.9377 / 0.9206, C 0.9248 / 0.9098 — zgodne
   z raportem do 0.001; seria M3 0.917–0.935. **Stanowisko jest dziś
   zdrowe** (odniesienie 0.928).
3. **Rozliczenie hipotez ANEKS_NADIR-3 §2:** H2 (bezczynność, okno
   w tle, rdzenie E) — sfalsyfikowana: M2 i 30 min M3 płaskie, ekran
   i uśpienie ustawione na „nigdy", częstotliwość stała. Była
   hipotezą nr 1 CC — błędnie. H1 (limit mocy CPU) i H3 (proces
   hosta) — bez poparcia w telemetrii. Profil turbo nie zmienia tempa.
4. **Znalezisko CC z telemetrii GPU (22 przebiegi z próbkami co
   5 s):** pod obciążeniem sondy karta pracuje w głębokim
   oszczędzaniu — zegar rdzenia **277 MHz**, stany **P5/P8**
   z epizodami P4, ok. **21 W** przy maksymalnym limicie 115 W, a flaga
   `clocks_event_reasons` = 0x4 („software power cap activated" wg
   NVML) jest aktywna w 33–100% próbek. Tempo idzie za stanem karty:
   r(tempo, udział P8) = −0.59, r(tempo, udział stanów wyższych) =
   +0.53. Trzy najwolniejsze przebiegi (0.868 / 0.869 / 0.876) nie
   mają ani jednej próbki w stanie wyższym (pamięć 9001 MHz), a P8
   zajmuje w nich 33–50% próbek; wśród pozostałych 19 zero takich
   próbek ma jeden (M3_07, P8 8%).
5. **„Niewyjaśnione 0.05" sondy B to stan karty, nie arytmetyka
   przyrządu:** ta sama ścieżka kodu w trybie serii (M3) czyta
   0.917–0.935, a niskie odczyty B (P2_B, P5_B) mają profil „start
   0.93–0.945, po 10–20 s zjazd do ~0.87" i w telemetrii przejście
   karty z 1612 MHz / P4 w pierwszej sekundzie na 277 MHz z dużym
   udziałem P8. **To ta sama sygnatura co poranny wolny boot** (0.897
   w pierwszych 10 s, potem 0.79). Wyzwalacz po stronie B niezmierzony.
6. Usterka narzędzia do naprawy: próbnik hosta w PowerShellu zwalnia
   z 5 s do ~50 s między próbkami w ciągu 30 min (55 wierszy na
   1822 s).

## §2. Diagnoza

Stos jest związany kartą graficzną (render d3d12 + detektor CUDA),
a obciążenie jest na tyle lekkie, że zarządca energii karty trzyma ją
na najniższych zegarach. W tym reżimie drobne decyzje zarządcy
przekładają się wprost na tempo. Zgadza się to ze wszystkim, co
zmierzono: w wolnych bootach najbardziej zwalniało wnioskowanie CUDA
(×1.30–1.45), potem symulacja związana renderem (×1.23–1.31),
najmniej czysty CPU (×1.2); po stronie procesora i Windows nie ma
żadnego śladu; skok ma charakter przełączenia stanu.
**Status: hipoteza wiodąca (H4′), poparta w małej skali (−6%)
i sygnaturą; dużego skoku (−20…−25%) z telemetrią GPU jeszcze nie
zarejestrowano.** Rozstrzygnie go telemetria §3.3 przy następnym
wystąpieniu albo test §3.4.

## §3. Decyzje

**3.1 Bramka zdrowia przed każdym bootem (zastępuje ANEKS_NADIR-3
§3.4).** Przyrząd **A bez zmian kodu** (`nadir_n1_ab.run`, rig A_5,
120 s — ten, z którego pochodzi odniesienie 0.9283 / 0.9271), przy
**zatrzymanym `systemd-timesyncd`** (asercja `inactive` przed
pomiarem). **GO ⇔ tempo ≥ 0.90.** NO-GO ⇒ boot nie startuje, nic nie
jest zużyte; po 3 min powtórka w wariancie C (A z telemetrią), po
trzecim NO-GO z rzędu STOP-NADIR4-STANOWISKO z telemetrią. Sonda B
zostaje narzędziem diagnozy, nie bramką. Bramka tempa w boocie (0.93)
bez zmian.

**3.2 Reguła zegara.** Żaden pomiar tempa nie jest ważny przy
aktywnym timesyncd — narzędzia pomiarowe odmawiają pracy, gdy
`is-active` zwraca `active`. Kolejka po STOP-ie nadal go wznawia
(litera ANEKS_SKAN2-0b bez zmian), więc każda diagnoza między
kolejkami zaczyna od jego zatrzymania.

**3.3 Telemetria w tle każdego bootu (zastępuje ANEKS_NADIR-3 §3.5):**
- GPU co 1 s jednym trwałym procesem (`nvidia-smi --query-gpu=… -lms
  1000`): zegary, pstate, moc, obciążenie, `clocks_event_reasons`;
- użycie GPU per proces Windows (klasa CIM
  `Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine`,
  czołówka 5) — żeby zobaczyć ewentualnego konkurenta do karty;
- próbnik hosta jak dotąd, po naprawie kadencji (§1.6).
Koszt telemetrii zmierzony testem przyrządu (C wobec A): w granicach
rozrzutu.

**3.4 Test remedium GPU (0 bootów, ok. 25 min, wymaga dwóch kliknięć
Olgi).** Timesyncd zatrzymany. Seria bazowa 4 × A z telemetrią 3.3;
potem Olga ustawia w panelu NVIDIA (ustawienia 3D, globalnie) tryb
zarządzania energią „preferuj maksymalną wydajność"; seria 4 × A.
**Przyjęcie:** udział P8 w oknach spada ∧ mediana tempa nie spada
o więcej niż 0.01 względem bazowej ⇒ ustawienie zostaje do końca S4
i jest zapisane w raporcie; inaczej wraca do poprzedniej wartości.
Skuteczność dla obciążeń WSL2 jest niepotwierdzona — rozstrzyga
pomiar. Test nie blokuje kolejki: bez Olgi przy komputerze kolejka
rusza pod bramką 3.1, a test czeka.

**3.5 Pomiar tempa zegara gościa (0 bootów, 5 min, nie blokuje).**
Skok +1.35 s co ~32 s oznacza, że zegar maszyny wirtualnej chodzi
ok. 4% wolniej od czasu serwerów NTP (w nodze SKAN2 było ~3%).
Tempo programu jest więc liczone w czasie gościa. Zmierzyć wprost:
zegar monotoniczny gościa wobec zegara Windows przez 120 s bezczynnie
i 120 s pod rigiem A — wynik (błąd tempa zegara i jego zależność od
obciążenia) do raportu i do kanonu jako dopisek do definicji tempa.

**3.6 Kolejność po commicie §CO:** 3.5 → 3.4 (jeśli Olga jest przy
komputerze) → po sygnale N3: bramka 3.1 → kolejka S4 z telemetrią
3.3 do STOP-NADIR4. Próg tempa 0.93, litera (a)–(g) i kolejność
siatki bez zmian.

## §4. KSIĘGA (append-only przy commicie §CO)

```
## NADIR S4 — diagnoza stanowiska (ANEKS_NADIR-4, 10.11.2026)
- Matryca M0–M3/M5 (0 bootów): okno w tle, profil turbo i 30 min
  bezczynności nie zmieniają tempa; częstotliwość CPU stała, brak
  procesu hosta. H2 (bezczynność / rdzenie E), hipoteza nr 1 CC —
  ✗ kalibracyjne CC.
- Znalezisko wykonawcy: dzisiejsze sondy zaniżał zegar — timesyncd
  wznowiony przez kolejkę przy STOP-ie daje skoki +1.35 s co ~33 s
  (ok. 4% tempa); po korekcie przyrząd A 0.937 / 0.920 ≈ odniesienie
  0.928 (CC przeliczył niezależnie, zgodność do 0.001). Wada
  wykonawcy nazwana: stan timesyncd zapisywany w każdej sondzie,
  niesprawdzony przed matrycą.
- Znalezisko CC: pod obciążeniem stosu karta graficzna pracuje na
  277 MHz w stanach P5/P8 przy ~21 W, z aktywnym programowym limitem
  mocy; tempo koreluje z udziałem P8 (r = −0.59, n = 22), a trzy
  najwolniejsze przebiegi nie mają żadnej próbki w stanie wyższym.
  Sygnatura
  „zdrowy start, zjazd po 10–20 s" wspólna z porannym wolnym bootem.
  Hipoteza wiodąca dla skoków −20…−25%, niepotwierdzona na dużym
  skoku.
- ✗ projektowe CC: ANEKS_NADIR-3 zlecił nową sondę zamiast użyć
  przyrządu, z którego pochodziło odniesienie — powstał przyrząd B
  o innym zachowaniu; bramka wraca na przyrząd A.
- Lekcje: pomiar tempa tylko przy zatrzymanym timesyncd (asercja
  w narzędziu); odniesienie i bramka muszą pochodzić z tego samego
  przyrządu; tempo programu liczone jest zegarem gościa, który chodzi
  ~3–4% wolniej od czasu rzeczywistego.
```

## §CO

Bramka: origin/master == **61be5d6d**. Commit 1: korzeń
`ANEKS_NADIR-4.md` verbatim (byte-check sha256 z wiadomości CC) +
KSIĘGA §4 append-only. Potem §3.6. Raport z 3.4 i 3.5 w
`results/NADIR/s4/DIAGNOZA_STANOWISKA_2.md`. Sygnał N3 uruchamia
commit 2 z ANEKS_NADIR-3 §CO i kolejkę. Push = Olga.
