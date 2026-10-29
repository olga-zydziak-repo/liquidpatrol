# ANEKS_WK2-1 — przyjęcie S1, werdykt nogi WK-II (V-A2), KSIĘGA P-WK2-1…4, CO (samowykonalny)

CC · 29.10.2026 · po STOP-WK2-1 (ARCH-1 `f68b51e9` + `3b64c4e0`), zweryfikowanym
z repo wykonaniem. §5 = zlecenie CO. Sygnały bez numeru wykonawca odrzuca.

## §1. Weryfikacja CC (niezależna) + errata w przód do PRE_WK2 §2

1. **ARCH-1 PASS:** `PRE_WK2.md` bajt w bajt (f83973c6…). Commit `3b64c4e0`:
   wyłącznie nowe pliki. Światy wiatrowe poziomu G różnią się od świata
   kalibracyjnego s = 0.63 tylko nazwą i wektorem wiatru (4 linie diffu);
   sha b8a9c8b7 / f8ccc51c zgodne z raportem. Driver `wk2_boot.sh` = kopia
   `wk_boot.sh` z różnicą wyłącznie w liście światów (z sha), katalogu wyjścia
   i komunikatach — piny i blok manifestu nietknięte. W logu każdego z 6 bootów:
   PIN OK ×2 + sha świata zgodny ze światem poziomu.
2. **Errata w przód do PRE_WK2 §2** („driver wk_boot.sh bez zmian, WORLD
   parametrem"): niewykonalne — driver WK odmawia światów spoza własnej listy
   i pisze do `results/WK`. Adjudykacja CC z 29.10 (decyzja Olgi): nowy driver
   jak wyżej. Odchylenie tej samej klasy co „route→orbit" w nodze W (etykieta
   z PRE niewykonalna literą narzędzia, złapana odmową zamrożonego przyrządu).
   PRE bez edycji.
3. **Rejudge sędzią bazowym 8ec0fcfb, ze świadkiem ERRATUM-DMIN i bez,
   wszystkie 24 epizody:** G0 **8/8** (pełny 8/8), G1.5 **6/8** (6/8), G3
   **8/8** (pełny 7/8 — c07 d_min 7.59 w obu, rozjazd na b_frac to artefakt
   pierwszych próbek GT, świadek rozstrzyga). Ważne V2′ 24/24. Mediana
   sweep/stock: 0.858 / 0.834 / 0.895 — co do liczby z raportem.
4. **Opór per boot, własna metoda** (orientacja z feedu + prędkość):
   0.496 / 0.495 (G0), 0.500 / 0.478 (G1.5), 0.511 / 0.504 (G3) — kalibracja
   0.494 trzyma w ±4%; habitat był taki, jak zamrożony.
5. **Porażki G1.5 przeliczone z logów:** c03 — pierwszy ważny track po 30.7 s,
   wejście w pasmo po 33.6 s (limit 25 s), potem pełna orbita (sweep 819°,
   frac 1.00); c06 — track stracony w t_rel 1.1–25.7 s (484 z 1879 ticków
   w hold), cel v = 0.5 podszedł, po ponownej akwizycji d_min 3D 3.28 m
   w t_rel 26.4 s, sweep 573°. Oba scenariusze zdały przy 0 i 3 m/s. Obie
   porażki to akwizycja/percepcja, nie tor orbity; wiatr 1.5 m/s nie ma
   dla nich mechanizmu (przy 3 m/s obie przeszły).

## §2. Werdykt (zdania zamrożone)

**Noga WK-II CLOSED werdyktem V-A2, 6/≤18 bootów (schodek S niepotrzebny);
śmierć nie zaszła; breach 0 / REFUSE 0 / sejwy 0.**

> **V-A2.** NCP-20 (20 neuronów, 1903 parametry, uczona bez oporu) prowadzi
> pełną misję na własnej kamerze w habitacie z oporem aerodynamicznym z górnego
> końca realnego pasma (k zmierzone 0.49 /s; pasmo [0.15, 0.55] /s z PX4
> EKF2_MCOEF i Faessler i in. 2018, z zastrzeżeniem masy) przy stałym wietrze
> 0 / 1.5 / 3 m/s z jednego kierunku, komórki v ≤ 0.5: **D6 8/8 · 6/8 · 8/8**,
> breach 0, sejwy osłony 0, przechył w zawisie 4.3° / 8.6°. Obie porażki
> przy 1.5 m/s to akwizycja (c03: track po 30.7 s; c06: utrata tracka na
> 25 s z d_min 3.3 m po ponownej akwizycji), nie tor orbity — oba scenariusze
> zdały przy 0 i 3 m/s. Tempo orbity: sweep 0.83–0.90 stocku (przy k = 1.05:
> 0.67), komenda styczna 1.84–1.87 wobec 1.96 m/s, realizacja 0.94 wobec 1.05.

