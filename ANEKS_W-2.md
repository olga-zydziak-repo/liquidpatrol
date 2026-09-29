# ANEKS_W-2 — werdykt nogi W + kanon roszczeń + zamknięcie (CO-W)

CC · 29.09.2026 · łańcuch W (po ANEKS_W-1b). Aneks zamykający i samowykonalny (§6): sesja
wykonuje CO-W i STOP; żadnych bootów — L3 s03 NIE lata.

## §1. Przyjęcie STOP-W2

STOP per S2-C wykonany literalnie po 16/18 — poprawnie: kryterium „każde REFUSE ⇒ STOP" było
zamrożone dokładnie na tę chwilę. Przyjęte bez zastrzeżeń: R-NC gałąź (a) (boot-0 orbit wznosi
się, z_max 12.05, t_entry 17.34 s, V2′ VALID; licznik 1/2), kampania 16 kryterialnych + boot-0
= 17/17 lotnych VALID na V2′ (dsw 0.908–0.960, zero env-fail, zero ponowień), commity 2803aad
+ 15a4f2a (push = Olga), rc=134 bootu STOP = artefakt teardownu po kompletnym locie (precedens
ławki — boot ważny), porcelain czysty.

## §2. WERDYKT NOGI (PRE_W §7, złożenie dwóch gałęzi)

**PASS ramienia dostępności na zmierzonej siatce ∧ ZNALEZISKO PIERWSZEJ WAGI.**

