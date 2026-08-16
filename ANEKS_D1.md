# ANEKS_D1 — zapis ratyfikacji PRE_D (Olga, 2026-08-16)

Aneks do `PRE_D.md`. Zapis decyzji ratyfikacyjnych Olgi z 16.08.2026 dla nogi D (DEMO-B).
Kanoniczny dla bloków budowy B1…Bn. Wzorzec korekt: adnotacje `> [KOREKTA …]` dopisywane,
oryginał nie kasowany (jak `RAPORT_MTI`).

## Decyzje ratyfikowane

- **D1 — akty:** 3 akty wg `PRE_D §1` (patrol→token, utrata→re-admisja, GPS-denied) — **RATYFIKOWANE**.
- **D2 — token:** **per-cel**, o semantyce operacyjnej **per-ADMISJA** (patrz „Semantyka" niżej);
  `T_auth` (okno czasowe) wyłącznie jako udokumentowana alternatywa **poza demem** — **RATYFIKOWANE**.
- **D3 — trajektorie:** wariant **(a)** roszczenie percepcji **wyłącznie w dwell-hold** + wariant
  **(b)** plansza „beyond characterized envelope — transit" na **każdym** tranzycie — **RATYFIKOWANE**.
- **D4 — habitat:** ANEKS-H + kamera filmowa 720p jako sensor w świecie; **nowy hash świata mrożony
  per akt** — **RATYFIKOWANE**.
- **D5 — produkcja:** 3 akty, 3–5 min łącznie, ≤3 próby/akt, wybór deterministyczny „pierwsza ważna",
  odrzucone próby zachowane i raportowane — **RATYFIKOWANE**.
- **D6 — re-certy tokenu:** P1+P4+P5 **od nowa**, `certs_selfcheck` ×2, testy deterministyczne
  automatu; **P2/P2-ε/P2_vmax3p1 NIETKNIĘTE** z uzasadnieniem arytmetycznym — **RATYFIKOWANE**.

## Adnotacje ratyfikacyjne

- **A1 — korekta `PRE_D §0`:** `certs_selfcheck` to **6/6**, nie 5/5 (`P2_eps` istnieje od R0.3a,
  a `P2_vmax3p1` to osobny wpis prowieniencji tego samego provera `geofence.py`). Naniesione w
  `PRE_D.md §0` jako `> [KOREKTA A1, 2026-08-16, ratyfikowana]`; oryginalne zdanie zachowane.
  Baseline B1 potwierdzony pomiarem: `certs_selfcheck` PASS **6/6** na czystym HEAD `83c7e9c`.
- **A2 — montaż:** akty = **osobne booty**; montaż wyłącznie z **jawnymi cięciami** (plansza między
  aktami). Zero sugestii jednego ciągłego lotu.
- **A3 — architektura produkcji:** orkiestrator wieloaktowy **OUT**; akty produkowane na
  **per-akt runnerach** wyprowadzonych z istniejących `gate_run_r02` / `gate_run_r03`.

## Semantyka tokenu (ZAMROŻONA na potrzeby B1)

Fundament (recon R4): łańcuch `r01/authz.py` (HMAC-SHA256 `sign()`, `Authorizer.admit()`,
`mode_of()` rzuca `PermissionError` przy ≠ALLOW), zamknięta gramatyka `r01/language.py`, łańcuch
PCDL (`seq`, `prev_hash`, `sig`, `verify_chain()`). Punkt-dławik eskalacji w
`r02/gate_run_r02.py`: `observe_authority` (linia 187 init / 222–226 `admit_observe` / 389 eskalacja
`tick()` / 399 `shield.step`) — **numery zweryfikowane grepem 2026-08-16, zgodne z recon**.

1. **Default-deny.** Brak ważnego tokenu ⇒ eskalacja do OBSERVE niemożliwa; próba eskalacji
   (locked ∧ ¬`auth_ok`) ⇒ `REFUSE(NO_AUTH)`. Stan **odwracalny, nieterminalny** (wzorzec
   `POS_DEGRADED`, nie latch): tryb pozostaje bez eskalacji, patrol/confirm trwa.
2. **Token = podpisana komenda operatora** w zamkniętej gramatyce (`language.py`, nowy element
   `OBSERVE_GRANT` — żadnych free-form stringów), przez istniejący łańcuch `authz`, rozszerzony
   o `operator_id`, `nonce` (jednorazowy — reuse odrzucany), `admission_seq` (wiązanie do epizodu).
3. **Per-admisja, jawnie.** System NIE ma re-identyfikacji celu → „per-cel" operacyjnie = per
   **epizod admisji** (licznik `admission_seq`, inkrement na każdym ENTRY). Token ważny wyłącznie
   dla epizodu wydania; **konsumpcja na EXPIRE**; re-admisja (nowy epizod) wymaga nowego tokenu.
   Różnica **admisja ≠ tożsamość celu** ma być respektowana w napisach (B3) — zero roszczenia
   tożsamości.
4. **Pre-autoryzacja zakazana.** Token wydany poza aktywną admisją (¬`locked` albo zły
   `admission_seq`) jest **odrzucany i logowany**; nie „czeka" na przyszłe ENTRY.
5. **Kolejność dominacji reasons.** `R-G (GEOFENCE)` i `R-POS (POS_DEGRADED)` **dominują** nad
   `R-AUTH (NO_AUTH)`; token niczego nie otwiera poza OBSERVE i nie osłabia żadnego guardu wyżej.
   > [PROWIENIENCJA — inwersja R-G/R-POS] Kod zamrożony R0.3a ma **R-POS ponad R-G** (bariera na
   > niepewnej pozycji niewiarygodna — prekondycja geofence, §4/D3 `RAPORT_R03A`). To NIE jest
   > zmieniane. Dla R-AUTH istotne i egzekwowane jest: **R-AUTH poniżej OBU** (latch > R-POS > R-G >
   > … > gałąź OBSERVE, w której żyje R-AUTH). Wektory krzyżowe P5/testów potwierdzają dominację
   > R-G i R-POS nad R-AUTH.
6. **Minimalny TCB.** Osłona (`shield.step`) dostaje wejście boolowskie `auth_ok` i realizuje gałąź
   R-AUTH; wyliczenie `auth_ok` (podpis ∧ nonce świeży ∧ epizod zgodny ∧ niekonsumowany) żyje w
   warstwie `authz`/runnera i jest kryte P4 + testami deterministycznymi.
7. **Uczciwość roszczenia.** HMAC z kluczem lokalnym = demonstracja **bramkowania uprawnień**
   (authority gating), NIE „secure C2". Tak nazywać w raporcie i na planszach.
