# RAPORT_PERC2_S2 — test celowany T6-geometrii @k=1 — STOP-PERC2-2

CC-wykonawca · 25.10.2026 · wykonanie ANEKS_PERC2-1 §3 (aktywacja PRE_PERC2 §3).
**Budżet S2: 2/≤10 bootów (bA_c08, bB_c1011); noga 5/≤14. Oba booty uzbrojone:
breach 0 / REFUSE 0; 8/8 epizodów ważnych (dsim 0.991–1.000).** Zero dotyku
percepcji/progów/sędziego/osłony; driver-kopia perc2_s2_boot.sh (reżim fantomS2
verbatim + pin + sonda przed uzbrojeniem + profil FastDDS dla mostu/percep).

**WERDYKT ZDANIAMI ZAMROŻONYMI (PRE §3.3, verbatim):**

- **SUKCES DŹWIGNI: run≥3 (admisja okna) w 6/6 epizodów T6 ≥ 5/6 ⇒ ZASZEDŁ.**
- FALSYFIKACJA (run<3 mimo k=1 w ≥3/6): **0/6 — NIE zaszła.**
- Kotwice-kontrole: **c08_s01 D6 PASS (d_min 6.85) · c08_s02 D6 PASS (5.47)** —
  obie miały zostać PASS @k=1 i są.

## §1. Bramki i reżim — PASS

ARCH-1: ANEKS_PERC2-1 verbatim w korzeniu (commit osobny `1503f880`). Bramka:
origin=3f3c7cc4 ✓ gate pusty ✓ porcelain czysty ✓; piny 5/5, certy 9/9, FROZEN
komplet (sędzia 8ec0fcfb, bench 05137098, fantom_scan e435ed7e, ncp 0337d5ea,
det_v2.pt 775ead15, percep_proc 38a3a765) + FREEZE_PERC2_OPS (sonda **8df528bb**,
profil **a68a450b**, pin model.sdf pełny). **Każdy boot:** checklist hosta → PIN
model.sdf + world_hash PRZED stackiem (2× PIN OK) → profil FastDDS wyłącznie dla
mostu obrazu i percep (GUARD sha profilu w driverze; XRCE/PX4 domyślne) →
percep+most przed uzbrojeniem → **sonda kadencji preflight: PASS w obu bootach
za pierwszym podejściem** (bA: dt_p50 0.068 / frac 0.0017; bB: 0.068 / 0.0) —
wynik w manifeście (`perc2.sondy[]`, `uzbrojony_po_sondzie: true`).

## §2. Tabela okien per epizod (przyrząd 1:1 z perc2_r1/transit_r1; pełne dane `s2_okna.json`)

| epizod | grupa | t_acq [s] | dt lotu p50/frac | okno: n kl / p̂(c∧m) / max run | admisja run≥3 | P_model DP | D6 (sędzia FROZEN, GT manifest) | d_min | świadek |
|---|---|---|---|---|---|---|---|---|---|
| c08_s01 | kotwica | **0.72** | 0.068 / 0.0 | 1090 / 0.990 / 1050 | **TAK** | 1.000 | **PASS** | 6.854 | 0/3187 |
| c08_s02 | kotwica | **0.27** | 0.068 / 0.0 | 1092 / 0.996 / 1084 | **TAK** | 1.000 | **PASS** | 5.465 | 1/3154 |
| c08_s03 | T6 | **0.31** | 0.068 / 0.0 | 1093 / 0.992 / 939 | **TAK** | 1.000 | **PASS** | 5.613 | 1/3168 |
| c08_s04 | T6 | **0.10** | 0.064 / 0.0 | 1091 / 0.997 / 941 | **TAK** | 1.000 | **PASS** | 6.733 | 2/3166 |
| c10_s02 | T6 | 8.78 | 0.064 / 0.0 | 1071 / 0.998 / 1069 | **TAK** | 1.000 | **PASS** | 5.584 | 0/3495 |
| c11_s02 | T6 | 12.23 | 0.068 / 0.0 | 40 / 0.300 / 6 | **TAK** | 0.540 | FAIL [b_frac, d_dmin] | 0.921 | 1/3635 |
| c11_s03 | T6 | 12.31 | 0.064 / 0.0 | 18 / 0.389 / 4 | **TAK** | 0.494 | FAIL [b_frac, d_dmin] | 1.326 | 3/3653 |
| c11_s04 | T6 | 24.97 | 0.068 / 0.0 | 881 / 0.990 / 795 | **TAK** | 1.000 | FAIL [b_frac, d_dmin] | 1.728 | 2/3665 |

**Vs przewidywania modelu DP (S0):** okna @k=1 są ~3× dłuższe w klatkach —
zgodnie z modelem admisja w oknach długich (n≥800, p̂≥0.99) jest pewnikiem
(P=1.0, runy 795–1084 vs 0–2 @WOLNY w kampanii); dwa okna KRÓTKIE przy małym dh
(c11_s02/s03: n=18–40, p̂ 0.30–0.39 — strefa zbocza bliskiego, jak w anatomii)
miały P_model 0.49–0.54 i obie wygrały (run 4–6) — dalej loteryjne, co model
przewiduje; przy k=1 loteria przestała dotyczyć WEJŚCIA w korytarz (c08/c10),
zostaje w resztkowych oknach głębokich. GT manifestu walidowane per epizod
(p50 0.060–0.072 m); jednostki per-klatkowe.

