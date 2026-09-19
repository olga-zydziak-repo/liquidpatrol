# PRE_W — noga W: wiatr (pozycja 2b) — dostępność osłony i przesunięcie domeny pod stałym wiatrem

CC · 19.09.2026 · wejście: RECON_W (commit 07a35a4, R1–R6 + Q1–Q12) · baza ramienia (−) 0/24
(RAPORT_K2 §4 + RAPORT_K4b) · incydent REPO zamknięty (ANEKS_REPO-1a; reguły REPO-1/REPO-2
obowiązują w tej nodze bez wyjątków). Trzy twierdzenia nośne tego PRE zweryfikowane przez CC
z repo (zip 14.09), nie z pamięci: bench_flight.py:361, gate_run_r03.py:268,
r4_envelope.json c11.r_1orb_p95=25.369, run_boot.sh:16.

## §0. Ratyfikacja

Pole ratyfikacji Olgi: **„W1–W14 TAK"** (albo korekty per numer — decyzje w §12). Po ratyfikacji
CC wystawia ANEKS_W-0 (zapis + zamrożenie + predykcje do księgi) i PROMPT_W_S1; build nie startuje
wcześniej. Zgodnie z ARCH-1 ten plik i aneksy wchodzą do repo pierwszym commitem S1. Łańcuch nogi
= ANEKS_W-n; sygnały bez numeru wykonawca odrzuca.

## §1. Pytanie nogi i hipotezy

Rdzeń: czy osłona zaczyna **fałszywie odmawiać** pod szumem świata — bo jeśli tak, ścieżka 1:N
pada na DOSTĘPNOŚCI, nie na bezpieczeństwie. Recon zawęził mechanizm do ostrej, falsyfikowalnej
postaci (R3.4): pos_flag = wyłącznie `VehicleLocalPosition.dead_reckoning`, a ten wchodzi w true
tylko, gdy EKF sam porzuci fuzję GNSS — więc fałszywy REFUSE wymaga, by wiatr wypchnął EKF
w dead-reckoning MIMO włączonego GPS. Hipotezy rozdzielone:

- **H1 (dostępność w locie):** wiatr w locie zmusza EKF do dead_reckoning przy zdrowym GPS ⇒
  REFUSE(POS) bez denialu. Klasyfikacja prawdziwy/fałszywy w §5; każdy wariant = znalezisko.
- **H2 (dostępność startu):** wiatr blokuje uzbrojenie z ziemi (boot3 sondy: przy 6 m/s ślizg
  +5.77 m, dywergencja EKF, arm-fail). Mierzona osobno, na ziemi, w W-A.
- **Wtórne (przesunięcie domeny):** degradacja misji egzekutora i NCP-20 (trenowanego BEZ wiatru,
  wagi zamrożone) pod rosnącym wiatrem — pierwsze krzywe odporności programu, parowane per
  scenariusz jak w nodze sieci.

Uczciwe oczekiwanie a priori: przy STAŁYM wektorze ≤3 m/s wynik (−) najpewniej będzie czysty
(hover pod stałym wiatrem = stały przechył, innowacje małe). Czyste (−) na poziomach do V_MAX
to pełnoprawny wynik nogi (rozszerzenie bazy 0/24 na wiatr), nie rozczarowanie; reżimy ostrzejsze
(≥4.5, turbulencja) mają w §12 jawne triggery, nie wchodzą tylnymi drzwiami.

## §2. KOREKTA RAMION — pułapka klasy erratum #3 w propozycji R5

`bench_flight.py:361`: `arm = (denial_done or (K2_ARM_MONITOR and t_entry is not None))` —
bez intruza `t_entry` nigdy nie powstaje ⇒ `pos_flag=None` ⇒ monitor POS **nieuzbrojony przez
cały lot**. Gate analogicznie: `gate_run_r03.py:268` `pos_flag=(dr if denial_done else None)` —
w nominale bez denialu monitor martwy, a gate jest PINOWANY (zmiana = ceremonia INFRA-3, nie
w tej nodze). Wniosek: ramię (i) „patrol-only bez intruza" w brzmieniu z R5 mierzyłoby na torze
POS dokładnie NIC — powtórka erratum #3, wykryta przed PRE zamiast po kampanii.

