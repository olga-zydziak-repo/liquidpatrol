# ANEKS_WABIK-1 — przyjęcie S1 (znalezisko: orbita unieważnia rozdzielenie azymutalne; konfiguracja czysta istnieje) + zlecenie S2

CC · 26.10.2026 · łańcuch WABIK (commity nogi na origin: bf776d20 ARCH-1 +
ea49de02 STOP-WABIK1). Aneks samowykonalny w zakresie §4 (sesja S2).
Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-WABIK1

Przyjęte po weryfikacji CC z repo WYKONANIEM: ARCH-1 bajt-w-bajcie (sha PRE
w korzeniu = dokument ratyfikowany, commit osobny); zakres czysty (103 pliki,
wszystkie NOWE, korzeń + results/WABIK/**); **oba werdykty smoke przesędziowane
niezależnie** (import FROZEN 8ec0fcfb, GT manifestu, świadek obok): konfiguracja
A — c08_s01 + W-LOITER — **D6 FAIL [b_frac]** (frac 0.766, d_min 5.14; u
wykonawcy 0.758/5.173 — znany pas GT-manifestu, werdykt identyczny), świadek
0/3310; konfiguracja B — c00_s01 + ten sam wabik — **D6 PASS** (frac 1.000,
d_min 8.11), świadek 0/3367; **statystyka przeskoków odtworzona z surowych**
(atrybucja trk→najbliższy obiekt): A = 24.3% klatek z trackiem na wabiku
(wykonawca: 25.5% na tickach — inny mianownik, ten sam rząd), **B = 0.0% co
do zera**; FREEZE_WABIK powstał PRZED smoke, progi wyłącznie z NULL
(V_RAD_MAX 0.30 vs p95 0.289 + margines ✓, T_FLAG 12 ≤ limit 15 ✓);
reżim OPS 2/2 bootów (pin, profil GUARD, sonda PASS, kadencja 0.068/0.0);
budżet 2/≤3 z deklarowanym powodem zapasu. Breach 0 / REFUSE 0.

## §2. ZNALEZISKO PIERWSZEJ WAGI i korekta projektowa (odchylenie jawne po stronie CC)

**Mechanizm zmierzony co do klatki:** w fazie orbity dron obraca stożek
widzenia przez pełne 360°, więc wabik stojący „w innym sektorze" wchodzi
w kadr cyklicznie; single-target tracker z REFRESH admituje każdy admitowalny
box (wizualia identyczne — admisja wabika 170/170 klatek, gdy był sam
w stożku), przez co track przeskakiwał na wabika w ~25% ticków, wszystkie
w fazach werdyktowych ⇒ kotwica sędziego złamana w konfiguracji A.
**Korekta projektowa: „rozdzielenie azymutalne" z PRE §1 było błędem
projektowym CC** — konfigurację przestrzenną zaprojektowano względem stożka
chwilowego, a fazę orbitalną dało się przewidzieć przy biurku z geometrii
skanu (ta sama arytmetyka, co w TRANSIT). Wpis kalibracyjny do KSIĘGI przy CO:
**konfiguracje przestrzenne projektować per FAZA (scan/track/orbit), nie per
epizod.** Smoke z kotwicą zadziałał dokładnie po to, po co był: wykrył
złamanie, nazwał mechanizm pomiarem i znalazł konfigurację czystą
(separacja ponad zasięg detekcji — B). **Śmierć S1 literą PRE §2.4 NIE
zachodzi** (konfiguracja rozdzielona z utrzymanym intruzem istnieje; spawn
runtime bez dotyku zamrożonych dowiedziony). To nie jest regresja programu —
dwa obiekty były w świecie pierwszy raz w jego historii; to zmierzona granica
zakresu single-target. **Nowa pozycja katalogowa (dopisanie przy CO nogi):
MULTI-TARGET / TOŻSAMOŚĆ TRACKA** — aktywa: pomiar 25.5%/24.3%, mechanizm
REFRESH-admituje-każdy-box, para kontrastowa A/B; trigger: przed jakimkolwiek
roszczeniem z ≥2 obiektami w zasięgu detekcji naraz i przed warstwą decyzji.
NIE otwierana tym aneksem.

## §3. Klasyfikator — przyjęty

Progi FROZEN przed pierwszym lotem, wyłącznie z populacji NULL ✓. Granica
nierozróżnialności zmierzona uczciwie: final-flaga na NULL 13/115 (11.3%),
z czego dominują wędrowce v=0.5 — antycypowana w PRE §1 klasa celów, które
ZACHOWUJĄ SIĘ jak wabiki (to granica metody na tej populacji, nie usterka
progów; rozliczenie wskaźników TP/FP wyłącznie na zbiorach S2). Podłoga
dh_min z odwołaniem zadziałała na smoke zgodnie z intencją: poważny epizod
bez flagi mimo przeskoków tracka.

## §4. Zlecenie S2 — testy celowane (aktywacja PRE §3; budżet ≤8 bootów)

1. **Bramka:** `git fetch` → origin/master zawiera **ea49de02 (STOP-WABIK1)**;
   `origin/master..HEAD` puste ⇒ dalej, inaczej STOP; porcelain PEŁNY (nazwane
   ?? wideo dozwolone). FROZEN wykonaniem: komplet + **FREEZE_WABIK**
   (progi NIETYKALNE — każda zmiana = ANEKS, nie poprawka). Każdy boot:
   reżim OPS. Loty UZBROJONE — twarde STOPy verbatim: breach ⇒ STOP;
   REFUSE(POS) ⇒ STOP; budżet ⇒ STOP; przerwania na granicach bootów.
2. **Jeden obiekt w świecie naraz we WSZYSTKICH testach** (litera PRE §3:
   T-W-TP = wabik solo, T-W-FP i T-W-ORB = intruz solo) — przeskoki z §2 nie
   dotyczą S2.
3. **BENCH_MANIFEST wchodzi pierwszy raz:** manifest WABIK niesie także
   przepisane 1:1 wpisy c08_s03 i c10_s02 (dla T-W-FP); równoważność wpisów
   dowiedziona diffem pól w raporcie (bez dodatkowego bootu).
4. **T-W-TP (6 epizodów):** W-LOITER / W-STYCZNY / W-ZBLIŻ-ODSKOK × 2 warianty
   parametrów (z manifestu). Klasyfikator posthoc z percep_feed; per epizod:
   cechy w oknach, etykieta, czas-do-flagi. **Zdania zamrożone PRE §3.2
   verbatim: SUKCES = etykieta „wabik" w ≤15 s śledzenia w ≥5/6;
   FALSYFIKACJA PROGÓW = ≤2/6 ⇒ STOP-ANEKS.** Pomiędzy: strefa opisowa
   z dekompozycją per cecha.
5. **T-W-FP (3 epizody):** c08_s03, c10_s02 (wpisy 1:1), M-ŁUK. **Zero
   etykiet „wabik"**; każda flaga = dekompozycja, która cecha pękła.
   Kotwica przy okazji: werdykty D6 c08_s03/c10_s02 vs S2-PERC2 (opisowo).
6. **T-W-ORB (2 epizody):** M-POD-ORBITĄ — utrzymanie tracka i separacji pod
   zmianą kursu celu; d_min, D6 opisowo; świadek-filtr obok każdego rachunku
   na GT; GT wabika = log wabik_motion (w S2 nieobecny — intruz solo).
7. **STOP-WABIK2:** commit (RAPORT_WABIK_S2: tabela epizodów
   cechy/etykieta/czas-do-flagi, kotwice FP, wyniki ORB, mody/sondy bootów,
   diff-stat, porcelain). **Push = Olga („wypchnięte" — CC czyta z repo).**
   Po weryfikacji CC: ANEKS_WABIK-2 — werdykt zdaniami zamrożonymi, KSIĘGA
   P-WB-1…6 (w tym uczciwe rozliczenie P-WB-1 i P-WB-2 na NIE z §2 — lekcja
   kalibracyjna fazy orbitalnej), dopisanie pozycji MULTI-TARGET do katalogu
   i CO. STOP.

## §5. Status nogi

Budżet: 2/≤11 bootów wydane; S2 ≤8 ⇒ najwyżej 10/11. Predykcje: P-WB-1
i P-WB-2 rozstrzygną się przy CO na NIE (konfiguracja A — z nazwaną lekcją);
P-WB-3…6 żywe. Nietykalne bez zmian (percepcja, sędzia, osłona, bench,
intruder_motion, manifest istniejący, worlds/*.sdf, FREEZE_PERC2_OPS,
FREEZE_WABIK). Raporty wstecz nietykalne; errata w przód.
