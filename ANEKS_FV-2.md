# ANEKS_FV-2 — werdykt nogi FV + kanon roszczeń FV (finalny) + zamknięcie (CO6)

CC · 14.09.2026 · łańcuch FV (po ANEKS_FV-1c). Aneks zamykający i samowykonalny (§4).

## §1. Replikacja niezależna CC (inna maszyna, z3 5.1.0 vs 5.0.0 w certach)
- Piny 5/5 (`k1_shield_pins.py`), `certs_selfcheck` **PASS 9/9** — odtworzone.
- Provery uruchomione u CC: **P6_d5** 10/10 obligacji unsat, N*=194; **P7_posmon** graf 103 stanów /
  206 krawędzi, a=2, b=100, c=102, z3 a-step/b-step unsat; **P8_geo_cont** G1 unsat, G2 unsat, G3 sat.
  Certy zregenerowane przez provery identyczne z commitowanymi we WSZYSTKICH polach poza `z3_lib`
  i `solver_ms` (oryginały przywrócone po porównaniu — regeneracja nie trafia do repo).
- `tests_fv_diff.py` + `tests_fv_mutants.py` u CC: siatka×4, fuzz×4 (4×10⁵), spójność z P1,
  IDENTITY, **27/27 mutantów** — PASS. Jeden FAIL: `test_fixture_d5_4221` — u CC 2588 ticków, bo zip
  zawiera **6 z 11** plików `results/K1/S/**/trace.jsonl` → §4 (prowieniencja fikstury).
- Prereg O3: `PREREG_DIFF_f01e083_cea1ab1.patch` = dokładnie jedna linia dekodera wyniku
  (`{z3.unsat:…}.get(r)` → `r == z3.unsat`); obligacje, domena i twierdzenia nietknięte — integralność
  prerejestracji POTWIERDZONA.
- CLARIFY-1 zamknięte własną lekturą: `bench_flight.py:75` desc_total = (ALT_M−H_SWITCH)/V_DESC_FAST
  + H_SWITCH/V_DESC_LAND + 1.5 = 16/3 + 20/7 + 3/2 = **407/42** ✓; człon +1.5 s = ~1.05 m komendowanego
  zejścia poza nominalny touchdown (margines dociśnięcia; stała literalna w kodzie, nie w config —
  cert cytuje linię, kanon ją nazywa).
- Cytaty stałych w P6/P8 zweryfikowane przeciw `r01/config.py` (V_MAX 3, A_BRAKE 2, R_E 32, V_E 20,
  GF_MAX_HOR_DIST 37, DT 0.05) i `r03/config.py` (V_DESC_FAST 1.5, V_DESC_LAND 0.7, H_SWITCH_AGL 2.0).

## §2. WERDYKT NOGI FV — **PASS** (PRE_FV §5)
O1 PROVED ∧ O2 PROVED ∧ różnicówka czysta (0 rozbieżności) ∧ przyrząd adekwatny (27/27; 25 siatką,
2 fuzzem). O3 PROVED (niebramkujące). O4: K1 (kanał komendy) i K2 (zawieranie na D) dowiedzione
ROZŁĄCZNIE; K3 (A-TRACK) = założenie, empirycznie łamane; L3 częściowy. ŚMIERĆ nie zaszła, TRIPWIRE
niewyzwolony (0 kontrprzykładów realnych w całej nodze). Błąd kategorii L2 złapany przed werdyktem
i poprawiony doc-only (CO5).

Warstwy nowości: koncepcyjnie nic nowego (Simplex/RTA, testy różnicowe, testy mutacyjne = znane
prymitywy); **nowe jako zdolność programu** — po raz pierwszy własności KODU PRODUKCYJNEGO osłony
dowiedzione z systematycznym wiązaniem model↔kod i ze zmierzoną mocą przyrządu, plus replikacja
niezależna na innej maszynie. To jest zdanie, które wchodzi do noty syntezy (0b) jako rozdział „dowód".

