# STOP-KONT4-V2P — pierwszy boot po mitygacji 4c poleciał 4/4, ale V2′ < 0.90 we wszystkich epizodach; kolejka nie bramkuje V2′ (wada wykonawcy) — zatrzymana przed kolejnym bootem

Wykonawca · 8.11.2026 · łańcuch KONT, S4 po ANEKS_KONT-4c (`c0630712`, `73c27796`, `542f3887`; S4 ≤ 20 ratyfikowane).
Podstawa STOP: PROMPT_KONT_S4 §2 („cokolwiek wymaga zmiany ⇒ STOP z opisem") — dalsza kolejka wymaga zmiany narzędzia.

## Co poleciało: nom_b1_r3 (boot 28 nogi, S4 4/20)

- **Mitygacja 4c zadziałała na żywo:** 1 wymuszony reinit EKF2 (`kont_ekf_preflight.json`: przed 6.42° / bias 0.00011, po
  6.39° / 0.00013, `ekf2 stop/start` rc 0/0), ostateczna asercja 6.41° / 0.00013 ⇒ ok; `intruder_motion` po asercji.
- **Lot nominalny 4/4 epizody** (c00–c03_s01, sieć net_skan2, nakładka KONT_MODE=1): wejście w pasmo 3.8 / 5.4 / 8.6 /
  27.0 s, r_GT max 23.25–23.44 m (a ✓), REFUSE(POS) 0, ticki KONT 0, R-G-NOM 0, R-G 0 (f ✓ na 4 epizodach ramienia (−)),
  breach 0 (`wyniki_s4.json`, analiza z GT i trace).
- **V2′ poniżej progu:** kanoniczne V2′ (`bench/campaign_analyze.py:30`, Δsim/Δwall z `rtf_stream.jsonl` na oknie
  epizodu, `bench/bench_judge.py:_stalls`) = **0.887 / 0.879 / 0.858 / 0.856** ⇒ wszystkie 4 epizody nieważne po literze §2.
  Deep-stalle: 4 w epizodzie 0 (0.0 s najdłuższy).

## Przyczyna spadku — nie driver (pomiar)

| boot | RTF settle 10–80 s (przed driverem) | po uzbrojeniu do 1. epizodu |
|---|---|---|
| S4 nom_b1_r3 | **0.861** | 0.886 |
| S4 nom_b2 (23:45, bez lotu) | 0.969 | — |
| S2 c08_s02b_r2 | 0.964 | 0.942 |
| S2 c02_s01_r4 | 0.967 | 0.940 |
| SKAN2/PERC2 (bez przepływu, ta sama sieć i percepcja) | — | epizody 0.991–1.000 |

Stos był wolniejszy już w settle, zanim proces drivera istniał — spowolnienie jest stanem stanowiska w tym boocie,
nie kosztem drivera S4. Model z przepływem kosztuje ~3–4 % (S2 0.94–0.97 vs SKAN2 ~1.0), co zostawia małą rezerwę nad
0.90. Przyczyna spadku do 0.86 w tym boocie: [MECHANIZM NIEZMIERZONY] (proc_gate CLEAN przed bootem, timesyncd stop jak
w S2, uptime ~2 h, 4. boot sesji).

## Wady wykonawcy

1. **Kolejka nie bramkuje V2′.** `kont_s4_campaign(_b,_c).py` ocenia ważność z fazy, sondy, asercji yaw i liczby
   epizodów — bez V2′, które PROMPT §2 wymienia jako warunek ważności. Kolejka uznała nom_b1_r3 za ważny i poszłaby dalej
   bez dolecenia.
2. **Analiza liczyła V2′ inną metodą niż kanon** (`kont_s4_analyze.py`: GT sim / monotonic na całym boocie = 0.868)
   zamiast per epizod z `rtf_stream.jsonl`. Wynik tego samego znaku, ale definicja nie ta.

Kolejkę zatrzymałem (SIGINT po PID) po próbniku zegara przed nom_b2_r2, zanim boot wystartował; stanowisko czyste,
timesyncd `active`. Budżet **S4 4/20, noga 28/45**.

## Do decyzji CC

1. Poprawka kolejki: ważność epizodu = kanoniczne V2′ (`bench_judge._stalls` na oknie epizodu: Δsim/Δwall ≥ 0.90 ∧
   najdłuższy deep-stall ≤ 1.5 s ∧ timejump 0) obok dotychczasowych warunków; nieważny ⇒ dolecenie w budżecie. Poprawka
   analizy na tę samą definicję. Obie to zmiany narzędzi, nie kryteriów.
2. Status nom_b1_r3: nieważny (V2′) ⇒ zużywa rezerwę; po literze 4c zostaje 16 bootów na 15 pozycji (1 rezerwa).
3. Ryzyko: jeśli spowolnienie stanowiska się powtarza, kampania wyczerpie rezerwy na V2′. Możliwy krok bez bootu:
   ustalenie, czy RTF settle przed bootem (np. z ostatnich 60 s próbnika) przewiduje V2′, i bramka RTF settle ≥ 0.90
   przed uzbrojeniem (boot przerwany przed lotem tańszy niż nieważny lot) — wymaga dokumentu.

Bez rozstrzygnięcia nie bootuję. **STOP-KONT4-V2P.** Push = Olga.
