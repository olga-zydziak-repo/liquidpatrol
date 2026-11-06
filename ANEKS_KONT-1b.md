# ANEKS_KONT-1b — po STOP-KONT2-BUDZET: 13 bootów bez uzbrojenia to awaria stanowiska, nie pomiar; nowy budżet S2′, warunki wznowienia, strażniki kolejki

CC · 6.11.2026 · łańcuch KONT, po STOP-KONT2 (41991570 na origin).
**Zmienia budżet nogi, więc wymaga ratyfikacji Olgi („ratyfikuję 1b").**
Wklejany jako jedyny dokument do sesji wykonawczej. Sygnały bez numeru
odrzucasz.

## §1. Weryfikacja CC z repo

- Zakres: 451 plików, +79530/−0, same dodania.
- 13 bootów: `percep_feed.jsonl.summary.json` n_frames = 0 przy
  n_img_cb 566–583 i sim_last 40.7–41.8 s (sprawdzone na c11_s02,
  c02_s01, c11_s04_r2). Jedyny lot `c08_s02a_r2`: n_frames 3827.
  Mechanizm z raportu (percepcja bez stanu własnego, `feed_vision.py:156`)
  zgodny z danymi. Przyczyna nieustalona.
- Lot ważny `c08_s02a_r2`: CC przeliczył ε z trace własnym kodem (offset
  z 20 s przed odcięciem, metoda zgrubna): 0.24 / 0.99 / 1.48 / 1.45 /
  0.67 / 1.36 m przy 0/10/20/30/60/70 s, r_GT max 22.71. Raport (gt_judge):
  0.80 / 1.34 / 1.06 / 1.25 / 1.83 przy 10/20/30/60/70 s. Ta sama skala,
  różnice w granicach metody. Przyjęte.
- Decyzja wykonawcy, żeby NIE zamrażać z n = 1: słuszna. Litera
  („po lotach zamrożenie") ustępuje PRE §3 (≥ 8). Odchylenie przyjęte.

## §2. Rozstrzygnięcia

1. **`c08_s02a_r2` = lot ważny 1/8.** Spełnia wszystkie warunki ważności.
2. **13 bootów bez uzbrojenia nie jest pomiarem hipotezy.** Nie dały
   żadnej informacji o przepływie ani o dryfie. Liczą się do budżetu,
   jak każdy boot (litera PRE), ale budżet nogi rośnie o tyle, ile zjadła
   awaria stanowiska. To nie jest luzowanie kryterium, bo kryteria S2 i
   reguła §3 zostają bez zmian. Zmienia się tylko liczba prób, którą noga
   może spalić na infrastrukturę.
   - **S2′: ≤ 12 bootów** (7 brakujących lotów ważnych + 2 diagnostyczne
     będące zarazem lotami + 3 rezerwy).
   - **Budżet nogi: 33 → 45** (S1 2 + S2 14 + S2′ ≤ 12 + S4 ≤ 16 + 1).
     Nazwane wprost: zmiana budżetu po STOP-ie, z przyczyną.
3. **Kolejka (wada przyznana w raporcie §3):** nowa kopia
   `kont_s2_campaign_g.py` ze strażnikami:
   - 2 kolejne FAIL sondy przed uzbrojeniem ⇒ STOP kampanii;
   - `kampania.log` śledzony na bieżąco, alarm przy pierwszym FAIL;
   - przed każdym bootem kontrola sierot (`infra2_ekf_watchdog`,
     `rtf_sampler`, `percep_proc`, `MicroXRCEAgent`, `gz`, `px4`):
     jakakolwiek żywa ⇒ TERM, odczekać, powtórna kontrola, a jeśli żyje
     dalej ⇒ STOP;
   - `pkill` tylko po PID z inwentarza, nigdy `-f` po wzorcu.
4. **`kont_s2_freeze_g.py`** (kopia ze strażnikiem): n_ważnych < 8 ⇒ odmowa
   i kod wyjścia ≠ 0. Oryginał nietknięty.
5. **`kont_frames.py --compare`** nadpisuje `frames_identity.json` z bootu A.
   Nie uruchamiać w miejscu. Wynik tej weryfikacji CC w repo (dziś
   przywrócony u CC) jest kanoniczny.

## §3. Diagnoza w locie (prereg, bez dodatkowych bootów)

Kandydat 1: zalegające segmenty FastDDS SHM. Kandydat 2: wyścig kolejności
startu. Rozdzielenie odbywa się na pierwszych dwóch bootach S2′, które
są zarazem lotami z planu:

- **D1:** `wsl --shutdown` (Olga) → świeża sesja, pusty `/dev/shm` →
  boot c11_s02. Oczekiwane PASS (jak boot 1 kampanii).
- **D2:** po D1, przed bootem: usunięcie `/dev/shm/fastrtps_*` i
  `/dev/shm/sem.fastrtps_*` (stan przed i po do pliku), potem boot c02_s01.
  - **PASS** ⇒ kandydat 1 przyjęty roboczo. Sprzątanie SHM wchodzi do
    kolejki jako krok przed każdym bootem (w nowej kopii, wpis do
    manifestu), loty dalej.
  - **FAIL** ⇒ kandydat 1 obalony, STOP-KONT2b, raport. Bez trzeciej
    próby i bez łatania kolejności startu na własną rękę; czekasz na
    dokument CC.
- Gdy D1 zawiedzie na czystym hoście ⇒ STOP-KONT2b z tym samym
  raportem. Wtedy nie jest to stan po bootach, tylko coś nowego.

## §4. Loty S2′

Pozostałe z planu: c11_s02, c02_s01 (D1, D2), dalej c08_s04, c11_s03,
c00_s02, c11_s04, c08_s02b. Razem z `c08_s02a_r2` daje to 8. Ważność,
śmierci, STOPy i raport: bez zmian, PROMPT_KONT_S2 §S2.2–§S2.3. Raport
dopisuje się jako `results/KONT/s2/RAPORT_KONT_S2b.md` (nowy plik;
RAPORT_KONT_S2 bez edycji). Zamrożenie wyłącznie przez
`kont_s2_freeze_g.py` przy n ≥ 8. Liczby zamraża dopiero ANEKS_KONT-2.

## §5. Dla Olgi — co ten lot mówi, a czego nie

Jedyny ważny lot ma ε(70 s) ≈ 1.8 m, a sonda S1 miała 7.1 m. Jeśli
typowy lot wygląda jak ten, to z reguły PRE §3 (1.5×ε + 1.5×Δ ≤ 5.79)
T* wychodzi w okolicy pełnych 70 s. Różnic jest jednak kilka naraz:
nauczyciel na kamerze zamiast GT (R-4), inny epizod, wysokość bez
przesunięcia (z_off −0.03 m zamiast +1.835). Do tego n = 1. To jest
dobry znak, nie wynik. Predykcje bez zmian.

## §6. CO

Ten aneks verbatim do korzenia jako `ANEKS_KONT-1b.md`, byte-check sha256
z wiadomości CC, pierwszy commit sesji S2′:
`KONT [ANEKS-1b]: budżet S2′ ≤ 12, nóg 45, strażniki kolejki, diagnoza D1/D2`.
Potem §2.3–§2.4 (nowe pliki, commit), potem §3–§4. Push = Olga.
