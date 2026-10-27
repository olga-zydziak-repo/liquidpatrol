# RAPORT_XAI_S1 — formalizacja, różnicówka, dowody, mutanty (0 bootów) — STOP-XAI1

CC-wykonawca · 27.10.2026 · wykonanie PRE_XAI (byte-check `95555eb3…` PASS,
commit ARCH-1 `ec22a8f7`) + PROMPT_XAI_S1. Sesja deskowa: zero bootów/SITL/
treningu, zero edycji istniejących; nowe pliki `PRE_XAI.md` (ARCH-1)
i `results/XAI/**`. **Kolejność wykonania (prereg wewnątrz sesji): §1
formalizacja ZAPISANA PRZED różnicówką i dowodami** (stałe pudełka z pomiaru
`measure` — xai_s1_pudelko.json; wybory T3/T4 zablokowane w tym paragrafie).

## §1. FORMALIZACJA (litera kodu; stałe z wag KOPIĄ)

**Krok CfC (models.py:127-138, step_np; wagi `net/frozen/ncp.npz` 0337d5ea
czytane kopią: IN=8, H=20, BB=20, V_MAX = vmax npz = 3.0, wszystkie parametry
skończone — `np.isfinite` 10/10 macierzy):**

```
c  = [x ; h]                 ∈ ℝ²⁸          (models.py:129)
bb = tanh(c·Wb + bb0)        ∈ (−1,1)²⁰     (:130)
g  = tanh(bb·Wg + bg)        ∈ (−1,1)²⁰     (:131)
hh = tanh(bb·Wh + bh)        ∈ (−1,1)²⁰     (:132)
γ  = σ(bb·Wt + bt)           ∈ (0,1)²⁰      (:133, bramka czasu)
h′ = γ⊙g + (1−γ)⊙hh                         (:134)
y  = tanh(h′·Wo + bo)·V_MAX  ∈ (−V_MAX,V_MAX)³  (:135-136)
```

Kontroler: `v = clip_v(y, V_MAX)` (net_controller.py:97; clip_v
common.py:11-17: ‖v‖₂ ≤ V_MAX, skalowanie dodatnie), wejście
x = (features − mean)/std po clip_age (features.py:30-33, dataset.py:104-110),
h₀ = 0 na starcie epizodu (net_controller.py:74), **sieć nie stepuje na hold**
(net_controller.py:106-111).

**Pudełko wejść Box_x (p1–p99 per cecha znorm., korpus replay 53 epizody /
74 708 ticków inferencji — LIQ 48 NCP po erratum + FANTOM r1_V2 + DEMO_C
d1_proba; `xai_s1_pudelko.json`, liczby do FREEZE):**

| cecha | p1 | p99 |
|---|---|---|
| rel_x | −1.5702 | 1.6301 |
| rel_y | −1.5982 | 1.6835 |
| rel_z | −3.7057 | 2.9803 |
| own_vn | −1.6925 | 1.6365 |
| own_ve | −1.6728 | 1.6845 |
| own_vd | −5.2115 | 3.9396 |
| age | −0.6440 | 4.5004 |
| valid | 0.0358 | 0.0358 (stała — valid≡1 na tickach inferencji) |

**Pudełko stanu Box_h** (p1–p99 per neuron, tamże w JSON) — używane
WYŁĄCZNIE w T4 i tak podpisane (założenie pomiarowe o stanach osiągalnych).

**Pasmo bramek + δ (pomiar, do FREEZE):** średnie orbity per neuron
∈ [0.4488, 0.5533] (20 wartości w JSON; zgodne z atlasem recon [0.45,0.55]);
δ = p99 chwilowego odchylenia max_i |γ_i(t) − mean_i^orbit| na tickach orbity
= **0.2873** ⇒ **założenie T3: γ_i ∈ [0.1615, 0.8405] ∀i** (z pomiaru,
tak podpisane).

**T1 (ograniczoność wyjść) — formalizacja:** dla KAŻDEGO x ∈ ℝ⁸ i każdego
h ∈ ℝ²⁰ o składowych skończonych: (a) per składowa |y_k| < V_MAX = 3.0;
(b) po clip_v: ‖v‖₂ ≤ V_MAX. Dowód strukturalny: zakres tanh + algebra
clip_v. Różnicówka: skan max_k |y_k| (głowa przed clip_v) po wszystkich
tickach inferencji korpusu + ‖v‖₂ po clip_v; kontrprzykład: |y_k| ≥ V_MAX.

**T2 (lemat stanu) — formalizacja:** h₀=0 oraz ∀t: h_{t+1} = γ⊙g + (1−γ)⊙hh
z γ∈(0,1)²⁰, g,hh∈(−1,1)²⁰ ⇒ ∀t ∀i: |h_{t,i}| < 1. Dowód symboliczny
(indukcja + lemat kombinacji wypukłej). Różnicówka: skan max_i |h_i| po
WSZYSTKICH tickach (również hold — stan zamrożony). Kontrprzykład: |h_i| ≥ 1.

