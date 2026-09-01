# ANEKS_BENCH-0 — ratyfikacja PRE_BENCH z poprawkami

LiquidPatrol · ławka (pozycja 2) · ratyfikowane przez Olgę 1.09.2026 („potwierdzam") · CC 1.09.2026
Obowiązuje razem z PRE_BENCH.md (1.09). Gdzie ten aneks różni się od PRE, aneks wygrywa.

## §1. Decyzje ratyfikowane

D1 = FEED-B: f = 10 Hz, L = 0.20 s, σ_xy = 0.5 m / σ_z = 0.3 m (Gauss iid), zaniki 5 % iid (hold-last, rośnie
`track_age`). POPRAWKA względem PRE D1: pozycja z feedu SUROWA (bez EMA — filtr pozycji dodawałby ~τ
opóźnienia); prędkość intruza `trk_vel` = regresja liniowa na oknie 1.0 s próbek feedu (σ_v ≈ 0.55 m/s,
opóźnienie ~0.5 s), liczona w CZASIE SIM. Uzasadnienie liczbowe w rozmowie ratyfikacyjnej: EMA τ 0.5 s
różnic skończonych zostawia ~2.4 m/s szumu prędkości — bezużyteczne wobec v_intr ≤ 1 m/s.
D2, D3, D4, D5, D7, D8, D10 — TAK bez zmian.
D6 = PASS p_exec ≥ 0.80 / śmierć < 0.60 / środek NIEROZSTRZYGNIĘTE; pasmo [6, 10] m; n = 48 (4 ziarna na
komórkę × 12 komórek) do p_exec; frakcja w [7, 9] jako metryka nienasycona w raporcie.
D9 = V2 (≤ 3 deep-stalle rtf < 0.5, najdłuższy ≤ 1.5 s wall, Δsim/Δwall ≥ 0.90 na epizodzie, metryki w czasie
sim, ticki w stallu flagowane). Shakeout liczy V1/V2/V3 równolegle na tych samych epizodach; wybór
POTWIERDZANY przy STOP-1, przed pierwszym lotem kryterialnym.

## §2. Poprawki do §4 PRE (schemat) — obowiązujące

P1 Kanoniczny wektor cech lotu ma 8 wymiarów, BEZ prędkości intruza:
[rel_x, rel_y, rel_z, own_vn, own_ve, own_vd, track_age_s, track_valid]; rel = trk_pos − own_pos (NED),
liczony jedną funkcją `bench/features.py` w treningu i w locie. `trk_vel_ned` ZOSTAJE w `demo.jsonl`
(analiza, tiny-MLP z oknem jako baseline), nie jest cechą lotu.
P2 Filtry feedu i egzekutora (regresja prędkości, wszelkie stany czasowe) liczone w czasie sim z telemetrii,
nigdy z zegara wall — inaczej stall lockstepu wydłuża okno i psuje to, co D9 chroni.
P3 Ziarna: manifest 12 komórek × 10 ziaren = 120 epizodów; blok 1 = ziarna 1–4 (48, p_exec), blok 2 = ziarna
5–10 (72, zbiór). Podział TEST = seed ≡ 0 (mod 4) ⇒ dokładnie jedno ziarno testowe na komórkę w bloku 1.
P4 Saturacja |v| ≤ V_MAX: fakt, gdzie jest egzekwowana dziś, ustala D0 buildu; niezależnie od wyniku
egzekutor saturuje własne wyjście, a test kontraktu sprawdza, że żaden kontroler nie wypuszcza |v| > V_MAX.

## §3. Świadomie otwarte (do PRE sieci)

Runda DAgger z egzekutorem-wyrocznią w capie 2 sesji — pole nieuzupełnione przy ratyfikacji; decyzja
Olgi przy PRE sieci. Ławka jej nie przesądza; zbiór i egzekutor-wyrocznia będą gotowe na obie opcje.

## §4. Bramka startu

Build może startować równolegle z dreamforge (sam kod). Shakeout dopiero po zejściu dreamforge i czystym
inwentarzu — bramka procesowa wrappera obowiązuje.
