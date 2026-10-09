# PRE_AKW — zamrożenie nogi AKW (akwizycja): wrapper skanu, smoke bramkowy, kampania powtórkowa

CC · 09.10.2026 · łańcuch AKW (po STOP-AKWR, commit 2110288 na origin — zweryfikowany
przez CC wykonaniem: twierdzenia R1 potwierdzone na cytowanych liniach [hold komenderuje
yaw=0.0 jako STAŁĄ, net_controller.py:108-111; shield.step bez yaw, :121; rejestr
z precedensami additive gru/mlp20], tabele R3 odtworzone CO DO KOMÓRKI z binów per-boot
w obu źródłach, geometria 86.9°/rachunek klatek przeliczone). Dokument przed-pomiarowy:
po ratyfikacji kryteria ZAMROŻONE. Sygnały bez numeru wykonawca odrzuca.

## §0. Pytanie nogi i zakres

**Pytanie:** czy skan yaw przed-ENTRY domyka lukę akwizycji zmierzoną w DET — to jest:
czy Δ_new na powtórce kampanii spada z 34 do strefy „system przeżywa" (≤4) przy
NIEZMIENIONYCH progach zdania zamrożonego PRE_2A §4?

**Jedna zmiana naraz:** jedyną zmianą w całym systemie jest WARTOŚĆ pola `yaw`
w komendzie kontrolera w fazie hold (pole istnieje w kontrakcie od zawsze). Poza
zakresem: gimbal, cue zewnętrzny, zmiany sieci/percepcji/admisji/osłony/ławki,
sonda wariantu (ii) z recon (ANEKS-owalna, nie otwierana tym PRE).

## §1. FROZEN wejściowe i nietykalne

Piny 5/5, certy 9/9; bench_flight 05137098, bench_judge 8ec0fcfb, feed_vision acc81df7,
det_v2.pt 775ead15, det_v2.py e801f7d5, percep_proc 38a3a765, feed_vision_proc 79633489,
feed_registry ee1481f9, ncp 0337d5ea, net_controller (bajty bez zmian — wrapper go
IMPORTUJE, nie edytuje). Edycja któregokolwiek = STOP.

## §2. D1 — Budowa: wrapper `net_akw` (rejestr kontrolerów, additive — SR-9)

- **NOWY plik `r03/controllers/akw_scan.py`:** klasa `AkwScan(SetpointSource)`,
  `name="net_akw"`; konstruktor buduje wewnętrzny `NetController(**kw)` (guard SR-2
  sha wag NIETKNIĘTY); `step()` deleguje i **wyłącznie gdy `extra.phase=="hold"`**
  podmienia pole `yaw` na profil ψ(t); każda inna ścieżka zwraca cmd delegata
  BEZ ZMIAN. `reset()` zeruje stan skanu (per epizod, jak bench instancjonuje).
- **EDYCJA `r03/controllers/__init__.py`: WYŁĄCZNIE 2 linie** (import + wpis
  `"net_akw": AkwScan` z komentarzem PRE_AKW/SR-9). Nic więcej w żadnym istniejącym
  pliku.
- **Profil skanu (FROZEN):** ciągły, jednokierunkowy CCW, **ω = 30°/s**; wejście
  w hold → **dwell 2.0 s trzymania ostatniego yaw** (okno odzysku REFRESH przed
  odkręceniem nosa; θ_age 3.0 − TRACK_LOSS 1.0), potem rampa OD BIEŻĄCEGO yaw
  (ciągłość, nigdy powrót do 0). Pierwsze wejście w hold w epizodzie: dwell liczy się
  tak samo. Parametry w kodzie jako stałe + env `AKW_SCAN_DPS`/`AKW_DWELL_S` wyłącznie
  do odczytu diagnostycznego — **kampania i smoke latają na wartościach FROZEN; zmiana
  wartości = ANEKS, nie env.**
- **FREEZE_AKW (init przy S1):** sha akw_scan.py, sha __init__.py PO wpisie, parametry
  profilu, sha drivera kampanii (kopia detS4_boot ze zmianą env — nowy plik narzędziowy,
  stary nietknięty); dziedziczone verbatim: FREEZE_DET w całości, piny, ncp.

