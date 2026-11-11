# STOP-NAD2-3-GUARD — kolejka S3 zatrzymana własnym strażnikiem po 2 ważnych bootach (wada kolejki, nie litery)

12.11.2026 · wykonawca · PROMPT_NAD2_S3 (sha256 c7e294a8 PASS), budowa `9720bae0`. **Budżet S3: 2/19, noga 4/22. Breach 0,
REFUSE(POS) fałszywy 0, naruszeń litery 0, STOP globalny żaden.**

## Booty ważne

| boot | tempo | sprawdziany (s1)–(s3) | wynik |
|---|---|---|---|
| nom_b1 (c00–c03_s01) | 0.964 | 100% | B1–B5 PASS ×4 epizody, margines R_E min 8.538 m, wyciąg ULG 2.8 MB |
| c01_s01 | 0.963 | 100% | B1–B4 PASS (max e_corr/U 0.231, margines 8.541 m, zapas bariery min 1.443 m); D1 dostępne (kontynuacja 110.548 s, track 1.000, pasmo 1.000, 0 REFUSE misji) |

## Co się stało (c01_s03)

1. Bramka zdrowia A GO (0.911), próbnik zegara 0 skoków.
2. Launcher (`nad2_launch.sh`, bd975df5) w swoim `proc_gate --self $PPID` zobaczył **proces kolejki** (`nad2_s3_run.py`, 2.2% CPU
   > 2.0) poza łańcuchem własnym i allowlistą ⇒ env-block, rc 3, stub `c01_s03/manifest.json` (kind env-block). PX4 nie ruszył
   (initial absolute time brak) — **nie boot**.
3. Kolejka powtórzyła boot po 120 s **pod tą samą nazwą** ⇒ `nad2_boot.sh` REPO-2 (manifest istnieje) rc 4 ⇒ STOP-NAD2-3-GUARD.

Przyczyny (moje):
- **pętla env-block w kolejce powtarza nazwę**, której katalog launcher już zajął stubem (ten wzorzec od S4 NADIR zakładał env-block
  z wczesnego strażnika kolizji bootu, przed `mkdir`, nie z bramki launchera);
- **CPU samej kolejki na granicy 2%** — telemetria §3.3 (`Telemetria2`: wątki czytające nvidia-smi i powershell) działa w procesie
  kolejki od bramki do końca bootu. Wcześniejsza bramka bootu (`proc_gate --self $$`) też widziała kolejkę jako brudną w c01_s03
  (13 linii „brudny”, 2.2–2.4%), ale doczekała 3× czysto; w nom_b1 i c01_s01 zero takich linii; w S2 zero.

## Propozycja (decyzja Olgi/CC; nic nie zmienione)

Poprawka wyłącznie w kolejce (`nad2_s3_run.py`, poza kodem zamrożonym §0.2):
- (a) env-block (rc 3) ⇒ następna próba pod **wolną nazwą** (`c01_s03_r2`), katalog stubu zostaje jako artefakt; nadal nie boot,
  ≤ 4 próby, potem STOP-NAD2-3-ENV;
- (b) opcjonalnie: telemetria w procesie potomnym zamiast wątków kolejki nie pomaga (potomek też poza allowlistą) — zostawiam bez
  zmian; (a) wystarcza, bo przekroczenie jest graniczne i bramka 3× czysto przechodzi.

Kolejka po poprawce startuje od księgi: ważne {nom_b1, c01_s01}, kolejka 14 pozycji, budżet 2/19 (rezerwa 3 nietknięta).
timesyncd: kolejka na końcu znów go włączyła — przed wznowieniem zatrzymuje go sama.

**Sygnał: STOP-NAD2-3-GUARD.**
