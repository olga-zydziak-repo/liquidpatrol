# RAPORT_NET_S2 — noga sieci, sesja 2 (retrain NCP + bramki) — STOP-N2

LiquidPatrol · pozycja 3 (OSTATNIA sesja) · CC 5.09.2026 · łańcuch: PRE_NET + ANEKS_NET-0 + ANEKS_NET-1
ZERO SITL · frozen nietknięty (`git diff` pusty) · commity: FREEZE+mapa `efa1ee1` · N-B3 `d8f143c` · N-B4 `c5940d5` (niepushowane, push=Olga)

## §1. Werdykt końcowy pozycji 3: OBA RAMIONA PRZECHODZĄ bramkę N3(i)

Reguła bramki (ANEKS_NET-1 §2): analog-D6 (wejście≤25s ∧ frac[6,10]≥0.85 ∧ d_min≥4) w **≥20/24 rolloutów** (komórka×ziarno TEST 4,8), model punktowy FEED-B.

| ramię | param | val_mse | TEST RMS (med) | **bramka N3(i)** | widok komórek (oba/którekolwiek) | TEST-touch |
|---|---|---|---|---|---|---|
| tiny-MLP | 2467 | 0.0308 | 0.179 | **21/24 = PASS** | 9/12 · 12/12 | 1× (S1) |
| NCP-20 | 1903 | 0.0485 | 0.215 | **24/24 = PASS** | 12/12 · 12/12 | 2× (S1+S2) |

Oba ramiona lecą w pozycji 4. Porównanie NCP↔MLP w locie ŻYJE.

## §2. NCP — naprawa przyrządu (ANEKS_NET-1 §3.1, N-B3)

S1 FAIL był UNDERFIT, nie architekturą: cap 200 epok był stałą, val malał monotonicznie do końca.
N-B3: cap 200→1000 + harmonogram lr (milestones [500,800], γ=0.5), selekcja WYŁĄCZNIE VAL.
- val_mse: **0.141 (S1) → 0.0485 (S2)** — 2.9× lepiej, blisko MLP.
- Bramka: 1/24 (S1) → **24/24 (S2)**. Pełny obrót.

**DAgger NIE użyty.** Decyzja podjęta NA VAL (ziarno 2, rollout-proxy — BEZ dotykania TEST, TEST-discipline ANEKS_NET-1 §3.3): VAL-proxy = **12/12** analog-D6 ⇒ retrain sam wystarczył, DAgger zbędny. Trigger N4 (FAIL S1) był spełniony, ale ścieżka §3.2 (DAgger tylko gdy potrzeba) nie wymagała rundy.

**Krotność dotknięć TEST dla NCP = 2** (S1 raz + S2 raz, ostateczne). Trzeciego nie było (SR-3, §3.3).

## §3. Diagnostyka N3(ii): RMS słabo przewiduje pętlę zamkniętą

NCP ma WYŻSZY błąd akcji (RMS 0.215) niż MLP (0.179), a JEDNOCZEŚNIE lepszy rollout (24/24 vs 21/24).
Potwierdza uzasadnienie N3(ii): błąd imitacji akcji per-tick słabo przewiduje zachowanie zamknięte;
składanie błędów łapie dopiero rollout. RMS pozostaje diagnostyką, nie bramką — słusznie.

## §4. Komórki porażek rolloutu (ANEKS_NET-1 §6, predykcja P-N5)

- **NCP: 0 komórek porażek** (24/24, w tym proximity c05/c07/c09 — wszystkie PASS).
- **MLP: 3 komórki porażek** (widok „oba ziarna"): **c03, c07, c08** (wszystkie na frac<0.85, d_min≥5.46 bezpiecznie). Tylko **c07** należy do zbioru proximity {c05,c07,c09}; c03/c08 to inne (frac-limited, nie proximity).
- **P-N5 (klasa porażek sieci = c05/c07/c09) NIE potwierdzona offline:** NCP nie pada nigdzie; MLP pada głównie poza zbiorem proximity. Dziedziczenie granicy nauczyciela w tym rolloutcie NIE wystąpiło wyraźnie. Właściwy test P-N5 = loty pozycji 4.

## §5. Predykcje (rozliczenie sesji poz.3)

- **P-N1** (NCP przechodzi N3(i)): S1 ✗ → **S2 ✓** (po naprawie capu). Nota: trafność zależna od naprawy przyrządu CC, nie od predykcji architektury.
- **P-N2** (MLP przechodzi): ✓* (reguła §2 po danych, uzasadnienie mechanizmowe — gwiazdka w księdze CC).
- **P-N5** (klasa porażek c05/c07/c09): offline **✗** (patrz §4) — do rozliczenia w locie.
- Księga nogi poz.3: P-N1 ✓(S2) / P-N2 ✓* / P-N5 ✗(offline). P-N3/P-N4/P-N6 = pozycja 4.

## §6. FREEZE_NET — kompletny (ANEKS_NET-1 §4)

`results/NET/FREEZE_NET.md`: oba ramiona zamrożone z weights_sha, configiem, preprocessingiem.
- tiny-MLP: `1d1900235724e938...` (2467 param, config N-B1)
- NCP-20: `0337d5eae1471bb9...` (1903 param, config N-B3)
Od teraz wagi NIETYKALNE aż do lotów (N6: zero uczenia w locie, `weights_sha` w manifeście).

## §7. Odchylenia

- **O1** (S1): brak torch/jax → numpy + ręczny backprop (gradcheck ~1e-10). Bez zmian.
- **O2** (S1): niejednoznaczność reguły bramki → rozstrzygnięta CC (ANEKS_NET-1 §2: ≥20/24 per rollout).
- **O3** (S1): NCP underfit → naprawiony N-B3 (cap×5 + lr sched, decyzja CC per SR-4). NIE strojenie TEST — selekcja VAL, TEST dotknięty raz na końcu.
- **O4** (S1, odziedziczone): stall/reset=0 w demo (flaga niewpięta w loggerze ławki, frozen). Bez wpływu (sim-time).
- Zero SITL, zero zmian harness/frozen, drivery wersjonowane w repo (ANEKS_NET-0 §2).

## §8. STOP-N2

Pozycja 3 domknięta: **oba ramiona PASS**, wagi zamrożone (FREEZE_NET kompletny), budżet 2/2 sesji zużyty.
Pytanie „liquid" offline: NCP (CfC) i MLP OBA przechodzą — offline NULL potwierdzony na bramce (24 vs 21,
oba ≥20); różnica architektur nie decyduje o przejściu. Rozstrzygnięcie właściwe = loty pozycji 4 (pary NCP↔MLP).

**Czeka na CC (ANEKS_NET-2):** zamknięcie pozycji 3 + PROMPT lotów pozycji 4 (N6/N7: siatka ziaren 1-4,
48 epizodów/ramię parowane sieć↔egzekutor i NCP↔MLP, przeplot ramion, próg ≥40/48, świeże ziarna s11-s13
jako luka uogólnienia, licznik REFUSE osłony). Wykonawca po STOP: nic. Olga: push {FREEZE+mapa, N-B3, N-B4, raport}.