## §3. Testy przedlotowe (pytest; FAIL któregokolwiek ⇒ nie latamy)

1. **Pass-through bajtowy:** na sekwencjach feedów odtworzonych z logów DET (ramię B
   i ważne tracki V2) `AkwScan.step()` zwraca cmd IDENTYCZNY polami z `NetController`
   dla każdego ticku z phase≠hold; różni się WYŁĄCZNIE polem yaw na tickach hold.
2. **Profil:** rampa ψ(t) 30°/s, unwrap/wrap poprawny, dwell 2.0 s respektowany,
   wznowienie od bieżącego yaw, reset() czyści stan.
3. **Rejestr:** `make_controller("net_akw")` działa; `controller_sha` w manifeście =
   sha akw_scan.py; `make_controller("net")` ścieżka NIEZMIENIONA (regresja).

## §4. Smoke BRAMKOWY (S1; 1 boot + ≤2 naprawcze) — akwizycja ZE SKANU na ślepych

Boot **KAMPANIJNY 4-epizodowy** (domyka klasę „smoke jednoepizodowy
niereprezentatywny"): scenariusze bloku r1 DET (c00_s01…c03_s01 — bearing 0/90/180/270,
czyli 3 epizody ślepe w DET + 1 kontrolny), FEED=V2, CONTROLLER=net_akw, pełne
uzbrojenie, reżim bootów jak DET S4 (driver-kopia, proc_gate, cooldown, manifesty
1. klasy, V2′ + żywość feedu per epizod).

**Bramki smoke:**
- **A (mechanizm, nośnik):** ENTRY w **3/3 epizodach ślepych** (c01/c02/c03), każdy
  z **t_entry ≤ 20 s** (rachunek: worst-case czekanie 9.1 s + dolot 2–3 s + margines;
  próg D6 to 25 s — bramka smoke celowo ostrzejsza o 5 s). 2/3 ⇒ JEDNA powtórka bootu
  z puli naprawczej; <3/3 po powtórce ⇒ STOP-ANEKS (inżynieria profilu, nie śmierć).
- **B (runtime, verbatim DET S3):** kadencja przetwarzania ≥8 Hz p50; E2E p95 ≤0.25 s.
- **C (S-BEZP):** breach R_E=0 wymagane; REFUSE per gałąź = wpis (oczekiwanie
  konstrukcyjne 0 — w hold target=own, v=0, geofence nieaktywny; R5.6 recon);
  REFUSE(POS) ⇒ STOP.
- Opisowo (bez progów): zero oscylacji skan↔ENTRY w 5 s po akwizycji, fałszywe ENTRY
  tła pod skanem (pokrycie pasma ω=30 — R3 miało je cienko próbkowane), err po
  akwizycji, zachowanie epizodu kontrolnego c00 (musi przejść jak w DET).

## §5. KAMPANIA powtórkowa (S2; 24 booty + zapas 3) — wariant (i) VERBATIM po DET S4

12 rund × 2 booty **{B, V2+skan}**, siatka 48 i przydział rund IDENTYCZNY z DET S4
(zweryfikowany wcześniej z manifestów LIQ), rotacja ramion naprzemienna, reżim/ważności/
telemetria/parowanie wzorem detS4 (narzędzia kopiowane, stare nietknięte).
**OBA ramiona CONTROLLER=net_akw** — odstępstwo od szkicu recon z uzasadnieniem:
pod FeedB track jest ważny od t0, więc skan się nie aktywuje i net_akw ≡ net
(dowód: test §3.1 + porównanie pass(B)_new z 47/48 DET jako kontrola dryfu habitatu
i pass-through w locie); dzięki temu ramiona różnią się WYŁĄCZNIE feedem, a zarzut
„dwóch zmian naraz" pada konstrukcyjnie.

Telemetria per epizod jak DET S4 **plus**: t_entry, czas od startu skanu do ENTRY,
liczba cykli skanu przed akwizycją, fałszywe ENTRY (z klasyfikacją F1/F2/F3 jak R3).
Dekompozycje prereg: per bearing / split / sceno-świeżość; porównanie per-para z 29
ślepymi epizodami DET (ile z nich teraz przechodzi).