Rozstrzygnięcie: ramienia (i) NIE MA jako osobnego bytu. Kampania = **2 ramiona nominalne bez
denialu** (route-executor, NCP-20), intruz obecny, monitor uzbrojony. Harness dostaje JEDNĄ jawną
zmianę: env **W_ARM_ALWAYS=1** uzbraja pos_flag od wejścia w OFFBOARD (nie od t_entry); default
OFF — replay-testy bit-zgodne; bench_flight jest harnessem NIEpinowanym (FREEZE_K2), zmiana
z unit-testem i diffem verbatim w raporcie S1. Kampania lata z flagą ON ⇒ **każdy epizod
kryterialny w całości jest próbką ramienia (−)**. Długi czysty patrol bez intruza = poza nogą,
trigger w §12/W2. Reguła E3 bez zmian: każdy materiał wymienia uzbrojone gałęzie.

## §3. Siatka kryterialna

- **Poziomy:** {0, 1.5, 3.0} m/s, wektor STAŁY. 3.0 = V_MAX (r01/config.py:24); 1.5 = połowa;
  0 = kontrola parowana.
- **Kierunek:** JEDEN, +x (East ENU). Orbita omiata pełne 360° kierunku WZGLĘDNEGO w każdym
  okrążeniu (tailwind/headwind/crosswind próbkowane w jednym epizodzie); analiza per-kierunek
  robi sędzia OFFLINE z faz orbity — zero mnożenia siatki (odpowiedź na drugą połowę Q1).
