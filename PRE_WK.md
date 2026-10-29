# PRE_WK — prerejestracja nogi WIATR-KAMERA: NCP-20 na własnej kamerze w habitacie z oporem aerodynamicznym, wiatr 0 / 1.5 / 3 m/s

CC · 29.10.2026 · po STOP-WKR (4d7d5196), zweryfikowanym z repo wykonaniem.
Wymaga ratyfikacji Olgi; po niej PROMPT_WK_S1 — na start DWA dokumenty.

**Weryfikacja reconu (CC, z repo):** złożony świat różni się od habitatu A3
wyłącznie nazwą świata i blokiem 21 linii (13 systemów + WindEffects + wektor
wiatru); kopia x500_base 13c9174d ma enable_wind na base_link; pin mono_cam
3354ae1e nietknięty. Rejudge kampanii W sędzią bazowym 8ec0fcfb (z filtrem-
świadkiem i bez): wszystkie 16 epizodów D6 FAIL — NCP na obrocie (sweep 367–594°
< 630°), nauczyciel na paśmie (frac 0.69–0.83 < 0.85). **Korekty do reconu
(w przód, bez edycji RECON_WK):** (k1) LIQ c11 NCP w świecie stock ze świadkiem
= **4/4**, nie 3/4 (r6 „d_min 1.26" to artefakt ERRATUM-DMIN, świadek 6.52 PASS);
(k2) d_min w kampanii W według sędziego bazowego **≥ 5.6 m we wszystkich 16
epizodach**, z filtrem i bez — liczby „1.7 / 3.4 / 1.9 m" i „nauczyciel < 4 m"
pochodzą z kolumny „d_min approach" RAPORT_W_S2 sprzed ERRATUM-DMIN i do tego PRE
nie wchodzą; (k3) pełzanie w oknie sędziego z GT drona: 3/8 epizodów W > 15 m
(recon liczył EKF po wierszach epizodu: 4/8) — wniosek bez zmian.

## §1. Teza i dwa pytania (FROZEN)

Teza Olgi: **mała sieć umie latać.** Obiekt: NCP-20 (1903 parametry, wagi
0337d5ea) w kanonicznej konfiguracji kamerowej (net_fantom, FEED=V2, reżim
OPS), w habitacie z modelem aerodynamicznym (enable_wind — opór działa także przy
wietrze 0), na komórkach c00–c07 (v ≤ 0.5; c08–c11 to zmierzony sufit profilu
misji). Sieć uczono i sprawdzano w świecie bez tego oporu, więc noga ma dwa
pytania, w tej kolejności:

- **Q1 — habitat:** czy sieć prowadzi misję przy wietrze 0 w habitacie z oporem
  (WK0)? Recon pokazał, że sam opór łamał c11 obu ramionom na feedzie emulowanym.
- **Q2 — wiatr:** jeśli tak, jak zmienia się D6 przy 1.5 i 3 m/s (WK1.5, WK3)?

## §2. Projekt (FROZEN)

- **Świat:** `world_wk_{s0,s1p5,s3}` skopiowane jako NOWE pliki do `worlds/`
  (wymóg world_hash.sh), bajt w bajt z `results/WK_RECON/worlds/` (sha s0
  4c179a14, s1p5 9713a8b1, s3 3a605ca3 — sprawdzane przed każdym bootem).
- **Model:** kopia x500_base 13c9174d (FREEZE_W) przez prepend
  GZ_SIM_RESOURCE_PATH; binaria odtworzone według README jako pliki nieśledzone.
  Piny per boot w manifeście: mono_cam 3354ae1e + x500_base 13c9174d + sha świata;
  rozjazd ⇒ STOP bootu.
- **Driver:** nowy plik, kopia perc2_s2_boot.sh; zmiany wyłącznie: WORLD, prepend
  ścieżki zasobów, dwa piny, sha świata w manifeście.
- **Konfiguracja:** CONTROLLER=net_fantom (rejestr 87203d29), NET_ARM=ncp,
  FEED=V2, INTRUDER=1, profil DDS a68a450b, sonda kadencji 8df528bb PASS przed
  uzbrojeniem (k = 1), ważność V2′ ≥ 0.90.
- **Siatka:** c00–c07 × ziarno s01 = 8 epizodów na poziom (4 na boot ⇒ 2 booty
  na poziom). Jeden stały kierunek wiatru +x ENU; orbita omiata wszystkie
  kierunki względne. Ramię nauczyciela: NIE (diagnostyczne, nie służy tezie;
  wpływ habitatu na nauczyciela jest już zmierzony na c11).
- **Kolejność (sekwencyjna, wiążąca):**
  1. **Dym** (1 boot, world_wk_s3, intruz statyczny c00): model ładuje się z
     enable_wind (dryf i przechył z ulogu), sonda k = 1, ≥ 1 admisja, world_hash
     i oba piny w manifeście. Wykonalność, nie pomiar — poza D6.
  2. **Etap A — WK0** (2 booty, 8 epizodów). **Bramka:** WK0 ≥ 6/8 D6 ⇒ etap B;
     WK0 < 6/8 ⇒ STOP i werdykt V-C (wiatru nie latamy, bo byłby skonfundowany
     habitatem). Próg z bazy kamerowej stock na tych komórkach (FANTOM S2 28/29,
     AKW S3 32/36) z luzem na 1–2 sejwy z pełzania.
  3. **Etap B — WK1.5 i WK3** (po 2 booty, 8 epizodów każdy).
- **Sędzia:** bazowy 8ec0fcfb, GT z manifestu, **filtr-świadek ERRATUM-DMIN obok
  każdego werdyktu.**

## §3. Osłona, STOPy, werdykty

- Twarde STOPy verbatim: **breach ⇒ STOP; REFUSE(POS) ⇒ STOP; budżet ⇒ STOP.**
- **REFUSE(GEOFENCE):** prawdziwy (estymator zdrowy według w_judge e68040ae,
  ε_false = 2.0 m) ⇒ epizod WAŻNY, liczony osobno jako sejw osłony (D6 FAIL);
  fałszywy ⇒ STOP. **≥ 3 prawdziwe GEOFENCE na jednym poziomie ⇒ STOP** —
  pełzanie dominuje, noga zamyka się zdaniem o pełzaniu.
- Boot nieważny (V2′, sonda, env-fail): jedna powtórka na poziom; druga ⇒ STOP.
- **Werdykty (prereg):**
  - **V-A** (WK0 ≥ 6/8 ∧ WK3 ≥ 6/8): „NCP-20 prowadzi pełną misję na własnej
    kamerze w habitacie z oporem aerodynamicznym przy stałym wietrze do 3 m/s:
    D6 a/8 · b/8 · c/8 (0 / 1.5 / 3 m/s), breach 0, sejwy osłony n."
  - **V-B** (WK0 ≥ 6/8 ∧ WK3 < 6/8): „lata w habitacie z oporem przy wietrze 0
    (a/8); wiatr 3 m/s obniża misję do c/8" + mechanizm z danych.
  - **V-C** (WK0 < 6/8): „sam habitat z oporem łamie misję kamerową sieci
    uczonej bez oporu: a/8" + mechanizm z danych. To wynik, nie śmierć.
- **ŚMIERĆ nogi (prereg):** złożenie niewykonalne na dymie (model nie ładuje
  wiatru, sonda k = 1 nie przechodzi albo brak admisji) w 2 podejściach ⇒
  STOP-ANEKS z diagnozą, punkt odroczenia.
- **Pomiary opisowe** (raport, nie bramka): pełzanie (alt_max, mediana cmd_vz),
  przechył p50/p95, obecność celu w kadrze, sweep i frac per epizod, czas
  akwizycji, odsetek klatek z MTI ok przy wietrze wobec WK0.

## §4. Predykcje CC (do KSIĘGI)

- **P-WK-1 (0.85):** dym PASS za pierwszym podejściem.
- **P-WK-2 (0.55):** WK0 ≥ 6/8 (bramka etapu A przechodzi).
- **P-WK-3 (0.40):** WK3 ≥ 6/8 (n.r., jeśli etap B nie poleci).
- **P-WK-4 (0.90):** breach 0 w całej nodze.
- **P-WK-5 (0.60):** co najmniej jeden prawdziwy sejw GEOFENCE w nodze.

## §5. Budżet, higiena, cytowanie

**Budżet: ≤ 9 bootów** (dym 1 + kampania 6 + ≤ 2 powtórki), ≤ 2 sesje + CO.
Env `WK_*`, katalog `results/WK/`, nowe pliki: światy WK w `worlds/` (kopie
bajt w bajt), driver, narzędzia; binaria modelu wiatrowego nieśledzone. ZERO
edycji istniejących plików; reguły REPO-1/REPO-2, proc_gate, cooldown.
NIETYKALNE: wagi, kod sieci, osłona, sędzia, percepcja, komplet FROZEN.
Cytowanie wyłącznie zdaniami V-A/V-B/V-C, zawsze z kwalifikatorem „habitat
z oporem aerodynamicznym, stały wektor wiatru, komórki v ≤ 0.5". Kanon W
obowiązuje: **zakaz „odporny na wiatr"**; nic o porywach i turbulencji.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
