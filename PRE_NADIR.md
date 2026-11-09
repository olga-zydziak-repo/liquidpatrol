# PRE_NADIR — patrol bez GNSS bez limitu czasu: kamera nadir + siatka znaczników; osłona B (zegar τ) + rama B+ w harnessie; kryteria zamrożone, śmierci prerejestrowane

CC · 9.11.2026 · łańcuch NADIR, po STOP-NADIRR (247d2e93 na origin,
zweryfikowany przez CC: narzędzia uruchomione ponownie, pokrycie
i komórka wiodąca przeliczone niezależnie własnym kodem — c08_s02
zapas 0.116 u CC wobec 0.11 wykonawcy). Ratyfikacja sygnałem
**„ratyfikuję PRE_NADIR"**; sygnały bez numeru wykonawca odrzuca.

## §1. Teza i zdolność

Sieć NCP-20 pod trwałym odcięciem GNSS prowadzi zadanie patrolu
**bez limitu czasu**, a certyfikowana osłona zawiera lot w strefie,
konsumując piłę niepewności ε_fix + ε_b(τ) + Δ_D5, gdzie τ to czas od
ostatniej przyjętej obserwacji znacznika. Zdolność do zmierzenia w S4:
epizody **≥ 110 s (5 × T* z 2d)** pod odcięciem, misja czynna do końca,
zero naruszeń. Granica ambicji: SITL, grunt płaski z dekalem i siatką
znaczników, bez wiatru — dopisek obowiązkowy jak w 2d.

## §2. Konfiguracja FROZEN (z liczb reconu; zmiany tylko aneksem)

1. **Siatka:** s = 10 m, węzeł w (0,0) pod home/hold, |węzeł| ≤ 32 m
   (37 znaczników). Znacznik **W = 1 m, ArUco 4×4 z ID**, płaski na
   gruncie — wariant świata klasy dekalu (addytywny, poza misją).
2. **Kamera nadir:** druga kamera w wariancie modelu x500, oś −z_body,
   f = 270 px, 640×480, stożek centralny 0.8 do admisji obserwacji.
   Kanon kamery misji nietknięty.
3. **Poprawka:** tryb 12 (para znaczników, gdy jest w kadrze — kurs
   z pary; inaczej jeden znacznik). Wariant budżetowy do rachunków:
   ZMIERZ (px 2, δψ 5.81°, δθ 0.5°, δz 0.2 m). Obserwacja przyjęta ⇔
   detekcja z ID ∧ bok ≥ 18 px ∧ reszta do najbliższego węzła < s/2.
4. **Bariera:** u = ε_fix + ε_b(⌊τ⌋) + Δ_D5 ≤ m per komórka; ε_b
   z `s2_freeze_bf.json` (ae19f66c) **bez zmian**, Δ_D5 = 1.524 bez
   zmian, marginesy z r4_margin bez zmian. Zejścia D5 poza u (Δ_D5
   zdjęte z zejść bez poprawek; poniżej ~6 m poprawek się nie wymaga,
   τ rośnie przez zejście i to jest w literze). R-KONT/T* nieaktywne
   w NADIR_MODE; REFUSE(POS) i reszta łańcucha reguł bez zmian.
5. **Architektura — decyzja CC z R3: B + B+ (nie A).** B: zegar τ od
   ostatniej przyjętej obserwacji zamiast t_KONT, reszta osłony jak
   po S3b. **B+ (rama w harnessie):** sieć i feed dostają p_corr =
   p_fix + (p_EKF(t) − p_EKF(t_fix)); setpointy wracają do ramy EKF:
   sp_EKF = sp_net + (p_EKF − p_corr). EKF, PX4, wagi sieci
   i detektor misji nietknięte. Uzasadnienie mechanizmem: tylko przy
   B+ każda liczba bariery zostaje z 2d (ε_b opisuje dryf tego samego,
   nietkniętego EKF); wariant A wymienia estymator i unieważnia krzywą,
   na której stoi dowód. Odmrożenie punktowe: źródło `own_pos`
   w `harness/feed_vision.py` i streamer setpointów — **wyłącznie
   w gałęzi `NADIR_MODE=1`**, z passthrough bitowym przy 0 (wzór
   nakładki KONT; dowód identyczności w S1 i S3). W tej samej gałęzi
   **bramka pozycji przewidywanej** w odświeżeniu tracku
   (`feed_vision.py:196–203`) — warunek niesiony od reconów KOTW.
6. **Środowisko:** instalacja OpenCV z modułem aruco na stanowisku —
   ratyfikacja PRE obejmuje tę zgodę; wersja zapisana w raporcie S1.
7. Standing red test `r02/test_deadman.py` bez zmian — „pełny zestaw
   PASS modulo ten zastany".

## §3. Łańcuch etapów, budżety, śmierci (prereg)

**S1 — sonda (≤ 4 booty).** Model x500 z kamerą nadir + świat ze
znacznikami; pomiary: (i) identyczność klatek kamery misji poza
pikselami znaczników (wzór dekalu KONT); (ii) det_v2 na świecie ze
znacznikami: top-1, admisja k = 3, przejęcie tracku — zero fałszywych
admisji; (iii) detekcja ID nadir na żywo: odsetek klatek orbity
z odczytanym ID znacznika ≥ 18 px; (iv) pierwsza poprawka vs GT;
(v) tempo V2′ ≥ 0.93 z drugim renderem; (vi) okluzja nogami x500
w stożku — zmierzyć, nie zakładać.
**Śmierć S1:** detekcja ID W1 < 95% klatek orbity ∨ |błąd poprawki|
p95 > model ZMIERZ ∨ fałszywa admisja / przejęcie tracku na znaczniku
∨ tempo < 0.93 ∨ klatki misji różne poza znacznikami.

