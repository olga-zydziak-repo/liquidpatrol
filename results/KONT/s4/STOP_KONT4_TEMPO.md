# STOP-KONT4-TEMPO — bramka tempa przerwała nom_b1_r4 (0.876 < 0.93); kolejka zatrzymana przez wykonawcę przed drugim bootem na tym samym stanowisku; czeka remedium operatora (wsl --shutdown)

Wykonawca · 8.11.2026 · łańcuch KONT, S4 po ANEKS_KONT-4d (`5e34049c`).

## Przebieg

- **nom_b1_r4** (boot 29 nogi, S4 5/20): stos wstał (faza 7.560 s), sonda kadencji ponad podłogą, settle 90 s; bramka tempa
  4d §1.3 (`kont_tempo.json`): **Δsim/Δwall = 0.8756** w oknie 59.96 s (726 próbek `rtf_stream.jsonl`) < 0.93 ⇒ driver
  kod 9 przed połączeniem z PX4, przed reinitem i uzbrojeniem. Bramka zadziałała zgodnie z projektem (lot nieważny
  nie powstał).
- To drugi z rzędu wolny boot na stanowisku: nom_b1_r3 (00:27) miał RTF settle 0.861, nom_b1_r4 (00:55) 0.876; wcześniejsze
  boote tej sesji 0.957–0.972. Stan stanowiska utrzymuje się od ~00:25 (uptime WSL 2.5 h).

## Dlaczego zatrzymałem kolejkę przed literą

Po regule 4d kolejka poszłaby dalej i stanęła na STOP-KONT4-STANOWISKO dopiero po drugim przerwaniu. Na tym samym,
nieodświeżonym stanowisku drugie przerwanie jest bardzo prawdopodobne, a budżet jest bez luzu: S4 **5/20** przy 15
pozycjach siatki (nom_b1, nom_b2, nom_b3 i 12 cięć) — każdy dodatkowy boot wyjęty teraz to brak dolecenia na końcu.
Remedium z 4d §1.3 (`wsl --shutdown` i świeża sesja) jest akcją operatora, której kolejka nie wykona, więc drugi boot
nic by nie zmienił poza zużyciem budżetu. Zatrzymanie (SIGINT po PID) po próbniku zegara przed nom_b2_r2, zanim boot
wystartował; stanowisko czyste, timesyncd `active`. Licznik `tempo_streak` = 1.

## Stan i dalej

- S4 **5/20**, noga **29/45**; ważnych epizodów S4: 0. Pozostało 15 bootów na 15 pozycji.
- Do wznowienia: Olga wykonuje `wsl --shutdown` i otwiera świeżą sesję; wykonawca w nowej sesji: higiena zegara,
  kontrola bramki tempa, wznowienie kolejki 4d od nom_b1 (dolecenie), nom_b2, nom_b3, cięcia. `tempo_streak` liczony od
  nowa po restarcie stanowiska — to zmiana reguły STOP 4d §1.3 (dwa kolejne przerwania), więc wymaga potwierdzenia CC
  albo Olgi; bez niego pierwszy boot po restarcie z tempem < 0.93 oznacza STOP-KONT4-STANOWISKO.