- **Komórka:** c11 — największa ekspozycja koperty: r_1orb_p95 = 25.369 m przy R_E=32
  (results/K2_RECON/r4_envelope.json, percell.c11; próg p95≤26 z ANEKS_K2-4 /
  MAPA_KRYTERIOW_KAMPANIA G4). To rozstrzyga Q7: identyfikator żyje w przestrzeni ławki/K2,
  grep reconu szukał w korpusie K1; brak źródła w moim prompcie = błąd CC (klasa „liczba bez
  źródła w prompcie"), wpis do księgi błędów.
- **Ziarna:** 3 na komórkę (identyfikatory z scenario_manifest e0527026 przy budowie, cytat
  w FREEZE_W).
- **Razem:** 2 ramiona × 3 poziomy × 3 ziarna = **18 bootów kryterialnych**, przeplot ramion,
  parowanie per (poziom, ziarno) — porównania NCP↔executor opisowo, zakaz języka istotności.

## §4. Faza W-A — sonda kalibracyjna pod wyłącznością, PRZED kampanią

Cel: dokończyć pomiar R2 przerwany kolizją executora. Zakres: hover 90 s × 1 boot per poziom
{0, 1.5, 3.0} (moduł infra1 — BEZ osłony w pętli: to pomiar WEJŚCIA toru pos_flag:
dead_reckoning / eph / xy_reset_counter + przechył średni liczony offline z boot.ulg) + 1 boot
informacyjny: próba uzbrojenia przy 4.5 m/s (H2). ALT=8 m zostaje (infra1 default; kalibracja,
nie kryterium — różnica do patrolowych 10 m odnotowana, Q8).

**Reguła wyłączenia (DETERMINISTYCZNA, zamrożona teraz — wzór drabiny P2-A2):** poziom, który
w W-A nie uzbroi się w ≤2 podejściach, WYPADA z siatki kryterialnej i staje się wynikiem H2
(„zmierzony próg uzbrajalności"); kryteria pozostałych poziomów bez zmian. Wypadnięcie poziomu
1.5 ⇒ STOP nogi (drabina nieuzbrajalna = ŚMIERĆ wg §7). W-A nie zmienia w PRE niczego poza
składem siatki tą regułą (SR-W-7).

## §5. Definicja fałszywego REFUSE (Q3) — ZAMROŻONA

REFUSE(POS_DEGRADED) w epizodzie bez denialu klasyfikuje sędzia po locie, z GT (GT wyłącznie
sędzią — reguła 8 reżimu):

- **FAŁSZYWY** ⇔ mediana |pos_EKF − pos_GT| z ostatnich 20 ticków (1 s) przed tripem
  < **ε_false = 2.0 m**. Prowieniencja progu: zdrowe błędy estymaty zmierzone w programie
  0.244–1.584 m (R0.3a S2; K1 S@0.2 boot7 ε_pos), EPS_CAP = 9.25 (r03/config.py:20) —
  2.0 leży tuż nad zmierzonym pasmem zdrowym i głęboko pod budżetem koperty.
- **PRAWDZIWY** ⇔ ≥ 2.0 m: wiatr realnie zdegradował estymację, osłona zadziałała poprawnie
  pod realnym stresem — znalezisko H1 pierwszej wagi, nie porażka osłony.

KAŻDE REFUSE w kampanii = natychmiastowy STOP + pełny ślad (trace, ulog, klasyfikacja §5) —
drabina nóg bezpieczeństwa: 1 zdarzenie = STOP i diagnoza, nigdy uśrednienie. Breach R_E
(jakikolwiek, każde ramię) = STOP natychmiast (domena certów).

## §6. Metryki i sędzia

- **w_judge.py** (NOWY, glue nad bench_judge + GT): klasyfikator §5; rozkład per-kierunek
  względny z faz orbity; ground-speed GT vs V_ENV=6.0 jako FLAGA (k1_finalize.py:113 — Q10,
  nie bramka); margines r_max vs R_E; zużycie budżetu EPS_CAP jako FLAGA; przechył. Zamrożony
  hashem w **FREEZE_W** (w_judge + światy + model wind_models + diff W_ARM_ALWAYS) commitowanym
  PRZED pierwszym bootem kryterialnym.
- **Degradacja misji:** metryki NIENASYCONE per poziom (frac pasma [6,10], d_min approach,
  werdykt D6-analog opisowo), parowane z poziomem 0 i między ramionami — **RAPORT-ONLY**, bez
  bramki: próg „akceptowalnej degradacji pod wiatrem" nie istnieje przed danymi i nie będzie
  dorabiany po nich; wynikiem są krzywe.
- **bench_judge 8ec0fcfb NIETKNIĘTY** (ważność epizodu V2′ jak w ławce: najdłuższy deep-stall
  ≤1.5 s ∧ Δsim/Δwall ≥0.90 — ANEKS_BENCH-1a); w_judge wyłącznie DOKŁADA pola.

## §7. Bramka nogi (ZAMROŻONA)

- **PASS** = 0 fałszywych REFUSE ∧ 0 breach na wszystkich ważnych epizodach kryterialnych
  ∧ komplet siatki (≥2/3 ważnych ziaren per komórka poziom×ramię; ponowienia w kolejce, cap 3)
  ∧ krzywe degradacji dostarczone.
- **ZNALEZISKO-STOP (nie FAIL):** REFUSE PRAWDZIWY (H1) — noga zamyka się raportem znaleziska
  pierwszej wagi; dalszy ruch = decyzja programowa osobnym dokumentem.
- **FAIL dostępności:** ≥1 REFUSE FAŁSZYWY — STOP + diagnoza; to jest zmierzona odpowiedź
  „ścieżka 1:N pada na dostępności".
- **NIEROZSTRZYGNIĘTE:** siatka niekompletna po budżecie (env), zero REFUSE — raport częściowy
  bez werdyktu (−).
- **ŚMIERĆ nogi:** drabina nieuzbrajalna od poziomu 1.5 w W-A ⇒ noga pada do noty H2
  z triggerem (mechanizm ramp/spawn-in-air zwalidowany w przyszłej sesji infra).

## §8. Budżety i wyłączność (Q11)

≤ **32 booty lotne** (18 kryterialnych + ≤6 W-A + ≤8 ponowień) / ≤ **3 sesje**; env-blocki poza
budżetem (auto-defer, precedens ławki). Arytmetyka wejściowa: ~5–6 min/boot pod wyłącznością
(R5) ⇒ W-B ≈ 2–2.5 h; wykonawca przelicza przed serią (reguła programu). Wyłączność: przed każdą
serią `pgrep -af 'run_sonda_boot|run_boot|gz sim|bin/px4'` MUSI być puste; jakikolwiek respawn
cudzego procesu = STOP infra (precedens 16.09), zero wojny killi. Launcher W utrzymuje lock
`results/W/.executor_lock` (PID; odmowa startu przy żywym). REPO-1: pełny `git status
--porcelain` w każdym raporcie sesji.

## §9. Guard wyjścia (Q13 / REPO-2)

Mechanizm ze źródłem: `harness/run_boot.sh:16` honoruje env `OUTDIR`
(`OUTDIR="${OUTDIR:-$ROOT/results/INFRA3/B/boot${BOOT_N}}"`) — override bez dotykania frozen
wrappera. Każdy boot W: OUTDIR jawnie pod `results/W/**` ustawiany przez launcher; launcher
**ODMAWIA startu, gdy docelowy katalog zawiera manifest.json**; zero dziedziczenia ścieżek
innych nóg (incydent 25.08 = udokumentowany dowód mechanizmu, ANEKS_REPO-1a §2).

## §10. Pliki dotykane (skonfrontowane z listami freeze)

`worlds/gen_world_wind.py` (istnieje; +poziom 1.5, +4.5; pełny stack 13 systemów + WindEffects —
pułapka R1.8 obowiązkowo) · `worlds/world_wind_s*.sdf` (osobny plik per poziom, sha w manifeście
— W6) · `worlds/wind_models/x500_base` (istnieje; sha do FREEZE_W) · `bench/bench_flight.py`
(+W_ARM_ALWAYS — jedyna zmiana harnessu, unit-test, diff verbatim) · `tools/w_launcher.sh`
(NOWY: lock §8, OUTDIR-guard §9, prepend GZ_SIM_RESOURCE_PATH — W9, dowód R1.7) ·
`bench/w_judge.py` + testy (frozen przed kampanią) · narzędzie przechyłu offline (ulog) ·
`results/W/**`. **NIETYKALNE:** `harness/run_boot.sh`, piny 5/5, bench_judge/k2_judge/features,
wagi net/frozen, provery/certy, gate (pinowany — dlatego W_ARM_ALWAYS żyje w bench_flight,
nie w gate).

## §11. Stop-rules

SR-W-1: bramka git każdej sesji (na wejściu S1: origin musi zawierać 07a35a4 + b43760a +
e4262da + 8b4f060; inaczej prośba o push). SR-W-2: REFUSE lub breach ⇒ STOP natychmiast, pełny
ślad, zero strojenia progów po danych. SR-W-3: zero edycji frozen; W_ARM_ALWAYS jedyną zmianą
harnessu. SR-W-4: liczba/nazwa bez źródła nie istnieje; parametry WindEffects czytane
z WindEffects.cc przy budowie, nie z pamięci. SR-W-5: wyłączność §8; kolizja = STOP infra.
SR-W-6: kryteria §5/§7 nietykalne po ratyfikacji — w żadną stronę. SR-W-7: W-A zmienia wyłącznie
skład siatki regułą §4. SR-W-8: booty wyłącznie przez run_boot.sh z OUTDIR §9; bieg bez
manifestu nie istnieje.

## §12. Decyzje W1–W14 (odpowiedzi na Q1–Q12 + Q13 + fazowanie)

**W1** (Q1): drabina {0, 1.5, 3.0}; 4.5 wyłącznie jako pojedyncza informacyjna próba arm w W-A;
6.0 poza nogą (trigger: zwalidowany ramp/spawn-in-air). Jeden kierunek +x; kierunkowość
względna z faz orbity offline (§3).
**W2** (Q2): kryterialnie WYŁĄCZNIE wektor stały — determinizm parowania jest nośny. Turbulencja
= aneks eksploracyjny ≤2 booty PO komplecie siatki, jawnie poza pre-rejestracją, tylko przy
zapasie budżetu; parametry z WindEffects.cc. Długi patrol-availability bez intruza — trigger:
osobna mini-noga po tej (wymaga trybu patrolowego w pętli ławki, nie dorabiamy go tu).
**W3** (Q3): ε_false = 2.0 m wg §5, okno 1 s przed tripem, klasyfikacja dwustronna.
**W4** (Q4): NCP wchodzi OD RAZU, pełna siatka, przeplot — degradacja jest raport-only, więc
„zmarnowanych" bootów nie ma; każdy boot NCP to jednocześnie próbka (−).
**W5** (Q5): N = 3 ziarna na komórkę; łącznie 18 uzbrojonych epizodów kryterialnych (w tym 6 na
poziomie 0 rozszerza bazę bezwietrzną 0/24); zero języka stóp — jak kanon K2.
**W6** (Q6): osobny plik świata per poziom z własnym sha (rekomendacja reconu przyjęta;
runtime-set odrzucony — brak źródłowego API).
**W7** (Q7): rozstrzygnięte źródłem — c11 = komórka ławki/K2, r_1orb_p95 = 25.369
(r4_envelope.json); wybrana jako komórka kampanii (§3).
**W8** (Q8): W-A na infra1/ALT=8 (kalibracja); kampania w pętli ławki na jej własnej geometrii;
różnica wysokości odnotowana w raporcie, zero zmian kodu pod to.
**W9** (Q9): prepend GZ_SIM_RESOURCE_PATH przyjęty (dowód R1.7); sha kopii modelu w FREEZE_W
i w manifeście bootu.
**W10** (Q10): V_ENV=6.0 zostaje FLAGĄ; żadnej nowej koperty przed danymi — najpierw pomiar
ground-speed, decyzja o kopercie wiatrowej ewentualnie w raporcie jako propozycja.
**W11** (Q11): protokół wyłączności §8 (zdarzenie z 15–16.09 zamknięte; lock + pgrep + STOP
przy respawnie).
**W12** (Q12): wariant (a) — kampania na poziomach uzbrajalnych z ziemi; (b) ramp ODRZUCONY
w tej nodze (brak źródłowego API runtime — SR-W-4); (c) spawn-in-air = nazwany trigger
przyszłego reżimu ≥4.5.
**W13** (Q13): guard wyjścia §9 (OUTDIR jawny + odmowa przy istniejącym manifeście + lock).
**W14**: fazowanie W-A → W-B z deterministyczną regułą wyłączenia §4; W-A nie dotyka kryteriów;
FREEZE_W przed pierwszym bootem kryterialnym.

## §13. Predykcje CC (prerejestrowane; do KSIEGA_PREDYKCJI przy ANEKS_W-0)

- **P-W-1:** 0 REFUSE jakiegokolwiek rodzaju na całej siatce kryterialnej — p≈0.75.
- **P-W-2:** próba arm z ziemi przy 4.5 m/s = FAIL — p≈0.7.
- **P-W-3:** W-A hover 3 m/s: dead_reckoning=false przez całe okno, eph_max < 1 m — p≈0.75.
- **P-W-4:** parowanie NCP↔executor przy 3 m/s: ≤2 różnice netto (brak załamania architektury
  pod stałym wiatrem) — p≈0.55.
- **P-W-5:** przechył średni w hoverze W-A rośnie monotonicznie z poziomem i separuje 0 od 3 m/s
  — p≈0.8.

## §14. Szkic kanonu roszczeń (finalizacja = aneks zamykający nogę)

WOLNO (kształt): „0 fałszywych REFUSE(POS) w N uzbrojonych epizodach nominalnych pod stałym
wiatrem do 3 m/s (SITL, wektor stały, feed emulowany, komórka c11, kryterium fałszywości
zamrożone przed kampanią)"; „zmierzony próg uzbrajalności z ziemi (H2)"; krzywe degradacji
misji parowane per poziom i ramię. NIE WOLNO: „odporny na wiatr"; jakiekolwiek zdanie
o turbulencji/podmuchach z pomiaru wektora stałego; stopy niezawodności; ekstrapolacja poza
SITL i zmierzone poziomy.
