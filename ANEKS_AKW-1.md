# ANEKS_AKW-1 — werdykt smoke, błąd jednostki do księgi CC, S2: klif ω·dt desk + profil + re-smoke

CC · 09.10.2026 · łańcuch AKW (po STOP-AKW1, commity b1f77856→50f83cf5→cc212d2a na
origin). Samowykonalny: §6 (sesja S2: desk + re-smoke; KAMPANIA NADAL NIEZWOLNIONA).
Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-AKW1 + rozliczenie odchyleń

Przyjęte po weryfikacji CC z repo: ARCH-1 finalnie BAJT-W-BAJT z ratyfikowanym
(ae670893… — amend naprawczy zadziałał); zakres commitów czysty (korzeń + wrapper +
2 linie rejestru + results/AKW/**); diff rejestru verbatim; kadencje potwierdzone
z surowych percep_feed (14.71 / 7.58 Hz co do wartości), refuse 0 / breach false we
wszystkich 8 epizodach, c03 bootu 3 INVALID (dsw 0.8835) zgodnie z raportem; testy
12/12 + regresja 210.

**Odchylenie #1 (edycja ratyfikowanego dokumentu przy ARCH-1):** przyjęte — naprawa
amendem PRZED pushem, stan końcowy verbatim, pełna jawność. Wpis do rejestru klas:
„adnotacja w dokumencie ratyfikowanym"; reguła wzmocniona: dokument ratyfikowany
commituje się WYŁĄCZNIE verbatim, wszelkie adnotacje żyją w raporcie.
**Odchylenie #2 (launch 1 przed nadejściem PROMPT):** przyjęte — przerwany w trakcie,
zero werdyktu, artefakty z ABORT_NOTE, policzony w budżecie. Reguła wzmocniona:
**brak promptu = sygnał bez numeru** — ratyfikacja PRE nie uruchamia lotów, uruchamia
je numerowany PROMPT.

## §2. Werdykty bramek S1 (formalnie)

- **A: FAIL** (2/3 → powtórka → 0/3) ⇒ inżynieria profilu wg PRE §4 — nie śmierć,
  kampania niezwolniona. Nota: boot 2 wg miary SĘDZIEGO (≤25 s) miał 3/3 ślepych
  (10.0/23.9/15.5) — padła moja ostrzejsza bramka 20 s; to nie zmienia werdyktu,
  ale mówi, że przy szybkim modzie profil 30°/s działa nawet z wieloprzebiegową
  admisją.
- **B: ROZSTRZYGNIĘTA PASS** — zdolność toru dowiedziona bootem 2 (14.71 Hz /
  0.080 s); litera bootu 3 (7.58 < 8) to wolny mod znanej bimodalności narzędziowej
  (ANEKS_DET-1 §2a), której zdanie śmierci czasowej padło już w 2A i nie wraca
  (detektor nie jest limitem: push_frame 13.9 ms). **Od teraz w nodze AKW B jest
  telemetrią opisową; bramkują A + C.**
- **C: PASS 2/2** — program utrzymuje breach 0 / REFUSE 0 we wszystkim, co
  kiedykolwiek poleciało uzbrojone (+2 booty).
- Predykcje: P-AKW-1 ✗; P-AKW-2 i P-AKW-5 trzymają się (zapis przy zamknięciu).

## §3. Wpis do księgi błędów CC (klasa NOWA: „zamrożono niewłaściwą zmienną sprawczą")

Zmienną sprawczą admisji pod rotacją jest obrót międzyklatkowy **ω·dt [°/klatkę]**,
nie prędkość ω [°/s]. PRE_AKW zamroziło ω=30°/s, cytując bimodalność kadencji
z ANEKS_DET-1 §2a w §2 — czyli znając OBA czynniki iloczynu, zamroziłem tylko jeden.
Pasmo R3 „10–25°/s czyste" maskowało jednostkę (mierzyło de facto 0.7–1.7°/klatkę).
Dowód jednozmienny z S1: ten sam profil fizyczny (ulog 29.9°/s p50), 2.04°/kl →
admisja 94.7%, 3.96°/kl → 0/235. Konsekwencja systemowa (obowiązuje od teraz):
**progi sprzężone z torem klatkowym zamraża się w jednostkach per-klatka.**

## §4. S2a — DESK: lokalizacja klifu admisji w ω·dt (zero bootów)

Rozszerzenie `akw_rot_strat` o: (a) binowanie po **°/klatkę** (ω·dt z własnych danych,
nie z nominału), (b) **decymację ×2** replayów dolotu i percep_feed kampanii
(syntetyczne pasmo ~1.4–3.4°/kl), (c) dołożenie obu bootów smoke (punkty 2.04 → 94.7%
i 3.96 → 0%). Wynik: tabela admisja-vs-°/kl w binach co ~0.3°/kl oraz
**κ₉₀ = największe °/kl z admisją ≥90% przy celu w FOV** (plus przebieg spadku —
klif czy zbocze). Dekompozycja mechanizmu przy okazji: który człon pada pierwszy
(gate mti vs central vs k=3) — po polach gate/window w rekordach.

## §5. Decyzja profilu — REGUŁA prerejestrowana (wykonawca stosuje mechanicznie)

Niech ω_safe = 0.85 · κ₉₀ · 7.58 Hz (margines 15% w WOLNYM modzie):

- **Ścieżka I (ciągły wolniejszy):** jeśli ω_safe ≥ 14°/s ⇒ profil ciągły
  z ω = min(30, ⌊ω_safe⌋)°/s, reszta parametrów bez zmian (dwell 2.0, CCW, ψ_last).
- **Ścieżka II (step-and-stare):** jeśli ω_safe < 14°/s (wtedy worst-case czekania
  ciągłego 273°/ω > 19.5 s — budżet sędziego topnieje) ⇒ profil krokowy:
  obrót o **40°** przy 60°/s (0.67 s) → **stare 1.2 s** (w oknie stare ω·dt = 0 ⇒
  admisja jak przy nosie nieruchomym — reżim dowiedziony całym programem) → kolejny
  krok; dwell po utracie 2.0 s bez zmian; worst-case pełny przegląd: 9 kroków ≈ 16.8 s.
- Bramka A re-smoke przeliczana z profilu wzorem: **t_A = min(23, ⌈worst_wait +
  3 s dolotu + 25%⌉)** — zawsze ≤ sędzia−2. (Dla ścieżki II: t_A = 23 s? wyliczyć:
  16.8+3 = 19.8 ×1.25 ≈ 24.7 → cap 23 s; dla ciągłego ω=15: 18.2+3=21.2 ×1.25 ≈ 26.5
  → cap 23 s. Cap obowiązuje.)
- Edycja dozwolona WYŁĄCZNIE w `akw_scan.py` (stałe/tryb profilu) + aktualizacja
  testu profilu; nowy sha → FREEZE_AKW z wpisem przed/po. Pass-through i rejestr
  NIETKNIĘTE (test §3.1 S1 musi przejść bez zmian).

## §6. Wykonanie S2 (jedna sesja; booty: re-smoke 1 + naprawczy 1)

1. **Bramka:** origin/master zawiera cc212d2a; ahead pusty; porcelain pełny; FROZEN
   wykonaniem (w tym akw_scan 2237cc7c i rejestr 4f58d204 sprzed edycji profilu).
2. **ARCH-1:** ten plik → korzeń VERBATIM, pierwszy commit.
3. **S2a desk (§4)** → tabela + κ₉₀ → **reguła §5** → edycja profilu + test +
   FREEZE_AKW update. Wynik desku i zastosowanie reguły w raporcie WPROST.
4. **Re-smoke:** 1 boot kampanijny r1 (c00–c03×s01), FEED=V2, CONTROLLER=net_akw,
   reżim jak S1. **Bramki: A′ = ENTRY ze skanu w 3/3 ślepych, każdy t_entry ≤ t_A(§5);
   C verbatim (breach 0; REFUSE wpis; POS⇒STOP); B opisowo.** INVALID epizodu ⇒ boot
   naprawczy (1). <3/3 ważnych ⇒ STOP i czeka ANEKS.
   **Nota modu (prereg):** jeśli boot wyląduje w SZYBKIM modzie kadencji, bramka A′
   liczy się normalnie, ale raport mówi to wprost i kampania dostaje bezpiecznik:
   pierwszy wolny-modowy boot V2 kampanii z ZEREM admisji przy celu w FOV ⇒ przerwanie
   na granicy rundy + ANEKS (wpis prereg do przyszłego zwolnienia kampanii —
   egzekwowalny, bo tryb widać w dt percep_feed na bieżąco).
5. **STOP-AKW2:** commit (desk: tabela+κ₉₀+reguła; diff profilu; FREEZE_AKW; tabela
   re-smoke per epizod z t_entry i klasami ENTRY; porcelain). Push = Olga
   („wypchnięte"). Dalej: **ANEKS_AKW-2** — werdykt re-smoke; przy PASS zwolnienie
   KAMPANII (24+3) z bezpiecznikiem modu. STOP.

ZAKAZ: kampanii i lotów poza §6.4; edycji czegokolwiek poza stałymi/trybem profilu
w akw_scan.py i testem profilu; zmian progów poza wzorem t_A; dotykania FROZEN.

## §7. Budżet

Sufit nogi skorygowany **30 → 32** (wpis jawny; reconowe ≤34 nienaruszone):
zużyte 3 + re-smoke ≤2 + kampania 24 + zapas 3 = 32. Sesje: S2 (desk+re-smoke) +
S3 (kampania) — razem 3 lotne w nodze.
