# RAPORT_SKAN2_S1 — wykonanie PRE_SKAN2: net_skan2 na siatce PERC2 S2 — STOP-SKAN2-1

Wykonawca · 1–2.11.2026 · PROMPT_SKAN2_S1 + ANEKS_SKAN2-0 (b1d4d77a) + ANEKS_SKAN2-0b (b9b67c36).
**Budżet: 2/≤8 bootów (bB_c1011, bA_c08). Oba uzbrojone po sondzie PASS; 8/8 epizodów ważnych
V2′; breach 0 / REFUSE 0.** Zero edycji istniejących plików poza 2 liniami rejestru.

## §0. Werdykt mechanicznie z PRE §3

**V-C** — przez jeden człon: **regresja kontroli c08_s04, t_acq 2.09 s > 1.0 s** (linia bazowa 0.10 s;
D6 PASS). Wszystkie pozostałe człony V-A spełnione: c11 3/3 D6 PASS ze świadkiem przy t_acq
6.83–7.31 s ≤ 10.0 s; c10_s02 t_acq 4.42 s ≤ 8.78 s i PASS; c08_s01/s02/s03 t_acq 0.78/0.16/0.10 s
i PASS; 0 ENTRY z |trk − GT| > 5 m przy GT ≥ 5 m; breach 0.

**Interpretacja nazwana przed lotami** (wiadomość do Olgi przed commitem 1, przy niejasności
zgłoszonej CC dwukrotnie i nierozstrzygniętej w PROMPT_SKAN2_S1): człon V-A „c08 t_acq ≤ 1.0 s
i D6 PASS” liczony dla wszystkich czterech c08 (tak liczy P-SK2-4). Przy literze Q2 (kontrole =
c08_s01, c08_s02 + c10_s02) wszystkie człony V-A są spełnione i werdykt brzmiałby V-A. Wykonawca
nie wybiera między nimi po wyniku; rozstrzyga CC w ANEKS_SKAN2-1.

Zdanie cytowalne V-C (PRE §3, wypełnione): „Admisja w rampie nie przenosi się na profil 68.3/0.4 —
sufit TRANSIT stoi także przy 14.7 Hz” + mechanizm — **zdanie V-C nie zgadza się z danymi
mechanizmu (§3): admisja w rampie przeniosła się w 4/4 epizodach boot 1 (c11 3/3 PASS, t_acq
≤ 7.31 s), a jedyny człon, który przesądził V-C, dotyczy epizodu z celem na wprost przy starcie.**
Zgłaszam to jako niezgodność litery zdania z mechanizmem, nie jako poprawkę werdyktu.

Zdanie V-A, gdyby rozstrzygnięcie poszło za Q2 (do cytowania tylko po ANEKS_SKAN2-1): „Przegląd
perymetru przeliczony na gwarantowaną kadencję — admisja w rampie, krok 68.3°, stare 0.4 s, dwell
startowy 1.0 s — przyjmuje najgorszy azymut przed zamknięciem pasa admisji: T6 bez wiatru 6/6
(c11 3/3, t_acq 6.85 / 6.83 / 7.31 s), kontrole bez regresji, zero fałszywych admisji.”
Profil: 68.3° / 60°/s / 0.4 s / dwell 1.0 start · 2.0 po utracie; bez wiatru, reżim OPS 14.7 Hz, SITL.

## §1. Tabela per epizod (sędzia FROZEN 8ec0fcfb, GT intruza z manifestu, świadek OBOK; `s1_okna.json`)

| epizod | grupa | t_acq [s] | baza net_fantom | D6 | d_min | sweep [°] | świadek | 1. fresh na celu | etykieta | kl. rampa/stare z celem w stożku przed fresh | yaw_rate przy admisji [°/s] | ENTRY FP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c10_s02 | T6 | **4.42** | 8.78 PASS | **PASS** | 7.122 | 731.6 | 0/3335 | 4.38 | PIERWSZE | 2/0 | 22.2 | 0 |
| c11_s02 | T6 | **6.85** | 12.23 FAIL | **PASS** | 7.120 | 911.3 | 2/3442 | 6.80 | PIERWSZE | 5/0 | 59.1 | 0 |
| c11_s03 | T6 | **6.83** | 12.31 FAIL | **PASS** | 6.713 | 726.2 | 1/3450 | 6.78 | PIERWSZE | 5/0 | 66.0 | 0 |
| c11_s04 | T6 | **7.31** | 24.97 FAIL | **PASS** | 6.640 | 798.1 | 1/3466 | 7.25 | PIERWSZE | 12/0 | 48.7 | 0 |
| c08_s01 | kotwica | 0.78 | 0.72 PASS | **PASS** | 6.855 | 853.6 | 0/3246 | 0.74 | PIERWSZE | 3/0 | — (bez ENTRY w epizodzie; 144.4 przy 1. fresh) | 0 |
| c08_s02 | kotwica | 0.16 | 0.27 PASS | **PASS** | 5.791 | 757.4 | 2/3269 | 0.10 | PIERWSZE | 0/0 | — (track sprzed t0) | 0 |
| c08_s03 | T6 | 0.10 | 0.31 PASS | **PASS** | 5.363 | 839.1 | 0/3216 | 0.06 | PIERWSZE | 0/0 | — (track sprzed t0) | 0 |
| c08_s04 | T6 | **2.09** | 0.10 PASS | **PASS** | 5.591 | 689.6 | 0/3217 | 2.06 | PIERWSZE | 9/21 | 69.2 | 0 |

