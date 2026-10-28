# ERRATUM_XAI-1 — dwie korekty nogi XAI: (A) wycofanie „generator, nie echo", (B) T4 zmierzyło inną pochodną (samowykonalny)

CC · 28.10.2026 · errata w przód do `ANEKS_XAI-1.md` (sha 65ef4393…, commit
7564a98e) i `results/XAI/FREEZE_XAI.md`. **Zastępuje poranną wersję tego
dokumentu (sha 2f217073…, niezacommitowaną).** Werdykt nogi (CLOSED,
T1/T2 PROVED, śmierć S1 nie zaszła) BEZ ZMIAN. Sygnały bez numeru wykonawca
odrzuca.

## §1. Korekta A — echo vs generator

Wycofuję akapit o mechanizmie w ANEKS_XAI-1 §2 („pomiar rozstrzygnął na
rzecz sieci-generatora… różnicówka ROZSTRZYGNĘŁA") i to samo zdanie
w opisie commita CO-XAI. T3 zmierzył ‖∂h′/∂h‖₂ ≥ 1 na każdym ticku założenia
(74 235/74 235, max 2.5766). Norma operatorowa ≥ 1 mówi tylko tyle, że krok
nie jest kontrakcją w normie 2: w każdym kroku istnieje kierunek o wzmocnieniu
≥ 1. Kontrakcja w jednym kroku jest warunkiem wystarczającym zapominania stanu
początkowego, nie koniecznym — iloczyn jakobianów po wielu krokach może się
kurczyć mimo norm pojedynczych kroków ≥ 1 (macierze nienormalne). Dane pasują
więc i do sieci-echa, i do generatora; obserwacja z atlasu (n0 ≈ sinus
kierunku na cel, |r| 0.95) też ich nie rozróżnia, bo oscylator zsynchronizowany
z wejściem obraca się razem z nim. Status: **NIEROZSTRZYGNIĘTE**. Z T3 zostaje
w mocy: dla tej sieci w paśmie orbity nie istnieje jednokrokowy certyfikat
stabilności.

Para hipotez na przyszłość: **H-echo** — przy zalogowanych wejściach stan
zapomina warunek początkowy, a przy zamrożonym wejściu zbiega do punktu
stałego; **H-gen** — przy zamrożonym wejściu stan oscyluje sam.

## §2. Korekta B — T4 nie zmierzyło prawa pościgu

Litera `bench/features.py` (9adc1505): x = [rel_n, rel_e, rel_d, own_vn,
own_ve, own_vd, age, valid]. **x₂ = rel_d**, offset pionowy (npz: mean
1.942 m, std 0.503). RAPORT_XAI_S1 §1 przyjął „x₂ = rel_y znormalizowane"
ze σ₂ = std[2] = 0.50327 — to odchylenie rel_d; rel_e ma std[1] = 6.034.
Narzędzia liczyły po Wb[2,:] (xai_thm_diff.py:186, xai_proofs.py:199).
Zmierzona wielkość to **∂v_n/∂rel_d**, czyli sprzężenie poziomej komendy N
z offsetem pionowym. Liczby 21.1% / 47.8% / 0.0% są prawdziwe dla tej
pochodnej i nic nie mówią o prawie pościgu.

Błąd leży po stronie CC, podwójnie. (i) PRE_XAI §1 sformułowało T4 jako
„∂v_n/∂sin_brg": wielkość niedookreśloną (sin_brg nie jest wejściem sieci
i nie powiedziano, co trzymamy stałe) i krzyżową (składowa N z sinusem
namiaru, który żyje na osi E). (ii) Weryfikacja w ANEKS_XAI-1 §1.2 przeliczyła
tę pochodną „co do sztuki" na tej samej złej cesze — sprawdziła arytmetykę,
nie mapowanie indeksu na cechę.

Status T4: **NIE-SFORMALIZOWANE** (S1 zmierzyło inną pochodną). Prawo
pościgu w S1 niezmierzone.

## §3. Stan po erracie

Zdanie zamrożone do cytowań — zastępuje wersję z ANEKS_XAI-1 §2:

