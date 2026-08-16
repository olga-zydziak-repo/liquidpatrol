# RAPORT_D_B3 — DEMO-B blok B3: patche trace (a/b/e/f) + generator napisów i plansz

Data: 2026-08-16. Zakres: **wyłącznie B3** — patche trace wg PRE_D §4 (a/b/e/f) + generator napisów/
plansz. NIE: runner per-akt (B4), nagrania (B5), montaż (B6). **`r01/proofs/` i `r01/shield.py`
NIETKNIĘTE** (SR-E1). Bez SITL. Reżim bez zmian; prowieniencja per liczba; FAIL=FAIL; **push = Olga**.

## Stan wejściowy / wyjściowy (SR-E5, SR-E1)

- **SR-E5 (pierwsza czynność):** `git log origin/master..HEAD` = PUSTE (Olga pushnęła B2). HEAD =
  origin/master = `7b711cd`, drzewo czyste.
- **`certs_selfcheck` bieg #1 (start): 6/6** · **bieg #2 (koniec): 6/6** — `r01/proofs/` i `r01/shield.py`
  NIETKNIĘTE (`git status` czysty na tych ścieżkach; SR-E1 spełniony).
- Łańcuch commitów B3 (niepushowane):
  - `<C1>` §1: patche trace a/b/e/f + schemat v2.
  - `<C2>` §2/§3: generator napisów/plansz + fixtures + golden + testy.
  - `<C3>` §4: RAPORT_D_B3.

## §1 — Patche trace: mapowanie na wiersze PRE_D §4 (1:1)

Schemat trace **wersjonowany** `TRACE_SCHEMA_V = 2` (bump z v1; changelog w kodzie: `gate_run_r02.py`
i `gate_run_r03.py`). Pola nowe **OPCJONALNE** → zgodność wsteczna (parser czyta v1 bez wywrotki).

| Wiersz PRE_D §4 | cytat wiersza | patch (commit) | plik:pole |
|---|---|---|---|
| **(a)** | „stan automatu + reason … dodać `d["state"]` do rec `gate_run_r02.py:413`" | ZROBIONE | `gate_run_r02.py` rec: `"state": d.get("state")` |
| **(b)** | „koniunkty box/central/mti_ok … dodać koniunkty do rec gate_live" | ZROBIONE (record-only w kanale) | `target_channel.py` `self.last_conj` (obserwacja, NIE logika); `gate_run_r02.py` rec: `"conj"` |
| **(c)** | „age vs θ_age — AVAILABLE" | bez zmian | `age` per-tick (już był) |
| **(d)** | „margines D_safe (`min_d`) — AVAILABLE" | bez zmian (R02); R03 patrz (e) | `min_d` (już był) |
| **(e)** | „ε/budżet w GPS-denied … dodać per-tick wiersz `r_est`/margines w `gate_run_r03.py`" | ZROBIONE | `gate_run_r03.py` row `{t:"tick", r_est, margin_R_E}` |
| **(f)** | „pozycje dron+intruz … dodać `intr_ned` do rec" | ZROBIONE | `gate_run_r02.py` rec: `"intr_ned"` (GT-fed z `gt_intruder_fn`; live/B4 ustawi runner) |

Pola tokenowe B1 (`token_issued`/`token_consumed`/`refuse_no_auth`) **włączone do schematu jawnie**
(`TRACE_EVENT_TYPES`) i dostały znacznik czasu `t` (do korelacji napisów). **Osłona byte-identyczna:**
`last_conj` to CZYSTA OBSERWACJA (te same wejścia box/cfg, zero mutacji `box`/logiki ENTRY) — REGATE
ENTRY-once nietknięte (regresja: `test_channel`/`test_mti` PASS).

### Schemat v2 (pola tick gate_live)
`k, t, decision, reason, rule, mode, state, locked, age, conj{box,central,mti_ok}, intr_ned[x,y,z]NED,
gt_fed, pos, yaw, applied, r_pos, flight_mode, min_d, auth_ok, admission_seq`. R03 tick:
`tick, mono, r_est[m], margin_R_E[m]=R_E−r_est, decision, reason, state, pos, dr, descending`. Nagłówek
`{t:"schema", v:2, …}` self-describing (brak = v1).

## §2 — Generator napisów i plansz (`tools/gen_subtitles.py`)

Zasada (SR-E2): **wszystko dynamiczne z trace / certów / spec / manifestów.** Hashe certów **czytane
programowo** z `r01/proofs/certs/P*.json` (SR-E3: hash/liczba na sztywno = naruszenie).

- **Asert kompletności:** brak któregokolwiek zdarzenia wymaganego aktem ⇒ `SystemExit` z nazwą
  brakującego (A1: entry/refuse_no_auth/grant/observe; A2: +expire/readmit/grant2; A3: denial/
  refuse_pos/touchdown). Wzorzec z `mti_flight` (asercja kompletności trace).
- **Roszczenie percepcji tylko zmierzone (D3(a)):** segment „claim" WYŁĄCZNIE gdy trace potwierdza
  jednocześnie `mode=OBSERVE ∧ decision=ALLOW` **i** `d = range3d(pos, intr_ned) ∈ ring_band` (band ze
  **spec**). Wszędzie indziej plansza D3(b) „beyond characterized envelope — transit". Granice segmentów
  liczone Z TRACE.
