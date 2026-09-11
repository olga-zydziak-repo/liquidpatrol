# PRE_FV — noga FV: weryfikacja formalna jądra osłony (pozycja 1b w rescopingu CC v2)

CC · 11.09.2026 · wejście: RECON_FV (commit 8e6206c) + inwentarz certów R1.

## §0. Ratyfikacja
Pole ratyfikacji Olgi: **„F1–F8 TAK"** (albo korekty per numer) — decyzje w §8. Po ratyfikacji CC
wystawia ANEKS_FV-0 (zapis ratyfikacji) i PROMPT_FV_S1; build nie startuje wcześniej. Zgodnie z
ARCH-1 (ANEKS_K2-7 §4) ten plik i aneksy wchodzą do repo w pierwszym commicie S1.

## §1. Teza i delta (czego NIE dowodzimy od nowa)

Stoi już: P1 (własności automatu decyzyjnego, z3), P2/P2_vmax3p1/P2_eps (geometria zawierania na
modelu wymiernym), P4 (admisja/tokeny), P5 (konformancja próbkowa spec↔`shield.step` per tick na
421 epizodach, mismatches 0). Delta nogi FV — trzy rzeczy, których w stosie certów nie ma:

D-A. **Nowe twierdzenia na kodzie produkcyjnym** dla dwóch elementów bez własnych certów:
zejście D5 (`safe_descend_step`) i monitor pozycji z histerezą (`_pos_monitor`).

D-B. **Rozszerzenie wiązania model↔kod** z próbkowego (P5: epizody, jakie się wydarzyły) na
systematyczne pokrycie przestrzeni wejść (różnicówka lustro↔produkcja, §4) — bez dotykania pinów.

D-C. **Ambitnie, niebramkująco:** zawieranie predykatu `_geofence_violation` w inwariancie certu P2
na domenie clampu (O3).

Stretch (ii): własności ZŁOŻENIA osłona∘sieć (O4) — nie wnętrza CfC.

## §2. Frozen i pliki dotykane

Dotykane WYŁĄCZNIE: `r01/proofs/**` (nowe provery, nowe certy JSON, lustro `fv_mirror.py`, testy
różnicowe, rozszerzenie mapy `certs_selfcheck.py` — diff mapy verbatim w raporcie sesji),
`results/FV/**`, aneksy/PRE per ARCH-1. Nietykalne: `r01/shield.py`, `r03/**` (config czytany, nie
edytowany), `bench/**`, `k1/**`, `harness/**`, sędziowie, wagi, raporty kanoniczne. **Import modułów
pinowanych w testach jest dozwolony i pożądany** (różnicówka §4); edycja = SR-FV-2. Obowiązuje
reguła końca sesji dotykających `proofs/`: czyste drzewo albo commit + `certs_selfcheck` PASS
w raporcie sesji (lekcja self-hash P2.json).

Zasada semantyki: PRE zamraża KSZTAŁT twierdzeń, progi bramki i domeny; dokładną semantykę
operacyjną (resety liczników, kolejność porównań, brzegi nierówności) definiuje KOD przez lustro
1:1 — nie ten dokument i nie pamięć. Każda stała w cercie z cytatem `plik:linia` (reguła V5).

## §3. Obligacje (kształty zamrożone)

**O1 — D5 (`safe_descend_step`), cert P6_d5 + prover `d5_verify.py`.** Przy założeniu A1-zegar
(`now` niemalejące; źródło: wywołania produkcyjne, cytaty w cercie) i stałych profilu z config:
(a) przełączenie faz dokładnie na progu H_SWITCH (semantyka brzegowa wg kodu); (b) wysokość zadana
monotonicznie nierosnąca; (c) touchdown osiągany w skończonej liczbie kroków N* policzonej z
stałych i zapisanej w cercie; (d) komenda ograniczona profilem (|v| ≤ max fazy). Narzędzie: z3 +
indukcja po krokach / arytmetyka zamknięta. Trudność wg reconu: NISKA.

**O2 — histereza (`_pos_monitor`), cert P7_posmon + prover `posmon_verify.py`.** Model: skończona
maszyna stanów monitora (liczniki debounce/hyst + flaga; przestrzeń rzędu setek stanów przy
hyst = round(5/dt)). Twierdzenia: (a) REFUSE(POS) dopiero po ≥ debounce kolejnych ticków
pos_flag=True; (b) wyjście ze stanu zdegradowanego wymaga ≥ hyst ticków czystych; (c) dolne
ograniczenie okresu oscylacji (brak trzepotania szybszego niż histereza). Narzędzie podstawowe:
**wyczerpująca enumeracja osiągalnego grafu stanów** (przestrzeń skończona i mała — pełne pokrycie,
nie próbka), z3-indukcja jako duplikat. To obniża wycenę reconu (ŚREDNIA → NISKA-ŚREDNIA): indukcja
po licznikach nie jest konieczna, gdy graf jest enumerowalny.

