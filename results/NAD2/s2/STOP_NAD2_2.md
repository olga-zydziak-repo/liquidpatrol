# STOP-NAD2-2 — smoke NADIR-II: passthrough bitowy (6405 ticków, 0 różnic) i cięcie c11_s02 pod literą NAD2 — (s1)–(s4) PASS, żadna śmierć S2

11.11.2026 · wykonawca · PROMPT_NAD2_S2 (sha256 4e31b935 PASS). Bramka §0: origin = HEAD = `075b02db`, porcelain czysty poza
zastanymi ?? `results/DEMO_C`. Budowa §1 w `3698e043` [S2-BUDOWA]; dry-run pod `set -uo pipefail` PASS 4/4
(`dryrun/dryrun_s2.json`). **Budżet S2: 2/3** (rezerwa nieużyta), noga NADIR-II 2/≤22. **Breach 0, REFUSE(POS) fałszywy 0,
STOP globalny żaden.**

## Lot P — passthrough

`p_passthrough`: `NADIR_MODE=0`, `KONT_MODE=0`, `NAD2_PASSTHROUGH=1`, litera NADIR1, epizody 0–3 (jak S3 B1), rc 0.
- **6405 ticków, decyzja produkcji = decyzja osłony-cienia `PatrolShield` bajt w bajt** (pełny dict, `passthrough.jsonl`
  i `passthrough_summary.json`: różnice 0) — **bitowo zgodny**.
- 0 REFUSE, breach 0. Tempo bootu 0.967, bramka zdrowia 0.932 (A, GO).
- Czerwony test zastany bez zmian: regresja S1 identyczna z bazą S3, kod osłony od S1 nietknięty; od S1 zmienione tylko meta
  `nadir_obs` i driver NAD2.

## Lot C — cięcie c11_s02

`c11_s02`: `NADIR_MODE=1`, `KONT_MODE=1`, `NADIR_LITERA=NAD2`, epizod 23, cięcie 30 s po ENTRY, rc 0.
- Zgodność litery przed epizodem: datagram NAD2, meta producenta NAD2, osłona NAD2.
- Tempo bootu 0.965, bramka zdrowia 0.925 (A, GO).

| sprawdzian | wynik |
|---|---|
| **(s1)** wierność na żywo | PASS — replay `Rama(litera=NAD2)` odtwarza 1499/1499 klatek (decyzja, tryb, koszyk, \|Δp_fix\| max 0.0 m); 0 przyjętych poprawek bez trybu lub litery w logu producenta |
| **(s2)** tabela w locie | PASS — R_k z logu = `r_nad2(przedział, koszyk, tryb)` w 2335/2335 ticków utraty z przedziałem; 761/761 poprawek w datagramach u konsumenta niesie tryb i literę NAD2 |
| **(s3)** rama | PASS — r_est osłony = \|p_corr\| w 2467/2467 ticków utraty i = \|p_EKF\| w 757/757 ticków NOMINAL (tol. 1e-3 m); pierwszy tick utraty (tick 757, sim 177.184) już w ramie poprawionej |
| **(s4)** litera bezpieczeństwa (`nad2_analyze`) | PASS — **B1** 0 przekroczeń, max e_corr/U 0.359 (2335 ticków ocenionych); **B2** margines do R_E min 7.022 m (GT); **B4** nav_state 14 i failsafe 0 od flagi do przyziemienia, 0 REFUSE(POS) w zdarzeniach, 0 fałszywych |

**(s5) Obserwable:**
- **Kontynuacja i track:** kontynuacja od `t_inj_sim` 110.532 s (D1: dostępne); track 1.000, pasmo 6–10 m 0.960.
- **Faza misji** (2228 ticków utraty przed zejściem): τ max 0.228 s, wszystkie ticki w przedziale 0, 0 REFUSE.
  - Tryby w utracie (ticki): para 2286, jeden 181.
  - u′ > m (3.02) w 4 tickach misji: tryb jeden, u′ 3.13–3.14 przy τ ≤ 0.25 s. Obserwabla, nie litera (PRE §5).
- **Zejście planowe** (od 287.608 s): od 292.77 s osłona w KONT_REFUSE z przyczyny τ* — 132 ticki, τ do 7.47 s.
  - Przy ziemi klatki przestają dawać poprawki.
  - Decyzje padły już w zejściu (driver opada D5 niezależnie), zgodne z regułą (τ ≥ 0.95 s), zakończone przyziemieniem GT
    w 299.272 s.
  - To nie jest zdarzenie `refuse` drivera i nie liczy się do REFUSE misji.
  - Analizator liczy obserwable τ / przedziałów / u′ także po zejściu (τ p95 1.44, „u′ > m” 49 ticków) — w misji wartości
    jak wyżej.
- **Zapas bariery min:** 1.255 m (ze zejściem; w replayu S4 tej komórki 1.706 m).
- **Błąd zakotwiczenia poprawek:** 761 poprawek, p95 0.152 m, max 0.226 m (max/1.5·F 0.62).
- **e_corr:** p50 0.126 / p95 0.225 / max 0.464 m.
- **Bias kursu z par:** mediana +0.69° (705 par).
- **Tempo:** 0.965. Horyzont prawdziwy − (τ + 0.012 s) — `wyniki_nad2.json`.

## Stanowisko i budżet

- Bramka zdrowia: 2 pomiary, 2 GO (0.932, 0.925); timesyncd zatrzymany na czas kolejki, wznowiony na końcu.
- Telemetria w tle bootów: `<boot>/host_telemetria.jsonl`.
- Czas: P 621 s, C 513 s.
- Księga: `kampania_ksiega.jsonl`, `bramka_ksiega.jsonl`, log `kampania_s2.log`.

## Pliki

Logi lotów: `p_passthrough/` i `c11_s02/` (trace, rama, nadir_obs, passthrough, wyniki analizatora `wyniki_nad2.json`, sprawdziany
`sprawdziany_s2.json`, wyciąg `ulg.jsonl.gz` 1.28 MB; `boot.ulg` poza repo, .gitignore). Launcher i boot:
`results/NAD2/tools/nad2_launch.sh`, `nad2_boot.sh`; kolejka `nad2_s2_run.py`; sprawdziany `nad2_s2_spr.py`; wyciąg `nad2_ulg.py`.

Reprodukcja sprawdzianów z repo:
```
python3 results/NAD2/tools/nad2_s2_spr.py results/NAD2/s2/c11_s02
python3 results/NAD2/tools/nad2_analyze.py results/NAD2/s2/c11_s02      # wymaga boot.ulg (lokalnie); e_corr z repo: ulg.jsonl.gz
```

**Sygnał: STOP-NAD2-2.** Push = Olga; CC przelicza (s1)–(s4) niezależnie i wydaje prompt bramki albo aneks.
