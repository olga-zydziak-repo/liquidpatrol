# STOP-NADIR1F — sonda S1 NADIR po naprawie ANEKS_NADIR-1: wszystkie śmierci S1 NIE zachodzą (4/4 booty)

Wykonawca · 9.11.2026 · łańcuch NADIR, PROMPT_NADIR_S1 §R (litera pomiarów i śmierci bez zmian) po ANEKS_NADIR-1.
Etap pasywny: rejestrator tylko loguje, lot = nominalny KONT_MODE=1 bez odcięcia GNSS. Konfiguracja v2:
`x500_nadir2_flow` (nadir pod płozami −0.215 m, 5 Hz), `world_nadir2_A3`, manifest v2, OpenCV 4.6.0 systemowe.

## Raport płaski

- **Detekcja ID (R2): 99.93% klatek orbity** z ≥ 1 ID przy boku ≥ 18 px w stożku centralnym (1375/1376; b2′ 99.85%,
  b3′ 100%). Próg ≥ 95% → **PASS**.
  - Parę ID ma 98.8% klatek orbity. Approach 100%, hold 96.5%.
  - Bok najbliższego wykrytego p5/p50 = 18.7/20.6 px (recon 19.6/22.2).
- **Poprawka vs GT (R3), tryb 1 z EKF:** p50 0.50 m, p95 1.04 m (5107 obserwacji). **p95 ≤ model ZMIERZ w każdym
  koszyku r_h** (0–2: 0.20 ≤ 0.32; 2–4: 0.36 ≤ 0.58; 4–6: 0.57 ≤ 0.80; 6–8: 0.75 ≤ 1.01; 8–10: 0.93 ≤ 1.24;
  10+: 1.22 ≤ 1.52) → **PASS**.
  - Para: p95 0.09 m (1420 par).
  - Wkład postawy nazwany: przy postawie i wysokości z GT („piksel”) p95 0.25 m; z postawą EKF p95 0.99 m. Prawie cały
    błąd trybu 1 to postawa estymatora, głównie kurs.
  - **Kurs EKF z pary: δψ p50 −4.0°** — ten sam bias co w KOTW (−3°), teraz zmierzony obserwacją z mapy.
  - Reszta do pozycji EKF max 1.82 m < s/2 = 5 m: asocjacja nie była zagrożona.
- **Percepcja misji na znacznikach (R4): 0 fałszywych admisji na znaczniku, 0 przejęć tracku** (miara po położeniu
  tracku: ≤ 3 m od znacznika ∧ > 5 m od intruza — 0 próbek w b2′ i b3′, tak jak w kontroli KONT bez znaczników) →
  **PASS**.
  - **Mój pierwszy test R4 był za grubą miarą, nazywam to wprost.** Test „środek ramki top-1 w rzucie płyty” daje 10/23
    trafień i 4/21 „REFRESH na znaczniku”. Rozbiór: duża ramka bliskiego intruza zahacza o rzut znacznika (track na
    intruzie, 0.4 m) albo śmieciowa ramka top-1 (conf ~0.001) w wierszu z etykietą stanu feedu.
  - Wszystkie 4 ENTRY w lotach są poza znacznikami (9.9–12.2 m od węzła albo 100 px od rzutu):
    - 2 przed startem epizodu: zaparkowany intruz na 11.4–11.7 m, ten sam artefakt co w kontroli KONT, 138.5 s;
    - 1 w epizodzie na intruzie (b3′ 225.8 s);
    - 1 po misji przy lądowaniu (b2′ 302.9 s, ~3 m wysokości, obiekt gruntu ~100 px od najbliższego znacznika —
      FP poza epizodem, bez związku ze znacznikami).
- **Tempo (R5): bramka settle 0.966 / 0.963, V2′ ważne 4/4 epizody (dsim/dwall 0.950–0.963)** → **PASS**.
- **Identyczność klatek (R1): PASS z b1** (0 px poza maską znaczników 10/10).
  - Montaż v2 nie dodaje geometrii (link bez visuala), więc imager jest bez zmian.
  - **Świata v2 bitowo nie sprawdzałam** (b1 był na v1). Jego różnica wobec v1 to wyłącznie pozycje 7 płyt, a te są
    w masce z definicji. Nazwane, nie zmierzone.
- **Okluzja (R6):** przewidzianych geometrią w stożku 5961 (znacznik × klatka), niewykrytych **3.4%**:
  - pod bryłą 32%, przy bryle 32%, za mały bok 12%, inne 24%;
  - **kadłub 0%** (montaż v2).
  - Do założeń S2: ~3% klatek-znaczników traci się na świat (korony, skrzynki), a nie na kamerę.
- **Werdykt S1: żadna śmierć S1 nie zachodzi.**
- **Budżet:** S1 4/4 (b1 statyczny, b2 przerwany bramką tempa, b2′, b3′), noga NADIR 4/≤30. Breach 0, REFUSE 0.

## Boot b2′ (`b2v2_c08`, epizody 20 c08_s02 i 44 c08_s04) i b3′ (`b3v2_c05c11`, epizody 5 c05_s01 i 23 c11_s02)

- Zegar 0 skoków przed każdym, timesyncd zatrzymany, sieroty 0, /dev/shm sprzątnięte.
- PIN mono_cam 3354ae1e, profil FastDDS a68a450b, sonda percepcji PASS (15.6 Hz).
- Asercja yaw i reinit EKF z drivera KONT bez zmian; oba booty uzbrojone, po 2 epizody, reset_done.
- Rejestrator: 1488 + 1522 klatek nadir (≈ 5 Hz), 0 zgubionych.
  - **Wada drobna:** plik `nadir_obs.jsonl.summary.json` nie powstał, bo proces dostał SIGKILL 4 s po SIGTERM, zanim
    pętla ROS skończyła. Liczniki są w ostatniej linii `nadir_obs_stdout.log`; dane klatek kompletne.

## Pliki

- Analiza: `n1/r2_detekcja.json` (R2 + R6), `n1/r3_poprawka.json` (wszystkie obserwacje), `n1/r4_fp.json`
  (test ramek + tempo/V2′), `n1/r4_trk.json` (R4 po tracku — miara rozstrzygająca).
- Narzędzia: `nadir_s1v2_analyze.py`, `nadir_s1v2_r4trk.py`.

## Do CC

1. **7 węzłów zasłoniętych z góry albo przy bryłach (id 0, 8, 15, 16, 22, 32, 35)** — poza listą aneksu, nieruszone.
   W lotach dają 64% z 3.4% niewykrytych. Detekcja i tak 99.93%; decyzja o manifeście v3 — CC.
2. **Bias kursu EKF −4° (z pary):** tryb 12 go usuwa (para p95 0.09 m). W trybie 1 (EKF) dominuje błąd. Dla S2 FREEZE
   ε_fix per koszyk wyjdzie z lotów bez GNSS, gdzie kurs może dryfować bardziej.
3. **Świat v2 bez osobnego testu bitowej identyczności** — do decyzji, czy wymagać go w S2 (0 bootów, gz).

Sygnał: **STOP-NADIR1F**. Push = Olga (CC przelicza R3 i R4 z logów).
