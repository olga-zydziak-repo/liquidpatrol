# ANEKS_NADIR-3 — po STOP-NADIR4-STANOWISKO (2): zwalnia maszyna, nie pozycja (wspólny czynnik prędkości ~0.75–0.81, r = 0.994); diagnoza hosta przy 0 bootach, czuła bramka zdrowia przed każdym bootem, budżet nogi 30 → 35 do ratyfikacji

CC · 10.11.2026 · łańcuch NADIR, po STOP-NADIR4-STANOWISKO-2 (377a8a54
na origin). Zmiana budżetu wymaga sygnału **„ratyfikuję N3"**; reszta
aneksu (diagnoza, bramka) nie wymaga ratyfikacji. Sygnały bez numeru
odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem)

1. **Tempo a czas wnioskowania detektora.** Percepcja loguje
   `push_frame_wall_ms` (det_v2 na CUDA). Po 15 bootach nogi (S1–S4)
   zależność 1/tempo ↔ p50 ma **r = 0.994**: stanowisko zdrowe
   15.2–15.5 ms przy 0.95–0.97; booty chore 22.1 / 21.8 / 20.1 ms przy
   0.734 / 0.740 / 0.781. Czysto procesorowa detekcja ArUco na ziemi:
   0.41–0.44 ms w bootach zdrowych, 0.50–0.52 ms w chorych (+20%).
   Zwalnia więc render, wnioskowanie i CPU naraz — **wspólny czynnik
   prędkości całej maszyny ~0.75–0.81**, nie koszt składnika stosu.
2. **Pozycja wykluczona.** nom_b1_r2 leciał c01_s01 jako epizod 1
   przy tempie 0.956; konfiguracja stosu przed driverem identyczna
   (spawn, tematy, hash świata, sha modelu — diff 0 linii).
   „3/3 wolne = c01_s01" wynika z kolejki: pierwsza nieudana pozycja
   jest ponawiana jako pierwsza. Zbieżność nie niesie informacji.
3. **Termika wykluczona dla wieczoru.** nom_b1_r2: 9 minut pełnego
   obciążenia, tempo per minuta 0.945–0.962, bez spadku. Przełączenie
   nastąpiło w bezczynnej przerwie 21:19:54–21:26:12, czyli 13–19 min
   po ostatnim sygnale operatora (21:07); c01_s01 był wolny od
   pierwszej sekundy.
4. **Rano obraz inny:** c01_s01_r3 ruszył zdrowo (pierwsze 10 s 0.897
   — tyle co pierwsze okno zdrowych bootów) i siadł po ~10 s do 0.79,
   płasko. Inna wielkość (0.78 wobec 0.73–0.74) i inny początek —
   możliwe, że inna przyczyna niż wieczorem.
5. **Kontrola „goły gz 0.994" była ślepa na tę chorobę.**
   `wk4_b0_ab.sh iii` uruchamia `world_wk3_p2`: bez drona, bez fizyki
   lotu, bez detektorów (jedna statyczna kamera). Serwer nie jest tam
   związany obliczeniowo, więc pokazuje ~1.0 także na maszynie
   wolniejszej o 25%. To narzędzie na zacięcia (noga WK4), nie na
   przepustowość.

## §2. Hipotezy (mechanizm hosta niezmierzony — mierzy go §3)

Stan faktyczny: efektywna prędkość maszyny wirtualnej spada skokiem
do ~0.75–0.81 i trzyma się minutami. Kandydaci i to, co każdy
przewiduje w telemetrii:

- **H2 — degradacja wątków VM przez Windows** (procesor hybrydowy
  P/E: praca w tle, zablokowana sesja albo wygaszony ekran trafia na
  rdzenie E lub pod dławienie zasilania). Przewiduje: częstotliwość
  rdzeni bez zmian, obciążenie na innych procesorach logicznych,
  odtwarzalność blokadą ekranu / oknem w tle, skok o wielkości
  stosunku E/P. Pasuje do wieczoru (bezczynna przerwa, skok, poziom).
- **H1 — limit mocy** (bateria, słaby zasilacz, automatyczny profil
  OEM). Przewiduje: `PercentofMaximumFrequency` /
  `PercentProcessorPerformance` w dół na wszystkich rdzeniach, niższy
  pobór GPU; odtwarzalność odłączeniem zasilacza. Pasuje do poranka
  (spadek ~10 s po starcie obciążenia).
- **H3 — proces hosta** (po restarcie: aktualizacje, Defender,
  indeksowanie). Przewiduje: nazwany proces w czołówce CPU,
  ograniczony czas trwania. Pasuje do poranka.
- **H4 — stan GPU.** Przewiduje: zmiana zegarów / stanu / powodów
  dławienia w `nvidia-smi` przy niezmienionej mikropróbie CPU.

## §3. Protokół stanowiska (0 bootów — żadna próba nie startuje PX4
i niczego nie uzbraja; całość poza budżetem jak dotychczasowe A/B)

