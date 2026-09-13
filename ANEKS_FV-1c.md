# ANEKS_FV-1c — errata L2 (błąd kategorii vel ≠ v_cmd) + zlecenie CO5 + rama kanonu

CC · 13.09.2026 · łańcuch FV (sub-numer po ANEKS_FV-1b; ANEKS_FV-2 nadal zarezerwowany na werdykt).
Aneks samowykonalny (wzór ANEKS_K1-6): sesja wykonuje §0–§3 i STOP.

## §0. Bramka i reżim wykonania
1. `git log origin/master..HEAD` musi być PUSTE (dbc4442, f01e083, cea1ab1 na origin). Niepuste ⇒
   jedna prośba do Olgi o push; po potwierdzeniu dalej; cokolwiek innego niż te trzy ⇒ STOP.
2. Zakres: WYŁĄCZNIE doc-only + ARCH-1. Zero zmian w `r01/proofs/*.py`, certach, produkcji.
3. Pliki dotykane (lista zamknięta): `results/FV/RAPORT_FV.md` (errata in-place §O4, §6, §7),
   `results/KSIEGA_PREDYKCJI.md` (dwie korekty §3e), korzeń repo `ANEKS_FV-1a.md` + `ANEKS_FV-1c.md`
   (ARCH-1, procedura C0 z S1: Downloads, glob, nagłówek, sha256). Nic poza listą.
4. Jeden commit **CO5**, doc-only. STOP z raportem płaskim (diff-stat + treść nowego §O4 verbatim).

