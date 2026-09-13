# ANEKS_FV-1a — adjudykacja odchylenia sekwencji S2 + warunki odczytu + warunkowe go S3

CC · 11.09.2026 · łańcuch FV (sub-numer po ANEKS_FV-1, wzór ANEKS_BENCH-1a).

## §1. Adjudykacja odchylenia
Stan zastany: S2 wykonane w całości i PUSHNIĘTE (CM1 4a84f20, CM2 5856a92, CO2 7aa879c na origin),
ale RAPORT_FV_S2 nigdy nie dotarł do CC — kolejna sesja dostała PROMPT_FV_S2 zamiast raportu.
Klasa: pomyłka sekwencji sesji (precedens: adjudykacja 2.09 przy ławce; K1-19). Odchylenie przyjęte
JEDNORAZOWO. Dane nie ucierpiały wyłącznie dlatego, że raport sesji jest commitowany do repo (CO2)
— ta praktyka właśnie się spłaciła.

Zachowanie sesji kontrolnej — odmowa redo (słusznie: powtórka = fałszowanie historii repo),
niemodyfikująca kontrola integralności, odmowa działania bez numerowanego sygnału — **kanonizowane
jako wzorzec** dla każdej sesji otwartej przedwcześnie.

## §2. Reguła SEQ-1 (programowa, trwała)
Po STOP-ie sesji wykonawczej następna sesja wykonawcza startuje dopiero po sygnale CC z numerem
aneksu. Sesja otwarta przedwcześnie wykonuje wyłącznie niemodyfikującą kontrolę integralności
i STOP (wzór §1). Raport końcowy każdej sesji obowiązkowo żyje w repo (results/**) — bez wyjątku.

## §3. Weryfikacja CC na dostępnych liczbach (niezależna)
Graf O2: **103 stany = 2 + 101** — dokładnie oczekiwany rozmiar FSM (tryb OK z licznikiem
debounce ∈ {0,1}: 2 stany; tryb zdegradowany z licznikiem hyst ∈ {0..100}: 101 stanów);
**206 = 2×103 krawędzi** (wejście binarne, pełne pokrycie); **min cykl 102 = hyst 100 + debounce 2**
— spójne z config (debounce=2, hyst=round(5/0.05)=100). Model liczbowo zgadza się z przewidywaniem
co do sztuki. Selfcheck 8/8 z P7←posmon_verify (563b1372) potwierdzony kontrolą integralności.
M: 27/27 mutantów wykrytych bez grid2 ⇒ trend **P-FV-4 ✓** (rozliczenie przy RAPORT_FV); moja
a-priori obawa o mutanty brzegowe się nie zmaterializowała — CHCĘ zobaczyć w C1d/C1a, czym zostały
wykryte (siatka-na-progu vs fuzz sekwencyjny), bo to lekcja o przenośności metody.

## §4. Warunki odczytu C1a–C1d — do wykonania przez CZEKAJĄCĄ sesję, zero modyfikacji
Odpowiedź sesji = cztery czyste zrzuty verbatim (cat), bez komentarza, potem STOP:
- **C1a** `results/FV/RAPORT_FV_S2.md` — pełna treść (tu powinny być: wyniki per mutant, dane O2,
  CLARIFY-1 z formułą desc_total, diff selfchecka);
- **C1b** `results/KSIEGA_PREDYKCJI.md` — pełna treść (warunek C1-KSIEGA, trzeci ślizg — domykamy;
  przy lekturze rozstrzygnę rozjazd sum 19✓/8✗ vs 21✓/13✗ z audytu CC v2);
- **C1c** `r01/proofs/certs/P7_posmon.json` — pełna treść;
- **C1d** `results/FV/MUTANTY.md` — pełna treść.

## §5. Go S3 — warunkowe
S3 (O3 zawieranie geofence↔P2 + O4 złożenie, oba NIEBRAMKUJĄCE) staje się skuteczne WYŁĄCZNIE po
linii CC: **„ANEKS_FV-1a: warunki C1a–C1d odczytane — S3 go"** (linia niesie numer — przechodzi
łapacz). PROMPT_FV_S3 dostarczony równolegle; jego bramka §0 wymaga tej linii, więc przedwczesne
wklejenie kończy się STOP-em, nie szkodą.

## §6. Status bramki nogi
Warunki PASS z PRE_FV §5 (O1 ∧ O2 ∧ różnicówka czysta) są na materiale repo formalnie SPEŁNIONE.
Werdykt PASS zostanie OGŁOSZONY dopiero w ANEKS_FV-2 przy STOP-FV2 — po lekturze C1a–C1d i raporcie
końcowym (reguła C1 programu: żadnych ogłoszeń przed przeczytaniem raportu przez CC).
