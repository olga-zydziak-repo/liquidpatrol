# RAPORT_PERC2_S1 — sesja S1 nogi PERCEPCJA-II (OPS-KADENCJA): macierz remediów + sonda + pin — STOP-PERC2-1

CC-wykonawca · 25.10.2026 · wykonanie PROMPT_PERC2_S1 (PRE_PERC2 ratyfikowany,
byte-check PASS `24369ed9…1d9e21`, commit 1 nogi = PRE verbatim `96718e90`).
Budżet S1: **3/≤4 bootów** (b1_diag · b2_diag ABORTED · b2r_diag), **0 uzbrojeń,
0 sędziego, breach 0 / REFUSE 0** (nic nie latało). Zero edycji istniejących
plików; nowe pliki wyłącznie korzeń (PRE) + `results/PERC2/**`.

**WYNIK GŁÓWNY: REMEDIUM SKUTECZNE ISTNIEJE I JEST ZMIERZONE (śmierć S1 NIE
zaszła; P-P2-1 = TAK), ale mechanizm okazał się INNY niż teza:**

1. **Render-vs-most ROZSTRZYGNIĘTE: klatki gubi TRANSPORT/MOST (DDS), nie render
   sensora.** Pomiar równoległy w tej samej chwili: poziom gz = 606 klatek/40 s,
   dt_sim p50 = p90 = 0.068 s, frac>0.10 = 0.0 (ZAWSZE, we wszystkich próbach,
   także 1362/90 s), podczas gdy percep w stanie zastanym dostaje 248–285
   (frac 0.47–0.61), a goły subskrybent ROS 47–114 klatek.
2. **Mechanizm (zmierzony):** klatka mono8 640×480 = 307 200 B przekracza
   pojemności domyślnego transportu FastDDS (segment SHM 512 KB ≈ 1.6 klatki;
   bufor UDP ~208 KB < 1 klatka) ⇒ losowa utrata wiadomości BEST_EFFORT per
   subskrybent. To wyjaśnia też literę R1 recon: rozkład k_hist (0.48/0.26/
   0.10/0.07…) jest GEOMETRYCZNY — „mod" bootu to per-bootowa stopa dostarczenia
   p, nie czysta podharmoniczna; dt_p50 ląduje na 1/2/3 tikach zależnie od p.
3. **KOREKTA TEZY PRE (odchylenie jawne, pomiar zamiast przyjęcia):** teza
   „wyborem k steruje stan GPU hosta" jest SFALSYFIKOWANA jako mechanizm
   bezpośredni — GPU zdrowe we wszystkich próbach S1 (push_frame p50 16.5–19.8 ms
   ≪ 68 ms; render pełne 14.71 Hz; pstate P4–P8, 47–63 °C). Korelacja push ×1.8
   @WOLNY z recon pozostaje faktem historycznym — współobjaw stanu hosta, nie
   przyczyna kadencji. DŹWIGNIA PRE (gwarancja k=1 środkami OPS) jest
   POTWIERDZONA: remedium transportowe, zero dotyku percepcji.
4. **Remedium SKUTECZNE:** profil FastDDS `perc2_fastdds_profile.xml`
   (SHM 16 MB + bufory UDP 4 MB, builtin off) dla mostu obrazu i percep →
   **dt_p50 = p90 = 0.068 s, frac>0.10 = 0.0000–0.0020, k=1 stabilnie 40/90/35 s**
   (sonda PASS ×3, w tym tryb LIVE). Strona: WSL, zero komend Windows, zero
   admina. Kandydaci GPU z listy PRE — zmierzeni/bezprzedmiotowi (niżej).

## §1. Bramka wejścia — PASS

Byte-check PRE: sha256 `24369ed95017f5256ac02947f521a9900cb289919996976590c5f5485e1d9e21`
ZGODNY ✓ → commit 1 nogi `96718e90` (PRE verbatim, osobny). `git fetch` →
origin/master = **a0bdc5e1 (STOP-PERC2R)** ✓, `origin/master..HEAD` puste ✓,
porcelain czysty ✓. FROZEN wykonaniem: piny osłony 5/5 (SHIELD FROZEN True),
certy 9/9, sędzia 8ec0fcfb · bench 05137098 · fantom_scan e435ed7e · rejestr
87203d29 · akw_scan b94cdeae · FREEZE_DET w całości (det_v2.pt 775ead15 ·
percep_proc 38a3a765 · feed_vision_proc 79633489 · feed_registry ee1481f9) ·
ncp 0337d5ea.

