# FREEZE_LIQ — zamrożenie wag kontroli nogi LIQ (PRE_LIQ §6, PROMPT_LIQ_S1 §4.1)

CC · 02.10.2026 · commit S1, PRZED jakimkolwiek lotem (S2). Zmiana wag po tym commicie =
nowa noga, nie poprawka. Lata wyłącznie seed 1; NCP wyłącznie kanoniczne 0337d5ea (FREEZE_NET).

| plik | sha256 | parametry | arm (CONTROLLER=) |
|------|--------|-----------|-------------------|
| net/frozen/gru.npz   | 5ec027555b8fc0bf12007a3dea0fdb5629fc46cdbbd859150b6963c4cdaac383 | 1956 | gru |
| net/frozen/mlp20.npz | 74b5ae7d041bb776c9352c19f80582ecaea6bb8c429cae6d5e1a89a2ea8a6c8e | 1939 | mlp20 |

Trening (echo zamrożonego mapowania, PROMPT §1(a); tor = net/train_liq.py, importy z net/train.py):
- GRU h=21 (seed init 1): lr 0.003 · cap 1000 epok · grad_clip 5.0 · β 0.9/0.999 ·
  lr_schedule [500,800]×0.5 · seed 1 · selekcja WYŁĄCZNIE VAL · best_val 0.049014 @ep 999
  (val malał do capu — wynik, nie licencja na strojenie) · wall 397.3 s.
- MLP k=20 h=11 (seed init 1): jw. (komplet gałęzi ncp) + batch 512 (FORMAT toru okiennego,
  z gałęzi mlp) · best_val 0.017939 @ep 989 · wall 214.1 s.
Dane: 114 D6 (44+70), split z kodu TRAIN 81 / VAL 10 / TEST 23; cechy bench.features 9adc1505;
standaryzacja TRAIN; MSE. Środowisko: numpy 1.26.4, Python 3.12.3.

Bramka offline G13′ (ANEKS_NET-1 §2, analog-D6 ≥20/24 rolloutów FEED-B, ziarna TEST {4,8}):
- GRU: **24/24 PASS** (per-cell oba=12/12) ⇒ LATA (S2).
- MLP-k20: **1/24 FAIL** (per-cell którekolwiek=1/12) ⇒ **NIE LATA** (PRE §2); zdanie kanonu:
  „pod zamrożonym torem treningu NCP kontrola MLP-k20 nie osiągnęła progu offline pozycji 3;
  porównanie lotne niewykonane". Wagi zamrożone dla tożsamości wyniku.
- NCP kanoniczny (punkt odniesienia przyrządu): 24/24 PASS.

Guard tożsamości: r03/controllers/liq_controller.py FREEZE_SHA_LIQ (rozjazd ⇒ RuntimeError,
ODMOWA LOTU, wzór SR-2). controller_sha pliku kontrolera w chwili freeze: 6d72437f7dd16d83….
