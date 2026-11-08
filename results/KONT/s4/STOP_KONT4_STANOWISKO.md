# STOP-KONT4-STANOWISKO — wolny boot bezpośrednio po restarcie (ANEKS_KONT-4e §1.2), remedium operatora nieskuteczne

8.11.2026 · kolejka `kont_s4_campaign_e.py` po `96207ec8` (decyzja CC: nazwy z plikami pomijane) · **S4 6/21, noga 30/45,
ważnych epizodów S4: 0**

## Przebieg

- 02:07:12 świeża sesja WSL po `wsl --shutdown` Olgi. 02:21:26 start kolejki (uptime 838 s), timesyncd zatrzymany.
- 02:22:27 próbnik zegara przed `nom_b2_r3`: **0 skoków, ok=True** (stanowisko zegarowo czyste; poprzednia próba
  tej sesji, 240 nowych próbek: 0 skoków, dryf 0.0 s).
- 02:26:05 `nom_b2_r3` rc=9: bramka tempa przed uzbrojeniem, **dsim/dwall 0.8731** (okno 59.92 s, n=723,
  rtf_stream.jsonl, próg 0.93). Faza ok, t0_us 7672000; lot nie ruszył (epizody 0/0, breach 0, REFUSE 0).
- Pierwszy boot po restarcie ⇒ STOP-KONT4-STANOWISKO natychmiast (4e §1.2), 14 pozycji pozostało; timesyncd przywrócony.

## Zapis stanu (bez interpretacji przyczyny — 4d §1.4: niezmierzona, nieścigana)

| boot | sesja | tempo przed uzbrojeniem |
|---|---|---|
| nom_b1_r2, nom_b2 | 7.11 (historycznie, obcięte do startu drivera) | 0.957, 0.972 |
| nom_b1_r3 | 8.11, ta sama sesja | 0.882 (historycznie) / RTF settle 0.861 |
| nom_b1_r4 | 8.11, ta sama sesja | 0.8756 |
| **nom_b2_r3** | **8.11, świeża po `wsl --shutdown`** | **0.8731** |

Jedyny fakt nowy: spowolnienie przeżyło restart VM, więc hipoteza „stanowisko zmęczone sesją” jest wykluczona
w zakresie, w jakim remedium ją testowało. Trzy kolejne booty 0.87–0.88 wobec 0.96–0.97 dzień wcześniej.

## Do decyzji CC / Olgi

Ścieżka do ustalenia (nie wykonuję niczego bez decyzji): np. restart Windows hosta, pomiar tempa w gołym gz bez PX4
(wzorzec B0 z `results/WK4/`, 0 bootów nogi), albo diagnoza stanowiska jako osobna pozycja. Budżet: 15 slotów na
14 pozycji (1 rezerwa) — przy kolejnym wolnym boocie rezerwa zniknie.