D6 pokładowy (litera manifestu, bez świadka): 8/8 PASS (d_min 5.67–7.15). D6 ze świadkiem: 8/8.
**T6 bez wiatru 6/6** (c08_s03, c08_s04, c10_s02, c11 ×3) vs 3/6 w PERC2 S2.
Kadencja w locie dt_p50 0.064–0.068 s, frac > 0.10 s = 0.0 we wszystkich 8.
Etykieta: 8/8 PIERWSZE PRZEJŚCIE, 0 CHYBIONE, 0 BRAK.

## §2. Mechanizm c08_s04 (opisowo, z logów)

W PERC2 S2 c08_s04 miał track na celu już w t0 (pierwsza fresh na celu 0.02 s, zero ENTRY w epizodzie,
kwarantanna wyszła po 0.10 s). W SKAN2 epizod startuje bez żywego tracka (kwarantanna 342.46 → 344.56 s,
2.09 s): cel jest w stożku centralnym od 0.01 s, nos stoi w dwell 1.0 s (21 klatek stare z celem
w stożku, koincydencja central∧MTI 0/22 przy 0–2°/klatkę — cel czołowo, MTI na celu nie odpala),
po dwell rusza rampa i admisja zachodzi w rampie przy 69.2°/s, ENTRY → fresh 2.06 s. Profil
skanu wpływa tu przez to, że nos w ogóle zaczyna się obracać po 1.0 s (z dwell 2.0 s rampa ruszyłaby
o 1.0 s później). Różnicy stanu tracka w t0 (żywy w PERC2, brak w SKAN2) ten raport nie wyjaśnia —
faza przed t0 nie jest sterowana profilem net_skan2 w hold, a przyczyny nie mierzyłem.

## §3. Pomiary opisowe

- **Admisja w rampie:** we wszystkich 5 epizodach z ENTRY w epizodzie (c10, c11 ×3, c08_s04) admisja
  zaszła w klatce rampy (22–69°/s); w c10/c11 nie było ani jednej klatki stare z celem w stożku
  przed fresh.
- **κ** (koincydencja central∧MTI per klatka, klatki z celem w stożku centralnym przed pierwszą
  fresh na celu, 8 epizodów łącznie): 0–2°/kl 1/23 (0.04); 2–4°/kl 3/20 (0.15); 4–6°/kl 7/11 (0.64);
  6–8°/kl 0/0; > 8°/kl 0/3. Profil 60°/s @14.7 Hz = 4.1°/kl — koszyk 4–6 najmocniejszy.
- **FP (§3 PRE):** 0 ENTRY z |trk − GT|_xy > 5 m przy |GT − dron| ≥ 5 m; 0 ENTRY bez tracka; łącznie
  5 ENTRY w 8 epizodach, wszystkie na celu.
- **Stalle:** n_deep 2 w c10_s02 i c08_s01, najdłuższy 0.0 s; dsim/dwall 0.9944–1.0000. Żadne zdarzenie
  deep nie pokrywa się ze skokiem w `zegar2.jsonl` (0 skoków) — etykieta „artefakt zegara” 0×.

## §4. Predykcje (TAK / NIE / n.r.; rozlicza CC)

- P-SK2-1 (c11 ≥ 2/3 D6 PASS ze świadkiem): **TAK** (3/3).
- P-SK2-2 (c11 przyjęte w pierwszym przejściu t_acq ≤ 8.0 s): **TAK** (6.83–7.31).
- P-SK2-3 (≥ 1 CHYBIONE w 8): **NIE** (0/8).
- P-SK2-4 (c08 4 epizody t_acq ≤ 1.0 s): **NIE** (c08_s04 2.09).
- P-SK2-5 (0 ENTRY FP): **TAK**.
- P-SK2-6 (breach 0): **TAK**.

## §5. Zegar, sondy, budżet

