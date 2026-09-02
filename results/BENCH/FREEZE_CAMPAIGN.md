# FREEZE_CAMPAIGN — przyrząd analizy kampanii blok1/48 (ANEKS_BENCH-1a §2 R1)

LiquidPatrol · ławka · zamrożone PRZED pierwszym bootem bloku 1 · D9 = V2′.
Zamraża się warstwę ANALIZY (nie sędziego — ten stoi na `8ec0fcfb`).

## Sha zamrożone (przyrząd kampanii)
```
campaign_analyze.py  322f7ea620900b7f5ab4906379c54c56e8556f66c503a0cd481ac2a207d86ddf
bench_finalize.py    508856dc1871ce438d4e575cd6663425dff432a8b38d5985b9e506cd12a2c36b
bench_judge.py       8ec0fcfbb7e46953d868553dcfbfcee20dddfdfa337e2d9f34e86117377ed7d2   (FROZEN, NIETKNIĘTY — źródło V1/V2/V3)
```

## Reguła ważności D9 = V2′ (ANEKS_BENCH-1a §2 R1)
Epizod WAŻNY ⇔ najdłuższy pojedynczy deep-stall (rtf<0.5) ≤ 1.5 s wall ∧ Δsim/Δwall ≥ 0.90 ∧ timejump=0.
LICZBA zdarzeń deep raportowana per epizod, NIEBRAMKUJĄCA. p_exec = udane D6 / ważne (V2′), z przedziałem Wilsona.

## Opis przyrządu (do raportu kampanii)
Przyrząd `campaign_analyze.py` czyta artefakty każdego bootu (trace, gt_intruder, rtf_stream) i orzeka per
epizod ważność kampanijną V2′ oraz sukces D6, nie dotykając zamrożonego sędziego — V2′ realizuje wyłącznie
przez nadpisanie progów slotu „V2" params sędziego (`max_deep_stall=∞` zdejmuje bramkę liczby stalli,
`longest_stall_s=1.5` i `dsim_dwall≥0.90` zostają), więc `bench_judge` liczy dokładnie te same metryki
geometryczne co w shakeout, a bramkuje dopiero agregacja. p_exec = udane D6 / ważne (V2′) raportowany z
95 % przedziałem Wilsona, odpornym na małe n (blok 1 = 48 epizodów). Wbudowany strażnik R1 zestawia sukces
D6 z liczbą deep-stalli (0 vs ≥1) na epizodach ważnych — ujemna korelacja byłaby sygnałem, że V2′ przepuszcza
choroby mostu, i wymusza rewizję dokumentem, nie cichą zmianą. Przyrząd jest czysto post-hoc i tylko-odczyt:
nie wpływa na lot ani na sędziego, a jego sha zamrożone tu przed pierwszym bootem bloku 1 gwarantuje, że ta
sama reguła orzeka wszystkie 48 epizodów kampanii.

## Granice (nie-cele)
- Nie zmienia sędziego, egzekutora, feedu, manifestu — te w FREEZE_BENCH_v1.2 (bajt-w-bajt).
- Rewizja V2′ = dokument CC (nie cicha zmiana), wyzwalacz: strażnik R1 ujemny LUB odrzucanie > 25 % na bloku 1 (D3).
