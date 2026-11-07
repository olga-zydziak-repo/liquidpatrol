# ANEKS_KONT-4b — po STOP-KONT4-DRIVER: poprawka ROOT w miejscu (wyjątek nazwany), obowiązkowa próba na sucho drivera, rezerwa +1 boota do ratyfikacji

CC · 7.11.2026 · łańcuch KONT, po STOP-KONT4-DRIVER (3e2d2082 na
origin). Wklejany jako jedyny dokument. Sygnały bez numeru odrzucasz.

## §1. Weryfikacja i rozstrzygnięcia

- Przyczyna potwierdzona z repo: `kont_s4_flight.py:31` liczy ROOT
  o dwa poziomy za płytko dla pliku w `results/KONT/tools/`
  (`…/results/KONT/results/BENCH/…` w logu). Boot wstał poprawnie
  (faza 7.604 s, sonda, settle), driver padł przed epizodem. Boot
  liczy się do budżetu po literze: S4 1/16, noga 25/45, lotów 0.
- **1. Poprawka jednej linii w miejscu: ZATWIERDZONA** (wyjątek wzoru
  ANEKS_KONT-1d §2.2 — plik nie wyprodukował żadnego lotu; linia jak
  w `kont_s2_probe_y.py:26`; diff verbatim w opisie commita).
- **2. Próba na sucho: ZATWIERDZONA I OBOWIĄZKOWA przed pierwszym
  bootem.** Dwie części: (i) skrypt asercji wszystkich ścieżek
  zależnych od ROOT (manifest, executor_params, sha, cwd selfchecku,
  intruder_motion) — istnieją i są plikami; (ii) `main()` drivera do
  pierwszego wywołania sieciowego z atrapą MAVSDK/ROS. Artefakty do
  `results/KONT/s4/dryrun/`, commit przed bootem. To druga instancja
  lekcji 1d §2.3 (przyrząd sprawdza się uruchomieniem skryptu, nie
  lintem) — obie do KSIĘGI przy zamknięciu nogi jako wada wykonawcy,
  z kosztem 1 boota tu i 8 minut tam.
- **3. Budżet — dwie opcje, wybór Olgi jednym słowem:**
  - **„ratyfikuję 4b"** ⇒ S4 ≤ 17 bootów (12 cięć + 3 nominały + 1
    rezerwa odtworzona po koszcie drivera); noga maks. 42/45, limit
    PRE ≤ 45 nietknięty. Uzasadnienie: kampania bez luzu zamienia
    pierwszy nieważny epizod w STOP budżetu w środku serii.
  - **brak ratyfikacji** ⇒ zostaje 16: 15 pozostałych bootów na 15
    pozycji, zero dolecenia; nieważny epizod ⇒ STOP budżetu i powrót
    do CC.
- Reszta PROMPT_KONT_S4 bez zmian (siatka, kryteria, drabina, STOPy).

## §CO

Bramka: origin/master == **3e2d2082**. Commit 1: korzeń
`ANEKS_KONT-4b.md` verbatim (byte-check sha256 z wiadomości CC) +
poprawka ROOT + próba na sucho (artefakty). Potem booty: nom_b1
(dolecenie), nom_b2, nom_b3, cięcia wg siatki. Raport STOP-KONT4 jak
w prompcie. Push = Olga.
