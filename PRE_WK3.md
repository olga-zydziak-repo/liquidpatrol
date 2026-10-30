# PRE_WK3 — prerejestracja nogi WK-III „porywy": NCP-20 na kamerze pod wiatrem zmiennym w czasie, w skalibrowanym habitacie (k ≈ 0.49 /s)

CC · 30.10.2026 · po STOP-WK3R (3274d21b), zweryfikowanym z repo wykonaniem.
Wymaga ratyfikacji Olgi; po niej PROMPT_WK3_S1 — na start DWA dokumenty.

**Weryfikacja reconu (CC, z repo):** światy P1/P2 różnią się od świata
s063_s0 wyłącznie blokiem `<horizontal>` i wektorem średnim (12 / 16 linii);
litera: P1 — średnia 2 m/s, sinus ±40%, okres 8 s, kierunek stały; P2 —
średnia 2 m/s, sinus ±80%, okres 4 s, kierunek ±30° z okresem 11 s. Z JSON-ów
kalibracji: wiatr odtworzony z odpowiedzi drona zgadza się z literą co do
amplitudy (0.814 vs 0.8; 1.617 vs 1.6) i fazy (≤ 2°); opór 0.495 / 0.489 przy
kalibracji 0.494 — habitat bez zmian. Szum losowy bez ziarna w launcherze ⇒
w nodze wyłącznie sinus (deterministyczny, faza od startu świata).

## §1. Teza i pytania (FROZEN)

Teza Olgi: **mała sieć umie latać.** Po WK-II wolno mówić „przy stałym
wietrze do 3 m/s". Ta noga pyta o wiatr zmienny w czasie — jedyną rzecz,
która wymaga od sieci reakcji na zmianę, a nie przesunięcia punktu pracy.

- **Q1 (P1, łagodny):** porywy 1.2–2.8 m/s, okres 8 s, kierunek stały.
- **Q2 (P2, ostry):** porywy 0.4–3.6 m/s, okres 4 s, kierunek ±30° / 11 s.
  Szczyt 3.6 m/s = 1.2× najsilniejszego stałego wiatru z WK-II.
- **Ramię odniesienia:** G1.5 i G3 z WK-II (stały wiatr, ten sam habitat,
  te same komórki) — bez nowych lotów stałych.

## §2. Projekt (FROZEN)

- **Światy:** `worlds/world_wk3_p1.sdf` fe96b096…, `worlds/world_wk3_p2.sdf`
  e47ef380… — bajt w bajt jak w reconie; żadnych nowych światów w nodze.
- **Driver:** NOWY `results/WK3/tools/wk3_boot.sh` = kopia `wk2_boot.sh`
  cf0959ef; zmiany wyłącznie: lista światów (P1, P2 z pełnym sha), katalog
  `results/WK3/booty`, komunikaty. Piny mono_cam 3354ae1e, x500_base 13c9174d,
  profil, sonda, blok manifestu bez zmian. Pełny diff w raporcie.
- **Konfiguracja:** net_fantom (rejestr 87203d29), NET_ARM=ncp, FEED=V2,
  INTRUDER=1, profil DDS a68a450b, sonda kadencji PASS przed uzbrojeniem,
  V2′ ≥ 0.90.
- **Siatka:** c00–c07 × s01, 8 epizodów na profil (4 na boot).
- **Kontrola oporu per boot:** metoda wk3_gust (bilans z literą wiatru
  z SDF — metoda „wiatr stały" zaniża k o 4–17% i jest zabroniona);
  odchylenie > 20% od 0.494 ⇒ STOP do adjudykacji CC.
- **Kolejność (sekwencyjna):** P1 (2 booty) → bramka ≥ 6/8 ⇒ P2 (2 booty);
  P1 < 6/8 ⇒ STOP, werdykt V-C3 bez P2.
- **Sędzia:** bazowy 8ec0fcfb, werdykty ze świadkiem ERRATUM-DMIN i bez;
  bramka ze świadkiem; rozjazd rozstrzygający ⇒ STOP do adjudykacji CC.
- **Epizod nieważny V2′:** jednorazowe dolecenie, liczone do budżetu.

## §3. Osłona, STOPy, werdykty

- Twarde STOPy verbatim: **breach ⇒ STOP; REFUSE(POS) ⇒ STOP; budżet ⇒ STOP.**
  Fałszywy REFUSE(GEOFENCE) ⇒ STOP; prawdziwy = epizod ważny, D6 FAIL, liczony
  osobno; ≥ 3 prawdziwe na profilu ⇒ STOP.
- **Ryzyko nazwane (recon R3): przechył chwilowy w P2 do 34.6° wobec
  pionowego pół-pola kamery 40.4° po marginesie MTI.** Utrata celu z kadru
  dołem jest WYNIKIEM tej nogi (mechanizm „kamera sztywna pod porywem"), nie
  artefaktem — raport liczy odsetek klatek z celem poza kadrem per epizod
  i oznacza porażki, w których poprzedza je wypadnięcie z kadru.
- **Werdykty (prereg):**
  - **V-A3** (P1 ≥ 6/8 ∧ P2 ≥ 6/8): „NCP-20 prowadzi pełną misję na własnej
    kamerze pod wiatrem zmiennym w czasie — porywy do 3.6 m/s (1.8× średniej)
    z okresem 4 s i obrotem kierunku ±30° — w habitacie z realnym oporem:
    D6 a/8 · b/8, breach 0, sejwy n."
  - **V-B3** (P1 ≥ 6/8 ∧ P2 < 6/8): „lata pod łagodnymi porywami (a/8); ostre
    obniżają misję do b/8" + mechanizm z danych (kadr / tor / akwizycja).
  - **V-C3** (P1 < 6/8): „porywy łagodne łamią misję: a/8" + mechanizm.
  - Każdy werdykt zamyka nogę; brak nowych pozycji katalogu z tej nogi.
- **Pomiary opisowe:** sweep/stock per scenariusz (baza FANTOM S2 ze
  świadkiem) i wobec G1.5/G3; składowa styczna komendy i zrealizowanej;
  przechył p50/p95/max; cel poza kadrem (odsetek, kiedy); czas akwizycji;
  k per boot.

## §4. Predykcje CC (do KSIĘGI)

- **P-WK3-1 (0.70):** P1 ≥ 6/8.
- **P-WK3-2 (0.45):** P2 ≥ 6/8 (n.r., jeśli nie poleci).
- **P-WK3-3 (0.60):** w P2 co najmniej jeden epizod z celem poza kadrem
  ≥ 5% klatek (mechanizm przechyłu widoczny w danych).
- **P-WK3-4 (0.90):** breach 0.

## §5. Budżet, higiena, cytowanie

**Budżet twardy: ≤ 8 bootów** (P1 2 + P2 2 + dolecenia/powtórki ≤ 4);
oczekiwane 4. 1 sesja + CO. Env `WK3_*`, katalog `results/WK3/`, nowe pliki
wyłącznie: driver, narzędzia. ZERO edycji istniejących plików; REPO-1/REPO-2,
proc_gate, cooldown. Cytowanie zdaniami z §3 z literą profilu (średnia,
amplituda, okres, kierunek) i „habitat k ≈ 0.49 /s, sinus deterministyczny,
komórki v ≤ 0.5". Nadal nie: „odporna na wiatr" (profil to dwa sinusy, nie
turbulencja); nic o realnym sprzęcie.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
