# STOP-NADIR4-STANOWISKO — po ważnym nominale (tempo 0.955) dwa kolejne booty cięcia przerwane bramką tempa 0.734 / 0.740 ⇒ STOP

Wykonawca · 9.11.2026 · łańcuch NADIR, PROMPT_NADIR_S4.

Stan wyjściowy:
- STOP-NADIR4-BUDZET `5eb4c14c` (wypchnięty).
- Restart WSL Olgi i sygnał rezerwy „cały luz” ⇒ `a060e140`: BUDZET S4 18, dolecenia, 2 kolejne przerwania bramką tempa ⇒ STANOWISKO.

## Booty tej kolejki (start 21:07, uptime 11 784 s)

| boot S4 / noga | pozycja | tempo settle | wynik |
|---|---|---|---|
| 2 / 13 | **nom_b1_r2** | 0.9598 | **ważny, (f) 4/4 PASS.** 0 fałszywych wejść KONT, 0 REFUSE; (b)–(g) czyste we wszystkich 4 epizodach; breach 0. Tempo przez cały lot 0.94–0.96 (średnio 0.955). |
| 3 / 14 | c01_s01 | **0.7335** | przerwany przed uzbrojeniem (kod 9), dolecenie |
| 4 / 15 | c01_s01_r2 | **0.7396** | przerwany przed uzbrojeniem ⇒ 2 kolejne ⇒ **STOP-NADIR4-STANOWISKO** |

**Charakter spowolnienia:**
- Skok, nie dryf: w c01_s01 cały settle mieścił się w 0.70–0.80, a 8 minut wcześniej nom_b1_r2 kończył lot przy 0.955.
- Po stronie WSL host jest czysty: load ~3 na 24 rdzeniach, CPU idle, brak sierot, zegar 0 skoków, sonda 14.71 Hz PASS.
- Przyczyna leży poza VM, prawdopodobnie po stronie Windows (tryb zasilania, inny proces). Mechanizm niezmierzony.

## Rachunek i błąd wykonawcy

- **Księga:** 4 booty S4 zużyte, ważne 1 (nom_b1). Pozostało 15 pozycji: 12 cięć i nom_b2–b4.
- **Moja wada (nazwana):** w pytaniu o rezerwę policzyłam luz nogi jako 2, a „cały luz” jako budżet S4 = 18. Poprawnie: noga przed S4 to 11, siatka 16, czyli 27/30, więc luz wynosi **3**, a „cały luz” daje budżet S4 = **19**. Przerwanie nom_b1 było już jednym z 16 bootów, nie dodatkowym. Przy budżecie 19 i 4 zużytych pozostałe 15 pozycji mieści się dokładnie, bez rezerwy, i noga kończy na 30/30. Przy 18 siatki nie da się domknąć.
- **STOP nie jest skutkiem tej wady.** Wywołały go 2 kolejne przerwania bramką tempa, a ta reguła działa niezależnie od budżetu.

## Do decyzji Olgi

1. **Stanowisko po stronie Windows:** tryb zasilania „wydajny” i obciążenie, potem `wsl --shutdown`. Wzorem KONT 4e/f warto zrobić kontrolę gołego gz przed kolejką.
2. **Budżet S4 = 19** (cały luz według poprawnego rachunku, noga do 30/30). Siatka mieści się bez rezerwy: każdy kolejny nieważny boot to STOP-NADIR4-BUDZET, a dokończenie wymagałoby budżetu ponad nogę, czyli decyzji CC.

## Pliki

- Katalogi bootów: `nom_b1_r2/` (`wyniki_nadir_s4.json`, `rama.jsonl`, trace), `c01_s01/`, `c01_s01_r2/` (`kont_tempo.json`, `rtf_stream.jsonl`).
- Kolejka: `kampania_ksiega.jsonl`, `kampania_s4.json`, `kampania_s4.log`, `nadir_s4_monitor.log`.

Sygnał: **STOP-NADIR4-STANOWISKO**. Push = Olga.
