# FREEZE_XAI — statusy twierdzeń o sieci NCP-20 + zasada cytowania (noga XAI, S1)

CC · 27.10.2026 · po STOP-XAI1 (PRE_XAI `95555eb3…` ARCH-1 `ec22a8f7`).
Obiekt: wagi `net/frozen/ncp.npz` **0337d5ea** (FROZEN), krok CfC
models.py:127-138, kontroler net_controller.py (V_MAX=3.0 r01/config.py:24).
Pełne formalizacje, dowody i różnicówki: `RAPORT_XAI_S1.md` + JSON-y obok.
Zmiana czegokolwiek niżej = ANEKS.

## Statusy twierdzeń (lista zamknięta PRE_XAI §1)

| twierdzenie | STATUS | liczby |
|---|---|---|
| **T1 — ograniczoność wyjść:** ∀x,h skończonych: \|y_k\| < 3.0 (arytm. dokładna; IEEE754: ≤), po clip_v ‖v‖₂ ≤ 3.0 | **PROVED** | różnicówka 0/74 708 ticków; max 2.985176 (margines 0.0148); ‖v‖₂ max = 3.0 (równość, clip aktywny) |
| **T2 — lemat stanu:** h₀=0 ⇒ ∀t,i: \|h_{t,i}\| < 1 (arytm. dokładna; IEEE754: ≤) | **PROVED** | różnicówka 0 kontrprzykładów (wszystkie ticki); max 0.964907 (margines 0.0351) |
| **T3 — kontrakcja lokalna kroku stanu przy γ∈[0.1615, 0.8405]:** ‖∂h′/∂h‖₂ < 1 | **COUNTEREXAMPLE** | 74 235/74 235 ticków w założeniu ma ‖J‖₂ ≥ 1; max 2.5766; przykład c00_s01 t=111.132 (‖J‖₂=1.2377) |
| **T4 — stałość znaku ∂y₀/∂x₂ (≡ ∂y₀/∂sin_brg) na Box_x×Box_h** | **COUNTEREXAMPLE** | korpus: 21.1% ticków ujemnych; siatka 3⁸×5h: 47.8%; interwałowo certyfikowane 0.0% objętości (20k komórek; metoda poprawna — zawieranie 40/40) |

## Pudełko wejść (p1–p99, cechy znormalizowane; korpus 53 ep. / 74 708 ticków — xai_s1_pudelko.json)

rel_x [−1.5702, 1.6301] · rel_y [−1.5982, 1.6835] · rel_z [−3.7057, 2.9803] ·
own_vn [−1.6925, 1.6365] · own_ve [−1.6728, 1.6845] · own_vd [−5.2115, 3.9396] ·
age [−0.6440, 4.5004] · valid = 0.0358 (stała). Pudełko stanu Box_h
(p1–p99 per neuron, 20 par) w `xai_s1_pudelko.json`.

## Pasmo bramek + δ (pomiar S1, zgodny z atlasem recon)

Średnie orbity per neuron ∈ **[0.4488, 0.5533]** (recon: [0.45, 0.55]);
**δ = 0.2873** (p99 chwilowego max_i |γ_i − średnia fazowa| na orbicie) ⇒
założenie T3: γ_i ∈ **[0.1615, 0.8405]** ∀i. Poza założeniem: 473/74 708
ticków korpusu.

## Narzędzia (sha256, 16) i przyrządy

`results/XAI/tools/xai_thm_diff.py` **b4454cb99f3c2fa9** (pomiary pudełka,
różnicówka T1–T4, mutanty M1–M5 w pamięci) ·
`results/XAI/tools/xai_proofs.py` **e7a65b37e478421f** (dowody: sympy 1.12 +
sondy przesłanek na wykonywalnym modelu + arytmetyka przedziałowa z adaptacyjną
bisekcją). FROZEN importem/kopią: xai_replay **ac9551ab**, wagi **0337d5ea**,
cechy **9adc1505**. Czułość: T1 pada na M2_skala/M4_glowa, T2 na M5_bramka
(tabela w RAPORT §4).

## ZASADA CYTOWANIA (FROZEN)

1. Twierdzenia cytowane na zewnątrz ZAWSZE ze STATUSEM z tabeli wyżej.
2. **T3 NIGDY bez przedziału założenia** γ∈[0.1615, 0.8405] — i dziś wyłącznie
   jako COUNTEREXAMPLE (lokalna kontrakcja kroku NIE zachodzi; stabilność
   cyklu granicznego pozostaje pytaniem o mnożniki Floqueta OKRESU —
   nazwane-niezmierzone).
3. **T4 NIGDY bez % pokrycia** (certyfikowane 0%; znak niestały: 21.1%
   korpusu / 47.8% siatki ujemnych) — „prawo pościgu" wolno cytować wyłącznie
   jako DOMINANTY saliency z atlasu (opisowe), nie jako znak globalny.
4. T1/T2: przy cytowaniu ścisłości (<) dopisać semantykę IEEE754 (≤,
   saturacja tanh/σ); marginesy korpusowe 0.0148 / 0.0351.
5. Twierdzenia są O SIECI, nie o misji — zero roszczeń D6 (PRE §1).
