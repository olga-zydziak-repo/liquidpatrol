# RAPORT_MTI_DIAG — analiza artefaktów bramki MTI (offline, ZERO lotów, ZERO budowy)

Data: 2026-08-16. HEAD wejściowy `e4c76ba` (RAPORT_MTI). Reżim: sesja pracuje **wyłącznie** na
artefaktach `results/R02/mti/**` (B4 charakteryzacja + B5 bramka). **Każda liczba niżej nosi etykietę
PROJEKCJA OFFLINE ≠ POMIAR.** Zdanie wprost (SR-D4): **projekcja przewiduje, pomiar rozstrzyga** —
decyzje i re-bramka live należą do Olgi po STOP. Artefakty tej sesji: `results/R02/mti/DIAG/`.

Stop-rules honorowane: **SR-D1** zero lotów (brak danych = raport braków). **SR-D2** zero zmian w
PRE / kodzie bramy / config / frozen / certach — kod DIAG to osobny instrument analityczny, brama
`r02/target_channel.py` NIETKNIĘTA; aneks żyje jako dokument-propozycja. **SR-D3** unit-test
symulatora **PASS 8/8** przed liczeniem. **SR-D5** artefakty w `DIAG/`, nigdy `/tmp`.

---

## D0 (ustalenie nadrzędne) — czego w artefaktach NIE MA. To przestawia całą sesję.

Prompt zakłada istnienie „per-frame logów hitów MTI, komponentów, struktury, attitude, poz, trace'ów
obu scen FP". **Ta przesłanka jest fałszywa dla utrwalonych artefaktów** i to falsyfikuje wykonalność
D1, D2 i D4, zanim policzymy cokolwiek.

**Mechanizm braku** (`results/R02/mti/mti_flight.py`): funkcja `decide_once()` zwraca rekord per-tick
`{sim_t, has_box, conf, central, n_comps, mti_ok, gate, entry, locked}`; `run_dwell()` zbiera je w
liście `recs`, po czym **agreguje przez `summ()`/zliczenia i listę PORZUCA**. Na dysk trafia tylko
`result.json` — agregaty per-sweep. Potwierdzenie negatywne: `grep` po wszystkich logach
(`agent/bridge/stack/px4/mti`) na `mti_ok|bearing|"gate"|tick=` → **0 trafień**. Węzeł subskrybuje
**tylko** `vehicle_attitude` (linia 79) — brak `vehicle_local_position`/odometrii; `position_velocity_ned`
czytane **raz** (alt do startu, linia 206). Pełny inwentarz: `DIAG/missing_fields.json`.

| pole per-tick potrzebne przez D1/D2/D4 | utrwalone? |
|---|---|
| sekwencja bramy `gate`/`mti_ok` per tick | **NIE** (recs porzucone; przeżywa frakcja `coverage_gate`) |
| pozorny ruch celu `|Δbearing|` (środek boxa cx,cy) | **NIE** (rec trzyma tylko bool `central`, nie cx,cy) |
| manewr platformy `|ω|`,`|v_lat|` per klatka | **NIE** (attitude buforowane→porzucone; przeżywa pairing-resid median) |
| ego-poza (pozycja) synchroniczna per klatka | **NIE** (brak subskrypcji local_position) |
| historia bearingu tracku, baseline `B_perp` | **NIE** |

**Konsekwencja atrybucyjna** (dotyka tezy RAPORT_MTI): `gate = box ∧ central ∧ mti_ok` zapisany jest
**łącznie**; człony `central` i `mti_ok` per tick były w porzuconych recs. Z przeżywających agregatów
**nie da się rozdzielić**, czy klatkowy spadek `coverage_gate` napędza człon MTI, czy centralność.
Teza „człon MTI przerywany klatkowo" opiera się na obserwacji **nie-utrwalonej** — w tej sesji
nieweryfikowalna.

---

## D1 — test mechanizmu: **NIEWYKONALNY** (raport braków, nie bieg)

