# ANEKS_SKAN2-1 — SKAN-II zamknięta werdyktem V-A: przegląd przeliczony na kadencję 14.7 Hz przyjmuje najgorszy azymut przed zamknięciem pasa admisji, T6 bez wiatru 6/6 (CO-SKAN2)

CC · 2.11.2026 · łańcuch SKAN2, po STOP-SKAN2-1 (c3a6d7ff na origin).
Aneks zamykający nogę i wątek akwizycji, samowykonalny (§5). Sesja CO
deskowa, zero bootów. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-SKAN2-1 — weryfikacja CC z repo

Zakres: 100 plików, +168457/−0, wszystko w `results/SKAN2/**`. Kod i rejestr
weszły wcześniej w 522c544c (2 linie rejestru, nowy `skan2_scan.py`).
akw_scan b94cdeae i fantom_scan e435ed7e nietknięte; PRE_SKAN2 7305f4d7,
ANEKS_SKAN2-0 b1d4d77a i ANEKS_SKAN2-0b w korzeniu. Wrapper zgodny z literą
PRE §2: CC policzył profil niezależnie, +273.1° osiągnięte 6.752 s po wejściu
w hold.

Przeliczenie niezależne CC, własnym kodem z surowych logów (sędzia 8ec0fcfb
importem, D9/V2′, świadek ERRATUM-DMIN jako filtr wierszy gt_intruder; t_acq
semantyką F1_cel z GT manifestu), obu kampanii na tej samej siatce:

- **c11_s02 / s03 / s04:** t_acq 6.85 / 6.83 / 7.31 s, D6 pełny i ze świadkiem
  PASS 3/3, d_min (świadek) 7.16 / 6.75 / 6.68 m. Linia bazowa net_fantom
  (PERC2 S2): 12.23 / 12.31 / 24.97 s, D6 0/3, d_min 0.96 / 1.34 / 1.75 m.
- **c10_s02:** 4.42 s, PASS (baza 8.78 s, PASS).
- **c08_s01…s04:** 0.78 / 0.16 / 0.10 / 2.09 s, D6 4/4 (baza 0.72 / 0.27 /
  0.31 / 0.10 s; ze świadkiem 4/4).
- V2′ 8/8 ważne. Breach 0, REFUSE 0.
- Fałszywe admisje: 0 ENTRY z błędem > 5 m. CC znalazł dwa wiersze `fresh`
  z błędem 11 i 22 m (c11_s03, c08_s02), oba w t = 0.04–0.05 s od t0. To
  track z poprzedniego epizodu, nie ENTRY; FANTOM wygasza go dla sterowania.
  Kryterium PRE (ENTRY) stoi.
- Zgadza się z raportem wykonawcy co do setnej.

## §2. Werdykt V-A i rozstrzygnięcie interpretacji c08

Wykonawca wydał mechanicznie V-C przez jeden człon (c08_s04 t_acq 2.09 s >
1.0 s), nazwał interpretację przed lotami i zostawił rozstrzygnięcie CC.
**Rozstrzygnięcie: V-A.**

1. **Litera.** PRE §1 Q2 definiuje kontrole: „c08_s01 / c08_s02 … i c10_s02”.
   Człon V-A „kontrole: c08 t_acq ≤ 1.0 s” i człon V-C „regresja kontroli”
   odnoszą się do tego zbioru. c08_s03 i c08_s04 są epizodami T6, a T6 PRE mierzy
   egzaminem D6 („T6 bez wiatru a/6”): 6/6. Szersze odczytanie bierze się
   z P-SK2-4 („c08 (4 epizody)”), które jest predykcją, nie kryterium.
   Niejednoznaczność zapisu jest winą CC i idzie do KSIĘGI (§4).
2. **Mechanizm, sprawdzony z logów przez CC.** W PERC2 S2 epizod c08_s04 zaczął
   się z żywym trackiem z poprzedniego epizodu, który cel przechwycił: fresh
   na celu od 0.15 s, wyjście kwarantanny przez K1-B po 0.10 s. W SKAN2 tracka
   w t0 nie było: zero fresh do 2.12 s, wyjście przez K1-A po 2.09 s. Przez
   pierwszą sekundę oba profile robią to samo (nos stoi na ψ = 0), więc różnica
   powstaje przed jakąkolwiek różnicą profilu. To stan startu, nie skan.
   Z profilem FROZEN (dwell 2.0 s) ten sam start dałby admisję najwcześniej
   w rampie po 2.0 s, czyli później niż 2.09 s. Raport wykonawcy: 21 klatek
   stojącego nosa z celem czołowo w stożku, koincydencja 0/22.
