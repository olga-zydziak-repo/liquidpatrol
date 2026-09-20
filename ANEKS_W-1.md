# ANEKS_W-1 — ratyfikacja W-A + reguła R-NC + go W-B (zapis do repo)

CC · 20.09.2026 · łańcuch nogi W (ANEKS_W-n). Dokument zapisuje ratyfikację dostarczoną przez Olgę
**inline jako PROMPT_W_S2** (nagłówek: „autoryzacja: ANEKS_W-1"). Wchodzi do korzenia repo
pierwszym commitem S2 (C-F), zgodnie z ARCH-1.

## §0. Prowieniencja (ARCH-1 / procedura C0) — UCZCIWY zapis

Procedura C0 (Downloads → glob na sufiksy → weryfikacja nagłówka → sha256 do raportu, jak dla
PRE_W/ANEKS_W-0 przy S1) tym razem **nie ma osobnego pliku źródłowego w ~/Downloads**: ratyfikacja
W-A + reguła R-NC + go zostały dostarczone treścią PROMPT_W_S2 (bez odrębnego artefaktu .md).
Krok „Downloads glob" = N/A (sprawdzone: brak dopasowań `aneks_w|prompt_w|w-1|w_s2`). Niniejszy
`ANEKS_W-1.md` jest zapisem tej ratyfikacji autorstwa CC z treści promptu — bez zmyślonego sha
pliku źródłowego. Zamrożenie merytoryczne = ta ratyfikacja; przyrząd nogi zamraża `results/W/FREEZE_W.md`
(commit C-F).

## §1. Ratyfikacja W-A

Faza W-A (sonda kalibracyjna, RAPORT_W_A) ratyfikowana. Commity S1 (na origin/master po pushu
20.09, bramka §0.1 S2 PASS):
- `2529c5a0b9060653f311f79793d70bb71ed1111d` — W noga S1 build [CB]
- `d7663100879ea7283ad9bd645ce2d1ba2dd79438` — W noga S1 [CW-A]

Wynik W-A przyjęty: wejście pos_flag CZYSTE na 0–4.5 m/s (dead_reckoning=False, eph≈0.15,
xy_reset=0); climb OK ≤1.5, no-climb ≥3.0 w infra1 (×2 repro @3.0); P-W-2 wstępnie obalone
(4.5 arm_ok=True). Reguła wyłączenia §4 literalnie (o UZBROJENIU): żaden poziom nie wypada
(wszystkie uzbroiły), 1.5 hoveruje ⇒ BRAK triggera ŚMIERCI; siatka literalna {0, 1.5, 3.0}.
Otwarta kwestia 3.0 (uzbraja, nie wznosi w infra1) → rozstrzyga R-NC (§3), NIE reguła §4.

## §2. Uzupełnienie danych W-A (zero relotów, z istniejących manifestów `results/W/probe/**`)

Do wypisania w RAPORT_W_S2 (§0.5 promptu): eph_max per boot i Δsim/Δwall per boot z manifestów
sondy. Wartości (wa_metrics.ekf_eph_max, habitat.dsim_dwall):

| boot | poziom | eph_max | Δsim/Δwall | min_rtf |
|------|--------|---------|------------|---------|
| 1 s0    | 0.0       | 0.1536 | 0.9437 | 0.0146 |
| 2 s1p5  | 1.5       | 0.1535 | 0.9353 | 0.0057 |
| 3 s3    | 3.0       | 0.1524 | 0.9364 | 0.0018 |
| 3b s3   | 3.0 retry | 0.1524 | 0.9581 | 0.0316 |
| 4 s4p5  | 4.5       | 0.1524 | 0.9875 | 0.0091 |

Wszystkie 5 habitatów INVALID (dsim_dwall <0.95 na 4/5 + głębokie dipy min_rtf) — env-bound
deep-stall mostu gz↔px4, niebramkujący w W-A (kalibracja).

## §3. Reguła R-NC — boot-0 diag @3.0 (rozstrzygnięcie składu siatki W-B)

Epizod ławki: c11, pierwsze ziarno (c11_s01, episode_id 11), CONTROLLER=route, W_ARM_ALWAYS=1,
world_wind_s3, kind=diag, OUTDIR `results/W/camp/diag_boot0[_r]`, przez w_launcher (lock + pgrep +
guard manifestu + cooldown ≥300 s).
- **Gałąź (a):** dron wznosi się i wchodzi w pasmo orbity (wejście w pasmo wg bench_judge) ⇒
  siatka = {0, 1.5, 3.0} × 2 ramiona × 3 ziarna = **18 bootów**. Kontynuacja automatyczna.
- **Gałąź (b):** nie wznosi się w ≤2 podejściach ⇒ 3.0 WYPADA (H2-b, próg wznoszenia z ziemi),
  siatka = {0, 1.5} × 2 × 3 = **12 bootów**. Kontynuacja automatyczna; wynik do raportu.
- **NIEZALEŻNIE:** habitat segmentu boot-0 na sędzim V2′ INVALID ⇒ **STOP sesji** + diagnoza przed
  kampanią, zero dalszych bootów.

R-NC wykonywana LITERALNIE (S2-B): żadnej trzeciej próby, żadnego strojenia poziomów.

## §4. Budżet W-B (§6 wg promptu §0.2)

Zostaje **≤27 bootów lotnych** łącznie z boot-0 i ponowieniami (budżet nogi ≤32 lotnych z PRE §8,
minus 5 zużytych w W-A). Arytmetyka przed serią: gałąź (a) 18 + 2 (boot-0 + ewent. retry) + 7
ponowień ≤ 27; gałąź (b) 12 + 2 + 7 z zapasem. Env-blocki poza budżetem (auto-defer). Wyczerpanie
bez kompletu ⇒ NIEROZSTRZYGNIĘTE (PRE §7), raport częściowy — bez dopalania.

## §5. Reszta reżimu (bez zmian, dziedziczone z PRE_W + ANEKS_W-0)

Definicja fałszywego REFUSE (PRE §5, ε_false=2.0 m / okno 1 s) — ZAMROŻONA. Ważność V2′ i podział
sędziów (PRE §6). Bramka nogi (PRE §7). Guard OUTDIR (PRE §9). Wyłączność + lock (PRE §8).
REFUSE dowolnego rodzaju lub breach R_E ⇒ natychmiastowy STOP kampanii (PRE §5/§7) — to główny
pomiar nogi, nie tryb awaryjny. FREEZE_W (C-F) zamraża przyrząd przed pierwszym bootem
kryterialnym. Ratyfikacja wróci jako ANEKS_W-2 (werdykt nogi + kanon wg PRE §14); sygnały bez
numeru CC odrzuca.