- Próbniki 60 s: pusty host po `wsl --shutdown` 2 skoki (+1.01/+1.02 s) → STOP-SKAN2-ZEGAR; przed b1
  wg ANEKS_SKAN2-0 1 skok +1.71 s → STOP-SKAN2-ZEGAR; po `systemctl stop systemd-timesyncd`
  (ANEKS_SKAN2-0b, jedna próba) 0 skoków, dryf 0.000 s → PASS; przed b2 (timesyncd dalej
  zatrzymany) 0 skoków → PASS.
- W locie `zegar2.jsonl`: b1 0 skoków / 485.8 s, b2 0 skoków / 461.5 s; V2′ wall vs mono tożsame
  (dryf 0.000 s). Manifesty: `zegar: {timesyncd: stopped, clocksource: tsc}`.
- Po sesji `systemctl start systemd-timesyncd` — stan po w `s1/zegar_stan_po.txt` (active, NTP active).
- **Reżim zegara obu kampanii:** PERC2 S2 (25.10) leciał na czystym zegarze przy aktywnym timesyncd;
  SKAN2 S1 na czystym zegarze przy zatrzymanym timesyncd — oba bez skoków realtime w locie.
- Diagnoza z danych: kroki realtime robił `systemd-timesyncd` (zatrzymanie usunęło je w całości).
  Uwaga: `uptime -s` przesunął się w sesji 23:17:47 → 23:18:48 (~61 s sumy kroków).
- Sondy kadencji preflight: b1 PASS (dt_p50 0.064, frac 0.0), b2 PASS (0.068, 0.002).
- **Budżet: 2/8**; zero doleceń, zero powtórek sondy.

## §6. Testy, diff drivera, kontrola kopii analizy

- T1–T4 PASS (commit 522c544c; wypis w opisie commitu): T1 12044 ticków (pass-through 10668, tożsamość
  obiektu), T2 rampa 60.000°/s, krok 68.3000°, stare 0.350 s (siatka 0.05 s), 273.1° o 6.80 s (wzór
  6.7515), T3 reset, T4 rejestr +2/−0, weights_sha 0337d5ea.
- `skan2_s1_boot.sh` (24bf5c24) vs `perc2_s2_boot.sh` 62fd9786 — zmiany wyłącznie: nagłówek-komentarz
  opisujący kopię; `OUTDIR`/`MONLOG` → results/SKAN2/s1 + skan2_s1_monitor.log; `mkdir` katalogu;
  start próbnika `skan2_zegar.py → OUTDIR/zegar2.jsonl` przed run_boot i `kill -TERM` po bootcie;
  `CONTROLLER=net_skan2`, `KIND=skan2` (także w echo monitora); blok manifestu `"skan2"` (sha skan2_scan,
  rejestru, fantom_scan, akw_scan; litera profilu); **pole `"zegar"` (ANEKS_SKAN2-0b §2.2) — dopisane
  po ANEKS-0b, przed bootem 1.** Blok `"fantom"` zostawiony verbatim, więc nadal opisuje profil
  delegata 40/1.2 (`scan_profile_delegata`) — w locie nadpisany przez net_skan2 w hold; prawdę o
  profilu niesie blok `"skan2"`. Prefiks logów `[perc2S2 …]` zostawiony verbatim.
- `skan2_analyze.py` (68e7d7d7) vs `perc2_s2_analyze.py` 7ae917f4: zmienione 3 linie (docstring
  pierwszy wiersz, `OUTD`, zapis pod `SKAN2_OUT`), dodana funkcja `skan2_kolumny` + klucz `"skan2"`;
  litera t_acq/D6/świadka/okna bez zmian. **Kontrola kopii:** na results/PERC2/s2/{bA_c08,bB_c1011}
  → `kontrola_perc2.json`: t_acq / D6 / d_min 8/8 co do setnej jak tabela RAPORT_PERC2_S2.
  Oryginał nieuruchamiany; `results/PERC2/s2_okna.json` nietknięty.

## §7. Diff-stat sesji, porcelain

Commity: 585f4d14 [PRE], 522c544c [S1-build], 962b0b4a [ANEKS-0], 2f9a5e2c [ANEKS-0b], commit 3
[STOP-SKAN2-1]. Pliki: PRE_SKAN2.md, ANEKS_SKAN2-0.md, ANEKS_SKAN2-0b.md, r03/controllers/skan2_scan.py,
r03/controllers/__init__.py (+2), results/SKAN2/** (boot.ulg pominięte regułą .gitignore; sha w
ulog_sha.txt). Porcelain po commicie 3: czysty poza nieśledzonymi results/DEMO_C/*. Push = Olga.

**STOP-SKAN2-1.**