> „NCP-20 ma dwa twierdzenia architektoniczne klasy dowodowej: T1 |y_k| < 3.0
> i T2 |h_i| < 1 (w IEEE754: ≤) — dowiedzione symbolicznie, potwierdzone
> różnicówką 0/74 708 ticków i czułe na mutanty — oraz jeden zmierzony
> kontrprzykład: (T3) kontrakcja w jednym kroku nie zachodzi — w każdym kroku
> orbity istnieje kierunek o wzmocnieniu ≥ 1 (max ‖J‖₂ 2.58), więc stabilność
> pierścienia to pytanie o zachowanie wielokrokowe (nazwane, niezmierzone).
> Znak prawa pościgu (T4) w S1 niezmierzony."

Bez zmian: T1/T2 PROVED, T3 COUNTEREXAMPLE, werdykt CLOSED, zdanie kanoniczne
programu, demo v5 (na ekranie wyłącznie T1/T2 i opisy). FREEZE_XAI: wiersz T4
i punkt 3 zasady cytowania tracą ważność na mocy tego dokumentu — T4 nie wolno
cytować jako wyniku; „prawo pościgu" wyłącznie jako opisowe dominanty saliency
z atlasu.

## §4. KSIĘGA

- **P-XA-2: ✗ → n.r.** (zmierzona wielkość ≠ prerejestrowana). Lekcja (a)
  przy P-XA-2 wycofana — oparta na złej wielkości. Lekcja (b) zostaje tylko
  w części negatywnej: pudełko całego korpusu × 20-wymiarowe pudełko stanu
  przy 20k komórek nie certyfikuje nic; teza, że metoda dowozi na małych
  pudełkach, jest hipotezą do sprawdzenia.
- **P-XA-3:** nawias lekcji („kontrakcja kroku = echo vs stabilność okresu =
  generator") nieścisły — kontrakcja kroku to warunek wystarczający, nie
  hipoteza pary; właściwa para H-echo / H-gen jak w §1.
- **Suma nogi XAI: 2 ✓ / 1 ✗ / 1 n.r.**
- Nowe wpisy kalibracyjne CC: (1) obalony warunek wystarczający nie potwierdza
  hipotezy przeciwnej; (2) twierdzenia o sieci formułować na wielkościach
  jednoznacznych — pochodna po wejściu (indeks i nazwa z features.py) albo po
  wielkości fizycznej z jawnym „co trzymamy stałe"; (3) weryfikacja CC
  sprawdza mapowanie indeks → cecha literą kodu, zanim przelicza liczby —
  zgodność „co do bitu" na złej cesze nic nie znaczy.

## §5. KIERUNKI — obie pozycje XAI przeformułowane

- **XAI-FLOQUET (T3′):** para H-echo / H-gen, dwa testy przy biurku: (a)
  zapominanie — replay tych samych lotów z losowych stanów początkowych,
  warunkowo na zalogowanych wejściach, plus warunkowe widmo Lapunowa; (b)
  autonomia — wejście zamrożone na wartościach z pasma orbity: punkt stały czy
  oscylacja.
- **XAI-ZNAK-PER-FAZA → XAI-ZNAK (T4′):** prawo pościgu od nowa, na
  wielkościach jednoznacznych — składowa radialna komendy względem celu jako
  funkcja dystansu (daleko ⇒ zbliża się; blisko ⇒ nie zbliża się) i kierunek
  orbity (opisowo). Przesłanka „znak żyje per faza" wycofana.
- Obie pozycje idą razem jako noga XAI-II (`PRE_XAI2.md`); trigger spełniony
  decyzją Olgi 28.10.

## §6. Wykonanie (jeden commit, 0 bootów)

1. Bramka: `git fetch` → origin/master == **f0e1147d**;
   `origin/master..HEAD` puste; porcelain czysty poza nazwanymi ??.
2. Commit ERRATUM-XAI: (a) `ERRATUM_XAI-1.md` verbatim do korzenia (ARCH-1:
   byte-check sha256 z wiadomości CC; wersję poranną 2f217073… odrzucić);
   (b) `results/KSIEGA_PREDYKCJI.md` — dopisek append-only pod sekcją NOGA
   XAI, treść §4; (c) `KIERUNKI_PO_PLANIE.md` — dopisek 28.10 append-only:
   zdanie zamrożone z §3 (do cytowań zamiast wersji 27.10) i pozycje według §5.
3. ZERO edycji `ANEKS_XAI-1.md`, FREEZE_XAI, RAPORT_XAI_S1, kodu i demo.
4. Push = Olga („wypchnięte" — CC weryfikuje z repo). STOP.
