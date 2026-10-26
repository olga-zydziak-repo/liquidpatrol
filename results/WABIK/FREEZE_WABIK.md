# FREEZE_WABIK — zamrożenie klasyfikatora i trajektorii nogi WABIK (init S1, PRZED smoke)

CC-wykonawca · 26.10.2026 · PRE_WABIK §1/§2.2 (ratyfikowany, sha
`f2cbf63b…cf3c79`) · PROMPT_WABIK_S1 §1.5. **Po tym commicie zmiana progów =
ANEKS, nie poprawka.** Progi kalibrowane WYŁĄCZNIE na NULL (r2_null.json
+ NULL-scan na percep_feed V2 trzech kampanii) — nigdy na danych wabikowych
(w danych programu nie ma ani jednego wabika). Klasyfikator = sidecar
diagnostyczny, NIE steruje lotem.

## Lista zamknięta cech (okno wygładzone 1.0 s; KRZYWIZNA POZA zestawem — NULL: nie separuje)

| cecha | jednostka | definicja |
|---|---|---|
| v_rad | m/s na oknie 1 s | prędkość radialna tracka DO home (dodatnia = zbliża) |
| speed | m/s na oknie 1 s | moduł prędkości tracka |
| dh | m | dystans poziomy tracka od home |
| dh_min dotychczasowe | m | minimum dh od startu tracka (online, bez przyszłości) |
| czas w strefie | s | przebywanie dh<18 (kontekst okna decyzji) |

Źródło strumienia: `percep_feed.jsonl` → `trk_pos_ned` per klatka (strumień
1:1 z live; posthoc werdyktowo równoważny — klasyfikator nie steruje).

## Progi FROZEN (uzasadnienie per cecha z kwantyli NULL)

| próg | wartość | uzasadnienie (NULL, 263 epizody demo + 115 epizodów percep_feed V2) |
|---|---|---|
| V_MOVE | **0.30 m/s** | warunek RUCHU (lekcja NULL: klasa v=0 = 84 epizody, 0 zejść <5 — bez warunku 100 % FP); speed_p50 klasy v=0: p5=0.068; cele ruchome ≥~0.5 ⇒ 0.30 rozdziela z marginesem z obu stron |
| V_RAD_MAX | **0.30 m/s** | „nie-zbliża": p95 NULL v_rad_p50 = 0.289 + margines (≈ próg V_CLOSE kalibracji NULL) |
| DH_MIN_FLOOR | **5.0 m** | podłoga pasa admisji; NULL ruchomi v=1.0 łamią w 88/90 (p50 dh_min=4.13) |
| R_ZONE | **18.0 m** | dysk ławki (t_in_zone NULL p95=74 s — strefa jest kontekstem, nie separatorem) |
| T_FLAG | **12.0 s** | NULL-scan T∈{4..20}: FP maleje monotonicznie (37→4/115), ale limit TP z PRE §3.2 („etykieta w ≤15 s śledzenia") ogranicza T_FLAG ≤ ~13 s ⇒ 12.0 s = maksimum zgodne z PRE |
| WIN | **1.0 s** | okno wygładzenia (kurs/prędkość tick-po-ticku = szum estymaty — recon R2) |

**Reguła decyzji (FROZEN):** W(t) = [speed>V_MOVE] ∧ [dh<R_ZONE] ∧
[v_rad<V_RAD_MAX] ∧ [dh_min_dotychczas≥DH_MIN_FLOOR]; **etykieta „wabik"
(AKTYWNA)** ⇔ W(t) ciągle przez ≥T_FLAG s; **ODWOŁANIE** ⇔ po fladze złamana
podłoga dh_min<5 (re-klasyfikacja do „poważny" — stan bieżący, nie wyrok).
Raportowane OBIE metryki: etykieta-kiedykolwiek i etykieta-końcowa.

**Pomiar NULL @T_FLAG=12 (zamrożony, przed smoke):** etykieta-kiedykolwiek
**23/115 (20.0 %)**, etykieta-końcowa **13/115 (11.3 %)**. Dekompozycja:
19/23 = cele **v=0.5** (wolne, wędrujące bez zejścia <5 trackiem —
**behawioralnie wabiko-podobne: to zmierzona GRANICA NIERGOZRÓŻNIALNOŚCI
z PRE §1**, nie wada progów), 4/23 = v=1.0 z późną akwizycją (track nigdy
nie widział zejścia). Zbiór T-W-FP S2 (c08_s03, c10_s02, M-ŁUK — szybkie
radiale schodzące <5) pozostaje twardym testem 0/3.

## Trajektorie i scenariusze (parametry FROZEN; `wabik_manifest.json` 046fa12b)

| id | parametry | dh (sanity gęstą próbą) |
|---|---|---|
| W-LOITER | łuk ping-pong R=10.0 m, sektor az 140–220°, v=1.0, z=10, dur 111.6 s | 9.96–10.00 |
| W-STYCZNY | cięciwa b=8.0 m (N −16.12→+16.12, E=−8), v=1.0, 32.2 s | 8.00–18.00 |
| W-ZBLIŻ-ODSKOK | 3×(radialne 15→7 m @az 200° + odskok), v=1.0, 48 s | 7.00–15.00 |
| M-ŁUK (m00_s01, eid 0) | polilinia 8 kroków r 15→4 / az 0→60° (~R_c 10), v=1.0 | r_min 3.97 (schodzi <5 — poważny) |
| M-POD-ORBITĄ (m01_s01, eid 1) | radial 9 s (15→6; ENTRY wcześniej) → kurs +90° 14 s → ku home 10 s → odejście 10 s, v=1.0 | r_min 5.23 |

Wszystkie v ≤ 1.0 (liga R4). Semantyka segmentów 1:1 z bench/scenarios
.position_at; manifest WABIK = NOWY plik (istniejący nietykalny; M-* przez env
`BENCH_MANIFEST` dopiero w S2 — smoke S1 leci na manifeście DOMYŚLNYM).

## Sha narzędzi (16)

| plik | sha |
|---|---|
| `tools/wabik_motion.py` (pusher wabika; GzPoseClient name="wabik"; GT=log wabik_motion.jsonl POZA sędzią) | e690850c0fb39a14 |
| `tools/wabik_sig.py` (klasyfikator; progi j.w. w kodzie = w FREEZE) | 475c972e3388c3e3 |
| `tools/wabik_manifest_gen.py` | ccdce1b9ae3412bd |
| `wabik_manifest.json` | 046fa12b8d074033 |

Reżim OPS w każdym boocie (FREEZE_PERC2_OPS: checklist + pin model.sdf +
profil a68a450b + sonda 8df528bb przed uzbrojeniem). Smoke: intruz = kotwica
**c08_s01 (eid 8)** — historyczne D6 PASS: S2-PERC2 d_min 6.854 / DEMO-C-era
6.877; wabik W-LOITER w sektorze 140–220° (przeciwnym do bearing 0°).