3. Pozostałe człony V-A spełnione: c11 3/3 ≥ 2/3, t_acq ≤ 10.0 s; c08_s01/s02
   ≤ 1.0 s i PASS; c10_s02 4.42 ≤ 8.78 s i PASS; 0 ENTRY FP; breach 0.

**Zdanie cytowalne (PRE §3 V-A, wypełnione):** „Przegląd perymetru przeliczony
na gwarantowaną kadencję — admisja w rampie, krok 68.3°, slew 60°/s, stare
0.4 s, dwell startowy 1.0 s (2.0 s po utracie) — przyjmuje najgorszy azymut
przed zamknięciem pasa admisji: T6 bez wiatru 6/6 (c11 3/3, t_acq 6.83–7.31 s
wobec 12.23–24.97 s), kontrole bez regresji, zero fałszywych admisji. Sufit
profilu misji z TRANSIT był sufitem epoki 5 Hz.” Dopisek obowiązkowy: „bez
wiatru, reżim OPS 14.7 Hz, SITL; jeden boot na scenariusz”.

**Czego nie wolno mówić:** że sufit jest zniesiony na całej ławce, bo
odnowiony jest T6, nie pełna siatka. Że to dotyczy wiatru, bo z wiatrem
rachunek daje 0 kombinacji, a kanon V-A3 jest bez zmian. Czegokolwiek
o realnym sprzęcie.

**Znalezisko nazwane (nie pozycja):** przy stojącym nosie i celu czołowym MTI
nie odpala (κ 0–2°/klatkę: 1/23; 4–6°/klatkę: 7/11). To ten sam mechanizm co
PERCEPCJA-II (ii) „MTI-czołowy”, teraz z czwartym przypadkiem i liczbą per
klatka. Najwcześniejsza akwizycja celu czołowego bez tracka sprzed startu
zależy od tego, jak szybko nos ruszy. Dopisek do (ii), bez nowej pozycji.

## §3. Status wątku

SKAN-II: **CLOSED (V-A)**, budżet 2/8. Wątek akwizycji zamknięty zgodnie
z zapisem z góry: nowych pozycji katalogu brak. Kanon zmienia się w jednym
miejscu. Twierdzenie sufitu TRANSIT (25.10) zostaje prawdziwe dla przesłanki
„w rampie admisja nie istnieje” (5 Hz). Przy 14.7 Hz bez wiatru jego przesłanka
jest sfalsyfikowana lotem. Errata forward, raporty TRANSIT i PERC2 bez edycji.
`net_skan2` jest kontrolerem kanonicznym dla lotów bez wiatru na kamerze;
net_fantom zostaje linią bazową i kanonem z wiatrem.

## §4. Katalog i KSIĘGA (treść do skopiowania, append-only)

Dopisek do `KIERUNKI_PO_PLANIE.md`:

```
## Dopisek stanu katalogu — 2.11.2026 (CO-SKAN2, ANEKS_SKAN2-1 §2–§3)

- **SKAN-II „admisja w rampie" (nota DET3 §3 → recon SKAN2R → PRE_SKAN2)** →
  **CLOSED, werdykt V-A** (2/8 bootów). net_skan2 (krok 68.3°, slew 60°/s,
  stare 0.4 s, dwell 1.0 s start / 2.0 s po utracie) na siatce PERC2 S2 1:1:
  T6 bez wiatru **6/6** (baza net_fantom 3/6); c11 3/3, t_acq 6.83–7.31 s
  (baza 12.23–24.97 s, D6 0/3); c10_s02 4.42 s (8.78); kontrole c08_s01/s02
  bez regresji; 0 ENTRY FP; breach 0; V2′ 8/8; 8/8 pierwsze przejście.
  Interpretacja „kontrole" = zbiór PRE §1 Q2 (rozstrzygnięcie CC, ANEKS_SKAN2-1
  §2); c08_s04 2.09 s (baza 0.10) = stan tracka w t0, nie profil.
  **Zdanie kanoniczne:** „Przegląd perymetru przeliczony na gwarantowaną
  kadencję przyjmuje najgorszy azymut przed zamknięciem pasa admisji: T6 bez
  wiatru 6/6. Sufit profilu misji z TRANSIT był sufitem epoki 5 Hz (bez wiatru,
  OPS 14.7 Hz, SITL)."
  **Errata forward:** twierdzenie sufitu TRANSIT (25.10) i zdanie kanoniczne
  DET3 („sufit … w geometrii przeglądu") obowiązują dla przesłanki 5 Hz;
  bez wiatru przy 14.7 Hz przesłanka sfalsyfikowana. Z wiatrem bez zmian.
- **PERCEPCJA-II (ii) MTI-czołowy** — dopisek (NIE nowa pozycja): czwarty
  przypadek (SKAN2 c08_s04, stojący nos, cel czołowo, koincydencja 0/22);
  κ per klatka 0–2°/kl 1/23, 4–6°/kl 7/11.
- Infrastruktura: skoki CLOCK_REALTIME w WSL (od ~26.10) usuwa zatrzymanie
  systemd-timesyncd na czas sesji (ANEKS_SKAN2-0b; próbniki 0 skoków,
  zegar2 w locie 0); `wsl --shutdown` nie wystarcza. Reguła dla kolejnych
  lotów: próbnik 60 s przed bootem.
- Stan: wątek akwizycji zamknięty; katalog 6 otwartych pozycji bez zmian.
  Breach 0 / REFUSE 0 programowo bez zmian.
```

