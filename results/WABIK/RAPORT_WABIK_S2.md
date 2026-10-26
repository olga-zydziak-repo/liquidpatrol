# RAPORT_WABIK_S2 — testy celowane S2 nogi WABIK — STOP-WABIK2

CC-wykonawca · 26.10.2026 · wykonanie ANEKS_WABIK-1 §4 (aktywacja PRE_WABIK §3).
**Budżet S2: 3/≤8 bootów (bA_tp1, bB_tp2fp, bC_fporb); noga 5+2=7/≤11. Wszystkie
uzbrojone: breach 0 / REFUSE 0; 11/11 epizodów VALID; reżim OPS 3/3 (pin, profil
GUARD, sonda preflight PASS 3/3, kadencja lotu 0.064–0.068/frac 0.0).**
Jeden obiekt w świecie naraz we wszystkich testach (wabik_motion nieobecny —
TP grane torem intruza z manifestu S2 przez BENCH_MANIFEST; litera §4.2).

**WERDYKTY ZDANIAMI ZAMROŻONYMI (PRE §3.2 / ANEKS §4.4-4.6):**

- **T-W-TP: FALSYFIKACJA PROGÓW — etykieta „wabik" w ≤15 s śledzenia
  w ≤2/6 (zaszła: ≤1/6)** ⇒ „progi z NULL nie przenoszą się na TP — wracamy
  do cech" (dekompozycja per cecha niżej; STOP-ANEKS = ANEKS_WABIK-2 po tym
  raporcie, zgodnie z łańcuchem §4.7).
- **T-W-FP: 0/3 flag ✓** (twardy wskaźnik spełniony).
- **T-W-ORB: 2/2 — track na celu 1.000 pod zmianą kursu, separacja ≥4 m ✓.**

## §1. Bramki i reżim — PASS

ARCH-1: ANEKS_WABIK-1 verbatim w korzeniu (commit `2729e988`). origin=ea49de02 ✓
gate pusty ✓ porcelain czysty (poza nazwanymi ??) ✓; FROZEN komplet +
FREEZE_WABIK wykonaniem (wabik_sig 475c972e NIETKNIĘTY — progi 1:1 z FREEZE;
wabik_manifest.json v1 046fa12b NIETKNIĘTY). **BENCH_MANIFEST pierwszy raz:**
NOWY `wabik_manifest_s2.json` (86268b02; generator d461a65c) — kopie c08_s03
i c10_s02 **dowiedzione diffem pól: jedyna różnica = `episode_id`**
(32→6, 22→7; assert w generatorze, log w repo). Driver: jedyna zmiana vs S1 =
parametr katalogu serii (`WABIK_S_DIR=s2`; sha po zmianie 0eb21a26 — driver
nie jest w tabeli FREEZE). Narzędzie analizy NOWE: wabik_s2_analyze.py 4eb498d6.

## §2. Tabela epizodów (pełne dane: `s2_wyniki.json`; cechy per klatka: `s2/*/wabik_sig_<sid>.jsonl`)

| ep | sid | rodzaj | etykieta (ever/końcowa) | t-do-flagi [s]¹ | t-odwołania | dh_min trk | t_acq | d_min GT | D6 opisowo | świadek |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | w00a_s01 LOITER r10 | TP | wabik/wabik | 17.62 | — | 8.44 | 8.86 | 7.362 | PASS | 0 |
| 1 | w00b_s01 LOITER r12 | TP | wabik/wabik | 20.99 | — | 11.10 | 8.66 | 5.326 | PASS | 2 |
| 2 | w01a_s01 STYCZNY b8 | TP | wabik/wabik | 15.51 | — | 7.80 | 10.82 | 6.886 | PASS | 1 |
| 3 | w01b_s01 STYCZNY b12 | TP | wabik/wabik | 24.88 (12.60²) | — | 10.33 | 12.42 | 6.727 | PASS | 1 |
| 4 | w02a_s01 ZBLIŻ 7 m | TP | **–/–** | — | — | 6.84 | 9.02 | 7.053 | PASS | 0 |
| 5 | w02b_s01 ZBLIŻ 8.5 m | TP | **–/–** | — | — | 8.41 | 9.01 | 7.189 | PASS | 0 |
| 6 | c08_s03 (kopia 1:1) | FP | **–/– ✓** | — | — | 0.09 | 3.26 | 5.863 | **PASS** 0.985 (vs S2-PERC2 5.613 ✓) | 1 |
| 7 | c10_s02 (kopia 1:1) | FP | **–/– ✓** | — | — | 0.04 | 8.94 | 5.179 | FAIL [c_sweep] 618.6° (wariancja pościgu granicznej c10 — klasa znana z FANTOM; frac 0.977 i d_min OK) | 2 |
| 8 | m00_s01 M-ŁUK | FP | **–/– ✓** | — | — | 3.40 | 17.11 | 5.451 | PASS | 0 |
| 9 | m01_s01 M-POD-ORBITĄ | ORB | wabik→ODWOŁANA | 21.78 | 33.0 | 4.95 | 0.15 | **7.064** | PASS (sweep 989.9) | 1 |
| 10 | m01_s02 (2. przebieg) | ORB | wabik→ODWOŁANA | 17.56 | 28.44 | 4.63 | 4.28 | **6.577** | PASS (sweep 921.1) | 2 |

