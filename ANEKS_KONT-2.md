# ANEKS_KONT-2 — werdykt S2: profil D5 (hamowanie równoczesne z opadaniem) zjada budżet bariery, T* = 4 s; dwie drogi — zamknięcie nogi z liczbą ALBO ratyfikowana poprawka akcji „brake-first" i 3 ostatnie loty

CC · 6.11.2026 · łańcuch KONT, po STOP-KONT2e (ff93367a na origin).
Dokument dwudrogowy: wykonuje się §CO-Z przy sygnale Olgi **„zamykamy"**
ALBO §CO-B przy sygnale **„ratyfikuję 2B"**. Sygnały bez numeru
odrzucasz. Push = Olga.

## §1. Weryfikacja CC z repo (ff93367a)

- Zakres: 4 pliki, +2691, zero edycji. 0 bootów, budżet 21/45 bez zmian.
- Tabela D4b przeliczona niezależnie przez CC z trace (wektor skoku 3 s
  vs 68–69 okien kontrolnych orbity): c08_s02a 3.64 vs raport 3.69,
  kontrola 1.31 = zgodnie; c00_s02 1.33 vs 1.25, kontrola 1.12 vs 1.16 —
  różnice metody. Zgodność trace↔ulog ≤ 0.041 m wyklucza W-B.
- Korelacja odjazdu z prędkością styczną ~0 przy zakresie v 1.55–2.32 —
  dyskryminator W-C w brzmieniu prereg nie zaszedł. **W-A przyjęty.**
- **Korekta nazwy (✗ kalibracyjne CC):** „sygnatura resetu pozycji"
  z ANEKS_KONT-1e §1 była błędna — liczniki resetów 0 we wszystkich
  lotach. Zjawisko to **szybki płynny odjazd pozycji przy zerwanej
  zgodności z własną prędkością** (1.9–5.1 m/s odjazdu przy raportowanym
  ~0.3 m/s), zaczynający się 0.8–1.2 s po wejściu w zejście, po szczycie
  innowacji przepływu (+0.24–0.30 s), który następuje po szczycie rate
  roll/pitch (+0.12–0.17 s).
- D4a: bias przy odcięciu 0.0005–0.0009 w 5/5 — założenie 1c §3 w oknie
  pomiaru utrzymane; moja hipoteza timestamp_sample 0 bez poparcia
  (kolejne ✗). Ryzyko stanowiska zanotowane: 2/3 bootów s2d startuje
  EKF z biasem na limicie 0.15, raz z błędem yaw 20.5° przy starcie.
- Werdykt liczbowy przy n = 5 (nie zamrożony, opis): Δ_D5 = 1.5 × 2.802 =
  4.20 m ⇒ **T* = 4 s** (koszyk 4: 1.5 × 1.244 + 4.20 = 6.07 > 5.79);
  R_nom ≈ 24.83 m. Monotoniczność reguły: kolejne loty mogą T* tylko
  obniżyć, więc T*(n ≥ 8) ≤ 4 s < 10 s — próg śmierci S2 przekroczony
  nierównością, bez dolatywania.

## §2. Co jest ustalone niezależnie od drogi

1. **Faza orbity działa.** W 5/5 lotów przepływ trzyma xy_valid i nav 14
   przez całe okno ≥ 70 s; ε w kontynuacji ≤ 2.4 m w 4/5 lotów
   (najgorszy 4.02 m), PX4 nie odbiera offboardu. To jest zmierzona,
   nowa zdolność stanowiska — niezależnie od losu nogi.
2. **Budżet zjada wejście w zejście D5**, nie kontynuacja: jednorazowy
   odjazd 1.25–3.69 m (wektorowo) w 2 s od komendy `v_ned = (0,0,vdesc)`,
   w każdym locie ponad kontrolę orbity. Δ skalarnie zależy od kąta
   (uwaga wykonawcy §3.1 przyjęta): uczciwy budżet wektorowy to ~3.7 m.
