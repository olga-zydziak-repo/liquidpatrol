# ANEKS_LIQ-2 — werdykt nogi LIQ + rozstrzygnięcie sondy + kanon roszczeń + zamknięcie (CO-LIQ)

CC · 03.10.2026 · łańcuch LIQ (po STOP-LIQ3, commit 6ea3013 na origin). Aneks zamykający
i samowykonalny (§6): sesja wykonuje CO-LIQ i STOP; zero bootów — loty nogi zakończone.

## §1. Przyjęcie STOP-LIQ3

Przyjęte po NIEZALEŻNEJ weryfikacji CC wprost z repo: zliczenia sędziego przeliczone
z 24 manifestów kampanii (per epizod: success_D6, valid_V2p, refuse_count, breach) —
**zgodne z raportem co do epizodu**: NCP 43/48, GRU 27/48, 48/48 ważnych w obu ramionach,
parowanie identyczne co do zbioru 48 scenariuszy, REFUSE 0, breach 0; zbiór FAIL-i obu
ramion i 4 scenariusze oblane wspólnie — identyczne. Sonda: manifesty potwierdzają świat
`world_wind_s0` = FREEZE_W (921bdda7, byte-identyczny), CONTROLLER=net 0337d5ea,
arm_monitor=True, dowód stock w obu bootach; z_max 13.10/14.26 przyjęte z raportu (źródło:
demo.jsonl, metodologia spójna z zadaniem biurkowym S1). Launcher 7324f850 bez zmian od S1
(byte-check), driver 43b8d2dd bez zmian od S2, kod repo nietknięty. Przyjęte odchylenia:
transientny lock `results/W/.executor_lock` (zdejmowany trapem, niecommitowany — lista
zamknięta dotyczy plików commitowanych); nota r11_ncp (szum teardownu MAVSDK po epizodach,
precedens F2). Wykonanie S2+S3: 27 bootów, 0 powtórek, 0 INVALID — czyste.

## §2. WERDYKT DRABINY (progi zamrożone w PRE_LIQ §4 i ANEKS_LIQ-1 §4, przed treningiem)

- **W0 — przyrząd trzyma:** NCP świeże 43/48 ≥ 40/48; dryf względem kanonu NET (45/48)
  w granicach szumu 48-epizodowej próby.
- **W2 — ŚMIERĆ NIE ZASZŁA:** Δ(GRU) = 43−27 = **+16** przy progu śmierci ≤ +2.
- **W3 — nieewaluowalne w locie** (kontrola okna odpadła offline); kierunek offline
  przeciwny tezie okna (0–1/24).
- **W1 pełne — niewykonalne** w tej nodze (wymagało obu kontroli w locie).
- **⇒ WERDYKT: W1′**, zdaniem zamrożonym w ANEKS_LIQ-1 §4: „NCP-20 przewyższył kontrolę
  rekurencji o tym samym budżecie (Δ≥6/48 par); kontrola okna odpadła offline — przewaga
  nad GRU wykazana, pełna izolacja mechanizmu liquid wymagałaby latającej kontroli okna."
  Wynik nie jest brzegowy: próg W1′ wynosił +6, zmierzono +16; kierunkowość par
  niezgodnych 17:1 (GRU wygrał parę wyłącznie na c11_s02).

Mechanizm przewagi (opisowo, bez języka istotności): FAIL-e GRU w 19/21 niosą gałąź
c_sweep (17 czysto + 2 z d_dmin) — kontrola rekurencji systematycznie traci pokrycie
orbity; do tego pełza wyżej (z_max do 16.8 m vs NCP ≤ 13.8 w kampanii). FAIL-e NCP to
4× d_dmin + 1× b_frac+d_dmin, z czego 4 scenariusze (c07_s02, c09_s02, c09_s03, c10_s04)
oblały OBA ramiona — trudność scenariusza, nie ramienia. Słaby scenariusz NCP: c11_s02
(FAIL na ławce, FAIL(b_frac) w sondzie) — wpis opisowy, spójny z epizodem sejwu nogi W
(ta sama konfiguracja geometrii).

## §3. Sonda STOCK — rozstrzygnięcie

**NIEROZSTRZYGAJĄCE** wg progów ANEKS_LIQ-1 §3 (zamrożone przed pomiarem): s01 13.10 ≤ 14.0,
ale s02 14.26 w przerwie 14.0–15.0; żaden boot ≥ 15.0. **Kwalifikator habitatowy ZOSTAJE** —
zdanie o pełzaniu NCP nadal wolno wypowiadać wyłącznie jako „w habitacie wiatrowym
(model enable_wind)". Nota opisowa do kanonu: rozszczepienie per ziarno — na s01 habitat
enable_wind dokłada +5.35 m (18.45 vs 13.10), na s02 różnica znika (14.43 vs 14.26);
modulacja habitatu jest silnie zależna od ziarna. Nota-z-triggerem z ANEKS_W-2 §3 zostaje
ZAMKNIĘTA wynikiem „nierozstrzygnięte przy 2 bootach"; ewentualne poszerzenie sondy to
osobna pozycja katalogu, nie kontynuacja tej nogi.

## §4. KANON ROSZCZEŃ LIQ — obowiązujący

**WOLNO** (każde zdanie niesie: SITL, ławka 48 sparowanych scenariuszy, feed emulowany,
budżet ~1.9k parametrów, zamrożony tor treningu NCP):
- „NCP-20 (CfC, 1903 parametry) przewyższył param-matched kontrolę GRU (1956): 43/48 vs
  27/48 na 48 wspólnych ważnych parach (Wilson 95%: [0.778, 0.955] vs [0.423, 0.693]);
  architektury, tor treningu, progi i kryterium śmierci zamrożone przed treningiem kontroli."
