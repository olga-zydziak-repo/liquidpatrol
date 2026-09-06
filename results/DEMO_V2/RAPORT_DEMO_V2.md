# RAPORT_DEMO_V2 — demo lotu sieci (pozycja 5, re-render FILM=1) — STOP-D1

LiquidPatrol · pozycja 5 · CC 6.09.2026 · **DEMO ≠ POMIAR** — żadna liczba tu NIE wchodzi do żadnej księgi.
Ziarna wybrane JAWNIE pod pokaz (PROMPT_DEMO_V2 D1). Werdykty nogi = RAPORT_NET/ANEKS_NET-4.
Pliki dotykane: wyłącznie `results/DEMO_V2/**`. commit 2a8563e.

## §1. Artefakty
- `results/DEMO_V2/DEMO_V2.mp4` — sha256 `24354b50a48017c2...`, 61.8 s @ 8 fps (494 klatek), 1280×720, cv2 (bez ffmpeg).
- Klatki źródłowe `.npy` (gitignore, ~1.5 GB/boot) zachowane lokalnie; boot.ulg per boot (nie commitowany po ścieżce).

## §2. Wybór ziaren (jawny, uzasadnienie 1-zdaniowe)
- **c10_s02** (intruz 1.0 m/s, brg180) — pełne podejście + orbita ruchomego intruza (D1a).
- **c09_s01** (proximity c09, 1.0 m/s) — trudne wejście komórki proximity, którą sieć oblała przy s02/s03 a ZALICZYŁA przy s01 (D1b).
- **c00_s11, c08_s11** (świeże ziarno s11) — uogólnienie na niewidziane ziarno (D1c).

## §3. Łańcuch prowieniencji per boot
### demo_b1 (bazowy manifest e0527026)
- scenariusze: c10_s02(D6=T), c09_s01(D6=T), c08_s02(D6=T) · kind=demo · rc=0 · D6 3/3 · klatek 550
- controller=net (NCP-20) · weights_sha `0337d5eae1471bb9` (== FREEZE_NET; net_controller odmówiłby lotu przy rozjeździe) · controller_sha `e8c1b6583a62`
- world_hash `adc918032bc00b08` · feed FEED-B 10 Hz / 0.2 s / σ 0.5 m
### demo_b2 (świeży manifest a2dacee6, s11-s13)
- scenariusze: c00_s11(D6=T), c08_s11(D6=T) · kind=demo · rc=0 · D6 2/2 · klatek 400
- controller=net (NCP-20) · weights_sha `0337d5eae1471bb9` · controller_sha `e8c1b6583a62`
- world_hash `adc918032bc00b08`

## §4. Lista prób (wybór jawny — nic nie znika)
2 booty demo, obie za 1. razem (rc=0), zero powtórek. Wszystkie 5 epizodów przelecane; D6: b1 3/3, b2 2/2
(zbieżne z kampanią F2 — ale to DEMO, nie pomiar; nie liczy się do żadnej księgi).

## §5. Trajektoria — zbliżona, nie identyczna
Determinizm D2 gwarantuje trajektorię INTRUZA (position_at = f(sim_t, ziarno)); lot SIECI jest zbliżony,
nie identyczny wobec kampanii — feed losuje szumy z ziarna epizodu (FEED-B). To jest w porządku i JEST
tu napisane wprost (PROMPT_DEMO_V2 D2/D3).

## §6. Zgodność z kanonem (ANEKS_NET-4 §2) + zakazy trwałe
Plansze mp4 zawierają WYŁĄCZNIE zdania kanonu §2 (WOLNO): parametry sieci, skuteczność nauczyciela
(45/48 vs 44/48; 47/48 par), próg 0.9·p_exec, feed. Footer osłony DOKŁADNIE: „the network flies through
the same certified gate and shield as every controller in the program; the shield did not need to
intervene" — nic mocniejszego. BRAK: „sieć lepsza", języka istotności, „failsafe zawodzi", „native ucieka".

## §7. STOP-D1
Artefakty: DEMO_V2.mp4 + ten raport + commit. Czeka na ratyfikację CC (ANEKS_NET-5) → push → pozycja 5
zamknięta → tryb katalogu (nota GRU/k=20, SPRIND follow-up, backlog §8). Wykonawca po STOP: nic.

## §8. ERRATUM #3 (ANEKS_K2-0 §2 E2)
Footer filmu zmieniony ze „the network flies through the same certified gate and shield…" na
**„the network flies under the same frozen shield and through the same controller socket as every
controller in the program; the shield did not need to intervene"** (bez „certified gate" — recon K2/R1:
ławka to WŁASNA pętla, nie gate; certs_selfcheck w niej nie biegł; POS_DEGRADED nieuzbrojony `pos_flag=None`).
DEMO_V2.mp4 = wersja poprawiona; stary plik zachowany jako `DEMO_V2_v1_erratum3.mp4`. PLANSZE_VERBATIM.txt
zregenerowane. Reguła trwała (E3): materiały nazywają pętlę po imieniu + listują uzbrojone gałęzie.
