# ANEKS_D8 — DEMO-B: konflikt sędzia↔GT-fed na A2 (RATYFIKOWANY §2, 2026-08-20)

Aneks do `ANEKS_D1..D7`. §2 ratyfikowany dokumentem CC (wklejenie z `PROMPT_D_P3` = ratyfikacja Olgi).
**Push = Olga.** Sędzia `79b1e936…` NIETKNIĘTY (SR-M1).

## §2 — Addendum po znalezisku konfliktu sędzia↔GT-fed

Kontekst: pod ANEKS_D6 (kanał GT-fed) + ANEKS_D7 (habitat) próby A1→A3→A2. **A1 VALID, A3 VALID**
(sędzia ∧ habitat). **A2 zablokowane strukturalnie** (patrz §2a).

### §2a — Znalezisko przyjęte jako WYNIK, nie usterka

Pod kanałem GT-fed **`conj.mti_ok` NIE jest liczone** (`None` w 1182/1182 tickach — `_channel_step`
gałąź gt woła `on_frame(box, t, gt_present=…)` BEZ `mti_ok`; GT-fed = idealizowany detektor karmiony
pozą GT, nie liczy frame-diff MTI). Kryterium sędziego `judge_A2.readmit_full_conjunction` wymaga
`box ∧ central ∧ mti_ok` (wszystkie prawdziwe) przy re-ENTRY (`admission_seq=1`) ⇒ **kategorialnie
niespełnialne** pod GT-fed. Deterministyczne (nie stochastyczne).

Sędzia `79b1e936` **NIETKNIĘTY** — zakaz „poprawiania" go pod przechodzenie prób (dokładnie ryzyko,
przed którym chroni freeze; ustawienie `mti_ok=True` twierdziłoby o koincydencji MTI, która nie
zaszła — nieuczciwe). **Wniosek strukturalny do RAPORTU: GT-fed NIE ćwiczy koniunktu RUCHU, więc nie
wolno nim twierdzić niczego o PEŁNEJ bramie.** (Niewidoczne w B4: far w FOV → brak EXPIRE → re-admisja
nieosiągnięta; ANEKS_D6 §2 naprawił EXPIRE i odsłonił głębszy konflikt.)

### §2b — Fallback zmieniony (zastępuje G2/G3 w zakresie A2)

Demo obejmuje **A1 + A3**. **A2 pod GT-fed jest NIEOSIĄGALNE — nie wolno go próbować.** Decyzja o A2
w wariancie GT-fed (rozszerzenie zakresu sędziego o predykat kanału idealizowanego vs usunięcie A2
z dema) wraca OSOBNYM dokumentem — nie jest pre-ratyfikowana, nie zapada w tej sesji.

### §2c — Licznik prób

Próby pod konfiguracją zastąpioną dokumentem (inny kanał detekcji / inne hashe spec) = **INVALID-
by-configuration**: zachowane i wyliczone w raporcie, ale NIE obciążają budżetu ≤3 nowej konfiguracji.
Reset liczy się WYŁĄCZNIE przy ratyfikowanej zmianie konfiguracji — nigdy jako sposób na przedłużenie
prób w tej samej konfiguracji.

### §2d — Nienaruszone (zweryfikowane elementy A2)

**EXPIRE (θ_age=3.0), re-admisja seq 0→1, dwa tokeny (wydane+skonsumowane), habitat pod APPLY_HZ=2**
zostają jako ZWERYFIKOWANE elementy A2 (proba_2: `n_expire=2`, `granted_seqs=[0,1]`, habitat VALID
ep0/ep1/expire Δsim/Δwall 0.996–0.998, frac<0.5=0). Wracają do gry w wariancie **LIVE** bez ponownego
dowodzenia mechanizmu (poza re-bramką T2b — profil live zmienia FOV).

## Stan prób (do RAPORTU §FINAL)

| akt | bieg | habitat | sędzia | status |
|-----|------|---------|--------|--------|
| A1  | proba_1 | VALID | VALID 5/5 | **VALID** (klip) |
| A3  | proba_1 | VALID | VALID 3/3 | **VALID** (klip) |
| A2  | proba_1 | INVALID (koszt: dipy FF→spurious EXPIRE) | INVALID | attempt (INVALID) |
| A2  | proba_2 | VALID | INVALID (mti_ok kat.-niespełn., §2a) | attempt (INVALID-strukturalny) |

Montaż B6 = **A1 + A3** (materiał osądzony, plansze §1c).