- **Plansze obowiązkowe (szablony statyczne, pola z plików):** PROVED (P1 `10/10 unsat` + P4/P5 +
  hashe `model_sha256` z P*.json), MEASURED (liczby z trace z podanym źródłem), operator=skrypt (A5),
  „per admission — no re-identification" (B1 §1.3), „authority gating, not secure C2" (B1 §1.7),
  „SITL only — TRL 2–3", CUT (A2, osobne booty), CONTRAST A3 (AUTO.LAND flyaway `42 m` czytane ze
  **spec** `A3_spec.contrast_plansza` z cytatem RAPORT_R03A vs touchdown zmierzony z trace).
- **Język:** EN (parametr `--lang`, treści w słowniku `STRINGS`); **decyzja EN do zatwierdzenia przez
  Olgę** — generator gotowy na dodanie PL jako drugiego klucza słownika bez zmian logiki.

## §3 — Testy deterministyczne (`tools/test_gen_subtitles.py`: 9/9 PASS)

Golden fixtures `tools/b3_fixtures/{A1,A2,A3}_fixture.jsonl` (deterministyczny maker `make_fixtures.py`,
oznaczone `"fixture": true` — NIE dowód, NIE pomiar).

| Test | co sprawdza |
|---|---|
| `snapshot_vtt_{A1,A2,A3}` | fixture → `.vtt` **bajt-w-bajt** vs golden `tools/b3_fixtures/golden/*.vtt` |
| `completeness_fail_names_missing_event` | usunięcie `token_issued` ⇒ FAIL z „grant" |
| `completeness_all_acts_pass` | wszystkie wymagane zdarzenia wykryte per akt |
| `no_hex64_literal_in_templates` | żaden szablon STRINGS nie zawiera literału hex≥16 (SR-E3) |
| `proved_plansza_reads_hash_from_cert` | PROVED zawiera AKTUALNY hash z P1/P5.json (czytany z pliku) |
| `contrast_number_from_spec_not_hardcoded` | „42" NIE w szablonie; flyaway pochodzi ze spec |
| `backward_compat_archival_regate_trace_loads` | archiwalny `regate2/trace.jsonl` ładuje się (v1, ticks>0, bez wywrotki) |

Regresja (nienaruszalność): `r01/test_core` 10, `r01/test_token_authz` 12, `r02/{channel,mti,guidance,
deadman}` + `r03/test_pos_degraded` = **64 PASS łącznie** (z 9 B3).

### Sanity zgodności mechanizmu ruchu celu (§3, ZWERYFIKOWANE)
- **Mechanizm ruchu:** charakteryzacja REGATE porusza cel przez `gz_set_intruder` = `set_pose` na
  modelu `intruder` (`intruder_model.sdf`) — **MODEL + runtime-teleport**, DOKŁADNIE ten sam mechanizm
  co choreografia aktów (spec: `intruder_model: r02/intruder_model.sdf`, teleport przez runner B4).
  Warunek przenoszalności `t_entry_p95` spełniony.
- **Metryka d:** REGATE `replacer` (`mti_flight.py:180`) stawia intruza na `R` = **range 3D**, z
  `R_h = √(R²−DALT²)`, `DALT=1.5`. Spec A1 używa `d` = **range 3D = 8.0** (horizontal `√(8²−1.5²)=7.86`,
  Δalt 1.5). **Ta sama wielkość, ta sama konstrukcja** — bez rozbieżności. Generator liczy claim po
  `range3d(pos, intr_ned)` = ta sama d.

## Rozbieżności (jawnie)

1. **Amplituda oscylacji intruza:** spec A1 `osc ±1.0 m`, REGATE charakteryzacja `±1.5 m/0.3 Hz`
   (`mti_flight.py:182`). Wybrałem MNIEJSZĄ (konserwatywnie bliżej środka pasma; range3d ∈ [8.00, 8.06]
   ⊂ [7,9]). Nie zmienia metryki d ani mechanizmu; zapisane w spec (`< REGATE ±1.5`).
2. **`intr_ned` w live/B4 nie jest jeszcze zasilany** — patch (f) dodaje pole; GT-fed zasila z
   `gt_intruder_fn`, dla aktów live runner per-akt (B4) ustawi `self._intr_ned` per-tick (teleportuje
   intruza, więc zna pozę). W B3 pole istnieje i jest logowane; wypełnienie live = B4.
3. **Napisy/plansze testowane na FIXTURES, nie na realnych trace aktów** (te powstają w B5). Fixtures
   jawnie oznaczone `fixture`; snapshot `.vtt` niezależny od hashy certów (hashe tylko w planszas.json,
   nie w `.vtt`) → snapshot stabilny przy regeneracji certów.
4. **Precedens `subtitles.vtt`/`ANEKS_DP1` nadal nie istniał** (PRE_D §4/R6) — generator to **build od
   zera** z asertem kompletności, zgodnie z ustaleniem recon.

## STOP

Blok B3 domknięty: 4 patche trace (a/b/e/f) 1:1 z PRE_D §4 + schemat v2 (zgodność wsteczna), generator
napisów/plansz z asertem kompletności i planszami czytającymi hashe z plików, 9 testów deterministycznych
(snapshot + completeness + no-hardcoded-hash + backward-compat), sanity mechanizmu/metryki ZWERYFIKOWANE,
selfcheck 6/6 ×2 (`r01/proofs`+`shield.py` nietknięte). **B4 (runner per-akt: assert `token_gated=True`,
echo flagi w manifeście/trace, kadr-check renderu przed próbami) — osobny prompt po przeczytaniu tego
raportu przez Olgę. Push = Olga.**