## §3. KANON ROSZCZEŃ FV — obowiązujący (zastępuje PROPOZYCJĘ RAPORT_FV §6)
**WOLNO** — wyłącznie wyliczanie własności z domenami i założeniami; każde zdanie niesie założenie
„lustro ≡ produkcja (różnicówka + mutanty)":
- Zejście D5 (`safe_descend_step`): (a) przełączenie faz na H_SWITCH, (b) wysokość zadana monotonicznie
  nierosnąca, (c) touchdown w N*=194 krokach (t=9.700 s przy dt=0.05; desc_total 407/42 s z formuły
  produkcyjnej `bench_flight.py:75`, w tym +1.5 s dociśnięcia), (d) 0 ≤ v_desc ≤ 1.5 — dowiedzione przy
  założeniu zegara niemalejącego (cert P6_d5).
- Histereza (`_pos_monitor`): (a) REFUSE(POS) po ≥2 kolejnych tickach degradacji, (b) wyjście po ≥100
  czystych, (c) minimalny cykl re-degradacji 102 — dowiedzione na PEŁNYM osiągalnym grafie 103 stanów /
  206 krawędzi pod abstrakcją saturacji licznika, której soundness wynika z kodu
  (shield.py:83 brak capu / :85 jedyne porównanie ≥debounce / :89 reset do 0) (cert P7_posmon).
- Predykat geofence implementacji ≡ model certu P2 na D = {|vel| ≤ 3.0, pr ≤ 37, |z| ≤ 20}, zmienna =
  prędkość MIERZONA; spójność kształtu i stałych (r_e = R_E = 32, a_brake = 2); zastępuje próbkową
  konformancję P5 dla tego predykatu (cert P8_geo_cont, niebramkujący).
- Kanał komendy kontrolera uczonego: |v_cmd| ≤ v_max architektonicznie (głowa tanh·V_MAX + clip_v),
  niezależnie od wag i stanu — twierdzenie o KONTROLERZE, rozłączne od zawierania osłony.
- Wiązanie model↔kod: siatka 54 punktów na brzegach progów (prerejestrowana przed biegiem), fuzz 4×10⁵
  na funkcję (ziarna 0–4), fikstura 4221/1791 ticków z lotów K1/S (manifest sha: §4) — 0 rozbieżności;
  moc przyrządu: 27/27 wstrzykniętych mutantów wykrytych.
- Replikacja niezależna CC (inna maszyna, inna wersja z3): identyczne werdykty i obligacje P6/P7/P8.

**NIE WOLNO:**
- „formally verified system" / „osłona zweryfikowana formalnie" — bez wyliczenia własności i domen
  zdanie nie istnieje.
- „sieć nie może wyprowadzić drona poza R_E" — wymaga A-TRACK (|vel| ≤ |v_cmd|), niedowiedzionego
  i zmierzonego jako fałszywy w zakrętach (K1: cmd 3.00 / EKF 3.74 / GT 5.34; ERRATUM_VMAX).
- jakiejkolwiek gwarancji przy |vel| > 3.0: poza D predykat z klampem ZANIŻA drogę hamowania (sufit
  2.25 m); pokrycie V_env=6.0 jest wyłącznie empiryczne (C_margin 1.146 m), nie dowiedzione.
- ekstrapolacji poza model/SITL; twierdzeń o wnętrzu CfC (NOTA_UNROLL: częściowy); cytowania
  fikstury bez manifestu; pomijania założenia „lustro ≡ produkcja" przy cytowaniu certów FV.

## §4. Zlecenie CO6 — commit zamykający (samowykonalny; jeden commit)
Bramka: `git log origin/master..HEAD` puste (320c06a na origin); inaczej prośba o push, potem dalej.
Pliki dotykane (lista zamknięta):
- NOWY `results/FV/FIXTURE_D5_MANIFEST.json`: 11 plików `results/K1/S/**/trace.jsonl` z sha256
  i liczbą ticków każdy (suma 4221 / 1791 descending) — generowany na maszynie Olgi, gdzie komplet
  istnieje. Do raportu: wyjście `git ls-files results/K1/S | grep -c trace.jsonl` (ile z 11 śledzonych).
  Jeśli < 11 — NIE commituj śladów samodzielnie; jedna linia pytania do Olgi w raporcie (commit 5 plików
  vs pozostają lokalne z manifestem). Zamknięcia nogi to nie blokuje.