Predykcja prerejestrowana (missy MTI klastrują przy ruchu pozornym ~0; hity przy manewrach) wymaga
trzech strumieni per-klatka: `|Δbearing|` celu, `|ω|/|v_lat|` ega, hit/miss MTI. **Wszystkie trzy
nieobecne** (D0). Histogram interwałów między hitami MTI również wymaga sekwencji hitów — nieobecnej.

**Werdykt D1:** hipoteza mechanizmu (geometria pościgu nulluje pozorny ruch celu — OBSERVE trzyma LOS,
derotacja usuwa rotację nie translację, cel na tle nieba quasi-statyczny ⇒ diff≈0; paralaksa tła daje
kandydatów FP zjadanych przez persist) **POZOSTAJE NIETESTOWANA — ani potwierdzona, ani obalona.**
Nota: re-placer intruza z założenia **oscyluje bocznie** (`mti_flight.py` nagłówek, linia 6) — projekt
celowo wstrzykuje ruch względny; czy pościg go nulluje, to dokładnie pytanie D1, którego artefakty nie
rozstrzygają. *(Nota kalibracyjna z promptu: predykcja służy falsyfikacji, nie trafieniu — tu nie ma
czego falsyfikować bez danych.)*

**Poszlaka pośrednia (NIE dowód), z agregatów:** `fix3@5m` ma `coverage_gate=0.393` (39% klatek bramy)
lecz `n_entry=0` — mimo licznych hitów bramy **ani jednej serii 3 spójnych** (`ENTRY_K=3`). To spójne
z obrazem „hity MTI klatkowo rozrzucone, nie ciągłe", ale **nie wyróżnia** hipotezy nullowania od
zwykłej klatkowej utraty koincydencji. Poszlaka, nie mechanizm.

---

## D2 — projekcja okna K: **symulator gotowy (SR-D3 PASS), brak wejścia realnego**

Symulator `DIAG/gate_sim.py` odtwarza **pełny** łańcuch okno→streak→ENTRY→ZOH-hold (nie skrót),
uzgodniony z `r02/target_channel.py` (`ENTRY_K=3`, `THETA_AGE_S=3.0`, `L_DELIVER_S=0.1`,
`decision_hz=2.0`→tick 0.5 s). Tryby: `consecutive` (wierny obecnej bramie) i `window` (m-of-M,
proponowane złagodzenie). **Unit-test `DIAG/test_gate_sim.py`: PASS 8/8** (SR-D3) — na syntetycznych
śladach o znanym wyniku (all-True→ENTRY@K; naprzemienny→brak ENTRY consecutive, ENTRY window;
pusty→0; izolowane spajki→0; ZOH trzyma <θ_age, wygasa >θ_age; jednostki czasu).

**Pułapka obsłużona jawnie:** okno zmienia wejście łańcucha persist, więc projekcja odtwarza **całą**
logikę — dlatego symulator, nie skrót. **ALE:** `coverage_gate_K` i `ε_FP_K` są **zależne od kolejności**
booleanów bramy per tick; z artefaktów znamy tylko **liczbę** klatek bramy (`round(cov_gate·n_ticks)`)
i `false_gate_frames` (50/26/46), **nie ich układ czasowy**. **Bez sekwencji per-tick tabela
K×(coverage, FP) na REALNYCH logach nie istnieje.**

**Werdykt D2:** instrument zwalidowany i gotowy; **projekcja na danych zmierzonych NIEWYKONALNA** —
żadne zmierzone K nie może być wybrane offline. Wybór K „z rozkładu, nie z ręki" (jak żąda prompt)
wymaga biegu z logowaniem per-tick (re-instrumentacja `recs`→JSONL). Symulator zostaje jako narzędzie
do policzenia tabeli **natychmiast**, gdy taki bieg dostarczy sekwencji.

---

## D3 — projekcja ENTRY-once (MTI tylko do admisji): **JEDYNA noga policzalna, wynik korzystny**

Definicja projekcji: MTI wymagane **wyłącznie do ADMISJI** (ENTRY); po admisji kanał karmi
**struktura** (`coverage_seen`); EXPIRE/sufit/age bez zmian; utrata struktury → starzenie jak dotąd.
Ta noga **nie potrzebuje** sekwencji per-tick — opiera się na polach, które przeżyły agregację:
`n_entry`, `time_to_entry_s`, `coverage_seen`, `coverage_locked_post_entry`, `false_entry`.
Skrypt: `DIAG/d3_entry_once.py` → `DIAG/d3_entry_once.json`.