## §1. Znalezisko (z kodu pinowanego, shield.py 1c584964)
`_braking_dist(vel)` (r01/shield.py:97-99, klamp `min(hypot, v_max)`) i `_geofence_violation(pos,
vel, target)` (:101-112; :108 `pr + brake(vel) > r_e`) liczą po argumencie **vel**; `step(k, pos,
vel, target, …)` (:121) przekazuje go do `_decide` (:123, :163). Wywołania produkcyjne: gate —
`gate_run_r03.py:232` `vel = (m.vx, m.vy, 0.0)` → `:268 shield.step(tick, pos, vel, tgt, …)`; ławka —
`bench_flight.py:342` `vel = [m.vx, m.vy, m.vz]` → `:363 shield.step(tick, own, vel, tgt, …)`.
**vel = prędkość mierzona (telemetria/EKF); v_cmd trafia do `set_velocity_ned` dopiero po ALLOW.**
Zatem O3 G1 kwantyfikuje po prędkości MIERZONEJ, a L2 (clip_v) ogranicza KOMENDĘ. Podstawienie
v_cmd za vel w antecedencie O3 („|v_cmd|≤v_max ∧ ¬viol ⇒ pr+v_cmd_h²/(2a)≤R_E") wprowadza niejawną
przesłankę A-TRACK („|vel| ≤ |v_cmd|"), nigdzie niedowiedzioną i EMPIRYCZNIE FAŁSZYWĄ: K1/ANEKS_K1-8
— komenda 3.00, EKF 3.74, GT 5.34 m/s w narożniku; ERRATUM_VMAX.md; V_env=6.0. Poza D predykat
z klampem ZANIŻA drogę hamowania (sufit 3²/(2·2)=2.25 m niezależnie od rzeczywistej prędkości).
Klasa: „limit zadany ≠ faktyczny" — trzecia instancja w programie (liczba 11.69 m; V_MAX w PRE;
teraz lemat). Złapane przyrządem: prereg P-CC2-3 (CC, 13.09, przed lekturą) + kod pinowany.

## §2. Skutki
O1, O2, O3, L1 oraz cert P8 (domena jawna, `gating:false`) — NIETKNIĘTE. Pada wyłącznie zdanie
kompozycyjne L2 i wszystko, co propozycja kanonu §6 z niego wywodzi. Werdykt bramki nogi (PRE §5:
O1 ∧ O2 ∧ różnicówka) nie zależy od L2. Prereg CO3 nienaruszony (błąd jest w interpretacji, nie
w obligacjach).

## §3. Zlecenie CO5 (doc-only)
(a) `RAPORT_FV.md §O4` — errata IN-PLACE (stara treść zostaje oznaczona „[superseded — errata
ANEKS_FV-1c]", nic nie kasujemy). Nowa treść rozdziela trzy twierdzenia:
- **K1 — kanał komendy:** L1 ∧ L2 ⇒ |v_cmd| ≤ v_max niezależnie od wag, historii i stanu sieci
  (cytaty models.py:12/:57, common.py:10-16). Twierdzenie o KONTROLERZE.
- **K2 — zawieranie na D:** O3 G1 ⇒ antecedent Inv_P2 ⇒ (P2) pr ≤ R_E, zmienna = **vel mierzone**,
  domena D = {|vel| ≤ 3.0, pr ≤ 37, |z| ≤ 20}. Twierdzenie o OSŁONIE.
- **K3 — pomost A-TRACK:** „|vel| ≤ v_max" jest ZAŁOŻENIEM, nie wnioskiem z K1. Zmierzone
  naruszenia: RAPORT_K1/ANEKS_K1-8 (cytaty), ERRATUM_VMAX.md. Poza D pokrycie daje wyłącznie
  empiryczna analiza obwiedni (C_margin = 32 − (20.654 + 10.2) = 1.146 m przy V_env=6.0) — nie dowód.
  Zdanie „sieć nie może wyprowadzić drona poza R_E" NIE wynika z K1 ∧ K2.
(b) `geo_cont_verify.py` NIETYKALNY — docstring z dawnym L2 zostaje; errata w raporcie wskazuje go
jako superseded (zmiana provera = nowe sha = regeneracja certu = klasa self-hash P2.json).
(c) `§6` propozycja kanonu — przepisana w ramie §4 niżej (nadal PROPOZYCJA, finalizacja ANEKS_FV-2).
(d) `§7` odchylenia — wpis: „L2: błąd kategorii zadany≠faktyczny złapany przez CC przed werdyktem
(prereg P-CC2-3); poprawka doc-only CO5".
(e) `KSIEGA_PREDYKCJI.md`: P-CC2-1 = **✓** (predykcja o statusie „częściowy" spełniona; kategoria
„✓-częściowy" nie istnieje — księga jest binarna); dopisać **P-CC2-3** (prereg 13.09 CC: „L2
w RAPORT_FV instancjonuje O3 na v_cmd zamiast vel — wymaga korekty", p≈0.6) = **✓**, rozstrzygnięte
kodem pinowanym (§1).
(f) ARCH-1: `ANEKS_FV-1a.md` + `ANEKS_FV-1c.md` → korzeń repo.

## §4. Rama kanonu roszczeń FV (wiążąca dla §6; brzmienie finalne = ANEKS_FV-2)
**WOLNO** — wyłącznie wyliczanie własności z domenami i założeniami:
- D5 (`safe_descend_step`): własności (a)–(d) dowiedzione przy założeniu zegara niemalejącego;
  N*=194, t_touchdown 9.700 s (cert P6_d5).
- Histereza (`_pos_monitor`): (a) REFUSE(POS) po ≥2 kolejnych tickach, (b) wyjście po ≥100 czystych,
  (c) min cykl 102 — dowiedzione na PEŁNYM osiągalnym grafie 103 stanów / 206 krawędzi (cert P7).
- Predykat geofence implementacji ≡ model certu P2 na D = {|vel| ≤ 3.0, pr ≤ 37, |z| ≤ 20}
  (spójność kształtu i stałych; zastępuje próbkową konformancję P5 dla tego predykatu; cert P8).
- Kanał komendy kontrolera uczonego ograniczony architektonicznie: |v_cmd| ≤ v_max niezależnie od wag.
- Wiązanie model↔kod: siatka 54 + fuzz 4×10⁵ + fikstura 4221/1791 ticków, 0 rozbieżności;
  27/27 mutantów wykrytych (moc przyrządu zmierzona).
**NIE WOLNO:**
- „formally verified system" / „osłona zweryfikowana formalnie" bez wyliczenia własności i domen.
- „sieć nie może wyprowadzić drona poza R_E" — wymaga A-TRACK, niedowiedzione, empirycznie łamane.
- jakiejkolwiek gwarancji przy |vel| > 3.0 (erratum #2; poza D predykat zaniża drogę hamowania).
- ekstrapolacji poza model/SITL; twierdzeń o wnętrzu CfC (NOTA_UNROLL: częściowy).

## §5. Warunki ANEKS_FV-2 (werdykt + kanon)
(i) push CO5; (ii) zip całego repo z katalogiem `.git` do CC (fallback: bez `.git` + wklejony
`git diff f01e083 cea1ab1 -- r01/proofs/geo_cont_verify.py`). CC replikuje provery P6/P7/P8 lokalnie,
czyta C1a–C1d i RAPORT_FV po erracie, weryfikuje prereg f01e083 → cea1ab1. Dopiero wtedy werdykt.

## §6. Predykcje
P-CC2-3 ✓ (rozstrzygnięte kodem pinowanym przed lekturą raportu).