**Co z tego wynika dla tezy „mała sieć umie latać":** granica z nogi WK
(k = 1.05 /s, 2/8) leżała 1.9× nad realnym pasmem; w górnym końcu pasma sieć
zdaje 22/24. Zdanie do raportu: „sieć uczona w świecie bez oporu przenosi się
na opór z górnego końca realnego zakresu i na stały wiatr do 3 m/s; pęka
dopiero przy oporze ~2× ponad realny". Nie wolno: „odporna na wiatr", nic
o porywach/turbulencji, nic o realnym sprzęcie (kanon W).

**Fizyka (opisowo, rozstrzyga otwarty punkt RECON_WK2 R1):** wyraz wolny
bilansu sił przy wietrze równa się k·w co do 1–2% (0.745 / 1.49 m/s² przy
1.5 / 3 m/s) ⇒ opór, także wirnikowy, liczony jest względem powietrza.

## §3. KSIĘGA — rozliczenie P-WK2-1…4 (4 ✓)

- **P-WK2-1 (0.60) ✓** — G0 8/8.
- **P-WK2-2 (0.45) ✓** — G3 8/8.
- **P-WK2-3 (0.55) ✓** — mediana sweep G0/stock 0.858 ≥ 0.85 (margines 0.008 —
  trafienie na krawędzi, zapisane jako takie).
- **P-WK2-4 (0.90) ✓** — breach 0.

Lekcje kalibracyjne: (1) etykietę narzędzia w PRE („driver bez zmian, parametr
X") sprawdzać literą tego narzędzia przed zamrożeniem — druga wpadka tej klasy
po route→orbit; (2) prognoza nieliniowości (opór ~ skala²) chybiła o 41%
i uratowała ją tolerancja kalibracji — zapisywać tolerancje przy każdej
interpolacji z dwóch punktów.

## §4. Następcy (KATALOG — nic nie otwieram)

- **Pozycja WK-II etap (b) „douczenie w habitacie z oporem" — SKREŚLONA:**
  trigger (V-D2) nie zaszedł.
- **Pytanie nazwane (nie pozycja):** akwizycja pod wiatrem 1.5 m/s — dwa
  epizody z 8 z późną/utraconą akwizycją wobec 0/8 przy 0 i 3 m/s; przy n = 8
  nierozróżnialne od wariancji. Wraca do istniejącej pozycji PERCEPCJA-II (ii)
  MTI-czołowy jako dodatkowy przypadek, bez nowej pozycji.
- Bez zmian: TOR-CECHY ∪ MULTI-TARGET, IMITACJE, daleki wzrok, ODPOWIEDŹ-
  EKONOMIA, 2c, 2d, 2e.

## §5. CO — zlecenie (lista zamknięta edycji)

1. Bramka: `git fetch` → origin/master == **3b64c4e0**; `origin/master..HEAD`
   puste; porcelain czysty poza nazwanymi ??.
2. Commit CO-WK2 (jeden): (a) `ANEKS_WK2-1.md` verbatim do korzenia (ARCH-1:
   byte-check sha256 z wiadomości CC — rozjazd ⇒ STOP); (b)
   `KIERUNKI_PO_PLANIE.md` dopisek 29.10 append-only: WK-II CLOSED (V-A2) ze
   zdaniami z §2 i odsyłaczami (RAPORT_WK2_S1, RECON_WK2); etap (b) skreślony;
   pytanie o akwizycję pod 1.5 m/s dopisane do PERCEPCJA-II (ii); (c)
   `results/KSIEGA_PREDYKCJI.md` sekcja NOGA WK-II append-only, treść §3.
3. ZERO edycji raportów, reconu, FREEZE, PRE i kodu.
4. Push = Olga („wypchnięte" — CC zamyka nogę z repo). STOP.

## §6. Status

Wątek wiatr+kamera zamknięty w dwóch nogach: 9 bootów łącznie (3 + 6),
breach 0 / REFUSE 0. Program zyskał: habitat z oporem skalibrowanym do fizyki
(wzór dla każdej przyszłej nogi fizycznej), pomiar, że opór w symulatorze
liczy się względem powietrza, oraz pierwszy wynik sieci w fizyce innej niż
treningowa. Katalog: 9 → 8 pozycji. Raport programu dostaje nowy punkt
w „Co system potrafi" i korektę granicy w „Czego nie potrafi".