**(i) czas-do-ENTRY per bieg** [PROJEKCJA z agregatów]:

| zasięg | fix1 | fix2 | fix3 | admisja |
|---|---|---|---|---|
| 5 m | 2.73 s | 3.08 s | **brak (n_entry=0)** | **2/3** |
| 7 m | 5.29 s | 1.66 s | 2.64 s | **3/3** |
| 9 m | 7.39 s | 2.18 s | 4.23 s | **3/3** |

**(ii) pokrycie kanału po admisji** [PROJEKCJA]: `coverage_locked_post_entry = 1.0` w każdej komórce
z admisją; `coverage_seen = 1.0` wszędzie. Pod ENTRY-once pokrycie operatywne po admisji = `coverage_seen`
= **1.0**. *Kawеat:* `coverage_locked_post_entry=1.0` jest częściowo ZOH-age hold — ale `coverage_seen=1.0`
(YOLO trafia strukturę każdy tick) znaczy, że lock jest **realnie odświeżany**, nie tylko dryfuje ZOH.

**(iii) kryterium (−) pod ENTRY-once** [PROJEKCJA]: `false_entry = 0` na `fp_empty` ∧ `fp_bg`, ×3 booty.
ENTRY-once **nie zmienia progu admisji** (dalej box∧central∧mti_ok, streak K) — zmienia tylko to, co
dzieje się PO admisji. Zatem 0 fałszywych ENTRY pozostaje 0. `false_gate_frames` 50/26/46 wciąż
pochłaniane przez persist+streak (0 ENTRY). **(−) NIENARUSZONE.**

**Werdykt D3 [PROJEKCJA]:** re-scope do ADMISJI przenosi **(+) z FAIL do PASS na 7 m i 9 m** (admisja
3/3, pokrycie po admisji 1.0 ≥ 0.8) oraz **2/3 na 5 m**, **bez naruszenia (−)**. Jedyna komórka bez
admisji: **fix3@5m** (najbliższy zasięg = najgorszy, zgodnie z `note_5m`) — 39% klatek bramy, lecz zero
serii 3-spójnych. To jest **zmiana DEFINICJI bramy** (nie strojenie kryterium PRE_R02C) → szkic
`ANEKS_MTI_2` niżej; wymaga **jednej re-bramki live**.

---

## D4 — wykonalność MTI-P (test anty-statyczny triangulacją): **ZATRZYMANY na braku pól (SR-D4)**

Test wymaga per track: historii bearingu + **synchronizowanej ego-pozy per klatka** → rezydual
hipotezy „obiekt statyczny", osobno cel vs komponenty tła, przy dostępnym `B_perp`. Braki (D0):
historia bearingu **nieobecna**; ego-poza (pozycja) per klatka **nieobecna** (brak subskrypcji
`vehicle_local_position`); `B_perp` **niewyznaczalny** bez translacji ega. Dodatkowo geometria pościgu
dead-ahead bywa **zdegenerowana** (czysty tail-chase, `B_perp≈0`) nawet gdyby pozy były logowane.

**Werdykt D4:** **STOP na braku pól** — żadnych doróbek biegów w tej sesji (SR-D1/D4). MTI-P niewykonalny
bez re-instrumentacji: `+bearing_history`, `+vehicle_local_position` synchroniczne, `+baseline B_perp`.
To osobna noga (nowy mechanizm MTI), nie projekcja z istniejących artefaktów.

---

## D5 — rekomendacja rutowania

Podsumowanie wykonalności z artefaktów:

| noga | co robi | status z artefaktów | koszt re-bramki live |
|---|---|---|---|
| **(a) okno K** | złagodź streak do m-of-M | **BLOKADA** — brak sekwencji per-tick; symulator gotowy | bieg z logowaniem per-tick **+** re-bramka |
| **(b) ENTRY-once** | MTI tylko do admisji | **POLICZALNA, (+) PASS 7/9m, (−) intakt** [PROJEKCJA] | **1 re-bramka live** pod zrewidowaną definicją |
| **(c) MTI-P** | test anty-statyczny triangulacją | **BLOKADA** — brak bearingu+pozy+baseline; geom. często zdegenerowana | re-instrumentacja + wiele biegów + nowy mechanizm |

