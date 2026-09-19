# ANEKS_W-0 — ratyfikacja PRE_W (zapis + zamrożenie)

CC · 19.09.2026 · łańcuch nogi W otwarty (ANEKS_W-n).

## §1. Ratyfikacja

PRE_W ratyfikowany przez Olgę 19.09.2026 („ratyfikuje") = **W1–W14 TAK bez korekt**. Żadne pole
decyzyjne nie było puste w chwili ratyfikacji (wszystkie W wypełnione rekomendacjami CC w §12
przed ratyfikacją) — zero rozstrzygnięć zastępczych. Jedyna alternatywa z realnym wyborem
(komórka: c11 × 3 ziarna vs 3 komórki × 1 ziarno) była nazwana wprost; ratyfikacja bez korekty
= przyjęta rekomendacja **c11 × 3 ziarna**.

## §2. Zamrożenie

Z chwilą tego aneksu ZAMROŻONE: siatka kryterialna (PRE §3), faza W-A z deterministyczną regułą
wyłączenia poziomu (§4), definicja fałszywego REFUSE ε_false=2.0 m / okno 1 s (§5), metryki
i podział sędziów (§6), bramka nogi PASS / ZNALEZISKO-STOP / FAIL dostępności /
NIEROZSTRZYGNIĘTE / ŚMIERĆ (§7), budżety ≤32 bootów lotnych / ≤3 sesje i protokół wyłączności
(§8), guard wyjścia OUTDIR (§9), lista plików dotykanych (§10), stop-rules SR-W-1..8 (§11),
decyzje W1–W14 (§12). Zmiana czegokolwiek z tej listy wymaga kolejnego numeru ANEKS_W-n;
wykonawca odrzuca sygnały bez numeru.

## §3. Predykcje

P-W-1..5 (PRE §13) wchodzą do `results/KSIEGA_PREDYKCJI.md` (sekcja OTWARTE) pierwszym commitem
sesji S1 — prereg żyje w repo PRZED pierwszym bootem nogi. Rozliczenie wyłącznie przy RAPORT_W.

## §4. Wykonanie

Build i W-A wyłącznie wg PROMPT_W_S1 (CC). Zgodnie z ARCH-1: `PRE_W.md` i niniejszy
`ANEKS_W-0.md` wchodzą do korzenia repo pierwszym commitem S1 (procedura C0: Downloads, glob na
sufiksy, weryfikacja nagłówka, sha256 do raportu). Kolejność nogi: S1 (build + W-A) → STOP-W1 →
ANEKS_W-1 (skład siatki po regule §4 + FREEZE_W + go W-B) → S2/S3 (kampania 18 bootów) →
STOP-W2 → RAPORT_W → ANEKS_W-2 (werdykt + kanon).