3. Mechanizm wewnętrzny filtra: [MECHANIZM NIEZMIERZONY]; zmierzona
   sekwencja czasowa wskazuje transjent hamowania równoczesnego
   z opadaniem jako wyzwalacz, ale w danych nie ma zejścia bez
   hamowania (kontrfaktyczny brak).

## §3. Dwie drogi

**Droga Z (zamknięcie teraz).** PRE §4: T* < 10 s ⇒ CLOSED z liczbą.
Zdanie kanoniczne: „Kontynuacja po utracie GNSS na przepływie optycznym:
orbita trzyma błąd pozycji ≤ 2.4 m przez 70 s w 4/5 lotów (najgorszy
4.0 m), ale wejście w zejście profilem D5 — hamowanie równoczesne
z opadaniem — kosztuje jednorazowo do ~3.7 m, więc budżet bariery
wyczerpuje się po T* = 4 s. Zamknięte z liczbą; SITL, grunt z dekalem,
bez wiatru, n = 5 + nierówność monotoniczności."

**Droga B (poprawka akcji, do ratyfikacji).** Rewizja PRE §2.6 w trybie,
w którym R0.3a zrewidowało samo D5 (AUTO.LAND → zejście prędkościowe):
**akcja terminalna KONT = brake-first** — po decyzji zejścia najpierw
`v_ned = (0,0,0)` do |v_xy_EKF| ≤ 0.2 m/s (limit 2.5 s), potem
istniejący profil `safe_descend_step` bez zmian. Uzasadnienie
mechanizmem: pod przepływem zejście nie jest ślepe (aiding żyje), więc
przesłanka R0.3a za równoczesnością („bez dodanego czasu, bo ślepe")
nie obowiązuje; równoczesność jest w danych jedynym wspólnym czynnikiem
wszystkich pięciu odjazdów. **To jest zmiana zamrożonego elementu po
danych — nazwana, wymaga ratyfikacji; stare liczby zostają w raportach.**

Wykonanie drogi B (mieści się w budżecie, S2′ 5/12):
- `results/KONT/tools/kont_s2_probe_bf.py` = kopia probe ze zmianą
  wyłącznie w sekwencji zejścia (brake-first jak wyżej) + asercja
  startowa |błąd yaw vs GT| ≤ 10° przy starcie (ryzyko s2d z D4a;
  naruszenie = boot nieważny, dolecenie). Osłona, analyze, freeze_g —
  nietknięte.
- Loty: **c11_s04, c08_s02b, c02_s01** (3 booty + dolecenia w budżecie).
  Kontynuacja tych lotów uzupełnia ε_b do n = 8; ich zejścia dają
  Δ_bf (≥ 3 pomiary).
- **Reguła decyzyjna (prereg, mechaniczna):**
  (a) którykolwiek lot bf z wektorem skoku 3 s > maksimum jego okien
  kontrolnych (metryka D4, `kont_d4.py` bez zmian) ⇒ transjent nie był
  przyczyną ⇒ **CLOSED natychmiast** z liczbami drogi Z;
  (b) inaczej zamrożenie `kont_s2_freeze_g.py` na n = 8: ε_b ze
  wszystkich 8 kontynuacji, **Δ_D5 = 1.5 × max Δ z zejść brake-first**
  (stara Δ raportowana obok); T* i R_nom tą samą regułą PRE §3;
  **T* < 10 s ⇒ CLOSED**, T* ≥ 10 s ⇒ ANEKS_KONT-3 zamraża i noga idzie
  do S3 wg PRE §4.
- Raport `results/KONT/s2/RAPORT_KONT_S2f.md`, sygnał STOP-KONT2f.

Ocena CC, do decyzji: szansę, że brake-first usuwa odjazd I T* wychodzi
≥ 10 s, oceniam na ~0.4 (sekwencja czasowa wskazuje transjent, ale
mechanizm niezmierzony i odjazd występuje też przy 1.55 m/s). Koszt:
3–5 bootów, jeden wieczór. Każde z zakończeń daje liczbę z mechanizmem.

## §4. KSIĘGA (append-only przy CO którejkolwiek drogi; droga B dopisuje
rozliczenia P-KONT-3/4/5/6 dopiero przy swoim zamknięciu)

