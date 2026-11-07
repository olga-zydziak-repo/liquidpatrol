# STOP-KONT4-BUDZET — dwa kolejne booty S4 nieważne przez asercję yaw przed uzbrojeniem; rezerwa 4b wyczerpana, 0 lotów

Wykonawca · 7.11.2026 · łańcuch KONT, S4 po ANEKS_KONT-4b (`b79ffb14`, ratyfikowane: S4 ≤ 17). Podstawa STOP: reguła
4b §1.3 i kolejka `kont_s4_campaign_b.py` — jedno dolecenie w serii, drugi nieważny boot ⇒ STOP-KONT4-BUDZET.

## Przebieg (kampania_s4.log, kampania_s4b.json)

| boot | pozycja | faza dołączenia | asercja yaw (próg 10°) | bias_max watchdog | wynik |
|---|---|---|---|---|---|
| 25 | nom_b1 | 7.604 s | — (driver padł przed asercją, STOP-KONT4-DRIVER) | — | nieważny |
| 26 | nom_b1_r2 | 7.448 s | **51.64°** | 0.107, `filter_fault` w 15 s | nieważny, dolecenie (rezerwa 4b) |
| 27 | nom_b2 | 7.496 s | **13.26°** | 0.073 | nieważny ⇒ **STOP** |

Budżet S4 **3/17**, noga **27/45**. Lotów 0, epizodów 0, twarde STOPy §2 nie zaszły (brak lotu). Stos i sonda kadencji
w obu bootach w normie; driver po poprawce 4b doszedł do asercji (próba na sucho potwierdzona w locie).

## Co wiadomo

- **To błąd estymatora, nie przyrządu.** W nom_b1_r2 heading EKF stoi na 141.6° we wszystkich próbkach przed uzbrojeniem,
  a GT daje kierunek o 51.6° inny; funkcja błędu jest kopią 1:1 `kont_s2_probe_y.py:106-109`, która w S2 dała 6.38 / 6.42
  / 6.43° w 3/3 bootach.
- Stan estymatora przy starcie gorszy niż w S2: bias_max 0.107 i 0.073 wobec 0.00012–0.00013 w dwóch z trzech bootów S2
  (trzeci 0.143 z restartem watchdoga). To ta sama klasa co ryzyko nazwane w ANEKS_KONT-3 §4 („bias na limicie 0.15
  w 3/6 bootów s2d … mechanizm niezmierzony"). CAL_MAG = baseline (`mag_hygiene.txt`) w obu.
- **[MECHANIZM NIEZMIERZONY]:** nie wiem, dlaczego yaw EKF startuje z błędem 13–52° w tych bootach. Różnice drivera S4
  względem S2 przed asercją: dodatkowe `HARNESS_PARAM_PREFLIGHT` (GPS_CTRL 7, HGT_REF 0 — te same wartości co preflight
  KONT), selfcheck certów jako podproces, start `intruder_motion`. Żadna nie dotyka EKF wprost, ale nie jest to wykluczone
  pomiarem.

## Wada wykonawcy (druga w S4)

Asercja yaw w driverze stoi PO starcie podprocesu `intruder_motion` (`kont_s4_flight.py:304` vs `:321`), więc `os._exit(7)`
zostawia go jako sierotę. Strażnik kolejki sprzątnął sierotę po nom_b1_r2 przed nom_b2 (TERM po PID, `kampania_s4.log`);
sierotę po nom_b2 zakończyłem po PID po STOP. Inwentarz pusty, timesyncd `active`. Na wynik bootów bez wpływu (asercja
działa przed uzbrojeniem), ale to wada przyrządu do poprawki.

## Do decyzji CC

1. Diagnoza bez bootów z ulogów nom_b1_r2/nom_b2 vs S2 (yaw EKF od startu PX4, fuzja mag, bias, `filter_fault`) —
   czy przyczyna jest w stanowisku, czy w sekwencji drivera S4.
2. Mitygacja na ryzyko stanowiska (np. restart EKF przed uzbrojeniem przy |błąd yaw| > 10°, ponowna asercja; albo
   czekanie na zbieżność yaw z limitem) — zmiana drivera i reguły, więc dokumentem.
3. Poprawka kolejności asercji yaw przed `intruder_motion` (wada wykonawcy, bez wpływu na kryteria).
4. Budżet: 14 bootów do limitu S4 (17), noga 27/45 — 15 pozycji siatki się nie mieści bez nowej decyzji.

Bez rozstrzygnięcia nie edytuję drivera i nie bootuję. **STOP-KONT4-BUDZET.** Push = Olga.