## §2. Stan hosta (desk, przed bootami)

WSL2, GPU RTX 5070 Laptop (driver Win 577.13, CUDA 12.9), interop
`nvidia-smi.exe` DZIAŁA (odczyty; zapisy wymagają admina). Zastane:
Persistence-M **On** · pstate P8 idle (180–277 MHz, max 3090) · **power-limit
55 W przy Default 70 / Max 115 W** (obniżony; zmiana = admin Windows — komenda
w FREEZE §checklist, NIEUŻYWANA) · pin zegarów `-lgc` = admin Windows (test
no-op: „does not have permission" po OBU stronach) · obce procesy GPU: **brak**
(wyłącznie explorer.exe) · zasilanie **AC 100 %** (Win32_Battery status 2), plan
„Acer". Bufory jądra: rmem_max/wmem_max 4 MB, **rmem_default/wmem_default
212 992 B** (po restarcie WSL wartości wracają do domyślnych — `sysctl -w` nie
jest trwały, co S1 zmierzyło w praktyce między bootami).

## §3. Macierz stan×remedium (pełne liczby: `s1_macierz.json`; manifesty bootów: pole `sondy[]`)

Per próba: sonda kadencji POSTHOC na percep_feed próby (percep_proc FROZEN
uruchamiany per próba) + równoległy `perc2_gzhz` (poziom gz) + goły subskrybent
`perc2_roscount` (strata DDS bez percepcji) + snapshot GPU + push_frame z summary.

| boot | próba | remedium | dt_p50 [s/kl] | frac>0.10 | hz | push p50 [ms] | sonda |
|---|---|---|---|---|---|---|---|
| b1 | A2 | stan zastany | 0.132 | 0.606 | 7.58 | 16.48 | **FAIL** |
| b1 | B (roscount d1 / +busy 17 ms) | stan zastany | 0.264 / 0.264 | 0.91 / 0.82 | 3.79 | — | — |
| b1 | C1 (roscount) | sysctl 4 MB (stare sockety mostu) | 0.396 | 0.84 | 2.53 | — | — |
| b2r | T1 | stan zastany (świeży host; sysctl zresetowany restartem WSL) | 0.068 | **0.474** | 14.71 | 17.39 | **FAIL** (frac) |
| b2r | T1 (roscount) | stan zastany | 0.196 | 0.67 | 5.10 | — | — |
| b2r | T2 | sysctl 4 MB + ŚWIEŻY most | 0.132 | 0.695 | 7.58 | — | **FAIL** |
| b2r | T2 (roscount) | sysctl 4 MB + świeży most | 0.396 | 0.92 | 2.53 | — | — |
| b2r | **T3** | **profil FastDDS (SHM 16 MB + UDP 4 MB, obie strony)** | **0.068** | **0.0017** | **14.71** | 17.80 | **PASS** |
| b2r | T3 (roscount) | profil FastDDS | 0.068 | 0.000 | 14.71 | — | — |
| b2r | **T4** | profil FastDDS, okno 90 s | **0.068** | **0.0000** | **14.71** | 19.84 | **PASS** |
| b2r | **T5** | profil FastDDS, sonda tryb **LIVE** 35 s | **0.068** | **0.0020** | **14.71** | — | **PASS** |

Poziom gz we WSZYSTKICH próbach: 14.71 Hz, frac 0.0 (606/40 s; 1362/90 s).
GPU we wszystkich próbach: pstate P4–P8, 277 MHz, 17–24 W, 47–63 °C, util
12–45 % — zdrowe, bez zmian między FAIL i PASS.

**Kandydaci z listy PRE §2.1 — rozliczenie:** persistence = zastane On (bez
akcji) · pin zegarów / power-limit = wymagają admina Windows; komendy zapisane
(FREEZE §checklist), NIE wykonane — **bezprzedmiotowe wobec zmierzonego
mechanizmu** (GPU wykluczone pomiarem: push ≪ budżetu, render pełny rate,
stany GPU identyczne przy FAIL i PASS) · obce procesy GPU = brak · kolejność
startu gz vs percep = bez wpływu (percep zawsze po stacku; mechanizm
transportowy, nie startowy) · **kandydat spoza listy (dopisany pomiarem):
transport DDS — SKUTECZNY** (sysctl sam NIE wystarcza: T2 FAIL — FastDDS używa
SHM lokalnie i własnych limitów; wymagany profil XML po obu stronach mostu).

## §4. Sonda kadencji — transkrypt zachowania (PASS i FAIL wystąpiły)

FAIL (stan zastany, b2r T1): `dt_p50 0.068 ∧ frac 0.4735 > 0.05 ⇒ FAIL` — sonda
łapie przypadek, w którym mediana przechodzi, a strumień jest dziurawy (47 %
delt > 0.10 s); dokładnie ten mod psuł okna admisji. FAIL (A2/T2): dt_p50
0.132 > 0.070 ⇒ FAIL. PASS (T3/T4 posthoc, T5 LIVE): liczby j.w., rc=0.
Procedura bramki (FROZEN): FAIL ⇒ remedium ⇒ powtórka ⇒ drugi FAIL = boot się
nie uzbraja. Wynik sondy w manifeście bootu jako pole 1. klasy (`sondy[]` —
b1_diag: 1 wpis; b2r_diag: 5 wpisów; wzór dla driverów S2).

## §5. Pin prowieniencji — wykonany

`mono_cam/model.sdf` sha256 = `3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c`
(prefiks **3354ae1e** = zgodny z recon ✓; pełny sha w FREEZE). Driver liczy pin
przy KAŻDYM boocie PRZED startem stacka, obok world_hash (world_demo_A3
`adc91803…`); rozjazd = STOP (perc2_s1_boot.sh; zero edycji world_hash.sh).
Wykonane w bootach b1/b2/b2r — 3× PIN OK.

## §6. Noty

- **Errata-w-przód (zapowiedziana przy ratyfikacji):** mod WOLNY to per boot
  mieszanka **49/50 kroków fizyki** (dt_p50 0.196/0.200 s — FANTOM r5/r7/r11 vs
  r4/r6/r8/r9/r10/r12): kwantyzacja ticków 16/17 kroków na niecałkowitej siatce
  15 Hz × 4 ms. RECON_PERC2 pisał „49", PRE „50" — obie wartości prawdziwe,
  obie = k=3; teza i progi bez zmian. (Po S1 wiadomo więcej: „k" to nie czysty
  licznik pominiętych ticków, lecz skutek losowej utraty — dt_p50 odzwierciedla
  stopę dostarczenia p; kwantyzacja do siatki ticków pozostaje faktem.)
- **Boot 2 (b2_diag) ABORTED:** driver zabity zewnętrznie (przerwanie sesji)
  tuż po starcie stacka — zero prób, stack nie przeżył, katalog z ABORTED.txt;
  liczony do budżetu S1 (3/4) uczciwie.
- **Trwałość remedium:** `sysctl -w` nie przeżywa restartu WSL (zmierzone:
  wartości wróciły do 212 992 B między b1 a b2r) — ale remedium skuteczne go
  NIE wymaga (profil XML ustawia bufory per proces); checklist w FREEZE.
- **Dla S2/kampanii:** boot z profilem = percep na k=1 — to jest dokładnie
  dźwignia nogi (kadencja percepcji), percepcja/progi/sędzia nietknięte; mod
  pozostaje telemetrią opisową (bramka sondy jest narzędziowa, przed
  uzbrojeniem); porównywalność z kampaniami historycznymi — przez kwalifikator
  reżimu kadencji, jak dotąd.

## §7. Artefakty

`results/PERC2/`: **FREEZE_PERC2_OPS.md** · **RAPORT_PERC2_S1.md** (ten plik) ·
`s1_macierz.json` · `s1/b1_diag/**`, `s1/b2_diag/**` (ABORTED), `s1/b2r_diag/**`
(manifesty z polem `sondy[]`, feedy prób, gzhz/gpu/push/roscount JSON-y, logi) ·
`tools/perc2_sonda.py` · `tools/perc2_gzhz.py` · `tools/perc2_roscount.py` ·
`tools/perc2_trial.sh` · `tools/perc2_s1_boot.sh` · `tools/perc2_fastdds_profile.xml`.
Korzeń: `PRE_PERC2.md` (commit 1, `96718e90`). **Push = Olga.** Po weryfikacji
CC: ANEKS_PERC2-1, dopiero wtedy S2. **STOP-PERC2-1.**
