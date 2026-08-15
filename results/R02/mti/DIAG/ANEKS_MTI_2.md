# ANEKS_MTI_2 (SZKIC / DOKUMENT-PROPOZYCJA — NIE NANOSZONY do PRE)

Status: **PROPOZYCJA**. Nie zmienia PRE_R02C, config, bramy, frozen ani certów (SR-D2). Żyje wyłącznie
jako dokument w `results/R02/mti/DIAG/`. Ratyfikacja + ewentualne naniesienie = Olga, po re-bramce live.
Wszystkie liczby wspierające = **PROJEKCJA OFFLINE ≠ POMIAR** (RAPORT_MTI_DIAG, D3).

## Motywacja

B5 pokazał: **(−) ε_FP=0 PASS**, **(+) FAIL strict** — mediana `coverage_gate` 0.393/0.632/0.632
@5/7/9 m < 0.8. Diagnoza offline (D0) ustaliła, że kryterium (+) w brzmieniu „coverage_gate (koincydencja
struktura∧MTI klatkowa) ≥ 0.8" żąda koincydencji MTI na ≥80% **klatek w sposób ciągły**. Tymczasem
kanał operacyjnie potrzebuje MTI tylko po to, by **wpuścić** cel (admisja ENTRY, odróżnić ruchomego
intruza od statycznego tła); po admisji kanał śledzi **strukturą** (YOLO), a `coverage_seen = 1.0`.

## Rewizja (proponowana)

> **MTI-do-admisji (ENTRY-once).** Koincydencja struktura∧MTI (`mti_ok`) jest wymagana **wyłącznie do
> ADMISJI** kanału (zdarzenie ENTRY). Po admisji kanał jest karmiony **strukturą** (`coverage_seen`);
> `mti_ok` nie jest już wymagane per klatka. EXPIRE, sufit wieku (`θ_age`), `L_deliver` i logika starzenia
> ZOH **bez zmian**. Utrata struktury → starzenie/EXPIRE jak dotąd (a re-admisja znów wymaga `mti_ok`).

Wzorzec rewizji: **A-drift→A-plateau** — kryteria PRE_R02C (zasięg, ε_FP wg def R3) **nietknięte**;
rewidowana jest **definicja pokrycia (+)**: z „`coverage_gate` klatkowe ≥0.8" na „**admisja ENTRY
osiągnięta** ∧ pokrycie-po-admisji (=`coverage_seen`) ≥0.8".

## (−) pozostaje bez zmian — to jest sedno bezpieczeństwa rewizji

ENTRY-once **nie rusza progu admisji**: ENTRY dalej wymaga box ∧ central ∧ `mti_ok` w serii `ENTRY_K`.
Rewizja dotyczy wyłącznie fazy PO admisji. Dlatego ε_FP jest **niezmieniony z konstrukcji**:
`false_entry = 0` na `fp_empty` ∧ `fp_bg` ×3 booty pozostaje 0 (`false_gate_frames` 50/26/46 dalej
pochłaniane przez persist+streak). **[PROJEKCJA — D3(iii)]**

## (+) pod rewizją [PROJEKCJA — D3]

| zasięg | admisja (booty) | pokrycie po admisji | werdykt projekcji |
|---|---|---|---|
| 5 m | 2/3 (fix3 brak ENTRY) | 1.0 gdzie admisja | **częściowy** — najbliższy = najgorszy |
| 7 m | 3/3 | 1.0 | **PASS** |
| 9 m | 3/3 | 1.0 | **PASS** |

## Otwarte ryzyko do rozstrzygnięcia POMIAREM (nie projekcją)

1. **fix3@5m brak admisji** — `coverage_gate=0.393` lecz 0 serii K=3. Czy to szum boot-a, czy
   systemowa trudność bliskiego zasięgu (większy cel → więcej komponentów tła w koincydencji → gorszy
   streak)? Re-bramka live @5m ×≥3 booty rozstrzyga.
2. **Wektor FP „ruchomy intruz vs ruchome tło po admisji"** — ENTRY-once ufa strukturze po admisji;
   trzeba potwierdzić, że utrata+re-admisja poprawnie żąda `mti_ok` ponownie (test kanału GT-fed).
3. **Instrumentacja** — re-bramka MUSI logować `recs`→JSONL per-tick + subskrybować
   `vehicle_local_position`, by (a) domknąć atrybucję central vs mti_ok, (b) odblokować okno-K (D2)
   i MTI-P (D4) w tej samej iteracji.

## Koszt

**Jedna re-bramka live** pod zrewidowaną definicją (osobny prompt). Zmiana kodu bramy = poza tą sesją.
Do naniesienia po ratyfikacji: (i) `coverage` (+) liczone jako `coverage_seen` po pierwszym ENTRY;
(ii) definicja w PRE/raporcie; (iii) instrumentacja per-tick. **Nic z tego nie jest nanoszone teraz.**
