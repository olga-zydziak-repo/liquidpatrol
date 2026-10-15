# FREEZE_FANTOM — zamrożenie przyrządu nogi FANTOM (init przy S1, PRE_FANTOM §2/§7)

Wykonawca · 15.10.2026 · po ratyfikacji PRE_FANTOM (Olga, 15.10) i PROMPT_FANTOM_S1;
ARCH-1 = commit a7f3073c (PRE_FANTOM.md VERBATIM, pierwszy commit sesji).

## Predykat i parametry kwarantanny (FROZEN — zmiana wartości = ANEKS, nie env)

| parametr | wartość |
|---|---|
| predykat wyjścia | **K1** — pierwsze z: (A) invalid→valid fd, (B) przeskok trk_pos > D_JUMP vs migawka z t_ref, (C) upływ T_q. WYBRANY regułą desku T2 (PRE §2 mechanicznie): K2 padł na (ii) — lock-real c05_s04 bez odświeżeń w epizodzie przez 3 s (age 0.14→3.18, pomiar) + outlier czysty c04_s03; K1 ze złagodzonym (ii) spełnia (i)/(ii≤T_q)/(iii 8/9) |
| T_q (C) | **3.0 s** (= θ_age kanału) |
| D_JUMP (B) | **5.0 m** (= próg fantomu z recon; REFRESH_GATE=3 m nie skacze dalej — skok to mti-przechwyt) |
| ε (K2) | 0.5 s — kandydacki, NIEUŻYWANY przy K1 (zapis jawny) |
| marker startu epizodu | **reset()** (bench_flight.py:312, per epizod) — BEZ env |
| t_ref | now_s PIERWSZEGO step() po reset() |
| zachowanie w kwarantannie | delegat (AkwScan b94cdeae) dostaje fd „brak tracku" (podmiana NOWYM dictem WYŁĄCZNIE dla fd ważnego; fd nieważny idzie surowy — sterowanie identyczne, echo telemetrii prawdziwe) ⇒ hold → dwell 2.0 → profil II od ψ_last=0 |
| wyjście | jednorazowe per epizod; po wyjściu pass-through VERBATIM (ten sam obiekt fd, cmd bez kopii) |
| telemetria | klucze q_active/q_exit_reason/q_exit_t w cmd["extra"] TYLKO na tickach kwarantanny + ticku wyjścia; dziennik diagnostyczny env `FANTOM_QLOG` (jsonl; brak env = brak logu) |
| koszt nazwany (T2) | wyjście (C) +3 s na 12/48 epizodach B (valid-statyczne bez skoku/utraty) i na lock-real/czystych-outlierach z admisją przedstartową |

## Sha zamrożone (sha256)

| plik | sha256 |
|---|---|
| `r03/controllers/fantom_scan.py` (wrapper, NOWY) | `e435ed7e3f3ce47dd7b3b88651dff02ae76ddb14823ac913e544d849cd09d849` |
| `r03/controllers/__init__.py` (PO wpisie net_fantom — wpis additive: import + linia rejestru; historia: 4f58d204 po net_akw) | `87203d292ac9c9169c6e986e22b534c6c578fd4a597720c2df89cec5d7749bd9` |
| `results/FANTOM/tools/test_pre_fantom.py` (testy przedlotowe: T1a/T1b/TP/TR — 12 testów) | `73c7825fa57c106671043ec9ae3cf47e19af0cb3d8e5a52f1dbc7625dcf9fba5` |
| `results/FANTOM/tools/fantom_t2.py` (desk T2 — reguła wyboru; wynik t2_desk.json) | `b7bf402a9b91db92c7197181bd4cd44ce8e27046b20620bc84bf19caf7103497` |

## Dziedziczone VERBATIM (bajty bez zmian — edycja = STOP)

FREEZE_AKW w całości (w tym profil II `akw_scan.py` **b94cdeae**, narzędzia kampanii
S3) · FREEZE_DET w całości · piny 5/5 (shield 1c584964 · config 4c440e42 · gate_run
5647ae20 · base 7fc45cf2 · safe_descend e3c1040b) · certy 9/9 · bench_flight
`05137098` · bench_judge `8ec0fcfb` · feed_vision `acc81df7` · det_v2.pt `775ead15` ·
percep_proc `38a3a765` · feed_vision_proc `79633489` · feed_registry `ee1481f9` ·
ncp `0337d5ea` · net_controller `e8c1b658` · bezpiecznik modu (ANEKS_AKW-2 §3).

Weryfikacja przy S1 (wykonaniem): piny 5/5 PASS, certy 9/9 PASS, sha zgodne.
Testy przedlotowe: **12/12 PASS**. Istniejące pytest + nowe: **155 passed, 0 failed**
pod ROS env ×2 przebiegi (pełny przegląd plików testowych repo jak AKW S2 + 12 FANTOM);
nota: w pierwszym przebiegu pełnego zakresu jednorazowa flaka
`test_cykl_zycia_percep_proc` (DET-tools, klasa środowiskowa rclpy/proces — test nie
importuje fantom_scan; dwa kolejne przebiegi czyste, solo-grupa czysta).