¹ od PIERWSZEJ klatki z trk w epizodzie (definicja operacyjna classify;
stale-klatki brzegu okna mogą zawyżać — patrz w01b).
² w01b: pierwsza klatka trk to pojedyncza stale-klatka @0.02 s, potem luka
12.3 s; od startu CIĄGŁEGO segmentu śledzenia flaga padła w **12.60 s ≤ 15** —
raportowane OBIE metryki; nawet przy życzliwszej definicji TP = **1/6**
(próg falsyfikacji ≤2/6 i tak przekroczony W DÓŁ).

## §3. T-W-TP — dekompozycja falsyfikacji per cecha (ANEKS §4.4)

1. **Szum v_rad tracka percepcyjnego rwie streaki (loiter/styczny):** warunek
   W wymaga CIĄGŁOŚCI 12 s, a pojedyncze klatki z |v_rad|>0.30 (szum estymaty
   na oknie 1 s; NULL pokazywał ogon) zerują licznik — flagi padają, ale po
   15.5–24.9 s zamiast <15 (4/6 oflagowanych „kiedykolwiek" dowodzi, że CECHY
   separują; pada TEMPO decyzji, nie kierunek).
2. **W-ZBLIŻ-ODSKOK strukturalnie niemożliwy przy T_FLAG=12 s:** rodzina ma
   fazy podejścia ~8 s (v_rad≈+1 ⇒ W=false co cykl) — maksymalny czysty
   segment ~8 s < 12 s wymaganych ⇒ 0/2 z konstrukcji progu, nie z szumu
   (przewidziane przed bootem B, potwierdzone pomiarem).
3. **Stale-klatki brzegu okna** zawyżają metrykę od-pierwszej-klatki (w01b).
   Kierunek „wracamy do cech" (decyzje CC przy ANEKS_WABIK-2; bez zmian progów
   w tej sesji — FROZEN): tolerancja krótkich przerw streaku zamiast twardej
   ciągłości, frac-closing w oknie decyzyjnym zamiast chwilowego v_rad,
   start zegara od ciągłego segmentu śledzenia.

## §4. T-W-FP i T-W-ORB

**FP 0/3 ✓** — podłoga dh_min (0.04–3.40 u intruzów schodzących) blokuje
flagę u wszystkich; M-ŁUK dodatkowo: późna akwizycja 17.11 s i zejście <5.
Kotwice opisowo: c08_s03 zgodna z S2-PERC2; c10_s02 FAIL [c_sweep] =
wariancja pościgu znanej granicznej komórki (nie dotyczy klasyfikatora).
**ORB 2/2:** pod zmianą kursu celu (+90° @9 s) **track na celu 1.000**
(666/666 ticków w [9,43] s, świadek obok), separacja d_min 7.064/6.577 ≥ 4 m,
D6 wręcz PASS (sweep 921–990°) — pomiar „manewr pod orbitą" z R4-niezmierzone
DOMKNIĘTY pozytywnie. Diagnostycznie cenne: klasyfikator na m01 flagował
(cel zaczyna jak wabik: 6 m bez zejścia) i **ODWOŁAŁ po zejściu <5 m**
(28.4/33.0 s) — semantyka etykiety-stanu zadziałała dokładnie wg FREEZE.

## §5. Budżet i artefakty

Booty S2: 3/≤8 (po 4+4+3 epizody); noga 7/≤11. Artefakty: `s2_wyniki.json`,
`wabik_manifest_s2.json`, `s2/bA_tp1/**`, `s2/bB_tp2fp/**`, `s2/bC_fporb/**`
(manifesty z `wabik.sondy[]`/pin, percep_feed, demo, trace, qlog,
wabik_sig_<sid>.jsonl; ulg wg polityki gitignore), narzędzia
wabik_manifest_s2_gen.py / wabik_s2_analyze.py. **Push = Olga („wypchnięte" —
CC czyta z repo).** Po weryfikacji CC: **ANEKS_WABIK-2** — werdykt zdaniami
zamrożonymi (falsyfikacja progów TP + FP 0/3 + ORB 2/2), KSIĘGA P-WB-1…6,
dopisanie pozycji MULTI-TARGET do katalogu i CO. **STOP-WABIK2.**
