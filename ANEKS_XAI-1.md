# ANEKS_XAI-1 — przyjęcie S1, werdykt nogi XAI, KSIĘGA P-XA-1…4, CO (samowykonalny)

CC · 27.10.2026 · po STOP-XAI1 (ARCH-1 `ec22a8f7` + `41dcb418`), zweryfikowanym
z repo wykonaniem. Dokument samowykonalny: §5 = zlecenie CO. Sygnały bez
numeru wykonawca odrzuca.

## §1. Weryfikacja CC (niezależna, z repo)

1. **ARCH-1 PASS:** `PRE_XAI.md` w korzeniu bajt w bajt
   `95555eb3…8760166`. Zakres `41dcb418`: 17 plików, wszystkie NOWE,
   wyłącznie `results/XAI/**`. Sha instrumentów zgodne z FREEZE_XAI:
   ncp.npz `0337d5ea`, xai_replay `ac9551ab`, xai_thm_diff `b4454cb9`,
   xai_proofs `e7a65b37`.
2. **Różnicówka przeliczona NIEZALEŻNIE** (własny forward przepisany
   z litery models.py:127-138 — nie `step_np`; własny analityczny jakobian
   ∂h′/∂h i ∂y₀/∂x₂ potwierdzony strukturą; własne SVD; replayer `ac9551ab`
   wyłącznie jako instrument rekonstrukcji WEJŚĆ): 53 epizody / 74 708
   ticków inferencji; zgodność mojego forwardu z wyjściem replayu
   **max |Δ| = 8.9e-16** (epsilon maszynowy).
   - **T1:** max |y_k| = 2.985176, kontrprzykłady 0, ‖v‖₂ po clip max 3.0
     — co do bitu zgodne z raportem.
   - **T2:** max |h_i| = 0.964907, kontrprzykłady 0 — zgodne. (Nota litery:
     stan zmienia się wyłącznie na tickach inferencji, więc skan po nich +
     h₀=0 jest zupełny — równoważny skanowi „po wszystkich tickach".)
   - **T3:** w założeniu γ∈[0.1615, 0.8405]: 74 235 ticków (473 poza);
     kontrprzykłady **74 235/74 235**, max ‖J‖₂ = 2.576646; przykład
     c00_s01 t=111.132 → ‖J‖₂ = 1.237702 (raport: 1.2377) — zgodne.
   - **T4:** znak ∂y₀/∂x₂: **15 791 ujemnych / 58 917 dodatnich / 0 zer**
     (21.1%) — co do sztuki; przykład c00_s01 t=111.892 → −2.8e-05 (raport
     −3e-05, zaokrąglenie).
3. **Dowód przeliczony NIEZALEŻNIE (T1+T2, własne sympy 1.12):**
   solveset(|tanh z| ≥ 1, ℝ) = ∅; tożsamości wypukłości z resztą 0:
   1−h′ ≡ γ(1−g)+(1−γ)(1−hh) i h′+1 ≡ γ(g+1)+(1−γ)(hh+1) — oba człony
   dodatnie dla γ∈(0,1), g,hh∈(−1,1); σ∈(0,1) (granice 0/1 + monotonia);
   vmax=3.0 z npz = kontrakt r01/config.py:24; wagi skończone 10/10;
   indukcja z h₀=0. **PASS — oba dowody stoją w mojej własnej rachubie.**
4. **Czułość:** różnicówki mutantów raportu jechały jawnie na korpusie
   MINI (13 ep. / 18 433 ticki — pole `korpus` w JSON-ach; litera zgodna).
   Moje WŁASNE sondy pełnokorpusowe wzmacniają tabelę: M2_skala —
   74 531 kontrprzykładów kontraktu V_MAX=3.0 (max |y| 4.4999); M4_glowa —
   5 238 (max 9.0012); M5_bramka łamie przesłankę zakresu bramki dowodu T2
   (litera proofs_M5: 36 złych zakresów). Wniosek bez zmian: **każdy
   domknięty dowód pada na ≥1 mutancie** — dowody mierzą sieć, nie tautologię.

## §2. WERDYKT (zdania zamrożone)

**Noga XAI CLOSED za 0 bootów. Śmierć S1 NIE zaszła.** Zdanie zamrożone:

> NCP-20 ma **dwa twierdzenia architektoniczne klasy dowodowej**:
> T1 |y_k| < 3.0 i T2 |h_i| < 1 (w IEEE754: ≤) — dowiedzione symbolicznie,
> potwierdzone różnicówką 0/74 708 ticków i czułe na mutanty — oraz **dwa
> zmierzone kontrprzykłady-wyniki**: (T3) lokalna kontrakcja kroku NIE
> zachodzi — każdy tick orbity jest krokowo ekspansywny (max ‖J‖₂ 2.58),
> więc stabilność pierścienia to pytanie o mnożniki Floqueta OKRESU
> (nazwane-niezmierzone); (T4) znak prawa pościgu NIE jest globalny
> (21.1% ticków ujemnych) — polityka z fazą orbitalną steruje stycznie,
> znak żyje per faza.

Mechanizm T3 wart osobnego zdania: kandydatka „kontrakcja krokowa" była
hipotezą **sieci-echa** (oscylacja niesiona wejściem na kontrakcyjnej
dynamice — wzór ESN); pomiar rozstrzygnął na rzecz **sieci-generatora**
(rekurencja krokowo ekspansywna, stabilizowana domknięciem pętli przez
środowisko). To nie jest porażka formalizacji — to różnicówka, która
ROZSTRZYGNĘŁA między dwiema klasami mechanizmów za 0 bootów.

Zdanie kanoniczne programu zyskuje literę: **„dowiedziona osłona + sieć
z dowiedzionymi twierdzeniami architektonicznymi"** — certyfikaty osłony
9/9 + T1/T2 PROVED. Cytowanie na zewnątrz WYŁĄCZNIE wg ZASADY CYTOWANIA
FREEZE_XAI (T3 nigdy bez przedziału i statusu COUNTEREXAMPLE; T4 nigdy
bez % pokrycia; zero roszczeń D6).

## §3. KSIĘGA — rozliczenie P-XA-1…4 (2/4)

- **P-XA-1 (0.85) TAK** — T1+T2 PROVED, różnicówka 0 kontrprzykładów.
- **P-XA-2 (0.55) NIE** — i to podwójnie: nie tylko luz interwałów
  (certyfikowane 0.0% przy metodzie POPRAWNEJ — zawieranie 40/40), ale
  znak jest FAKTYCZNIE niestały (21.1% korpusu) — żadna ciasność metody
  nie dałaby ≥80%. **Lekcje kalibracyjne:** (a) twierdzenia o ZNAKU prawa
  sterowania polityki z fazą orbitalną formalizować per FAZA od początku —
  orbitowanie wymaga sterowania stycznego, globalny znak jest strukturalnie
  fałszywy; (b) arytmetyki przedziałowej przez ≥3 warstwy tanh nie
  preregować na pudełkach rzędu p1–p99 całego korpusu — dowozi wyłącznie
  na małych pudełkach lokalnych.
- **P-XA-3 (0.60) NIE** — kandydatka obalona na KAŻDYM ticku założenia.
  **Lekcja kalibracyjna:** własności stabilności preregować PARĄ
  rozstrzygalnych hipotez (kontrakcja kroku = echo vs stabilność okresu =
  generator), nie pojedynczą kandydatką — wtedy różnicówka rozstrzyga,
  zamiast tylko obalać; następca (Floquet) od razu nazwany.
- **P-XA-4 (0.80) TAK** — każdy dowód pada na ≥1 mutancie (T1: M2/M4,
  T2: M5); potwierdzone przez CC niezależnie, pełnokorpusowo dla M2/M4.

Bilans uczciwy: 2/4, przy czym obie porażki to predykcje postawione
z konstrukcji blisko monety (0.55 / 0.60) — kalibracja bez wstydu.

## §4. Wartości trwałe + następcy (KATALOG — nic nie otwieram)

Trwałe: FREEZE_XAI (statusy + zasada cytowania) jako stały punkt cytowań;
atlas XAIR + 2 twierdzenia + 2 kontrprzykłady z mechanizmami; narzędzia
dowodowe wielokrotnego użytku (xai_thm_diff/xai_proofs — wzór dla każdej
przyszłej sieci programu). Nowe pozycje katalogu (trigger: decyzja Olgi):

- **XAI-FLOQUET (T3′):** mnożniki Floqueta cyklu z replay (monodromia =
  iloczyn jakobianów po okresie orbity) — deskowe, 0 bootów; uzbrojone
  liczbą: krokowo max ‖J‖₂ 2.58, pytanie czy widmo monodromii < 1.
- **XAI-ZNAK-PER-FAZA (T4′):** znak ∂y₀/∂sin_brg na pudełkach per faza
  (approach vs orbit) + przedziałówka wyłącznie na małych pudełkach;
  frakcje korpusowe już w ręku.
- **Nakładka demo „co myśli sieć"** — era montażu; wycena z recon aktualna;
  nieprekomitowana.

## §5. CO — zlecenie (lista zamknięta edycji)

1. **Bramka:** `git fetch` → origin/master == **41dcb418**;
   `origin/master..HEAD` puste; porcelain czysty poza nazwanymi ??.
2. **Commit CO-XAI (jeden):** (a) `ANEKS_XAI-1.md` **verbatim do korzenia**
   (ARCH-1: byte-check sha256 z wiadomości CC przy wklejeniu — rozjazd ⇒
   STOP); (b) `KIERUNKI_PO_PLANIE.md` dopisek 27.10 append-only: XAI CLOSED
   ze zdaniem zamrożonym §2, odsyłaczami (RAPORT_XAI_S1, FREEZE_XAI,
   RECON_XAI) i trzema pozycjami §4 z triggerami; (c)
   `results/KSIEGA_PREDYKCJI.md` sekcja NOGA XAI append-only: P-XA-1 TAK
   (0.85), P-XA-2 NIE (0.55) + lekcje (a)(b), P-XA-3 NIE (0.60) + lekcja
   pary hipotez, P-XA-4 TAK (0.80).
3. **ZERO edycji** raportów, RECON-ów, FREEZE i kodu. Komunikat commita:
   wzór CO-WABIK2 (werdykt §2 skrótem + KSIĘGA 2/4 + status §6).
4. **Push = Olga** („wypchnięte" — CC zamyka nogę z repo). STOP.

## §6. Status nogi i programu

Noga XAI: **CLOSED, 0/0 bootów** (recon 0 + S1 0 + CO 0) — pierwsza noga
programu zamknięta przy biurku SUKCESEM po pełnej prerejestracji (WABIK-II
był desk-death; to jest druga strona tej samej monety reżimu). Breach 0 /
REFUSE 0 programowo bez zmian — w tej nodze nic nie latało. Program wraca
do trybu katalogu: TOR-CECHY ∪ MULTI-TARGET, IMITACJE/MIKRO-SYGNATURA,
daleki wzrok (trigger), ODPOWIEDŹ-EKONOMIA, XAI-FLOQUET, XAI-ZNAK-PER-FAZA,
nakładka demo. Warstwa 0 (raport, demo v3.1, pytania pilota) bez zmian;
dopisek XAI do raportu programu = osobna decyzja przy następnej
aktualizacji, nie edycja wstecz.