Sekcja do `results/KSIEGA_PREDYKCJI.md`:

```
## NOGA SKAN-II — ZAMKNIĘTA przy CO-SKAN2 (ANEKS_SKAN2-1, 2.11.2026), werdykt V-A
- P-SK2-1 (0.55) c11 ≥ 2/3 D6 PASS ze świadkiem — ✓ (3/3).
- P-SK2-2 (0.70) c11 w pierwszym przejściu t_acq ≤ 8.0 s — ✓ (6.83–7.31).
- P-SK2-3 (0.65) ≥ 1 chybione pierwsze przejście w 8 epizodach — ✗ (0/8).
- P-SK2-4 (0.80) c08 4/4 t_acq ≤ 1.0 s — ✗ (c08_s04 2.09 s; stan tracka w t0).
- P-SK2-5 (0.85) 0 ENTRY FP — ✓.
- P-SK2-6 (0.90) breach 0 — ✓.
- ✗ kalibracyjne CC (1): hipoteza PROMPT_SKAN2_S0 celowała w czas wpatrywania;
  przy 14.7 Hz admisja zachodzi w rampie (recon: 22/36 ENTRY; lot: 5/5).
- ✗ kalibracyjne CC (2): §0.4 PROMPT_SKAN2_S1 zakładał, że `wsl --shutdown`
  usuwa skoki zegara; nie usuwa (usuwa zatrzymanie timesyncd). Bramka napisana
  bez sprawdzenia, kto w torze lotu czyta zegar ścienny (nikt).
- ✗ kalibracyjne CC (3): PRE_SKAN2 V-A pisze „c08" bez sufiksu, a P-SK2-4
  „c08 (4 epizody)"; niejednoznaczność rozstrzygnięta literą Q2 dopiero po
  locie, na korzyść hipotezy. Wykonawca nazwał interpretację przed lotami.

**Suma nogi SKAN-II: 4 ✓ / 2 ✗ / 0 n.r. (+3 ✗ kalibracyjne poza numeracją).**

Lekcje kalibracyjne: (1) przy zmianie kadencji przeliczyć nie tylko stałe,
ale przesłanki, z których je wyprowadzono — sufit TRANSIT był poprawnym
rachunkiem na przesłance z innego reżimu; (2) P-SK2-3 i P-SK2-1 = 0.55 były
zbyt ostrożne: model B-kal przewidział t_acq c11 6.6–7.6 s, lot dał 6.83–7.31;
gdy model skalibrowany na danych trafia w przedział, następna predykcja może
mu ufać bardziej; (3) zbiory w kryteriach PRE nazywać identyfikatorami
epizodów, nie prefiksem komórki.
```

## §5. Zlecenie CO-SKAN2 — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git fetch` → origin/master == **c3a6d7ff**; `origin/master..HEAD`
puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista zamknięta): korzeń
**`ANEKS_SKAN2-1.md`** (ARCH-1, verbatim, pierwszy w commicie; byte-check
sha256 podany przez CC w wiadomości); **EDYCJA `KIERUNKI_PO_PLANIE.md`** —
dopisek §4 verbatim, append-only; **EDYCJA `results/KSIEGA_PREDYKCJI.md`** —
sekcja §4 verbatim, append-only. ŻADNYCH edycji RAPORT_SKAN2_S1, narzędzi,
PRE, aneksów 0/0b ani kodu; żadnych bootów. Raport płaski: diff-stat, pełna
treść dopisków, porcelain. **Push = Olga (CC sprawdza byte-check,
append-only, verbatim).** STOP.

## §6. Status

SKAN-II: CLOSED V-A. Program: wiatr zamknięty, wabiki zamknięte, daleki wzrok
zamknięty, akwizycja zamknięta z wynikiem dodatnim. Katalog 6 pozycji, żadna
nie jest techniczną nogą wymagającą lotów w obecnym planie. Raport programu
dostaje aktualizację akapitu o granicy (CC, poza repo).