**T3 (twierdzenie warunkowe bramek) — WYBÓR WŁASNOŚCI, zapisany przed
dowodzeniem:** *kandydat PRE („kontrakcja/ograniczenie ‖Δh‖") konkretyzuję
jako KONTRAKCJĘ LOKALNĄ KROKU STANU:*

> **T3:** dla każdego (x,h) spełniającego założenie przedziałowe
> γ_i(x,h) ∈ [0.1615, 0.8405] ∀i (pasmo orbity ± δ, Z POMIARU) zachodzi
> ‖∂h′/∂h‖₂ < 1 (lokalna kontrakcja kroku stanu w normie spektralnej).

Uzasadnienie strukturą równań (przed dowodem): (i) h wpływa na h′ WYŁĄCZNIE
przez bb (models.py:129-134) — jakobian faktoryzuje się J = C·D,
C[j,k]=∂h′_k/∂bb_j, D[j,i]=∂bb_j/∂x… =(1−bb_j²)·Wb[8+i,j]; (ii) pasmo bramek
ogranicza wagi interpolacji γ, (1−γ) oraz człon pochodnej bramki
γ(1−γ)(g−hh); (iii) kontrakcja = formalizacja „stabilności kroku stanu":
zaburzenie stanu wygasa lokalnie, sieć nie ma trybu zatrzaśniętego wzmocnienia.
**Falsyfikowalność różnicówką:** na każdym ticku korpusu spełniającym
założenie liczymy DOKŁADNY jakobian analitycznie; ‖J‖₂ ≥ 1 = kontrprzykład.
Raportowany też licznik ticków poza założeniem. Dowód: arytmetyka
norm/przedziałów na granicach pasma (narzędzie xai_proofs.py); wynik może
nie domknąć się globalnie — wtedy status liczbą (PRE: WYNIK, nie śmierć).

**T4 (znak prawa pościgu interwałowo) — formalizacja:** sin_brg = rel_y/d,
d = √(rel_x²+rel_y²) > 0 na pudełku; przy pozostałych współrzędnych stałych
∂/∂sin_brg = d·∂/∂rel_y_raw = (d/σ₂)·∂/∂x₂ ze stałą σ₂ = std[2] =
0.50327 > 0 i d > 0 ⇒ **stałość znaku ∂y₀/∂sin_brg ⇔ stałość znaku
∂y₀/∂x₂** (x₂ = rel_y znormalizowane). Zastrzeżenie jawne: twierdzenie
o GŁOWIE SIECI y₀ (przed clip_v) — clip_v skaluje dodatnio WARTOŚCI (znak
v zachowany), ale nie pochodne; tak cytować.

> **T4:** na pudełku Box_x × Box_h (p1–p99 z pomiaru, liczby wyżej/FREEZE)
> pochodna ∂y₀/∂x₂ zachowuje stały znak.

Różnicówka: (1) znak dokładnej pochodnej analitycznej na wszystkich tickach
korpusu; (2) znak różnic skończonych (centralne, eps=10⁻³ znorm.) na siatce
3⁸ pudełka × 5 stanów h z korpusu (seed 0). Dowód: arytmetyka przedziałowa
przez warstwy z adaptacyjnym podziałem pudełka; **raport % objętości ze
stałym (jednym, nazwanym po certyfikacji) znakiem**; certyfikaty przeciwnych
znaków w dwóch komórkach = obalenie stałości (status z liczbą).

**Mutanty (konfiguracje nazwane; wyłącznie w pamięci):** M1_znak (seed 1:
znak jednej losowej wagi), M2_skala (wszystkie parametry ×1.5 **łącznie
z vmax** — metadana npz; kontrakt V_MAX=3.0 bez zmian), M3_zero (seed 3:
neuron wyzerowany — kolumny Wg/Wh/Wt + wiersz Wo), **M4_glowa** (strukturalny:
głowa bez tanh, y=zo·vmax) i **M5_bramka** (strukturalny: γ=1.2σ — wypukłość
złamana) — dwa strukturalne DODANE ponad listę kanoniczną (≥3 spełnione),
bo T1/T2 są architektoniczne i żadna mutacja samych WARTOŚCI wag ich nie
łamie; bez M4/M5 tabela czułości T1/T2 byłaby pusta.


## §1a. Weryfikacja rachunku (zanim liczby stały się werdyktami)

- Jakobian analityczny ∂h′/∂h i pochodna ∂y₀/∂x₂ vs różnice skończone
  (5 losowych stanów, eps=10⁻⁶): max rozjazd **1.9·10⁻¹⁰ / 3.0·10⁻¹⁰** —
  analityka poprawna.
- Arytmetyka przedziałowa T4: POPRAWNOŚĆ (zawieranie wartości analitycznej
  w przedziale S) **40/40** prób na komórkach ±0.001/±0.01; przedziały LUŹNE
  (±0.11 przy szerokości 0.01) — nazwane w werdykcie T4.

## §2. RÓŻNICÓWKA (xai_s1_diff.json; korpus pełny: 53 epizody, 74 708 ticków inferencji)

| T | wynik skanu | kontrprzykłady | margines |
|---|---|---|---|
| **T1** | max_k\|y_k\| (głowa) = **2.985176**; ‖v‖₂ po clip_v max = 3.0 (równość: clip aktywny, ≤ trzyma) | **0** | 0.0148 do V_MAX (sieć niemal saturuje głowę) |
| **T2** | max_i\|h_i\| = **0.964907** (wszystkie ticki, też hold) | **0** | 0.0351 do 1 |
| **T3** | ticki w założeniu γ∈[0.1615,0.8405]: 74 235 (poza: 473); ‖∂h′/∂h‖₂ max = **2.5766** | **74 235 — KAŻDY tick w założeniu ma ‖J‖₂ ≥ 1** (przykład: c00_s01 t=111.132, ‖J‖₂=1.2377) | — |
| **T4** | korpus analitycznie: 58 917 (+) / **15 791 (−)** / 0 (21.1% ujemnych; przykład c00_s01 t=111.892, −3·10⁻⁵); siatka 3⁸×5h FD: 17 109 (+) / **15 696 (−)** (47.8%) | znak NIE jest stały — kontrprzykłady na korpusie I na siatce | — |

**T3 i T4 ODPADAJĄ RÓŻNICÓWKĄ przed dowodem (reżim PRE §1(1)) — status
COUNTEREXAMPLE z przykładami liczbowymi.** Mechanizm-kandydat T3 (opisowy,
nie dowodzony): stan NCP żyje na pierścieniu (atlas XAIR) — krok wzdłuż cyklu
granicznego bywa lokalnie EKSPANSYWNY (‖J‖₂>1 w każdym punkcie pracy),
a stabilność cyklu jest własnością mnożników Floqueta OKRESU, nie pojedynczego
kroku; lokalna kontrakcja kroku była złą konkretyzacją „stabilności".
T4: pochodna ∂y₀/∂x₂ przy typowych stanach jest MAŁA (|·|~10⁻³–10⁻¹)
i zmienia znak — „prawo pościgu" z atlasu (saliency CZYTELNE co do dominant)
nie implikuje globalnej stałości znaku składowej poprzecznej.

## §3. DOWODY (xai_s1_proofs.json; narzędzia: sympy 1.12 + sondy przesłanek na wykonywalnym modelu + arytmetyka przedziałowa własna)

**T1 — PROVED.** Kroki (każdy sprawdzany skryptem): P1a tożsamość głowy
y = tanh(h′·Wo+bo)·vmax na 82 sondach (losowe seed 0 + ekstremalne x=±10⁶,
h=±1) — 0 rozjazdów; P1b stała kontraktu vmax==V_MAX==3.0; P1c sympy:
solveset(|tanh z|≥1, ℝ) = ∅; P1d sympy: ‖v·vmax/n‖² − vmax² ≡ 0 (n>vmax>0;
obie strony ≥0 ⇒ równość norm); P1e wagi skończone 10/10. Wniosek:
|y_k| < 3.0 (arytmetyka dokładna); **semantyka IEEE754 (nazwana):** tanh
saturuje do ±1 przy ekstremach ⇒ float gwarantuje |y_k| ≤ 3.0 i ‖v‖₂ ≤ 3.0;
na korpusie max 2.985.

**T2 — PROVED.** P2a struktura kroku h′ == γ⊙g+(1−γ)⊙hh bitowo (82 sondy,
0 rozjazdów) + zakresy słabe (γ∈[0,1], |g|,|hh|≤1 — float); P2b sympy:
solveset(σ≤0)=∅, solveset(σ≥1)=∅, tożsamości kombinacji wypukłej
1−[λa+(1−λ)b] = λ(1−a)+(1−λ)(1−b) (expand≡0, symetrycznie dolna)
+ pozytywność członów (ask przy Q.positive); P2c baza h₀=0
(net_controller.py:74). Indukcja: |h_t|<1 ∀t (arytmetyka dokładna);
float: ≤1 (saturacja); korpus max 0.9649.

**T3 — dowód NIE uruchamiany** (COUNTEREXAMPLE różnicówką, §2).

**T4 — arytmetyka przedziałowa: certyfikowane 0.0% objętości** (20 000
komórek adaptacyjnej bisekcji na Box_x×Box_h, 28 wymiarów; 0% znak+, 0%
znak−, 100% nierozstrzygnięte). Metoda poprawna (zawieranie 40/40, §1a),
ale (i) przedziały przez 3 warstwy tanh/σ zbyt luźne przy tej szerokości
pudełka, (ii) **znak faktycznie nie jest stały** (§2) — więcej komórek nie
uratuje twierdzenia, co najwyżej certyfikowałoby obszary obu znaków.
Status T4: **COUNTEREXAMPLE** (różnicówka); liczba dowodowa: 0% pokrycia.

## §4. MUTANTY (xai_s1_diff_M*.json, xai_s1_proofs_M*.json; korpus mini = r1/r5_ncp + OPS, 13 ep. / 18 433 ticki; dowody pełne)

| mutant (konfiguracja) | T1 diff cex / dowód | T2 diff cex / dowód | T3 diff (w założeniu) | T4 diff neg korpus / siatka |
|---|---|---|---|---|
| M1_znak (seed 1: `Wb.flat[373] *= −1`) | 0 / PROVED | 0 / PROVED | 18 345/18 345 cex | 3 828 / 17 295 |
| M2_skala (wszystko ×1.5 + vmax ×1.5) | **18 424 cex (max 4.4997) / FAIL (P1b)** | 0 (max 0.999) / PROVED | założenie ZAPADA SIĘ: 72 ticki; cex 72 | **17 482 (95%)** / 25 353 |
| M3_zero (seed 3: neuron wyzerowany) | 0 / PROVED | 0 / PROVED | 17 853/17 853 cex | 9 029 / 17 325 |
| M4_glowa (y=zo·vmax, bez tanh) | **782 cex (max 7.8223) / FAIL (P1a)** | 0 / PROVED | 18 345 cex | 3 808 / 17 298 |
| M5_bramka (γ=1.2σ) | 0 / PROVED | 0 na korpusie mini (max 0.9687 — tryb niewzbudzony) / **FAIL (P2a: γ>1 na sondach)** | 6 736 cex | n.d. (pochodna bramki zmieniona) |

**Czułość dowodów: T1 pada na M2 i M4; T2 pada na M5 — każdy DOMKNIĘTY dowód
pada na ≥1 mutancie ✓.** T2 PROVED na M1–M4 to nie trywialność, tylko treść
twierdzenia: lemat stanu jest ARCHITEKTONICZNY (żadna mutacja WARTOŚCI wag go
nie łamie — łamie go dopiero mutacja struktury bramki M5); dlatego mutanty
strukturalne M4/M5 zostały dodane ponad listę kanoniczną. T4 (bez domkniętego
dowodu) czułość przez różnicówkę: M2 odwraca rozkład znaku 21%→95% ujemnych.
Mutanty wyłącznie w pamięci — zero plików wag.

## §5. STATUSY + predykcje + STOP

| twierdzenie | STATUS | liczby kluczowe |
|---|---|---|
| **T1** | **PROVED** | diff 0/74 708; margines 0.0148; ‖v‖₂≤3.0 (równość osiągana); float: ≤ |
| **T2** | **PROVED** | diff 0 (wszystkie ticki); margines 0.0351; float: ≤1 |
| **T3** | **COUNTEREXAMPLE** | 74 235/74 235 ticków w założeniu z ‖J‖₂≥1; max 2.5766; przykład c00_s01 @111.132 |
| **T4** | **COUNTEREXAMPLE** | korpus 21.1% ujemnych, siatka 47.8%; interwałowo certyfikowane 0% |

ŚMIERĆ S1 (PRE §2.6) NIE zaszła: T1 i T2 domknięte. Predykcje (do KSIĘGI
w ANEKS_XAI-1): P-XA-1 **TAK** (T1+T2 PROVED, 0 kontrprzykładów);
P-XA-2 **NIE** (znak niestały; certyfikacja 0% < 80%); P-XA-3 **NIE**
(kontrakcja lokalna — jedyna sformalizowana własność — obalona różnicówką);
P-XA-4 **TAK** (oba domknięte dowody padają: T1 na M2/M4, T2 na M5).

Narzędzia (sha256,16): `tools/xai_thm_diff.py` **b4454cb99f3c2fa9**
(pomiary + różnicówka + mutanty), `tools/xai_proofs.py` **e7a65b37e478421f**
(dowody sympy 1.12 + sondy + arytmetyka przedziałowa). Przyrządy FROZEN
czytane importem/kopią: xai_replay ac9551ab, wagi 0337d5ea, cechy 9adc1505;
GRU w dowodach nieużywany (litera PROMPT §0.3). Diff-stat i porcelain
w komunikacie commita. **STOP-XAI1. Push = Olga („wypchnięte" — CC przeliczy
niezależnie różnicówkę i ≥1 dowód). Potem ANEKS_XAI-1 (werdykt, KSIĘGA
P-XA-1…4, CO).**