**3.1 Sonda stanowiska** — nowe narzędzie w `results/NADIR/tools/`,
wynik `stanowisko_<tag>.json`:
- (a) `gz_a5`: goły gz z rigiem A_5 dokładnie jak w `nadir_n1_ab.py`
  (model z trzema kamerami, konsumenci jak w boocie), 60 s →
  dsim/dwall. **Odniesienie zdrowe: 0.9283 / 0.9271** (NAPRAWA-N1).
- (b) po (a), sekwencyjnie: det_v2 na CUDA na stałej klatce z repo,
  300 wnioskowań po rozgrzewce → p50/p95 ms; mikropróba CPU: stała
  praca jednowątkowa ×10 oraz ta sama w 8 procesach równolegle →
  mediany ms.
- (c) telemetria hosta przez `powershell.exe` z WSL, **klasami CIM
  (nazwy niezależne od języka systemu)**, co 5 s przez czas sondy:
  `Win32_PerfFormattedData_Counters_ProcessorInformation`
  (PercentProcessorPerformance, PercentofMaximumFrequency,
  PercentProcessorUtility per procesor logiczny), czołówka 5 procesów
  po CPU, `Win32_Battery.BatteryStatus`, `powercfg /getactivescheme`;
  z WSL `nvidia-smi` (utilization, temperature, power.draw, clocks,
  pstate, powody dławienia, jeśli dostępne).
- (d) raz na sesję: nazwa procesora i liczba rdzeni/wątków, wersja
  Windows i WSL, sterownik GPU, limity czasu ekranu i uśpienia.

**3.2 Matryca przyczyn** (jednorazowo; każda komórka = pełna sonda,
kolejność M0, M1, M2, M3, M1, M3, M2; ~12 min):
- M0 stan zastany, niczego nie dotykamy;
- M1 operator aktywny, okno terminala na wierzchu;
- M2 terminal zminimalizowany, inne okno na wierzchu, operator
  aktywny w tamtym oknie;
- M3 sesja zablokowana (Win+L), operator nie dotyka 3 min, sonda
  startuje w 75. sekundzie blokady (po wygaszeniu ekranu);
- M4 (tylko gdy M1–M3 płaskie) zasilacz odłączony na czas sondy.

Reguły: komórka X jest przyczyną, gdy w obu powtórzeniach
gz_a5(X) ≤ 0.90 × gz_a5(M1). M0 chore i M1 nie pomaga ⇒ czytamy
telemetrię: częstotliwość (H1), czołówka procesów (H3), GPU (H4).
Wszystko zdrowe i równe ⇒ mechanizm nieodtworzony; kolejka idzie pod
bramką 3.4, a telemetria 3.5 złapie chory stan przy pierwszym NO-GO —
bez straty bootu.

**3.3 Remedia — kandydaci, każdy weryfikowany powtórzeniem chorej
komórki (wymóg ≥ 0.97 × M1).** Zmiany ustawień Windows wykonuje Olga
albo wykonawca za jej zgodą w rozmowie; poprzednie wartości zapisane
w raporcie do przywrócenia.
- R1: tryb zasilania Windows „najlepsza wydajność" (niezależnie od
  profilu OEM); na czas kampanii ekran i uśpienie na zasilaczu
  wyłączone (`powercfg /change monitor-timeout-ac 0`,
  `powercfg /change standby-timeout-ac 0`); sesja niezablokowana.
- R2: polityka planowania dla procesorów hybrydowych (ustawienia
  ukryte, aliasy z dokumentacji Microsoft):
  `powercfg /setacvalueindex scheme_current sub_processor SCHEDPOLICY 2`,
  to samo dla `SHORTSCHEDPOLICY`, potem
  `powercfg /setactive scheme_current` (2 = preferuj rdzenie wydajne).
- R3: wyłączenie dławienia zasilania dla procesu maszyny wirtualnej
  (`powercfg /powerthrottling disable /path …`, kontrola
  `powercfg /powerthrottling list`). Dla WSL2 właściwy proces i sama
  skuteczność są niepotwierdzone — rozstrzyga matryca, nie deklaracja.
- R4 (H3): poczekać na koniec pracy procesu hosta albo go wstrzymać
  na czas kampanii — decyzja Olgi.
- R5 (H1): oryginalny zasilacz, stały profil OEM zamiast
  automatycznego.

**3.4 Bramka zdrowia przed KAŻDYM bootem kolejki** (zastępuje kontrolę
gołego gz na `world_wk3_p2`): sonda 3.1(a); **GO ⇔ gz_a5 ≥ 0.90**
(0.97 × odniesienie). NO-GO ⇒ boot nie startuje i nic nie jest zużyte;
odczekanie 3 min i ponowienie, po trzecim NO-GO z rzędu
**STOP-NADIR4-STANOWISKO** z telemetrią w raporcie. Bramka tempa
w boocie (0.93) zostaje bez zmian jako druga linia.