**Werdykt (progi VERBATIM PRE_2A §4, zdanie zamrożone):** Δ_new = pass(B) − pass(V2+skan)
na 48 parach: **Δ_new ≤ 4 ⇒ „system przeżywa zejście z wyroczni — luka akwizycji
domknięta zachowaniem"; Δ_new ≥ 10 ⇒ ŚMIERĆ-AKW: „skan nie wystarcza — akwizycja nie
była jedynym ogniwem"** (publikowalny negatyw z mechanizmem per porażka z telemetrii);
5–9 strefa opisowa; V2 lepszy o ≥3 ⇒ zdanie jawne + podejrzliwość przyrządu.
Zdanie porównawcze (prereg): ΔΔ = 34 − Δ_new, ZAWSZE z kwalifikatorem dwóch kampanii
(ten sam habitat i siatka; świeże ramię B jako kontrola dryfu). Kwalifikatory cytowań
= DET (SITL, rendering syntetyczny, detektor in-domain, tło naziemne, c-siatka, NCP)
**plus** „akwizycja skanem yaw 30°/s". Zakazy PRE_2A §4 i kanonu DET bez zmian.

## §6. Budżet, pliki, rytm

**Booty: smoke 1 (+≤2) + kampania 24 (+≤3) ⇒ sufit ≤30; 2 sesje lotne** (S1
build+testy+smoke; S2 kampania). Przekroczenie ⇒ STOP. Przerwanie kampanii tylko na
granicy rundy; bez decyzji na cząstkowym Δ.

**Pliki (lista zamknięta):** korzeń PRE_AKW.md (ARCH-1, pierwszy commit S1);
NOWE: `r03/controllers/akw_scan.py`, `results/AKW/**` (FREEZE_AKW, raporty, driver-kopia,
testy, narzędzia parowania-kopia); EDYCJA istniejących: **WYŁĄCZNIE
`r03/controllers/__init__.py` 2 linie additive.** ZERO: bench, percepcja, r02, osłona,
wagi, rejestr feedów, net_controller, drivery DET.

Rytm: S1 → STOP-AKW1 (build+testy+smoke, raport z bramkami A/B/C) → push → ANEKS_AKW-1
(werdykt smoke, zwolnienie kampanii) → S2 → STOP-AKW2 → ANEKS_AKW-2 (werdykt Δ_new,
kanon nogi, KSIĘGA, CO-AKW).

## §7. Predykcje CC (reguła 9 + kalibracja z ANEKS_2A-4/DET-4: techniczno-integracyjne ↓;
mechanizm tu jest ZMIERZONY, nie nadziejowy, więc korekta w dół umiarkowana)

- **P-AKW-1** (integracyjna ↓): smoke A+B+C PASS za pierwszym bootem — **p 0.50**
- **P-AKW-2:** zero potwierdzonych fałszywych ENTRY tła w smoke i kampanii — **p 0.70**
  (R3: 0 potwierdzonych, ale pasmo ω=30 cienko próbkowane i geometria transitu
  niemierzona)
- **P-AKW-3** (wynik nogi): **Δ_new ≤ 4 — p 0.60** (mechanizm 29/35 czysto
  geometryczny i usuwany; niepewność: intruz ruchomy × skan, R5.8)
- **P-AKW-4:** pass(B)_new ≥ 46/48 (pass-through + stabilność habitatu) — **p 0.80**
- **P-AKW-5:** REFUSE = 0 w całej nodze (konstrukcyjnie nieaktywny geofence w hold;
  historia programu) — **p 0.85**

Rozliczenie w KSIĘDZE przy zamknięciu, sekcja NOGA AKW.

## §8. Ratyfikacja

Czekam na **„ratyfikuję"**. Po ratyfikacji wydaję PROMPT_AKW_S1 (build + testy + smoke;
kampania dopiero po ANEKS_AKW-1). Zmiany po ratyfikacji wyłącznie ANEKS-em numerowanym.
