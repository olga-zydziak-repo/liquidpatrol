# PRE_WK2 — prerejestracja nogi WK-II „opór realny": NCP-20 na kamerze przy oporze z górnego końca realnego pasma, potem wiatr 1.5 / 3 m/s; schodek w środku pasma

CC · 29.10.2026 · po STOP-WK2R (0d2a5926), zweryfikowanym z repo wykonaniem.
Wymaga ratyfikacji Olgi; po niej PROMPT_WK2_S1 — na start DWA dokumenty.

**Weryfikacja reconu (CC, z repo):** światy kalibracyjne różnią się od świata WK
wyłącznie nazwą, komentarzem i skalą WindEffects. Opór przeliczony niezależnie
inną drogą (orientacja z feedu + prędkość): **0.326 /s przy s = 0.46 i 0.498 /s
przy s = 0.63**, wobec 0.322 i 0.494 w reconie — zgodność około 1%. Prawo siły:
opór liniowy w prędkości i w przybliżeniu kwadratowy w skali (k ≈ 0.117 +
0.936·s^1.96). Interpolacja liniowa CC chybiła o −41%; złapała to tolerancja
kalibracji, a drugi boot trafił w −10% celu. Odniesienie zewnętrzne: domyślny
opór pędowy PX4 (EKF2_MCOEF) 0.15 /s, Faessler i in. 2018 (RA-L) 0.24–0.54 /s
dla quadrocoptera 610 g. Pasmo realne [0.15, 0.55] /s, z zastrzeżeniem różnicy
masy (x500 ma 2.1 kg). Habitat nogi WK (1.05 /s) leżał 1.9× nad górną granicą.

## §1. Teza i pytania (FROZEN)

Teza Olgi: **mała sieć umie latać.** Obiekt jak w PRE_WK: NCP-20 (wagi 0337d5ea)
w konfiguracji kamerowej net_fantom, FEED=V2, reżim OPS, komórki c00–c07.

- **Q1:** czy sieć prowadzi misję przy oporze z górnego końca realnego pasma
  (poziom G, k = 0.494 /s zmierzone) bez wiatru?
- **Q2:** jeśli tak — czy także przy stałym wietrze 1.5 i 3 m/s przy tym samym
  oporze?
- **Schodek** (wyłącznie gdy Q1 nie przejdzie): to samo przy oporze ze środka
  pasma (poziom S, k = 0.322 /s zmierzone). Oba poziomy zapisane tutaj, przed
  jakimkolwiek lotem sieci.

## §2. Projekt (FROZEN)

- **Światy poziomu G:** `worlds/world_wk2_s063_s0.sdf` (s = 0.63, sha 73205686…)
  + NOWE światy wiatrowe s = 0.63 dla 1.5 i 3 m/s z generatora reconu
  (wk2_gen_world.py), sha zapisane przed pierwszym lotem. **Poziomu S:**
  `worlds/world_wk2_k055_s0.sdf` (s = 0.46, sha ff60c065…; nazwa z planu, treść
  s = 0.46) + nowe światy wiatrowe s = 0.46, tylko jeśli schodek ruszy.
- **Model, piny, driver:** jak w nodze WK — x500_base 13c9174d, mono_cam
  3354ae1e, driver `results/WK/tools/wk_boot.sh` (ecf8071c) bez zmian,
  WORLD parametrem; sha świata w manifeście; rozjazd pinu ⇒ STOP bootu.
- **Konfiguracja:** net_fantom (rejestr 87203d29), NET_ARM=ncp, FEED=V2,
  INTRUDER=1, profil DDS a68a450b, sonda kadencji 8df528bb PASS przed
  uzbrojeniem, V2′ ≥ 0.90.
- **Siatka:** c00–c07 × s01, 8 epizodów na poziom (4 na boot). Bez dymu —
  złożenie potwierdził dym nogi WK, zmienia się wyłącznie skala.
- **Kontrola oporu per boot:** k z fazy orbity (metoda reconu); odchylenie
  > 20% od kalibracji ⇒ STOP do adjudykacji CC.