**Rekomendacja: (b) ENTRY-once jako droga główna, natychmiast.** Jest to jedyna noga, którą artefakty
**wspierają danymi**, i projektuje korzystnie: (+) domyka się na 7 m i 9 m (admisja 3/3, pokrycie po
admisji 1.0), (−) nienaruszone, dowód to zmiana **definicji** bramy (wzorzec rewizji A-drift→A-plateau:
kryteria PRE_R02C nietknięte, definicja rewidowana jawnie). Szkic: `ANEKS_MTI_2` (dokument-propozycja,
**nie nanoszony** do PRE — SR-D2).

**Kombinacja zalecana:** (b) teraz (najtańsza, wsparta danymi) → jedna re-bramka live pod ENTRY-once,
która przy okazji **musi** dołożyć logowanie per-tick (`recs`→JSONL) i subskrypcję `vehicle_local_position`.
Ten sam bieg **odblokowuje (a)** (sekwencja per-tick → tabela K przez `gate_sim.py`) **i (c)**
(bearing+poza→triangulacja). Czyli: (b) rozstrzyga rutowanie, a jego instrumentacja czyni (a)/(c)
policzalnymi w następnej iteracji — bez ślepego mnożenia biegów.

**Gdyby Olga odrzuciła zmianę definicji:** żadna projekcja z obecnych artefaktów nie domyka (+) pod
**oryginalnym** kryterium (coverage_gate ciągłe ≥0.8) bez naruszenia (−) — bo to kryterium żąda
koincydencji MTI na ≥80% **klatek**, a mediana to 0.393/0.632/0.632. Wtedy rekomendacja jawna z promptu:
**akty dema na GT-fed (DEMO-A, jawny overlay)**, a nowy mechanizm MTI (MTI-P / okno K) osobną nogą po
re-instrumentacji.

**Co wymaga re-bramki live (wycena):** wszystko, co zmienia bramę. (b) ENTRY-once = zmiana definicji →
**re-bramka wymagana**. (a),(c) = dodatkowo re-instrumentacja przed jakimkolwiek pomiarem. Nic z D1–D4
**nie jest pomiarem** — to projekcje i raporty braków.

---

## Bilans stop-rules

- **SR-D1** — zero lotów; D1/D4 zamknięte jako raporty braków, nie biegi. ✓
- **SR-D2** — brama `r02/target_channel.py`, config, PRE, frozen, certy **NIETKNIĘTE**; `ANEKS_MTI_2` to
  dokument-propozycja w tym raporcie, nie nanoszony. Kod DIAG jest osobnym instrumentem. ✓
- **SR-D3** — `test_gate_sim.py` **PASS 8/8** przed jakąkolwiek liczbą projekcji. ✓
- **SR-D4** — każda liczba projekcji z etykietą PROJEKCJA; zdanie „projekcja przewiduje, pomiar
  rozstrzyga" na wstępie. ✓
- **SR-D5** — artefakty w `results/R02/mti/DIAG/`. ✓

## Artefakty sesji (`results/R02/mti/DIAG/`)
- `gate_sim.py` — symulator projekcji bramy (okno→streak→ENTRY→ZOH).
- `test_gate_sim.py` — unit-test SR-D3 (PASS 8/8).
- `d3_entry_once.py` + `d3_entry_once.json` — projekcja D3 ENTRY-once.
- `missing_fields.json` — inwentarz braków D1/D2/D4.
- `RAPORT_MTI_DIAG.md` — ten raport.
- `ANEKS_MTI_2.md` — szkic dokumentu-propozycji (ENTRY-once).

**STOP. Push = Olga.** Po ratyfikacji: albo jedna re-bramka live pod ENTRY-once (osobny prompt,
z logowaniem per-tick + local_position), albo decyzja DEMO-A i przejście do nogi D (dem).