- EDYCJA `r01/proofs/tests_fv_diff.py`: `test_fixture_d5_4221` czyta manifest; brak któregokolwiek
  pliku ⇒ `pytest.skip` z listą brakujących; komplet ⇒ assert 4221/1791 ∧ sha zgodne. Diff verbatim
  do raportu. Żadnych innych zmian w testach.
- EDYCJA `r01/proofs/posmon_verify.py`: dopisanie do `assumptions` certu zdania o abstrakcji saturacji
  z argumentem soundness (shield.py:83/85/89) — WYŁĄCZNIE ta zmiana (diff verbatim); regeneracja
  `P7_posmon.json` WYŁĄCZNIE przez uruchomienie provera (nowe model_sha256 — ścieżka legalna, treść
  dowodowa bez zmian: graf 103/206, a/b/c, z3 unsat); `certs_selfcheck` 9/9 po regeneracji.
- EDYCJA `results/KSIEGA_PREDYKCJI.md`: K2 — dopisać **P-K2-5 ✓** (`results/K2/RAPORT_K4b.md:17`,
  pominięte przy konsolidacji) ⇒ K2 **3 ✓ / 2 ✗**, RAZEM zakres obowiązkowy **20 ✓ / 8 ✗**; sekcja FV bez
  zmian; P-CC2-1 i P-CC2-3 = ✓ (bez dopisków „częściowy" w kolumnie werdyktu).
- EDYCJA `results/FV/RAPORT_FV.md`: §6 = kanon z §3 tego aneksu verbatim z nagłówkiem „KANON
  OBOWIĄZUJĄCY — ANEKS_FV-2 (zastępuje propozycję)"; §7 dopisek: replikacja niezależna CC (§1) oraz
  „fikstura: zip repo bez .git zawierał 6/11 śladów — manifest §4".
- Korzeń repo: `ANEKS_FV-2.md` (ARCH-1, procedura C0).
Stop-rules CO6: zero zmian w pinach/frozen/produkcji; zmiany w `proofs/` ograniczone do dwóch
wymienionych; po commicie `certs_selfcheck` 9/9 i pytest (u Olgi fikstura pełna = assert; skip tylko
przy braku plików). Raport płaski: diff-stat, oba diffy verbatim, wynik `git ls-files`, selfcheck, pytest.

## §5. Status nogi
**FV CLOSED — PASS** z chwilą commita CO6 i pushu. Linia skuteczności CC nie jest wymagana (aneks
zamykający); odchylenie przy CO6 ⇒ pytanie do CC przed wpisem, jak zawsze.

## §6. Księga predykcji CC — noga FV
P-FV-1 ✓ · P-FV-2 ✗ · P-FV-3 ✓ · P-FV-4 ✓ · P-CC2-1 ✓ · P-CC2-3 ✓ ⇒ **5 ✓ / 1 ✗**. Kalibracja:
chybienie P-FV-2 = przeszacowanie tarcia lustra przy funkcjach czystych <250 linii — na przyszłość
prognozować 0–1 rozbieżności dla takich celów; dwie ✓ (P-FV-4, P-CC2-3) zdobyte na wątpliwościach
zgłoszonych PRZED danymi, co jest właściwym użyciem księgi.

## §7. Po zamknięciu (bez otwierania niczego)
Trigger pozycji 2d katalogu („po 1b(i)") jest spełniony — nie otwieram; wybór następnej nogi należy do
kryterium 2-miesięcy z KIERUNKI_PO_PLANIE. Nota syntezy 0b zyskała rozdział „dowód" (P6–P8 + wiązanie
+ replikacja); 0a/0b nadal czekają na brief SPRIND. P-CC2-2 pozostaje OTWARTA.