**S2 — charakteryzacja piły pod misją (≤ 6 bootów).** Loty bez GNSS,
B+ w pętli, osłona w trybie obserwatora: (i) warunek ważności B —
przyrost dryfu EKF w oknach [t_fix, t_fix+τ] ≤ ε_b(τ) dla τ ≤ 2 s;
(ii) rozkład rzeczywistych błędów poprawki per koszyk r_h
(0–2/2–4/4–6/6–8/8–10/10+ m); (iii) zachowanie sieci na p_corr:
ENTRY i orbita jak w 2d, zero REFUSE poza barierą, V2′ ≥ 0.93.
**FREEZE aneksem po S2 (lekcja 2d „nauczyciel ≠ sieć"):**
ε_fix_freeze per koszyk = 1.5 × max |błąd poprawki vs GT| zmierzony
w S2 na żywym torze detekcji — S4 sądzi po tej obwiedni, nie po
modelu analitycznym.
**Śmierć S2:** przyrost dryfu w oknie > ε_b(τ) ∨ max u > m w komórce
∨ degradacja misji na p_corr ∨ ε_fix_freeze czyni rachunek R5
pustym (żadna komórka siatki scenariuszy się nie domyka).

**S3 — osłona i certy (≤ 2 booty).** Nakładka NADIR (zegar τ + rama
B+ + bramka predykcji) za `NADIR_MODE=1`; passthrough bitowy przy 0;
certy: **P9_nadir** (piła z resetem zegara: unsat główne + ostrość),
P1/P5/P7 na nakładce; replikacja proverów u CC jak zawsze.
**Śmierć S3:** cert nie przechodzi ∨ passthrough różni się bitowo.

**S4 — bramka (≤ 16 bootów).** 12 epizodów ciętych ≥ 110 s pod
odcięciem (siatka komórek jak KONT S4, w tym 4 komórki wąskie
c08/c11) + 4 nominalne ramię (−). Litera per epizod:
(a) misja czynna do końca epizodu, bez REFUSE;
(b) u ≤ m per tick w fazach misji, z ε_fix_freeze z S2;
(c) margines do R_E > 0 w każdej chwili;
(d) zero natywnego failsafe (offboard do końca);
(e) zdrowie toru: τ_p95 misji ≤ 2 s;
(f) ramię (−): zero fałszywych wejść i REFUSE.
**Śmierć S4:** dowolne naruszenie (a)–(f) = FAIL nogi, nie strojenie.

**Budżet nogi: ≤ 30 bootów** (27 planowych + 3 na stanowisko).
STOPy globalne verbatim: **breach ⇒ STOP; REFUSE(POS) fałszywy ⇒
STOP; budżet ⇒ STOP.** Errata wyłącznie w przód; jedna noga, jeden
łańcuch; ratyfikacje tylko sygnałem numerowanym.

## §4. KSIĘGA (predykcje przy ratyfikacji; dopisek z pierwszym CO)

```
## NADIR — otwarcie nogi (PRE_NADIR, 9.11.2026)
- Recon NADIR (0 bootów): 264/540 kombinacji dopuszczalnych; s10 "0",
  ID W1, tryb 12: 48/48 komórek, wąskie gardło c08_s02 zapas 0.11 m
  (ZMIERZ, tryb 1) / 0.60 m (tryb 12); pokrycie pełną postawą ≥1
  znacznik 100% misji, τ_max ≤ 0.96 s. CC niezależnie: pokrycie 100%,
  r_h p50 3.7 m, c08_s02 zapas 0.116 — zgodne.
- ✗ mechanizmowe CC (rozmowa, 9.11): założenie „poprawka tylko
  w osłonie wystarcza, sieć nie widzi znaczników" obalone w R3 —
  setpointy pozycyjne żyją w ramie EKF, misja bez ramy B+ kończyłaby
  się ~21 s. Znalazł wykonawca; stąd B+ w PRE.
- P-NADIR-1 (0.70): S1 przechodzi w całości (detekcja ID ≥ 95%,
  zero fałszywych admisji, tempo ≥ 0.93).
- P-NADIR-2 (0.75): warunek ważności B przechodzi w S2.
- P-NADIR-3 (0.55): S4 PASS pełną literą (a)–(f).
- P-NADIR-4 (0.90): breach 0 w całej nodze.
- Uwaga kalibracyjna: po dwóch zawyżonych szansach w KOTW powyższe
  dawane ostrożnie; różnica mechaniczna — geometria NADIR położona
  pod kamerą i zmierzona na GT, nie zgadywana.
```

## §CO

Bramka: origin/master == **247d2e93**. Po sygnale „ratyfikuję
PRE_NADIR": commit 1 — korzeń `PRE_NADIR.md` verbatim (byte-check
sha256 z wiadomości CC) + KSIĘGA §4 append-only; potem CC dostarcza
PROMPT_NADIR_S1. Push = Olga.
