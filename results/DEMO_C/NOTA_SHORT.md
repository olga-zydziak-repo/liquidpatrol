# NOTA_SHORT — wariant dynamiczny DEMO_C_SHORT (dopisek po STOP-DEMOC-1, na prośbę Olgi 26.10)

Errata-w-przód (RAPORT_DEMO_C nietknięty). Wariant SHORT korzysta z JEDYNEJ
dozwolonej formy dynamizacji z PROMPT_DEMO_C §1.2: **przyspieszenie z jawnym
podpisem** (plakietka „TEMPO ×N" wypalona w prawym górnym rogu przez cały czas
trwania segmentu przyspieszonego) + cięcia MIĘDZY fazami z ciągłym zegarem
epizodu. Te same ujęcia sędziowane co w DEMO_C (zero nowych bootów, zero
inscenizacji); kluczowe momenty (detekcja, znalezienie po skanie, denial→REFUSE)
pozostają w czasie rzeczywistym.

**Segmenty (czas epizodu : tempo):**
- AKT 1 c08_s03: 0–8 s ×1 (podejście+detekcja) · 8–24 s ×3 (orbita) → 13.4 s
- AKT 2 c10_s02: 0–6 s ×2 (skan) · 6–14 s ×1 (znalezienie+pościg) · 14–30 s ×3 (orbita) → 16.3 s
- AKT 3 c03_s01: 22.7–30 s ×2 (orbita) · 30–36 s ×1 (denial+REFUSE) · 36–46.5 s ×2 (zejście) → 15.1 s
- plansza 9 s · **całość 53.8 s**, 1920×1080 @10 fps.

**Pliki (na dysku, polityka §5 — poza repo); sha256 pełne:**
- `results/DEMO_C/DEMO_C_SHORT.mp4` — `04c514801ed0f3ce1c3ca7c04bae02c41b4afa42e31eb8bcd03d8f7095396a89`
- `clips/akt1_short.mp4` — `4eb3aace0d39880c49f351c24ce8952c22b68cb43bc6265a43c1a491090c911f`
- `clips/akt2_short.mp4` — `f4a6c411f8b0ebcfb2aae6d7b23fecea84fe69435fd2f9261c162f3189d8abbd`
- `clips/akt3_short.mp4` — `0de7d57799c0ecb29c61e8981fd54215f7d322b848a3562506e68e4a1a9ecddd`

Narzędzie: `tools/democ_overlay.py` rozszerzone o opcjonalny argument segmentów
(kompatybilne wstecz: bez argumentu renderuje jak dotąd — DEMO_C odtwarzalne 1:1).