- **(−) dostępność — czysta:** 0 fałszywych REFUSE jakiegokolwiek rodzaju, 0 REFUSE(POS),
  0 breach R_E, dead_reckoning=False 17/17, eph ~0.151 (nominał) na wszystkich poziomach.
  Rdzeń pytania nogi („czy osłona fałszywie odmawia pod szumem świata") ma odpowiedź: NIE,
  w zmierzonym zakresie (wektor stały ≤3 m/s, c11). Komplet siatki wg zamrożonej reguły
  ≥2/3 ważnych ziaren per komórkę JEST spełniony: L3×route 2 ważne (s01,s02), L3×net 2 ważne
  (s01, s02 — epizod REFUSE jest WAŻNY habitatowo, jego wynikiem jest odmowa). s03 nielatane
  wskutek obowiązkowego STOP — zapisane, nie dolatywane (dolatywanie po znalezisku = selekcja).
- **ZNALEZISKO (nie FAIL):** pierwsza w historii programu **aktywna interwencja osłony wobec
  kontrolera uczonego w locie nominalnym** — REFUSE(GEOFENCE) gałęzią pionową NA CELU
  (|tgt_z| > V_E=20 przy pozycji EKF 19.787 — prewencja na komendzie, zanim pozycja przekroczyła
  obwiednię), przy estymatorze zdrowym (|EKF−GT| pion med 0.024 m, dr=False) ⇒ PRAWDZIWY wg
  zamrożonego kryterium. Domknięcie łuku programu: predykat, którego równoważność z modelem
  certu dowiodła noga FV (P8), wykonał pierwszy realny sejw. Zdanie zakazane w RAPORT_NET §11
  („osłona zawierała złą sieć" — ledger pusty 0/132) POZOSTAJE zakazane dla danych NET;
  noga W dostarcza pierwszy zmierzony przypadek aktywnego zawierania — cytuje się go z W.
- ŚMIERĆ nie zaszła (R-NC rozstrzygnęła no-climb jako artefakt modułu infra1); FAIL
  dostępności nie zaszedł.

## §3. Mechanizm zdarzenia — co wolno o nim mówić

Przyczyna: pełzanie wysokości ramienia NCP (uporczywa komenda wznoszenia, cmd_vz med −0.118
przez ostatnie 30 s; profil 8.2→19.78 m w 68 s). Kontekst z siatki: egzekutor trzyma pion
wszędzie (z_max 11.8–12.4); net pełza już przy WIETRZE ZERO (18.45 m, L0/net_s01) — skłonność
jest własnością ramienia net, poziom/ziarno modulują amplitudę. ATRYBUCJA OTWARTA w jednym
punkcie: habitat kampanii różni się od habitatu nogi sieci kopią modelu z `enable_wind`
(opór aerodynamiczny działa także przy wektorze 0), więc „net pełza" wolno twierdzić wyłącznie
z kwalifikatorem „w habitacie wiatrowym"; rozstrzygnięcie = tania sonda (1–2 booty net L0 na
modelu stock) — NOTA Z TRIGGEREM: przed jakimkolwiek zewnętrznym użyciem zdania o pełzaniu
poza tym habitatem. Nie otwieram jej teraz.

## §4. Rozliczenie predykcji (do KSIEGA, sekcja NOGA W)

**P-W-1 ✗ — moja predykcja pada** (0 REFUSE, p≈0.75): chybienie przyniosło główny wynik nogi;
dokładnie po to REFUSE⇒STOP było zamrożone. **P-W-2 ✗** (4.5 armuje — rozstrzygnięte w W-A).
**P-W-5 ✓** (przechył monotoniczny ~3°→~9°→~10–13°, parytet ramion). **P-W-3 i P-W-4 poza
sumą** — nietestowalne: hover @3.0 nie zaistniał (no-climb infra1), siatka L3 przerwana
obowiązkowym STOP (2 pary to za mało na zdanie o ≤2 różnicach netto). Suma nogi: 1✓/2✗
(+2 poza sumą). Kalibracja CC: obie ✗ to przewidywania o zachowaniu środowiska/systemu pod
wiatrem — reguła 9 potwierdzona kolejny raz.

## §5. KANON ROSZCZEŃ W — obowiązujący

**WOLNO** (każde zdanie niesie: SITL, wektor stały, komórka c11, feed emulowany):
- „0 fałszywych odmów jakiegokolwiek rodzaju i 0 REFUSE(POS) w 17 uzbrojonych bootach pod
  stałym wiatrem do 3 m/s; dead_reckoning=False w każdym; kryterium fałszywości (ε_false=2.0 m,
  okno 1 s) zamrożone przed kampanią; baza bezwietrzna programu rośnie do 0 fałszywych odmów
  w 24+17 uzbrojonych epizodach".
- „Zmierzony próg dostępności STARTU jest własnością modułu startu, nie platformy: natywny
  takeoff (infra1) nie wznosi drona od 3 m/s, start offboard pętli ławki wznosi się przy
  3 m/s (boot-0, z_max 12.05)".
- „Osłona wykonała prewencyjną, aktywną interwencję wobec kontrolera uczonego w locie
  nominalnym: REFUSE(GEOFENCE) na KOMENDZIE (|tgt_z|>V_E) przy pozycji 19.79 m < V_E=20
  i zdrowym estymatorze (0.024 m błędu pionu); pełzanie wysokości sieci obecne już przy
  wietrze 0 w habitacie wiatrowym; n=1 wpis — istnienie i mechanizm, nie stopa".
- Sygnatura wiatru na platformie: przechył w zawisie/orbicie monotoniczny z poziomem
  (mediany ~3°/~9°/~10–13°); krzywe degradacji parowane per (poziom, ziarno); net wyżej
  w frac[6,10] w 7/8 par — opisowo, zakaz języka istotności.

**NIE WOLNO:**
- „odporny na wiatr"; czegokolwiek o turbulencji/podmuchach/uskoku z pomiaru wektora stałego;
  stóp niezawodności; ekstrapolacji poza SITL, poziomy {0, 1.5, 3} i komórkę c11.
- „sieć niebezpieczna" — net nie naruszył koperty (breach 0); to degradacja MISJI zawarta
  prewencyjnie przez osłonę. Symetrycznie: z n=1 nie wolno robić „osłona zawiera złe sieci"
  jako stopy.
- przypisywać pełzania wysokości wiatrowi (obecne przy L0) ani sieciom w ogólności
  (kwalifikator habitatowy §3 obowiązuje do rozstrzygnięcia notą z triggerem).

## §6. Zlecenie CO-W — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` = dokładnie {2803aad, 15a4f2a} ⇒ prośba o push, po
potwierdzeniu dalej; puste ⇒ dalej; inny stan ⇒ STOP. Pliki dotykane (lista zamknięta):
- korzeń: `ANEKS_W-2.md` (ARCH-1, procedura C0);
- NOWY `results/W/RAPORT_W.md`: §1 werdykt §2 verbatim; §2 zdarzenie (liczby, klasyfikacja,
  mechanizm §3 z kwalifikatorem habitatowym i notą z triggerem); §3 siatka i krzywe (odsyłacz
  do RAPORT_W_S2 §2, przechył per poziom); §4 R-NC i doprecyzowanie H2 (no-climb = artefakt
  infra1); §5 kanon §5 verbatim z nagłówkiem „KANON OBOWIĄZUJĄCY — ANEKS_W-2"; §6 rozliczenie
  predykcji §4; §7 odchylenia nogi (errata route→orbit ANEKS_W-1b, crash 20.09 poza budżetem,
  rc=134 nota, `.last_boot_end`); §8 odsyłacz krzyżowy do RAPORT_NET §11 (zdanie o zawieraniu
  — skąd wolno cytować);
- EDYCJA `results/KSIEGA_PREDYKCJI.md`: sekcja NOGA W wg §4 (1✓/2✗, dwie poza sumą
  z przyczynami);
- INDEKS: `git rm --cached results/INFRA3/.last_boot_end results/K1/.last_boot_end`
  (dokończenie ratyfikowanego ANEKS_REPO-1a §4 — te same racje co wykonane już w S2 dla
  `results/.last_boot_end`, które niniejszym PRZYJMUJĘ).
Raport płaski: diff-stat, pełna treść RAPORT_W.md, porcelain. STOP. Push = Olga.

## §7. Status i dalej

**Noga W: CLOSED — PASS + znalezisko** z chwilą commita CO-W i pushu (linia skuteczności CC
niewymagana; odchylenie przy CO-W ⇒ pytanie przed wpisem). Budżet zamknięty na 17/27 lotnych.
Po pushu program wraca do trybu katalogu; nic nie otwieram — nota syntezy zyskuje rozdział
o dostępności i pierwszy sejw osłony, nota-z-triggerem (sonda atrybucyjna pełzania) czeka na
decyzję przy następnym wyborze z kolejki.