```
## KONT S2 (ANEKS_KONT-2, 6.11.2026)
- Droga Z: P-KONT-3 (0.55, T* ≥ 30 s) — ✗ (T* = 4 s, profil D5);
  P-KONT-4 (0.45, koszt bariery 0 scenariuszy) — ✗ (R_nom 24.83 < 26.2;
  koszt ≥ 1 scenariusz); P-KONT-5 — n.r. (S4 nie poleciał); P-KONT-6
  breach 0 — ✓ (cała noga, 21 bootów). [Droga B: te rozliczenia przy
  STOP-KONT2f.]
- ✗ kalibracyjne CC (seria): R-3 „skala przepływu" (obalona S2.0);
  kandydat „samozatrucie BSON" (obalony S2b); „sygnatura resetu pozycji"
  (liczniki 0 — poprawna nazwa: szybki odjazd przy zerwanej zgodności
  pozycja–prędkość); hipoteza timestamp_sample 0 (D4a, bez poparcia);
  ✗ rachunkowe: kolejka 1c §4 liczyła 7 lotów zamiast 8.
- Wady wykonawcy nazwane: próba na sucho ręczna zamiast skryptem
  (1d §2.3, koszt 8 min); klucz `verdict` zamiast `werdykt` w kampanii;
  korekta S2b §2: `ekf2 missing data` nie jest wyróżnikiem awarii
  (jest nim urwany sensor_combined).
- Infrastruktura: launcher s2d (gz przed PX4) usuwa 14/14 FAIL
  drugiego bootu; ryzyko s2d: start EKF z biasem na limicie 0.15
  w 2/3 bootów, raz yaw 20.5° na starcie — asercja yaw w driverach
  od drogi B / S4.
```

## §CO-Z (sygnał „zamykamy")

Bramka: origin/master == ff93367a. Pliki: korzeń `ANEKS_KONT-2.md`
(verbatim, byte-check z wiadomości CC); `KIERUNKI_PO_PLANIE.md`
append-only:

```
## Dopisek stanu katalogu — <data> (CO-KONT-Z, ANEKS_KONT-2)
- **2d KONTYNUACJA PO UTRACIE GNSS — CLOSED z liczbą (droga Z).**
  Przepływ optyczny: orbita bez GNSS trzyma ε ≤ 2.4 m przez 70 s w 4/5
  lotów (najgorszy 4.0 m), PX4 nie odbiera offboardu (launcher s2d).
  Śmierć: wejście w zejście D5 (hamowanie równoczesne z opadaniem)
  kosztuje jednorazowo do ~3.7 m ⇒ T* = 4 s < 10 s (nierówność przy
  n = 5; reguła maksimów). Katalog: 6 pozycji, 2d zamknięta.
```

oraz `results/KSIEGA_PREDYKCJI.md` append-only (§4). Commit
`KONT [CO-KONT-Z]: zamknięcie 2d z liczbą (ANEKS_KONT-2 droga Z)`.
Raport płaski, STOP. Potem CC aktualizuje raport programu (poza repo).

## §CO-B (sygnał „ratyfikuję 2B")

Bramka: origin/master == ff93367a. Commit 1: korzeń `ANEKS_KONT-2.md`
verbatim + KSIĘGA §4 (bez rozliczeń P-KONT-3…6). Commit 2: probe_bf +
asercja yaw. Potem loty §3B, raport, STOP-KONT2f. **CC przelicza z repo;
zamyka ANEKS_KONT-3.**
