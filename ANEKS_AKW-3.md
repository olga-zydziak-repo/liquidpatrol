# ANEKS_AKW-3 — ŚMIERĆ-AKW wg progu zamrożonego + kanon obu prawd + KSIĘGA + zamknięcie (CO-AKW)

CC · 11.10.2026 · łańcuch AKW (po STOP-AKW3, commity c9149e93→cfee6722 na origin).
Aneks zamykający, samowykonalny (§7): sesja wykonuje CO-AKW i STOP; zero bootów —
loty nogi zakończone na 29/≤32.

## §1. Przyjęcie STOP-AKW3

Przyjęte po weryfikacji CC z repo wykonaniem: ARCH-1 bajt-w-bajt (e1900f1b…); zakres
commitów = korzeń + results/AKW/**; liczniki przeliczone NIEZALEŻNIE z akw_pairs.json:
n_common 48, pass(B) 46, pass(V2+skan) 34, **Δ_new = 12**; dekompozycje odtworzone:
bearingi 3/3/3/3, prędkości 1/2/9, saldo vs DET **+24/−3** z regresjami dokładnie
c08_s02/s03/s04; refuse 0/0; z telemetrii per boot: **10 bootów wolnomodowych,
admisja ślepe@FOV 96.1–99.0%, nigdy zero** — bezpiecznik modu bez tripa. Odchylenia
przyjęte: pad hosta między r7_B a r7_V2 (narzędziowe; zero artefaktów, wznowienie
czyste, koszt 1 launch); r12_B nieważny → powtórka ważna (zapas 1/3); kroki liczone
z fizycznego yaw (nie pól nominalnych) — zgodnie z notą S2. Wykonanie wzorcowe.

## §2. WERDYKT KAMPANII — ŚMIERĆ-AKW (zdanie zamrożone PRE_AKW §5 / PRE_2A §4)

**Δ_new = 12 ≥ 10 ⇒ ŚMIERĆ-AKW: „skan nie wystarcza — akwizycja nie była jedynym
ogniwem."** Próg był zamrożony przed pierwszym lotem nogi; liczby się z nim nie
targują. Obowiązkowa dekompozycja przy każdym cytowaniu:

- **Luka GEOMETRYCZNA akwizycji jest DOMKNIĘTA:** Δ po bearingach 3/3/3/3 (wzorzec
  DET: cały deficyt w bearing≠0); **24 z 35 ślepych porażek DET przechodzi**; koszt
  akwizycji deterministyczny (p50 1/4/6 kroków dla 90/180/270°).
- **Rezyduum siedzi w CELU SZYBKIM:** v=1.0 niesie 9 z 12 Δ (v=0: 1; v=0.5: 2).
  ENTRY zachodzi niemal wszędzie (klasy F1_cel, **F3=0 w całej kampanii**) — pada
  budżet D6 PO akwizycji, nie percepcja.
- **Mechanizm regresji (c08_s02/s03/s04, bearing 0 + v=1.0):** po utracie szybkiego
  celu skan rusza od ψ_last — kierunkowo ŚLEPY (7–13 kroków reakwizycji), choć
  kontrakt feedu od zawsze niesie trk_vel_ned, którego re-akwizycja nie czyta.
- **ΔΔ = 34 − 12 = 22** — największa pojedyncza poprawa programu; ZAWSZE
  z kwalifikatorem dwóch kampanii (ten sam habitat/siatka; świeże B 46/48 vs 47/48
  jako kontrola dryfu — obie nowe porażki B to v=1.0 i padły też w V2).
- **Ryzyko wolnego modu ZAMKNIĘTE POMIAREM** (10 bootów, 96.1–99.0%, nigdy zero) —
  prereg-bezpiecznik zarobił na siebie bez odpalenia.

## §3. WERDYKT NOGI AKW (całość — trzy rzeczy zmierzone, każda z mechanizmem)

1. **Mechanizm admisji pod rotacją zlokalizowany:** zmienna sprawcza ω·dt [°/klatkę],
   ogniwo = persystencja MTI nad celem transitującym kadr (fail_mti 70–95%; śledzenie
   toleruje ≥4.5°/kl); profil krokowy 40°/1.2 s omija go KONSTRUKCYJNIE — admisja
   98.4% (szybki mod) i 96–99% (wolny), vs 0/235 ciągłego @3.96°/kl.
2. **Skan krokowy domyka lukę geometryczną akwizycji** (dekompozycje §2) — pierwszy
   raz w programie D6 przechodzi na wszystkich bearingach; dron realnie znajduje cel,
   którego nie widział na starcie, w 9–16 s.
3. **Kampania powtórkowa 48/48 par wykonana i rozstrzygnięta progiem zamrożonym:
   ŚMIERĆ-AKW** — następne ogniwo nazwane co do mechanizmu i co do danych (dynamika
   celu szybkiego; re-akwizycja kierunkowo ślepa). Bezpieczeństwo: **breach 0 /
   REFUSE 0 w 25 uzbrojonych bootach nogi**; prawda programu (0/0 we wszystkim, co
   kiedykolwiek poleciało uzbrojone) utrzymana.

**Noga AKW: CLOSED — „luka geometryczna domknięta zachowaniem; skan nie wystarcza na
cel szybki; następne ogniwo: re-akwizycja kierunkowa".**

## §4. KANON ROSZCZEŃ AKW — obowiązujący

**WOLNO** (kwalifikatory DET w całości + „akwizycja skanem krokowym 40°/1.2 s"):
- zdania 1–3 z §3 verbatim, z liczbami;
- „dron lata na kamerze w 34/48 scenariuszy pełnej geometrii (wyrocznia 46/48);
  rezydualne ogniwo = cel szybki, nie percepcja" — zdanie ZAWSZE z kwalifikatorem
  dynamiki celu;
- „ΔΔ=22 (34→12)" wyłącznie z kwalifikatorem dwóch kampanii i z jawnym Δ_new=12;
- „ryzyko wolnego modu zamknięte pomiarem (10 bootów, 96–99%, nigdy zero)";
- mechanizm c08 z trk_vel_ned jako nazwana droga dalej.

**NIE WOLNO:**
- „skan wystarcza" / „akwizycja rozwiązana" jako całość — ŚMIERĆ-AKW obowiązuje;
- „dron lata na kamerze" bez kwalifikatora dynamiki celu;
- przypisywać rezyduum detektorowi/percepcji (ENTRY F1 wszędzie, F3=0) ani osłonie
  (nie interweniowała: REFUSE 0);
- cytować ΔΔ bez Δ_new; porównań międzykampanijnych bez kwalifikatora;
- ekstrapolacji na realne sensory/warunki (PRE_2A §4 verbatim).

## §5. Rozliczenie predykcji (do KSIĘGI, sekcja NOGA AKW)

**P-AKW-1 ✗** (0.50; smoke padł na pierwszym profilu) · **P-AKW-2 ✓** (0.70; FP tła 0
w całej nodze, F3=0 w kampanii) · **P-AKW-3 ✗** (0.60; Δ_new=12 zamiast ≤4) ·
**P-AKW-4 ✓** (0.80; pass(B) dokładnie 46/48) · **P-AKW-5 ✓** (0.85; REFUSE 0).
**Suma: 3✓/2✗.** Kalibracja CC, wpis: TRZECI kolejny przestrzał wyniku systemowego
(2A → DET-5 → AKW-3), tym razem dokładnie w interakcji NAZWANEJ-A-NIEZMIERZONEJ
(recon R5.8: „intruz ruchomy × skan — desk nie rozstrzyga"). Doprecyzowanie reguły
kalibracyjnej: predykcja wyniku systemowego z nazwaną-a-niezmierzoną interakcją
dostaje korektę w dół GŁĘBSZĄ niż standardowa (nie ≈0.6, raczej ≈0.4–0.5), dopóki
interakcja nie ma pomiaru choćby sondą.

## §6. Rejestr odchyleń nogi (do RAPORT_AKW §7)

Błąd jednostki CC — zamrożono ω zamiast ω·dt (ANEKS_AKW-1 §3, klasa nowa); edycja
ratyfikowanego dokumentu przy ARCH-1 S1 (naprawiona amendem przed pushem); launch
przed promptem (reguła wzmocniona); ODMOWA decymacji rekordów bez klatek (dobra
praktyka, nazwana fałszerstwem wprost); rozbicie locked/unlocked wymuszone danymi;
pola nominalne analyzera (prawda = yaw_ulog); pad hosta r7 (narzędziowy); powtórka
r12_B (zapas 1/3); pole scan_dps_frozen historyczne od S2.

## §7. Zlecenie CO-AKW — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista
zamknięta): korzeń `ANEKS_AKW-3.md` (ARCH-1, verbatim, pierwszy w commicie); NOWY
`results/AKW/RAPORT_AKW.md`: §1 werdykt §3 verbatim; §2 łańcuch S0→S3 z liczbami
(recon/PRE/S1 smoke-FAIL z mechanizmem ω·dt/S2 desk+profil II+re-smoke/S3 kampania,
odsyłacze); §3 kampania — Δ_new, dekompozycje §2, tabela 48 par przez odsyłacz;
§4 mechanizmy (ω·dt + MTI-persystencja; regresje c08 + trk_vel_ned); §5 kanon §4
verbatim z nagłówkiem „KANON OBOWIĄZUJĄCY — ANEKS_AKW-3"; §6 predykcje §5;
§7 odchylenia §6; §8 roadmapa: **RE-AKW (re-akwizycja kierunkowa)** jako pozycja
katalogu z triggerem „przed roszczeniem pełnej geometrii z celem szybkim": dwell +
obrót w kierunku ekstrapolowanym z trk_vel_ned (dane już w kontrakcie feedu) przed
wznowieniem pełnego skanu — jedno zachowanie w TYM SAMYM wrapperze; aktywa: 3 regresje
c08 + 14 porażek V2 jako zbiór odniesienia, dwie kampanie-wzorce, profil II FROZEN
b94cdeae, cała ewaluacja. EDYCJE: `results/KSIEGA_PREDYKCJI.md` — sekcja NOGA AKW
wg §5 (3✓/2✗ + doprecyzowanie reguły); `KIERUNKI_PO_PLANIE.md` — AKW → CLOSED
z odsyłaczem, dopisana pozycja RE-AKW z triggerem. Raport płaski: diff-stat, pełna
treść RAPORT_AKW.md, porcelain. STOP. Push = Olga („wypchnięte").

## §8. Status i dalej

**Noga AKW: CLOSED** z chwilą commita CO-AKW i pushu. Bilans: 29/≤32 bootów, 3 sesje
lotne + 2 deski, 3 dni; przyniosła: zlokalizowany mechanizm admisji pod rotacją,
pierwszą akwizycję ze skanu w historii programu, domkniętą lukę geometryczną
(ΔΔ=22) i uczciwą śmierć progu zamrożonego z nazwanym następnym ogniwem. Program
wraca do trybu katalogu; breach 0 / REFUSE 0 pozostaje prawdą o wszystkim, co
kiedykolwiek poleciało uzbrojone. Rekomendacja jawna już teraz: **RE-AKW** ma
najkrótszą ścieżkę (jedno zachowanie w istniejącym wrapperze, zero nowych komponentów,
ewaluacja i wzorce gotowe) od 34/48 do pytania „ile naprawdę zostało". Wybór nogi
należy do trybu katalogu.