- „FAIL-e kontroli GRU są zdominowane jedną gałęzią (pokrycie orbity, 19/21); GRU wykazuje
  też silniejsze pełzanie wysokości (do 16.8 m vs ≤13.8 u NCP), bez naruszeń koperty —
  degradacja misji, nie bezpieczeństwa (0 REFUSE, 0 breach w 96 epizodach kampanii)."
- „Param-matched kontrola okna (MLP k=20, 1939 par.) nie osiągnęła progu offline
  (0–1/24 rolloutów na trzech ziarnach init) przy NAJLEPSZYM val-MSE z trzech architektur —
  rozjazd model-punktowy↔rollout widoczny już offline."
- „Pierwszy kontrolowany wynik liquid-dodatni programu; odwraca null LiquidWatch
  (CfC vs GRU) w pętli lotu, z prerejestracją i parowaniem."
- Zdanie W1′ verbatim (§2).
- Pełzanie NCP: wyłącznie z kwalifikatorem habitatowym (§3), z notą o rozszczepieniu
  per ziarno.

**NIE WOLNO:**
- „liquid > MLP w ogólności" (trwale; k=20/h=11 i k=5/h=32 to dwa punkty przestrzeni);
- „liquid lepszy w zadaniach sterowania" ani jakiejkolwiek generalizacji poza tę ławkę,
  budżet i tor; stóp niezawodności z 48 epizodów; języka istotności;
- przypisywać przewagi „płynnej dynamice" jako wyizolowanemu mechanizmowi — izolacja
  niepełna (okno nie latało); wolno: „przewaga nad rekurencją GRU przy tym budżecie";
- „GRU niebezpieczny" — breach 0; symetrycznie: z porażki treningowej MLP-k20 nie wolno
  robić dowodu mechanizmu liquid;
- wnioskować z sondy w którąkolwiek stronę (wynik nierozstrzygający).

## §5. Rozliczenie predykcji (do KSIĘGI, sekcja NOGA LIQ)

**P-LIQ-1 ✓** (GRU offline PASS). **P-LIQ-2 ✗** (MLP-k20 offline PASS, p≈0.7 — padł).
**P-LIQ-3 ✗ — moja predykcja modalna pada** (W2∪W3 p≈0.6; zaszedł wariant klasy W1,
któremu dawałem 0.2). **P-LIQ-4 ✗** (sonda NIEOBECNE p≈0.65 — wyszło nierozstrzygające;
s02 nad progiem). **P-LIQ-5 ✓** (NCP ≥ 43/48 — dokładnie na progu). **Suma nogi: 2✓/3✗.**
Kalibracja CC, wpis do księgi błędów: wszystkie trzy ✗ mają TEN SAM kierunek —
niedoszacowanie wyników komponentu uczonego/liquid; łącznie z nogą W (P-W-1, P-W-2) to
pięć chybień w jedną stronę przy zerze w drugą. Reguła 9 (predykcje CC nie są priorami)
potwierdzona i zaostrzona: w ocenach jakościowych stosuję korektę na udokumentowany
kierunek błędu.

## §6. Zlecenie CO-LIQ — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP. Pliki dotykane
(lista zamknięta):
- korzeń: `ANEKS_LIQ-2.md` (ARCH-1, verbatim, pierwszy w commicie);
- NOWY `results/LIQ/RAPORT_LIQ.md`: §1 werdykt W1′ (zdanie verbatim + drabina §2 tego
  aneksu); §2 liczby kompletu (tabela 48 par per ramię, gałęzie FAIL, kierunkowość par
  17:1, z_max zakresy, Wilsony); §3 bramka offline i kolaps MLP-k20 + dyspersja (odsyłacz
  RAPORT_LIQ_S1 §3); §4 sonda (progi, wynik, rozszczepienie per ziarno, status
  kwalifikatora, zamknięcie noty-z-triggerem ANEKS_W-2 §3); §5 kanon §4 verbatim
  z nagłówkiem „KANON OBOWIĄZUJĄCY — ANEKS_LIQ-2"; §6 rozliczenie predykcji §5;
  §7 odchylenia nogi (errata progu sondy 13.0→14.0 ANEKS_LIQ-1 §3 z historią; mapowanie
  lr dla MLP-k20 — nota z RAPORT_LIQ_S1 §1; teardown r11_ncp; lock W transientny);
  §8 odsyłacze krzyżowe (RAPORT_NET §11 — relacja kanonów NET↔LIQ; RAPORT_W §2/§5 —
  c11_s02 i kwalifikator pełzania);
- EDYCJA `results/KSIEGA_PREDYKCJI.md`: sekcja NOGA LIQ wg §5 (2✓/3✗ z przyczynami
  i notą kierunku błędu CC).
Raport płaski: diff-stat, pełna treść RAPORT_LIQ.md, porcelain. STOP. Push = Olga.

## §7. Status i dalej

**Noga LIQ: CLOSED — W1′** z chwilą commita CO-LIQ i pushu. Budżet zamknięty na 27/31
bootów, 0 powtórek, kod repo nietknięty poza ratyfikowaną dopiską rejestru (S1). Program
wraca do trybu katalogu; kolejka ustalona wcześniej bez zmian: **warstwa 0** (nota —
zyskuje teraz akapit LIQ; follow-up SPRIND — „video available" + najmocniejsze zdanie
programu świeżo wzmocnione), potem **2a**. Nowe pozycje dopisane do katalogu w rozmowach
3.10 (NN-weryfikacja sieci, VIO/denial-continuation, pokaz przenośności klatki) czekają
na regularny wybór — żadna nie jest otwarta.