- **Epizod nieważny V2′:** jednorazowe dolecenie tylko tego epizodu, liczone
  do budżetu i nazwane w raporcie.
- **Kolejność (sekwencyjna, wiążąca):**
  1. **G0** (2 booty). Bramka: ≥ 6/8 D6 ⇒ krok 2; < 6/8 ⇒ krok 3.
  2. **G1.5 i G3** z przeplotem (4 booty) ⇒ werdykt na poziomie G.
  3. **S0** (2 booty). ≥ 6/8 ⇒ **S1.5 i S3** z przeplotem (4 booty) ⇒ werdykt
     na poziomie S; < 6/8 ⇒ STOP, werdykt V-D2.
- **Sędzia:** bazowy 8ec0fcfb, GT z manifestu, werdykty z filtrem-świadkiem
  i bez obok siebie; bramki liczone ze świadkiem; rozjazd, który rozstrzyga
  bramkę ⇒ STOP do adjudykacji CC.

## §3. Osłona, STOPy, werdykty

- Twarde STOPy verbatim: **breach ⇒ STOP; REFUSE(POS) ⇒ STOP; budżet ⇒ STOP.**
  Fałszywy REFUSE(GEOFENCE) ⇒ STOP; prawdziwy = epizod ważny, D6 FAIL, liczony
  osobno jako sejw; ≥ 3 prawdziwe na poziomie ⇒ STOP. Kontrola oporu poza
  tolerancją dwukrotnie ⇒ STOP-ANEKS (habitat nie taki, jak skalibrowany).
- **Werdykty (prereg):**
  - **V-A2** (G0 ≥ 6/8 ∧ G3 ≥ 6/8): „NCP-20 prowadzi pełną misję na własnej
    kamerze przy oporze z górnego końca realnego pasma (k ≈ 0.49 /s) i stałym
    wietrze do 3 m/s: D6 a/8 · b/8 · c/8, breach 0, sejwy n."
  - **V-B2** (G0 ≥ 6/8 ∧ G3 < 6/8): „przy realnym oporze lata bez wiatru (a/8);
    wiatr 3 m/s obniża misję do c/8" + mechanizm z danych.
  - **V-S** (G0 < 6/8 ∧ S0 ≥ 6/8): werdykt na poziomie S według wzoru V-A2/V-B2,
    z granicą „górny koniec pasma łamie misję, środek nie".
  - **V-D2** (G0 < 6/8 ∧ S0 < 6/8): „sieć uczona bez oporu nie przenosi się na
    realny opór nawet ze środka pasma" — trigger etapu (b) WK-II (douczenie).
- **Pomiary opisowe:** stosunek sweep do bazy stock per scenariusz, składowa
  styczna komendy i zrealizowana, czas akwizycji, przechył, k per boot.

## §4. Predykcje CC (do KSIĘGI)

- **P-WK2-1 (0.60):** G0 ≥ 6/8.
- **P-WK2-2 (0.45):** G3 ≥ 6/8 (n.r., jeśli nie poleci).
- **P-WK2-3 (0.55):** mediana stosunku sweep G0 / stock ≥ 0.85.
- **P-WK2-4 (0.90):** breach 0 w całej nodze.

## §5. Budżet, higiena, cytowanie

**Budżet twardy: ≤ 18 bootów** (poziom G: 6; schodek: +6; dolecenia
i powtórki: reszta); oczekiwane 6 przy V-A2/V-B2. ≤ 3 sesje + CO. Env `WK2_*`,
katalog `results/WK2/`, nowe pliki wyłącznie: światy wiatrowe z generatora
reconu, narzędzia. ZERO edycji istniejących plików; REPO-1/REPO-2, proc_gate,
cooldown. Cytowanie wyłącznie zdaniami z §3, zawsze z „k zmierzone, pasmo
z PX4 i literatury, stały wektor wiatru, komórki v ≤ 0.5"; kanon W: zakaz
„odporny na wiatr"; nic o porywach.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
