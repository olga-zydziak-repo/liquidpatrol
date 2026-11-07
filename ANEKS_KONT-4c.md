# ANEKS_KONT-4c — po STOP-KONT4-BUDZET: diagnoza inicjalizacji estymatora przy biurku (yaw 141.6°, bias 0.07–0.11), mitygacja = wymuszony restart EKF2 w preflight pod warunkiem z diagnozy, kontrola yaw przed intruder_motion, rezerwa do ratyfikacji

CC · 8.11.2026 · łańcuch KONT, po STOP-KONT4-BUDZET (commity b79ffb14,
31478732 — bramka tego aneksu wymaga ich na origin). Zero bootów do
§4. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP i zakres weryfikacji CC

STOP po regule 4b prawidłowy (nieważny boot przy wyczerpanej rezerwie).
Liczby raportu (yaw 51.6°/13.3°, EKF heading 141.6° płasko, bias 0.107
z filter_fault / 0.073) CC zweryfikuje z ulogów przy pushu diagnozy —
rozstrzygnięcia poniżej są proceduralne i nie wprowadzają tych liczb do
kanonu. Wada wykonawcy (kontrola yaw po starcie intruder_motion ⇒
sierota przy przerwaniu) nazwana, do KSIĘGI przy zamknięciu nogi.

## §2. D5-diag — diagnoza przy biurku (0 bootów; ulogi S4 i S2 z dysku)

Pytanie: skąd zepsuty heading na starcie i czy restart EKF2 go czyści.
Z ulogów nom_b1, nom_b1_r2, nom_b2 kontra 3 booty s2y (S2-Y) i booty
S2 z restartem watchdoga (c11_s04_r3, c00_s02_r3):

1. **yaw(t) od startu PX4**: wartość inicjalna, czy stoi płasko (brak
   fuzji) czy dryfuje; moment i skutek ewentualnego reinitu watchdoga
   (w S2 reinit dawał bias 0.128 → 0.0002 i poprawny yaw — czy tu
   reinit był, a jeśli był, czy heading po nim dalej zły).
2. **Fuzja magnetometru**: flagi cs_mag_hdg/cs_mag_3d/mag_fault,
   innowacje mag, EKF2_MAG_TYPE i pokrewne (nazwy z metadanych ulogu,
   nie z pamięci).
3. **Bias startowy vs faza dołączenia**: zestawienie wszystkich bootów
   s2y/s4 (faza, pierwsza próbka bias, pierwsza próbka yaw, znacznik
   pierwszej próbki IMU) — hipoteza do sprawdzenia: przy dołączeniu
   PX4 ~7.5 s czasu symulacji pierwsze próbki sensorów niosą skok
   znaczników i inicjalizacja estymatora je zjada. S1/SKAN2/PERC2
   (stary launcher, dołączenie 0.016–0.43 s) jako kontrola.
4. **Różnice toru S4 vs S2 przed kontrolą** (selfcheck jako proces,
   intruder_motion, preflight) — wykluczyć pomiarem (czasy procesów
   vs okno inicjalizacji EKF), nie deklaracją.

**Wynik jednym zdaniem** + werdykt warunkowy:
- **W-R:** ulogi pokazują, że reinit EKF2 czyści heading i bias
  (dowód z S2 albo z nom_b1_r2, jeśli watchdog tam działał) ⇒ §3
  wchodzi w życie bez dodatkowej sondy.
- **W-N:** reinit nie czyści albo dowodu brak ⇒ STOP-KONT4c z raportem
  diagnozy, bez zmian drivera; CC decyduje dokumentem (kandydat:
  jedna sonda bootowa z reinitem, poza siatką).

## §3. Mitygacja (wchodzi tylko przy W-R; zmiana drivera dokumentem —
tym)

- **Preflight drivera**: po settle wymuszony restart EKF2 tym samym
  mechanizmem, którego używa watchdog (cytat narzędzia/komendy
  z istniejącego kodu watchdoga, nie nowy wynalazek), odczekanie
  konwergencji, potem istniejąca kontrola |błąd yaw| ≤ 10° i bias
  poniżej progu watchdoga; maks. 2 podejścia, potem boot nieważny.
  Kontrola yaw i bias **przed startem intruder_motion** (pkt 3
  wykonawcy — zatwierdzone; usuwa też sierotę).
- Asercja pozostaje ostateczną bramką — mitygacja nie luzuje progu 10°.
- **Nowy STOP:** 2 kolejne booty nieważne na asercji MIMO mitygacji ⇒
  STOP-KONT4-STANOWISKO (nie palić budżetu w pętli).
- Wartości reinitu i yaw per boot w manifeście i wyciągu ulogu.

## §4. Budżet — do ratyfikacji jednym słowem

Zostało 14 bootów przy 15 pozycjach siatki. **„ratyfikuję 4c"** ⇒
S4 ≤ 20 łącznie (3 zużyte + 12 cięć + 3 nominały + 2 rezerwy);
noga maks. 44/45, limit PRE ≤ 45 nietknięty. Bez ratyfikacji ⇒ S4
zostaje ≤ 17 (14 na 15 pozycji — braknie 1 boota: wtedy pierwszy
nominał łączy się z doleceniem tylko przez skrócenie siatki, czego
nie robimy — realnie oznacza to STOP budżetu przed końcem siatki).
Rekomendacja CC: ratyfikować; przyczyny zużycia rezerw są nazwane
(driver ROOT, stanowisko), żadna nie jest miarą hipotezy.

## §CO

Bramka: origin/master == **31478732** (push obu commitów przed
startem). Commit 1: korzeń `ANEKS_KONT-4c.md` verbatim (byte-check
sha256 z wiadomości CC). Potem D5-diag (narzędzia i wyniki w
`results/KONT/s4/d5diag/`), raport krótki
`results/KONT/s4/RAPORT_KONT_S4_D5.md` z werdyktem W-R/W-N; przy W-R
commit mitygacji (§3) i dalej booty: nom_b1_r3, nom_b2_r2, nom_b3,
cięcia wg siatki; przy W-N STOP. Push = Olga. **CC przy najbliższym
pushu weryfikuje też liczby STOP-KONT4-BUDZET z ulogów.**
