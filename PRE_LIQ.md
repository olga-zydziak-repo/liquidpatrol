# PRE_LIQ — prerejestracja nogi LIQ: kontrola architektury (liquid vs rekurencja vs okno)

CC · 29.09.2026 · po RECON_K3 (commit b4f0225). Kryteria, progi i zdania kanonu zamrożone
PONIŻEJ, przed pierwszą epoką treningu i pierwszym bootem. Ratyfikacja Olgi ⇒ PROMPT_LIQ_S1.

**Przemianowanie łańcucha:** kolizja nazwy potwierdzona w recon (SR-K3 w KIERUNKI_SOTA) ⇒
noga nazywa się **LIQ**. RECON_K3 pozostaje ważnym S0 tej nogi (mapowanie jawne: K3→LIQ);
dalej: PROMPT_LIQ_S1/S2/S3, ANEKS_LIQ-n, PRE_LIQ, RAPORT_LIQ, results/LIQ/**. Katalog
results/K3_RECON zostaje jak jest (historia, już zacommitowana).

## §1. Pytanie i ramiona

Kanon NET mówi „20-neuronowa sieć liquid dorównuje nauczycielowi" — i to zdanie wychodzi na
zewnątrz. Recon pokazał, że program NIGDY nie miał uczciwego porównania architektur: stara
kontrola TinyMLP (k=5, h=32) ma **2467 parametrów, +29.6% względem NCP** i mimo tej przewagi
budżetu poleciała 8/48 FAIL — nie była param-matched, więc nic nie rozstrzyga. Ta noga robi
pierwsze związane porównanie. Ramiona (budżety z uruchomionego count_params.py, RECON R2.4):

- **NCP-20** (CfC, 1903 parametry, ncp.npz 0337d5ea) — kanoniczne wagi, BEZ retreningu;
- **GRU h=21** (1956 parametrów, +2.8%) — kontrola rekurencji: czy wystarczy jakakolwiek
  pamięć stanowa o tym budżecie;
- **MLP k=20, h=11** (1939 parametrów, +1.9%) — kontrola okna: czy wystarczy pamięć podana
  wprost konkatenacją 20 ramek, bez stanu.

## §2. Tor treningu kontroli — identyczność jako LISTA (zamrożona)

Nie istnieje „identyczna pętla" między architekturami; zamraża się listę, nie frazes:
cechy = `import bench.features` (9adc1505, ten sam obiekt co w locie); zbiór 114 demonstracji
(44+70), split z kodu TRAIN 81 / VAL 10 / TEST 23; standaryzacja na TRAIN; strata MSE;
Adam+clip z hiperparametrami VERBATIM z zamrożonego configu NCP — S1 wypisuje je w raporcie
PRZED treningiem (echo = freeze); cap 1000 epok (prawo z ANEKS_NET-1 §3.1 przyznane kontrolom
z góry, nie jako naprawa w biegu); seed treningu 1; selekcja checkpointu wyłącznie po VAL;
`numpy==1.26.4` zapisane w raporcie i FREEZE_LIQ.

**Wyjątki architektoniczne (lista zamknięta):** init stanu GRU = zera; wejście MLP-k20 =
konkatenacja 20 ostatnich ramek cech z zero-paddingiem na początku epizodu. NIC więcej.
Brak zbieżności pod capem przy zamrożonych hiperparametrach = WYNIK ramienia, nie licencja
na strojenie (NCP też nie był strojony — config zamrożony przed 1. epoką).

**Bramka offline:** próg pozycji 3 VERBATIM z RAPORT_NET, echo w raporcie S1 przed
treningiem. Ramię bez PASS offline **nie lata**; zdanie kanonu wtedy: „pod zamrożonym torem
treningu NCP kontrola X nie osiągnęła progu offline pozycji 3; porównanie lotne niewykonane".
Z porażki treningowej kontroli NIE wolno robić awansu liquid.

**Dyspersja (opisowa, zero lotów, zero selekcji):** seedy {2,3} trenowane offline dla
wszystkich trzech architektur; wyniki TEST do raportu; pliki wag poza net/frozen/
(results/LIQ/offline_dispersion/). Lata wyłącznie seed 1, a dla NCP — wyłącznie kanoniczne
0337d5ea.

## §3. Loty — trzy ramiona, pełny przeplot

**NCP leci ponownie.** Rozszerzenie względem kosztorysu recon (2 ramiona) jest celowe:
porównanie międzyarchitekturowe musi być współczesne — świeży GRU vs NCP sprzed trzech
tygodni to skład przez czas, dokładnie klasa błędu, którą ta noga ma eliminować. Historyczne
45/48 zostaje kanonem NET i punktem kontroli dryfu ławki (za darmo).

Siatka: te same 48 scenariuszy ławki (scenario_manifest e0527026), 4 epizody/boot ⇒
12 bootów/ramię, **36 bootów kryterialnych** w **12 rundach po 3 booty** (jedna na ramię;
blok 4 scenariuszy stały w rundzie; kolejność ramion rotowana per runda). Ważność = V2′
per boot; boot INVALID ⇒ jedna powtórka (te same scenariusze, to samo ramię); nadal INVALID
⇒ jego scenariusze wypadają PAROWO ze wszystkich ramion. n_common < 40 ⇒ STOP diagnoza.
Osłona uzbrojona jak zawsze; REFUSE w epizodzie = wynik epizodu wg sędziego + wpis (dane
o pełzaniu GRU/MLP są darmowym produktem ubocznym — z_max per epizod per ramię do raportu);
REFUSE(POS) lub breach R_E ⇒ STOP. Sędziowie i features bez JEDNEGO bajta zmian.

## §4. Kryteria, drabina werdyktów, ŚMIERĆ

Δ(X) = pass(NCP) − pass(X) na wspólnych ważnych scenariuszach; progi w licznikach epizodów.
Kolejność rozstrzygania:

- **W0 (przyrząd):** NCP świeże < 40/48 ważnych ⇒ ławka dryfuje, STOP diagnoza, ZERO zdań
  o architekturach.
- **W3 (okno wystarcza):** Δ(MLP-k20) ≤ +2 ⇒ „pamięć oknem wystarcza w tym zadaniu; etykiety
  architektoniczne (liquid, rekurencja) bez poparcia w tej ławce".
- **W2 (rekurencja, nie liquid):** Δ(GRU) ≤ +2 (a nie-W3) ⇒ „kontrola GRU o tym samym
  budżecie dorównała NCP-20; przewaga przypisywalna płynnej dynamice niewykazana —
  wystarcza rekurencja. Etykieta liquid = opis architektury, nie mechanizm przewagi".
- **W1 (liquid-specyficzny):** Δ(GRU) ≥ +6 ∧ Δ(MLP-k20) ≥ +6 (oba ramiona LATAŁY) ⇒
  „na 48 sparowanych scenariuszach (SITL, feed emulowany) NCP-20 przewyższył kontrolę GRU
  o tym samym budżecie i kontrolę okna; pierwszy wynik programu, w którym liquid wskazuje
  mechanizm". Zakres: ta ławka, ten budżet; „liquid > MLP w ogólności" POZOSTAJE zakazane.
- **W4 (nierozstrzygające):** pozostałe układy (szczelina 3–5, albo jedno ramię w W1-strefie
  a drugie nie) ⇒ „różnice poniżej progu rozstrzygalności siatki; bez werdyktu o mechanizmie".
- Kontrola LEPSZA od NCP o ≥3 ⇒ zdanie jawne w kanonie („kontrola X przewyższyła NCP-20"),
  bez łagodzenia.

**KRYTERIUM ŚMIERCI (prereg):** werdykt W2 lub W3 ⇒ etykieta „liquid" trwale zdegradowana
we wszystkich przyszłych materiałach zewnętrznych do opisu architektury z obowiązkowym
zastrzeżeniem („kontrola GRU/okna dorównała w locie"). Bez negocjacji po danych; progi 2 i 6
są zamrożone teraz, w tym dokumencie, zanim istnieje jakakolwiek waga GRU. Nota syntezy NIE
wymaga wtedy retrakcji — jej zdania są opisowe i kanoniczne; zmienia się przyszłość, nie
przeszłość.

## §5. Sonda atrybucyjna pełzania (STOCK) — w tej samej kampanii

Nota z triggerem z ANEKS_W-2 §3, domykana tu: **2 booty**, CONTROLLER=net (0337d5ea),
world_wind_s0 BYTE-IDENTYCZNY, komórka c11, ziarna s01+s02, W_ARM_ALWAYS=1, model **stock
x500_base** (bez kopii enable_wind). Mechanizm: NOWY plik `tools/w_launcher_stock.sh` =
kopia w_launcher.sh minus dźwignia kopii modelu (RECON R2.7), byte-diff w raporcie; locki,
guardy i cooldowny zachowane 1:1; w_launcher.sh nietykalny.

Progi zamrożone: pełzanie **POTWIERDZONE na stock** gdy z_max ≥ 15.0 m w ≥1/2 bootów ⇒
kwalifikator habitatowy SPADA („pełzanie jest własnością ramienia net, także na modelu
stock"). Pełzanie **NIEOBECNE** gdy z_max ≤ 13.0 m w 2/2 ⇒ kwalifikator TWARDNIEJE
(„własność habitatu enable_wind — modelu aerodynamiki — nie sieci"; caption DEMO_V3 @52-68
pozostaje poprawny w obu wypadkach, bo mówi o habitacie wiatrowym). Pomiędzy ⇒
nierozstrzygające, kwalifikator zostaje. REFUSE(GEOFENCE) w sondzie = datum (mocna forma
potwierdzenia), kontynuacja; każde inne REFUSE/anomalia ⇒ STOP. Zadanie biurkowe do S1
(read-only, zero bootów): z_max ramienia net z ISTNIEJĄCYCH trace'ów nogi NET w c11 — trzeci
punkt odniesienia do raportu.

## §6. Budżet i stop-rules

Trening: S1, poza oknami lotów (numpy-only, GPU bezprzedmiotowe). **FREEZE_LIQ** (sha
gru.npz i mlp20.npz + config echo + numpy) commitowany PRZED pierwszym bootem lotnym;
zmiana wag po freeze = nowa noga, nie poprawka. Loty: smoke 2 booty (po 1 na nowe ramię,
1 scenariusz, jawnie niekryterialne — plumbing rejestru, lekcja route→orbit) + kampania 36
+ sonda 2 + powtórki/zapas 4 = **≤44 booty, ≤3 sesje lotne** (S2: smoke + rundy 1–6;
S3: rundy 7–12 + sonda). Przekroczenie któregokolwiek ⇒ STOP i pytanie. Wyłączność maszyny,
cooldowny ≥300 s, manifesty 1. klasy, kind=liq.

## §7. Pliki dotykane (lista zamknięta)

Korzeń: `PRE_LIQ.md` (ARCH-1, pierwszy commit S1). NOWE: pliki treningu kontroli obok toru
NCP (zero edycji istniejących plików treningu); `net/frozen/gru.npz`, `net/frozen/mlp20.npz`,
`net/frozen/FREEZE_LIQ.md`; kontroler(y) nowych ramion; `tools/w_launcher_stock.sh`;
`results/LIQ/**`. JEDNA edycja pliku istniejącego: addytywne wpisy rejestru kontrolerów
dokładnie w miejscu wskazanym w RECON R2.3 (diff verbatim w raporcie S1); wartości
CONTROLLER= dla nowych ramion czytamy Z KODU po edycji i echem w raporcie — PRE ich nie
wymyśla. NIETYKALNE: sędziowie, bench.features, shield i piny 5/5, harness/run_boot.sh,
w_launcher.sh, światy FREEZE_W, ncp.npz, mlp.npz, wszystko w FREEZE_*.

## §8. Predykcje CC (do KSIEGA przy ratyfikacji; moje predykcje nie są priorami)

- **P-LIQ-1:** GRU przechodzi bramkę offline (p≈0.9).
- **P-LIQ-2:** MLP-k20 przechodzi bramkę offline (p≈0.7) — okno 20 ramek może nie unieść
  fazy podejścia, którą stan niesie za darmo.
- **P-LIQ-3:** werdykt = W2 lub W3, czyli ŚMIERĆ etykiety (p≈0.6); W1 p≈0.2; W4 p≈0.2.
  Mechanizm: parytet CfC↔GRU przy małej skali to modalny wynik literatury i Twój własny
  null z LiquidWatch.
- **P-LIQ-4:** sonda: pełzanie NIEOBECNE na stock, 2/2 ≤13 m (p≈0.65) — net trenował na
  plancie stock; enable_wind zmienia równowagę ciągu i pion, którego sieć nie kompensuje.
- **P-LIQ-5:** NCP świeże ≥ 43/48 (p≈0.75).

## §9. Po ratyfikacji

„Ratyfikuję" ⇒ piszę PROMPT_LIQ_S1 (trening + bramka offline + dyspersja + FREEZE_LIQ +
rejestr + zadanie biurkowe sondy; zero bootów lotnych). S2/S3 wg §6. Zamknięcie: RAPORT_LIQ
+ ANEKS_LIQ-n z werdyktem drabiny §4 i rozliczeniem predykcji. Wynik W2/W3 jest tak samo
publikowalny jak W1 — to jest noga, która nie może się nie udać, może tylko powiedzieć
prawdę.