**O3 — zawieranie geofence↔P2 (ambitne, NIEBRAMKUJĄCE), ewentualny cert P8_geo_cont.** Forma d2:
∀ (pos, vel, target) ∈ D: ¬`_geofence_violation` ⇒ Inv_P2, gdzie D = domena clampu: |v| ≤ v_max=3.0
(dokładnie ta wielkość, którą liczy `_braking_dist`), pozycje ograniczone kopertą (granice z config,
cytowane), pion w [0, V_E]. Stałe wymierne z P2.json. Wynik: dowiedzione → cert; kontrprzykład
MODELOWY → analiza osiągalności + raport; kontrprzykład POTWIERDZONY NA PRODUKCJI przy wejściu
osiągalnym → TRIPWIRE (§5). Wariant informacyjny: te same zdania przy v_max=3.1 (spójność z
P2_vmax3p1). **Domena V_env=6.0 jest POZA zakresem O3** — to własność środowiska (limit zadany ≠
faktyczny), adresowana erratum #2 (ERRATUM_VMAX.md); raport daje jawny odsyłacz zamiast udawać, że
predykat ją pokrywa.

**O4 — stretch (ii): złożenie osłona∘sieć.** (a) |y_net| ≤ v_max architektonicznie (tanh·v_max,
cytat z net/models.py) — lemat z dowodem jednolinijkowym + zapis; (b) kompozycja: niezależnie od
wyjścia sieci, clip_v + koperta (+ O3, jeśli dowiedzione) ⇒ ograniczenia toru — dokładna forma
lematów ustalana w sesji O4, raportowana z założeniami. CfC-unroll (weryfikacja wnętrza sieci):
wyłącznie desk-note ze statusem „częściowy", zero instalacji narzędzi. Zgodne z prerejestrowaną
P-CC2-1.

## §4. Wiązanie model↔kod (rdzeń metody)

Lustro `fv_mirror.py`: przepisanie 1:1 `_pos_monitor`, `_geofence_violation`, `_braking_dist`,
`safe_descend_step` ze stanem zreifikowanym jako jawny wektor (recon R2: jądro deterministyczne,
ale mutuje atrybuty instancji). **Różnicówka lustro↔produkcja** — produkcja importowana bez
modyfikacji:
(a) siatka deterministyczna pokrywająca brzegi progów (debounce/hyst ±1 tick, R_E±, V_E±, v_max±,
H_SWITCH±) — lista punktów commitowana PRZED uruchomieniem;
(b) fuzz z ziarnami {0..4}, ≥10⁵ przypadków na funkcję;
(c) regresja fikstur: istniejący zestaw 4221/1791 ticków D5 przegoniony przez lustro.
Kryterium: **0 rozbieżności końcowych**. Każda rozbieżność = poprawka LUSTRA z wpisem do rejestru
rozbieżności (kod produkcyjny nietykalny). Rozbieżność niedomykalna po stronie lustra (semantyka
zależna od stanu nieuchwytnego bez reifikacji w produkcji) ⇒ STOP i decyzja osobnym dokumentem —
kandydatem jest wtedy ceremonia α (INFRA-3), ale NIE uruchamia się automatycznie.

Uzasadnienie wobec R4 reconu: β na śladach lotu jest martwe (ślady nie niosą target/mode/vel/auth_ok
— RECON_FV R4), ale różnicówka NIE potrzebuje śladów lotu: wejścia syntetyczne pokrywają przestrzeń
lepiej niż jakikolwiek lot, a import pinowanych modułów nie dotyka pinów. To zamyka pytanie R6/2 bez
ceremonii.

## §5. Bramka nogi (ZAMROŻONE przed pierwszym dowodem)

