# PRE_P2 — dokument przed budową (tor P2: rdzeń estymatora stanu celu pod nieregularną obserwacją)

Data: 2026-08-06. Poprzednik: `p2/recon_P2.md` (ETAP R). Kontekst: `RAPORT_R01.md` (port R0.1 zamknięty).

> **SZKIELET ZAMROŻONY** (od Olgi i CC). Wykonawca **nie proponuje alternatyw struktury** — wypełnia sloty **[PROPOZYCJA]** liczbami z reconu. **STATUS: RATYFIKOWANE 2026-08-06 z aneksami P2-A1…A4** (poniżej — wiążące, wpięte do §1/§2/§5/§6/§9). Rozbieżności (1)–(5) zaakceptowane w brzmieniu z PRE (w tym 12.5→13 i „anotacje, nie klatki"). Wariant B zatwierdzony, A jako fallback. **Budowa po naniesieniu aneksów; push teraz (Olga). STOP.**
>
> Sens P2: **jeden rdzeń zasila dwa tory** — figura na publicznym wideo (offline) + komponent kanału celu w R0.2 (pętla). Werdykt offline **wybiera kandydata**, nie przesądza pętli (lekcja 3d, §8).

---

## ANEKSY P2-A1…A4 (wiążące, ratyfikowane 2026-08-06)

- **A1 — modalność + licencja:** kanoniczna modalność = **IR**; RGB co najwyżej jako **osobno raportowany split** (nie miesza się z werdyktem IR). Współrzędne (cx,cy,w,h) **znormalizowane do rozdzielczości modalności IR**. Anotacje **challenge per-klatka** (rozbieżność 4). Licencja: **kod MIT ≠ warunki samego datasetu** — figura z **krzywych/metryk = bez ryzyka**; ewentualne **przykładowe klatki** w publikacji = do sprawdzenia dopiero przy pisaniu. → §1.
- **A2 — krok 0 = PRE-uzupełnienie:** reguły decyzyjne kroku 0 zapisane **Z GÓRY i deterministyczne** (w tym reguła progu długości, gdy sekwencji ≥30 s za mało). Krok 0 kończy się **commitem ZAMRAŻAJĄCYM splity, maski i statystyki PRZED pierwszym treningiem**, i **ten commit idzie na push przed treningiem** — zewnętrzny znacznik zamrożenia przed pomiarem. **Kryteria werdyktu po kroku 0 NIETYKALNE.** → §2, §9.
- **A3 — baseline mocny:** Kalman CV / IMM dostają **prawdziwe σ** wstrzykniętego szumu (macierz R = σ²), **albo** strojenie **wyłącznie na train** wg procedury zapisanej w PRE — jawnie. Teza przeciwko **mocnemu filtrowi**, nie słomianemu. → §5, §6.
- **A4 — Mamba:** dopuszczona **referencyjna implementacja czysto-PyTorch (S6)**, **jedna wspólna** dla wariantu time-blind i +Δt; wydajność kerneli nieistotna przy tej skali. → §5.

---

## §1 — Dataset (z reconu R1)

**Wariant B — oryginał Anti-UAV (ZhaoJ9014).** fps **25**. Split predefiniowany **po SEKWENCJACH**: train 160 / val 67 / **test 91 (ZAMROŻONY przed treningiem)**. Gęstość ≈ per-klatka. Rekomendacja i uzasadnienie: `recon_P2.md` R1.
- **[A1] Modalność kanoniczna = IR.** Werdykt (§7) liczony wyłącznie na boxach IR. **RGB — co najwyżej osobno raportowany split** (nie miesza się z werdyktem IR). Współrzędne (cx,cy,w,h) **znormalizowane do rozdzielczości modalności IR** (nie obrazu RGB). Anotacje **challenge per-klatka**.
- **[A1] Licencja — rozróżnienie:** **kod repo = MIT**; **warunki samego datasetu = odrębne**. **Figura z krzywych/metryk** (RMSE/ADE/FDE vs horyzont/p/L) — **bez ryzyka licencyjnego** (nie zawiera treści datasetu). **Przykładowe klatki** w publikacji — **do sprawdzenia dopiero przy pisaniu figury**, nie blokuje budowy (P2 uczy się na boxach, nie klatkach — rozbieżność „anotacje, nie klatki").
- **Krok 0 budowy (przed protokołem):** pobrać etykiety B (per-klatka, wersja challenge — NIE coarse baza 2021), policzyć: rozkład długości, **licznik sekwencji ≥ 30 s**, **rate naturalnych dziur** (frakcja exist=0 + rozkład długości dziur). Zainstalować torch, zbenchmarkować rdzeń.
- Fallback: wariant A (Anti-UAV410, IR, 410 seq) — po weryfikacji kompletności flag i licencji.

## §2 — Protokół wyroczni [szkielet zamrożony; liczby [PROPOZYCJA]]

Gęste GT (per-klatka box) traktowane jako **detekcje wyroczni**, na które nakładamy:
1. **Szum obserwacyjny σ jako frakcja rozmiaru boxa** — [PROPOZYCJA] nominał **σ = 0.05** (per-oś: σ_cx=0.05·w, σ_cy=0.05·h, σ_w=0.05·w, σ_h=0.05·h, szum gaussowski i.i.d.). Siatka robustności [PROPOZYCJA]: **σ ∈ {0.02, 0.05, 0.10}**.
2. **Maski nieregularności** — model dziur obserwacyjnych:
   - **Bernoulli p** (frakcja klatek zamaskowanych/miss): [PROPOZYCJA] siatka **p ∈ {0.3, 0.5, 0.7}**.
   - **Burst L** (długość ciągłej dziury w klatkach): [PROPOZYCJA] siatka **L ∈ {13, 25, 50}** kl (= horyzonty predykcji, §4).
   - Punkt operacyjny nominalny [PROPOZYCJA]: **(p=0.5, L=25)**.
   - **„Duch G2"**: naturalne dziury `exist=0` z datasetu (realna struktura dropoutu) nakładane jako **referencja realizmu** — sprawdzian, czy syntetyczne maski Bernoulli+burst przypominają realny dropout (rate + rozkład długości z kroku 0). Nie zastępują masek syntetycznych; są kontrolą.
3. **Seedy przypięte:** seed splitu = predefiniowany split B (jeśli re-split — [PROPOZYCJA] seed **1234**); **seedy masek [PROPOZYCJA] {0,1,2,3,4}**; test zamrożony przed treningiem (żaden bieg strojący nie dotyka testu).

## §3 — Interfejs rdzenia [zamrożony]

- **Wejście 5-dim: (cx, cy, w, h, age/Δt)** — jak kanał celu LiquidSight, z jawnym **wiekiem obserwacji** (Δt od ostatniej detekcji; przy masce age rośnie, przy detekcji zeruje).
- **Wyjście:** (a) **estymata** stanu w chwili bieżącej; (b) **predykcje na horyzontach** {0.5, 1, 2} s.
- Normalizacja: box w jednostkach obrazu (cx,cy,w,h ∈ [0,1]); RMSE/ADE/FDE w tych jednostkach (raport także w pikselach/rozmiarze boxa).

## §4 — Metryki [zamrożone]

Horyzonty (z reconu R2, fps=25): **{0.5, 1, 2} s = {13, 25, 50} klatek** (0.5 s = 12.5 → 13, round-up; jawnie).
- **Filtracja: RMSE w chwilach OBSERWACJI** (klatki niezamaskowane) — jak dobrze rdzeń odtwarza stan gdy widzi detekcję.
- **Predykcja: ADE/FDE w głąb DZIUR** — na horyzontach {13,25,50} kl; ADE = średni błąd po dziurze do horyzontu, FDE = błąd na końcu horyzontu. Liczone na dziurach z dostępnym GT (do porównania).

## §5 — Ramiona (parytet parametrów ±2%) [zamrożone]

Budżet rdzenia ~**30k parametrów**; ramiona uczone dostrojone szerokością ukrytą do **±2%** tego budżetu.
| Ramię | Typ | Uwaga |
|---|---|---|
| **ZOH-age** | kotwica (0 param) | trzymaj ostatnią detekcję z wiekiem age — dolna kotwica |
| **Kalman CV** | analityczny (mocny) | constant-velocity, update Δt-aware (age); **[A3] R = σ² (PRAWDZIWE σ szumu)** |
| **IMM** | analityczny (mocny) | mieszanka (CV + CA / CV + stationary); **[A3] R = σ² (prawdziwe σ)** |
| **GRU+Δt** | uczony ~30k | Δt jako wejście |
| **CfC** | uczony ~30k | closed-form continuous-time |
| **Mamba bez czasu** | uczony ~30k | **[A4] S6 czysto-PyTorch**, wariant time-blind |
| **Mamba+Δt** | uczony ~30k | **[A4] TA SAMA implementacja S6**, wariant +Δt |
| **latent-ODE (mały)** | uczony ~30k | **opcjonalnie**, jeśli budżet §9 pozwoli |

**[A3] Baseline MOCNY (nie słomiany):** Kalman CV / IMM dostają **prawdziwe σ** wstrzykniętego szumu obserwacyjnego (macierz obserwacji R = σ²·I dla σ z §2). **Wariant alternatywny (jeśli tak zdecyduje build):** strojenie Q/R **wyłącznie na train** wg procedury zapisanej w PRE (grid Q na train, wybór po val, zero dotykania testu) — **jawnie odnotowane, które wariant użyty**. Teza §7 ma bić mocny filtr.
**[A4] Mamba:** **jedna wspólna referencyjna implementacja S6 czysto-PyTorch** dla obu wariantów (time-blind i +Δt) — różnica wyłącznie w podaniu Δt; wydajność kerneli nieistotna przy tej skali.

Analityczne (ZOH/Kalman/IMM) — bez treningu. Uczone — trening identyczny (§6).

## §6 — Trening [zamrożony]

- **Identyczny dla wszystkich uczonych:** te same seedy danych/masek, ten sam optymalizator/harmonogram, ta sama liczba epok.
- **best-val z JAWNYM selektorem epoki (lekcja F-3b-3):** kryterium wyboru epoki zapisane wprost (np. min val **FDE @ 25 kl**), zero ukrytego early-stop; log wybranej epoki + kryterium w artefakcie.
- **PRECONDITION (brama sensowności): każde ramię uczone MUSI bić ZOH-age na FILTRACJI RMSE** (w chwilach obserwacji). Jeśli nie → **FAIL_EARLY** (ramię wypada z porównania predykcji, raportowane jako fail — nie ukrywane).

## §7 — Teza główna (dwustronna) [zamrożona]

**Czy najlepsze ramię uczone bije Kalman/IMM (lepszy z dwóch) na PREDYKCJI W DZIURY (ADE/FDE @ horyzonty) o margines > `pooled_std`?**
- `pooled_std` = odchylenie zpoolowane po **(sekwencje × seedy masek × seedy treningu)**.
- **Dwustronnie:** margines ≤ pooled_std (przedziały się nakładają) → **WYNIK NULL**; Kalman/IMM ≥ uczone → **WYNIK NEGATYWNY**.
- **WYNIK NULL / NEGATYWNY = PEŁNOPRAWNY WYNIK** (nie zmiękczamy, nie ścigamy pozytywu).

## §8 — Lekcja 3d (jawnie) [zamrożona]

Werdykt offline **wybiera KANDYDATA** rdzenia do R0.2 — **nie przesądza wyniku w pętli**. Arbitrem finalnym jest **bramka w pętli zamkniętej** (możliwa **inwersja proxy↔pętla**: ranking offline może się odwrócić w pętli — `RAPORT_3D`). **Figura na publicznym wideo raportuje TYLKO to, co zmierzono offline** (predykcja w dziury) — nie twierdzi o wydajności w pętli sterowania.

## §9 — Krok 0, stop-rules, budżet, rozbieżności

### [A2] Krok 0 — reguły decyzyjne Z GÓRY, deterministyczne, zakończone commitem zamrażającym
Reguły ustalone **przed** jakimkolwiek pomiarem (nietykalne po kroku 0):
1. **Modalność/split:** IR (A1); split predefiniowany B (160/67/91) po sekwencjach; test 91 zamrożony.
2. **Reguła progu długości (deterministyczna):** próg pierwotny **T_min = 30 s** (750 kl). Sekwencja kwalifikuje się do EWALUACJI, jeśli długość ≥ T_min **oraz** zawiera dziurę mieszczącą horyzont 2 s (50 kl) + kontekst. **Jeśli test ma < N_min = 30 sekwencji kwalifikujących**, obniżaj T_min po **drabinie {30, 20, 15, 10} s** do pierwszej wartości dającej ≥ N_min; **zapisz wybrane T_min**. Jeśli przy T_min < 20 s wciąż < N_min → **odrzuć horyzont 2 s** (zostają {0.5, 1} s = {13, 25} kl), odnotowane jawnie.
3. **Maski:** siatka (p, L, σ) z §2, seedy masek {0..4}, seed splitu 1234 — **realizacje wyznaczone deterministycznie z seedów** (odtwarzalne).
4. **Statystyki do zamrożenia:** rozkład długości, licznik ≥ T_min, **rate naturalnych dziur** (frakcja exist=0 + rozkład długości dziur — „duch G2"), porównanie z syntetyczną siatką (p,L).
5. **Baseline (A3):** ustalić wariant Kalman/IMM — **R = σ² (prawdziwe σ)** [domyślny] lub strojenie Q/R wyłącznie na train wg procedury zapisanej tu — **zapisać który**.
- **Commit zamrażający** (koniec kroku 0): zamraża split (ID sekwencji), realizacje/seedy masek, σ i siatkę, wybrane T_min, statystyki oraz wariant baseline — **PRZED pierwszym treningiem**. **Ten commit idzie na PUSH przed treningiem** = zewnętrzny znacznik zamrożenia przed pomiarem. **Kryteria werdyktu (§4/§6/§7) po tym commicie NIETYKALNE.**

**Stop-rules:**
- **FAIL_EARLY** (§6): ramię nie bijące ZOH na filtracji → poza porównaniem predykcji, raportowane.
- Żadne uczone nie bije Kalman/IMM o > pooled_std → **WYNIK NULL** (raport, koniec — nie strojenie pod pozytyw).
- **Test zamrożony**: nie dotykać testu do finalnego werdyktu; strojenie wyłącznie na val.
- **Selektor epoki jawny** (F-3b-3) — brak ukrytego early-stop.
- **Compute overrun**: przekroczenie budżetu → redukcja siatki/seedów **JAWNIE odnotowana** (nie ciche obcięcie).

**Budżet sesji [PROPOZYCJA] (z reconu R3):** ~15 min/run worst-case (realnie 3–8 min). ~**25 runów** (5 uczonych × 5 seedów treningu) ≈ 2–6 h; seedy masek {0..4} × siatka (p,L,σ) w EWALUACJI (tanie, bez re-treningu). **~2–3 sesje:** (1) dane (krok 0) + protokół + ramiona analityczne + precondition; (2) trening uczonych + ewaluacja po siatce/seedach; (3) werdykt (teza §7) + figura + `RAPORT_P2.md`.

**Rozbieżności / do domknięcia w budowie (jawnie):**
1. Dokładny rozkład długości, **licznik ≥30 s**, **rate naturalnych dziur** — NIE policzone w recon (etykiety nie w repo git) → krok 0.
2. **torch nie zainstalowany** → build; precyzyjny benchmark (R3) po instalacji.
3. Horyzont 0.5 s = 12.5 kl → **13** (round-up) — jawnie.
4. Wariant B: użyć anotacji **challenge (per-klatka)**, nie coarse bazy 2021 — potwierdzić gęstość splitu.
5. Wariant A (410) jako fallback — licencja i kompletność flag do weryfikacji.

**RATYFIKOWANE z aneksami A1–A4. Budowa: krok 0 (dane + reguły §9 [A2]) → COMMIT ZAMRAŻAJĄCY → PUSH przed treningiem (znacznik zewnętrzny) → protokół §2 → ramiona §5 → trening §6 → teza §7 → RAPORT_P2. Kryteria werdyktu po kroku 0 nietykalne. Push teraz (Olga). STOP na PRE.**
