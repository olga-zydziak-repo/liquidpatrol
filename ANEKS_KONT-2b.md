# ANEKS_KONT-2b — po NOTA-2B: sonda zamienia się z brake-first na trzymanie yaw (wariant Y), bisekcja dwóch czynników zamiast jednego zakładu; wymaga ratyfikacji „ratyfikuję 2Y"

CC · 6.11.2026 · łańcuch KONT, po NOTA-2B (12a02db6 na origin). Zastępuje
§3B i regułę (a)/(b) ANEKS_KONT-2; drogi Z i §4 (KSIĘGA) zostają. Budżet
bez zmian (S2′ 5/12, noga 21/45). Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- Korelacje noty odtworzone niezależnie co do setnej: obrót~wektor skoku
  Pearson 0.84 / Spearman 0.80, obrót~rezyduum 0.91 / 0.90 (n = 5).
- Produkcyjne D5 komenduje yaw = 0 — potwierdzone cytatem:
  `gate_run_r03.py:284` `VelocityNedYaw(0, 0, vdesc, 0)`; sonda tak samo.
  Skok yaw przy zejściu: 51–134° w 3 s, rate do 3.1 rad/s wobec p99
  orbity ~0.4 rad/s. To własność akcji D5 nienazwana od R0.3a — pod
  GNSS i pod czystym zliczeniem była łagodna, pod przepływem jest
  głównym podejrzanym (derotacja przepływu przy szybkim obrocie).
- **Zatrzymanie lotów przez wykonawcę było słuszne:** reguła (a) z 2B
  zamknęłaby nogę z fałszywym uzasadnieniem, bo brake-first zachowywał
  skok yaw.
- ✗ CC do KSIĘGI (przy zamknięciu): zdanie §3B „równoczesność jest
  jedynym wspólnym czynnikiem" było fałszywe; w zdaniu kanonicznym
  drogi Z „≤ 2.4 m" ma być **„≤ 2.5 m"** (maksima 1.93–2.49 w 4/5).
  Wada wykonawcy nazwana (d4c nie rozłożył osi rate) — też do KSIĘGI.

## §2. Nowa sonda: wariant Y (bisekcja czynników)

Zasada: dwa podejrzane czynniki (skok yaw; hamowanie równoczesne
z opadaniem) rozdziela się dwiema sondami jednoczynnikowymi, nie jednym
zakładem na oba naraz.

**Sonda Y (pierwsza, 3 loty):** D5 bez żadnej innej zmiany, ale yaw
w zejściu = heading z chwili decyzji, trzymany do przyziemienia
(`VelocityNedYaw(0, 0, vdesc, yaw_decyzji)`). Hamowanie równoczesne
zostaje — względem 5 zmierzonych lotów zmienia się dokładnie jeden
czynnik, więc metryka D4 (wektor skoku 3 s od decyzji vs maksimum
własnych okien kontrolnych; `kont_d4.py` metodą bez zmian, nakładka
z listą lotów) jest wprost porównywalna.

- Loty: **c11_s04, c08_s02b, c02_s01** (kontynuacje uzupełniają ε_b do
  n = 8; zejścia dają Δ_Y). Asercja startowa |błąd yaw| ≤ 10° jak w 2B.
- **Reguła Y (prereg, mechaniczna):**
  - (Y-a) wszystkie 3 zejścia z wektorem skoku ≤ kontrola ⇒ mechanizm =
    skok yaw. Zamrożenie kopią `kont_s2_freeze_bf.py`: ε_b z 8
    kontynuacji, **Δ_D5 = 1.5 × max Δ z zejść Y**, stara Δ obok; T*
    i R_nom regułą PRE §3. **T* ≥ 10 s ⇒ ANEKS_KONT-3 zamraża i noga
    idzie do S3 z akcją „D5 + trzymanie yaw"** (zmiana akcji najmniejsza
    z możliwych; w S3 obowiązkowy punkt: czy któryś cert zakłada yaw = 0
    — sprawdzić cytatem, nie z pamięci). **T* < 10 s ⇒ CLOSED.**
  - (Y-b) którekolwiek zejście Y > kontrola ⇒ yaw nie jest jedyną
    przyczyną ⇒ **sonda B-yaw, ostatnia** (≤ 3 loty, budżet): brake-first
    z 2B **plus** trzymanie yaw — względem Y zmienia się znowu jeden
    czynnik (równoczesność). Metryka w dwóch oknach (od decyzji i od
    początku opadania, nota §4.3). Wszystkie zejścia ≤ kontrola ⇒
    mechanizm = równoczesność, zamrożenie jak wyżej z Δ z zejść B-yaw;
    inaczej ⇒ **CLOSED** liczbami drogi Z ze zdaniem: „odjazd występuje
    także bez skoku yaw i bez hamowania równoczesnego — mechanizm
    w fuzji przepływu, niezmierzony". Po B-yaw nie ma trzeciej sondy.
- Budżet: Y 3 + ewentualne B-yaw ≤ 3 + dolecenia — mieści się w S2′ ≤ 12.

## §3. Porządki narzędziowe (nota §4, wszystkie przyjęte; NOWE pliki,
bo s2d-pliki wyprodukowały już loty i wyjątek 1d wygasł)

1. `kont_s2_freeze_bf.py` — kopia freeze_g: Δ wyłącznie z zejść sondy
   (lista lotów argumentem), ε_b ze wszystkich ważnych; n kontynuacji
   ≥ 8 nadal wymagane.
2. Nakładka na `kont_d4.py` z listą lotów argumentem; metryka bajtowo ta
   sama.
3. `descent_start` = chwila decyzji; dla Y okna się pokrywają, dla
   B-yaw raport w dwóch oknach.
4. Nowe kopie: `harness/kont_boot_s2y.sh` (probe_y zamiast probe),
   `results/KONT/tools/kont_s2_probe_y.py` (yaw-hold + asercja yaw),
   kolejka `kont_s2_campaign_y.py` (przeskoki liczone od startu, 1e §2;
   strażniki 1b bez zmian).
5. Zdanie kanoniczne drogi Z: korekta na „≤ 2.5 m w 4/5 lotów
   (najgorszy 4.0 m)" — obowiązuje, jeśli kiedykolwiek wykona się §CO-Z.
6. Koszt bariery do rozliczenia P-KONT-4 przy zamknięciu: **6/48
   scenariuszy ponad R_nom 24.83** (r4_margin.json, za notą §5).

## §4. CO (sygnał „ratyfikuję 2Y")

Bramka: origin/master == **12a02db6**. Commit 1: korzeń
`ANEKS_KONT-2b.md` verbatim, byte-check sha256 z wiadomości CC. Commit 2:
pliki §3 (nowe). Potem loty Y, raport NOWY
`results/KONT/s2/RAPORT_KONT_S2f.md` (werdykt Y-a/Y-b, tabela jak D4
+ Δ per zejście, dwie krzywe ε_b: n = 8), sygnał **STOP-KONT2f**;
przy Y-b dalej B-yaw w tej samej sesji tylko po osobnym podpisie CC
w prompcie — domyślnie STOP po Y. Push = Olga. CC przelicza z repo
i wydaje ANEKS_KONT-3 (zamrożenie albo zamknięcie).

Jeśli zamiast tego pada sygnał „zamykamy" — §CO-Z z ANEKS_KONT-2
z korektą §3.5 tego dokumentu.