**3.5 Telemetria hosta w tle każdego bootu** (3.1(c), co 5 s) →
`host_telemetria.jsonl` w katalogu bootu. Od tego aneksu każde
spowolnienie zostawia ślad po stronie Windows.

## §4. Rozstrzygnięcia

1. Hipoteza pozycji zamknięta danymi (§1.2); kolejność kolejki bez
   zmian.
2. **Test pełnego stosu 90 s bez lotu: niepotrzebny** — pytanie
   „stanowisko czy pozycja" rozstrzygają dane. Gdyby kiedyś miał być
   uruchomiony, liczy się jako boot: fizycznie jest tym samym, co boot
   przerwany bramką tempa. Jego rolę przejmuje sonda 3.1 (0 bootów).
3. **Próg tempa 0.93, kadencje kamer i litera S4 (a)–(g) bez zmian.**
   Bramki nie obniżamy: percepcja i driver mają elementy sprzężone
   z zegarem ściennym (wygasanie feedu, limity czasu), więc wolna
   symulacja zmienia zachowanie w czasie symulowanym. Choruje
   stanowisko — leczymy stanowisko, nie kryterium.
4. **Budżet — zmiana PRE, nazwana wprost (wymaga „ratyfikuję N3"):
   limit nogi 30 → 35, limit S4 19 → 24** (16 zużytych + 15 pozycji
   + 4 rezerwy). Uzasadnienie: 7 z 16 bootów nogi spłonęło na bramce
   tempa przed uzbrojeniem (S1: 1, S2: 2, S4: 4) i nie niosło żadnej
   informacji o tezie; S4 nie odsłoniło dotąd ani jednego cięcia.
   Limit chroni przed ponawianiem lotów pod wynik — tu wyniku jeszcze
   nie ma, więc podniesienie nie może przechylić werdyktu. Wczorajsza
   rekomendacja CC („ponad nogę nie w środku bramki") zostaje tym
   samym odwrócona — z tego powodu, nie innego. Przerwania bramką
   tempa nadal liczą się jako booty; reguła dwóch kolejnych przerwań
   bez zmian.
5. Kolejka rusza dopiero po: commicie §CO, matrycy 3.2, weryfikacji
   remedium (jeśli przyczyna znaleziona) i bramce 3.4 = GO.

## §5. KSIĘGA (append-only przy commicie §CO)

```
## NADIR S4 — stanowisko (ANEKS_NADIR-3, 10.11.2026)
- S4: 5 bootów zużytych, 1 ważny (nominał); 4 przerwane bramką tempa
  przed uzbrojeniem (0.928 / 0.734 / 0.740 / 0.781). W nodze 7 z 16
  bootów spłonęło przed uzbrojeniem — zero informacji o tezie.
- Znalezisko CC z danych: tempo ↔ czas wnioskowania detektora
  r = 0.994 (15 bootów), ArUco na CPU +20% ⇒ wspólny, skokowy czynnik
  prędkości maszyny ~0.75–0.81. Pozycja c01_s01 wykluczona (leciała
  w nominale przy 0.956; „3/3" to artefakt kolejki ponowień). Termika
  wykluczona dla wieczoru (9 min płasko; przełączenie w bezczynnej
  przerwie 13–19 min po ostatnim sygnale operatora).
- ✗ CC ×2: (i) zatwierdzona kontrola „goły gz" (wzór 4e/f) nie jest
  związana obliczeniowo — ślepa na spowolnienie maszyny; (ii) grant
  „+2" przyjęty bez przeliczenia 11 + 16 = 27.
- Wykonawca: zbieżność z pozycją nazwana jako nierozstrzygnięta
  zamiast ogłoszona mechanizmem — dobra praktyka; luz nogi policzony
  2 zamiast 3 (nazwane w STOP-STANOWISKO).
- Lekcje: kontrola stanowiska musi być związana obliczeniowo; bramka
  zdrowia należy przed bootem, nie w nim; „ta sama pozycja" przy
  kolejce z ponowieniami nie niesie informacji o pozycji.
```

Wiersz dopisywany osobno, wyłącznie po sygnale N3:

```
- Zmiana PRE (sygnał „ratyfikuję N3", ANEKS_NADIR-3 §4.4): limit nogi
  30 → 35, limit S4 19 → 24.
```

## §CO

Bramka: origin/master == **377a8a54**.
**Commit 1 (zawsze):** korzeń `ANEKS_NADIR-3.md` verbatim (byte-check
sha256 z wiadomości CC) + pierwszy blok KSIĘGI §5 append-only. Potem
§3.1–3.3 (0 bootów) i raport
`results/NADIR/s4/DIAGNOZA_STANOWISKA.md`: matryca, telemetria, co
zmieniono w Windows i z jakich wartości.
**Commit 2 (wyłącznie po „ratyfikuję N3"):** drugi blok KSIĘGI +
budżet kolejki 24/35; kolejka pod bramką §3.4 z telemetrią §3.5 do
STOP-NADIR4. Bez sygnału N3 po diagnozie STOP z raportem.
Push = Olga.