**PASS** = O1 ∧ O2 dowiedzione (certy P6/P7 + provery + wpisy w mapie `certs_selfcheck`) ∧
różnicówka §4 czysta (0 rozbieżności końcowych na commitowanej siatce + fuzz + fikstury).
**CZĘŚCIOWY** = dokładnie jedna z {O1, O2} dowiedziona ∧ różnicówka czysta.
**O3** raportowana niezależnie (dowiedziona / kontrprzykład modelowy / nierozstrzygnięta) — nie
zmienia werdyktu PASS/CZĘŚCIOWY. **O4** analogicznie (stretch).
**ŚMIERĆ nogi** = wiarygodnego lustra nie da się zbudować bez reifikacji produkcji (rozbieżność
strukturalna §4) — raport negatywu metodologicznego, STOP, decyzja o ceremonii α osobnym dokumentem.
**TRIPWIRE (nadrzędny):** kontrprzykład REALNY jakiejkolwiek własności na kodzie produkcyjnym przy
wejściu osiągalnym = ZNALEZISKO PIERWSZEJ WAGI (kandydat: bug osłony) ⇒ natychmiastowy STOP
diagnostyczny; ZAKAZ naprawiania osłony w tej nodze; dalszy ruch = decyzja programowa dokumentem.
**Zakaz języka:** „formally verified system" nie istnieje jako zdanie. Wolno wyłącznie wyliczać
dowiedzione własności z założeniami i domenami. Kanon roszczeń FV powstanie w aneksie zamykającym
(wzór RAPORT_NET §11 / RAPORT_K2 §7).

## §6. Budżety i STOP-y

≤ 4 sesje robocze; zero bootów, zero GPU, zero treningu. Narzędzia: z3 (`.certdeps`) + stdlib +
numpy już obecny w repo. Kolejność: S1 = lustro + różnicówka bazowa + dowód O1 → **STOP-FV1**
(CC czyta format certu P6, diff mapy selfchecka, rejestr rozbieżności) → ANEKS_FV-1 → S2 = O2 →
S3 = O3 + O4 → **STOP-FV2** = RAPORT_FV → ANEKS_FV-2 (werdykt + kanon). Bufor: 4. sesja.

## §7. Stop-rules

SR-FV-1: bramka wejścia git każdej sesji. SR-FV-2: zakaz edycji plików pinowanych/frozen (import w
testach dozwolony). SR-FV-3: zero instalacji pakietów. SR-FV-4: kryteria §5 nietykalne po
ratyfikacji — w żadną stronę. SR-FV-5: tripwire §5 natychmiastowy, bez „jeszcze jednego sprawdzenia
zanim zgłoszę". SR-FV-6: każda liczba i stała ze źródłem `plik:linia`. SR-FV-7: koniec każdej sesji
dotykającej `proofs/` = czyste drzewo albo commit + `certs_selfcheck` PASS wklejony do raportu.

## §8. Decyzje F1–F8 (odpowiedzi na PYTANIA DO PRE z RECON_FV; wpisane wg rekomendacji CC)

**F1.** R3a/R3b (dominacja, latch) POZA obligacjami — P1d/P1f/P1h już je kwantyfikują; duplikat nie
jest deltą. Wchodzą za darmo jako test spójności lustra z P1 (lustro musi reprodukować własności
P1 — jedna asercja, nie osobne twierdzenie). Rdzeń nogi = O1 + O2.
**F2.** Reifikacji α NIE MA w tej nodze. Wiązanie = §4 (lustro + różnicówka syntetyczna + fikstury).
Ceremonia α wyłącznie osobną decyzją przy ŚMIERCI §5 — nigdy automatycznie.
**F3.** O3 w formie ZAWIERANIA (d2) na domenie |v| ≤ 3.0 (clamp kodu, stałe P2.json); wariant
informacyjny 3.1; V_env=6.0 poza zakresem z jawnym odsyłaczem do erratum #2.
**F4.** TAK — zegar monotoniczny jako jawne assumption certu P6 z cytatami wywołań produkcyjnych.
**F5.** Dead-man POZA nogą FV (pozostaje testem `test_deadman` + nota z triggerem: wejdzie przy
rozszerzaniu osłony — 2d — albo jako osobna mini-noga temporalna, jeśli kiedyś potrzebna).
**F6.** Stretch (ii) = dowód ZŁOŻENIA (O4) jako główny wynik; wnętrze CfC wyłącznie desk-note
„częściowy"; zero instalacji.
**F7.** Narzędzia: tylko z3 + stdlib + numpy z repo. Żadnych nowych zależności w tej nodze.
**F8.** Re-instrumentacja logów per-tick (pełne wejścia `_decide`) NIE teraz — backlog §8 programu
z triggerem: pierwsza noga potrzebująca replayu decyzji z lotów (kandydat: 2b wiatr).

## §9. Predykcje CC (prerejestrowane; rozliczenie w KSIEGA_PREDYKCJI przy RAPORT_FV)

- **P-FV-1:** O1 dowiedzione w ≤ 1 sesji dowodowej od startu S1 — p ≈ 0.75.
- **P-FV-2:** różnicówka znajdzie ≥ 1 rozbieżność wymagającą poprawki LUSTRA (nie kodu produkcji) —
  p ≈ 0.6 (kalibracja: chroniczne zaniżanie glue przez CC).
- **P-FV-3:** O4(a)+(b) domknięte w ≤ 1 sesji — p ≈ 0.7.