## §3. D6 OPISOWO (sufit TRANSIT obowiązuje — cytowanie wyłącznie z tym kwalifikatorem)

**T6 @k=1: D6 3/6** (c08_s03, c08_s04, c10_s02 PASS / c11_s02, c11_s03, c11_s04
FAIL) — **dokładnie w prerejestrowanym oczekiwaniu 2–3/6**; sufit TRANSIT
(przegląd perymetru 11.15 s > pas admisji 10.0 s, niezależny od kadencji) trzyma
dla bearingu 270° (c11): t_acq 12.2–25.0 s = skan dociera w korytarz po
zamknięciu pasa; admisja wtedy ZACHODZI (ENTRY, runy 4–795), ale za późno na
konwersję (d_min 0.92–1.73 przed/w trakcie akwizycji — ślepy tranzyt się odbył).
Dla bearingu 0° (c08) okno dwell jest natychmiastowe: **t_acq 0.10–0.72 s**
(vs 19.5–31.2 s tych samych epizodów @WOLNY w kampanii FANTOM) — loteria czołowa
ZNIKŁA, oba T6 c08 przechodzą D6; c10 (180°) łapie korytarz w pierwszym przeglądzie
(t_acq 8.78 s < pas 10.0 s) i przechodzi.

**ROZJAZD POKŁADOWY (nazwany; reguła ERRATUM_DMIN w akcji):** pokładowa litera
manifestu dała c08_s03 FAIL d_min=1.251 i c08_s04 FAIL d_min=0.557 — to artefakt
tranzientu teleportu w surowym gt_intruder (świadek: 1–2 próbki na brzegu startu;
d_min z GT manifestu: 5.613/6.733, sędzia FROZEN pełną literą t_entry 2.86–3.37 s,
frac_band 0.90–1.00, sweep 766–849°). Werdykty tego raportu liczone na GT
z manifestu ze świadkiem OBOK (obowiązująca reguła od ANEKS_POSCIG-1);
litera pokładowa pozostaje w manifestach nietknięta. FAILe c11 są REALNE
(d_min z manifestu 0.92–1.73, świadek 1–3 próbki nie-werdykto-nośne).

## §4. Predykcje (wskaźniki; rozliczenie KSIĘGI przy CO)

- **P-P2-2 (admisja ≥5/6 T6): TAK — 6/6.**
- **P-P2-3 (oba c08 D6): TAK rachunkiem erratum** (pokładowa litera: NIE przez
  artefakt tranzientu — rozliczenie w CO z tym kwalifikatorem).
- **P-P2-4 (breach 0 / REFUSE 0): dotąd TAK** (0/0 w 2 uzbrojonych bootach S2;
  5 bootów nogi łącznie).
- **P-P2-5 (sonda jako predyktor): TAK — oba booty przeszły sondę i oba trzymały
  k=1 w locie** (dt_p50 lotu 0.064–0.068 ≤ 0.070, frac>0.10 = 0.0 we wszystkich
  8 epizodach).

## §5. Noty

- Zbiór NIELOSOWY (T6 + kotwice): żadnej interpretacji progowej siatki, zero Δ —
  sonda mechanizmowa (słabość nazwana w recon §R6, PRE §3.2 i tu powtórzona).
- Kadencja lotu = reżim z profilem (czystszy niż najlepszy boot historyczny —
  ANEKS_PERC2-1 §2.2); porównania z kampaniami wyłącznie z kwalifikatorem reżimu.
- `ENTRY_w_oknie` w bootach bA = False przy natychmiastowej akwizycji (track
  admitowany na pierwszych klatkach rozbiegu epizodu — zdarzenie ENTRY pada
  przed/na granicy okna stożka); admisja dowiedziona runami i t_acq; w bB ENTRY
  w epizodzie True 4/4.
- Kwarantanna: q_events 2/epizod (wejście/wyjście czyste), bez udziału
  w mechanizmie.

## §6. Artefakty

`results/PERC2/`: **RAPORT_PERC2_S2.md** (ten plik) · `s2_okna.json` (pełne okna
per epizod + sędzia + świadek + kadencje) · `s2/bA_c08/**`, `s2/bB_c1011/**`
(manifesty z blokami perc2/fantom/feed_v2 i polem sondy[], percep_feed, demo,
trace, qlog, boot.ulg, sonda_preflight.json) · `tools/perc2_s2_boot.sh` ·
`tools/perc2_s2_analyze.py`. **Push = Olga („wypchnięte").** Po weryfikacji CC:
ANEKS_PERC2-2 (werdykt, KSIĘGA P-P2-1…5, decyzja o kampanii metrologicznej —
osobna, nieprekomitowana — i CO). **STOP-PERC2-2.**
