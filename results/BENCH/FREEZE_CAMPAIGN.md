# FREEZE_CAMPAIGN — przyrząd analizy + kolejka kampanii blok1/48 (ANEKS_BENCH-1a §2 R1 + ANEKS_BENCH-1 C8)

LiquidPatrol · ławka · zamrożone PRZED pierwszym bootem bloku 1 · D9 = V2′.
Zamraża się warstwę ANALIZY + KOLEJKĘ (nie sędziego — ten stoi na `8ec0fcfb`).

## Sha zamrożone (przyrząd kampanii)
```
campaign_analyze.py  f31e81e38a732ac16693ebc806aace0eac416a26b88e5592d1b6483f75e759de
campaign_queue.py    89619514f0e9ef452d30566286c6fcbb70d3714142e2b287d387278b83dd4122
bench_finalize.py    508856dc1871ce438d4e575cd6663425dff432a8b38d5985b9e506cd12a2c36b
bench_judge.py       8ec0fcfbb7e46953d868553dcfbfcee20dddfdfa337e2d9f34e86117377ed7d2   (FROZEN, NIETKNIĘTY — źródło V1/V2/V3)
```

## Harness kampanii (POZA frozen-7; wersja lotu = v1.3)
```
bench_flight.py      b8eb68caafb7558d7d99c327042bb4b3a0b2664aff524cf8bd71c9c6ad4843fb   (v1.3: konsumpcja kolejki — in_flight zamiast listy rozwiązanej, propagacja attempt)
```
Zbiór zamrożony §3 (egzekutor 840514361e, params 12c14adb, sędzia 8ec0fcfb, feed 674d78ab, cechy 9adc1505,
manifest e0527026, piny) NIETKNIĘTY. bench_flight/intruder_motion to harness (poza listą §7 PRE, per ANEKS-1 §2).

## Reguła ważności D9 = V2′ (ANEKS_BENCH-1a §2 R1)
Epizod WAŻNY ⇔ najdłuższy pojedynczy deep-stall (rtf<0.5) ≤ 1.5 s wall ∧ Δsim/Δwall ≥ 0.90 ∧ timejump=0.
LICZBA zdarzeń deep raportowana per epizod, NIEBRAMKUJĄCA (max_deep_stall=∞). Override slotu „V2" sędziego frozen.

## Kolejka z ponowieniami (ANEKS_BENCH-1 C8, PRE §3/D8)
Init: 48 × {scenario_id, episode_id, attempt=1}. Driver: pop 4 (pending→in_flight) → boot → record.
Po boocie per scenariusz: ważna (V2′) = DONE (PIERWSZA ważna liczy się); INVALID_START/V2′-nieważny = re-append
attempt+1; twardy cap attempt ≤ 3; 3 nieważne = UNRESOLVED (nie liczy do sukcesów ani porażek); env/crash =
re-append bez inkrementu. > 4 UNRESOLVED ⇒ STOP sesji dla CC. Roll-up (aggregate_campaign): p_exec po pierwszej
ważnej próbie + Wilson, lista UNRESOLVED.

## Opis przyrządu (do raportu kampanii)
Przyrząd `campaign_analyze.py` czyta artefakty każdego bootu (trace, gt_intruder, rtf_stream) i orzeka per
epizod ważność kampanijną V2′ oraz sukces D6, nie dotykając zamrożonego sędziego — V2′ realizuje wyłącznie
przez nadpisanie progów slotu „V2" params sędziego (`max_deep_stall=∞` zdejmuje bramkę liczby stalli,
`longest_stall_s=1.5` i `dsim_dwall≥0.90` zostają), więc `bench_judge` liczy dokładnie te same metryki
geometryczne co w shakeout, a bramkuje dopiero agregacja. `campaign_queue.py` prowadzi kolejność 48 scenariuszy
przez ponowienia z twardym capem 3 prób, licząc scenariusz po PIERWSZEJ ważnej próbie i listując UNRESOLVED,
tak że p_exec zawsze ma spójny mianownik (scenariusze rozstrzygnięte) z 95 % przedziałem Wilsona odpornym na
małe n. Wbudowany strażnik R1 zestawia sukces D6 z liczbą deep-stalli (0 vs ≥1) na epizodach ważnych — ujemna
korelacja byłaby sygnałem, że V2′ przepuszcza choroby mostu, i wymusza rewizję dokumentem, nie cichą zmianą.
Przyrząd jest czysto post-hoc i tylko-odczyt: nie wpływa na lot ani na sędziego, a jego sha zamrożone tu przed
pierwszym bootem bloku 1 gwarantuje, że ta sama reguła orzeka wszystkie 48 epizodów kampanii.

## Granice (nie-cele)
- Nie zmienia sędziego, egzekutora, feedu, cech, manifestu scenariuszy — te w FREEZE_BENCH_v1.2 (bajt-w-bajt).
- Rewizja V2′ = dokument CC (nie cicha zmiana), wyzwalacz: strażnik R1 ujemny LUB odrzucanie > 25 % na bloku 1 (D3).
- > 4 UNRESOLVED w bloku ⇒ STOP sesji (kolejka), decyzja CC.
