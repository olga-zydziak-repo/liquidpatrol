# ANEKS_KONT-5 — werdykt S4: drabina daje FAIL przez (b) w 1/12 epizodów (obwiednia nauczyciela za ciasna dla sieci o 11.3%), cała reszta czysta; dwie drogi — zamknięcie nogi z liczbami ALBO ratyfikowany cykl K5 (obwiednia sieci, T* ≈ 10–13 s, świeże potwierdzenie)

CC · 8.11.2026 · łańcuch KONT, po STOP-KONT4-BUDZET-F (0f4e6a25 na
origin). Dokument dwudrogowy: §CO-Z przy sygnale Olgi **„zamykamy"**,
§CO-K5 przy **„ratyfikuję K5"**. Sygnały bez numeru odrzucasz.

## §1. Weryfikacja CC z repo

- `kont_s4_analyze.py` uruchomiony u CC na c11_s01: `wyniki_s4.json`
  **identyczny bajtowo** (część ulogowa z committed wyciągu; sam ulog
  poza gitem). Kryteria (c)(d) zweryfikowane tą reprodukcją.
- Niezależna pętla CC po 12 cięciach (własny kod, trace, obwiednia
  z `s2_freeze_bf.json`): 11/12 bez naruszeń (ratio 0.74–0.95),
  **c11_s01 narusza obwiednię w rejonie płaskim** (u CC ε_max 3.67
  przy 3.478; kanonicznie 3.872, ratio 1.113, 548/1411 ticków od
  ~14.9 s). Metoda zgrubna CC daje też pozorne naruszenie w pierwszych
  0.1 s — artefakt offsetu T_home metody zgrubnej, nieobecny w
  kanonicznym; nazwane, nie propagowane.
- Wyciągi ulogów: flaga przy cięciu 0.000/0.004 s (A-flag trzyma),
  nav_state 14 do REFUSE, zero natywnego failsafe w cięciach — (e) ✓.
- Zaległe weryfikacje: V2P nom_b1_r3 = 0.887/0.879/0.858/0.856
  (zgodne); mitygacja D5-diag działa na żywo w 15/15 bootów kolejki f
  (yaw po reinicie 6.16–6.45°).
- Budżety: S4 21/21, noga 45/45; wada kolejki f (utrata nom_b2 z listy
  `pozostało`) potwierdzona w commitach; przyczyna spowolnień
  stanowiska znaleziona przez Olgę: tryb zasilania (cichy → wydajny;
  od zmiany 0.972–0.981).

## §2. Werdykt drabiny (mechanicznie, PROMPT_KONT_S4 §2)

**FAIL przez (b):** c11_s01 przekracza zamrożoną obwiednię ε_b.
Litera „przekroczenie = FAIL nogi, nie strojenie" obowiązuje. Znaczenie
mechaniczne: założenie A-kont — obwiednia dryfu zdjęta z 8 lotów
nauczyciela — nie przenosi się na sieć w 1/12 komórek; dowód P9_kont
nie obejmuje tego epizodu (jego przesłanka była tam fałszywa).
Zawieranie fizyczne nie ucierpiało: margines do R_E ≥ 8.5 m w każdym
epizodzie. Luka pokrycia osobno: nominały 2/3 bootów (8/12 epizodów;
ramię (−) = 20 zamiast 24, wszystkie czyste) — to brak pomiaru przez
wadę kolejki, nie porażka kryterium.

## §3. Co stoi niezależnie od drogi (zdania do kanonu)

1. Sieć NCP-20 pod odcięciem GNSS prowadzi zadanie na przepływie
   optycznym przez pełne 21.9–22.0 s w 12/12 epizodów; REFUSE(T*)
   w deadline 12/12; offboard do REFUSE i zero natywnego failsafe;
   zero naruszeń R_E (margines ≥ 8.5 m); zero fałszywych wejść
   w 20 epizodach ramienia nominalnego; R-G-NOM 0.
2. Dowód zawierania P9_kont obowiązuje dla epizodów spełniających
   A-kont: 11/12. W c11_s01 obwiednia nauczyciela okazała się za
   ciasna o 11.3% — dla tego epizodu zawieranie jest zmierzone,
   nie dowiedzione.
3. Dopisek obowiązkowy: SITL, grunt z dekalem pod przepływ, bez
   wiatru; T* = 22 s z obwiedni nauczyciela (n = 8).

## §4. Dwie drogi

**Droga Z — zamknięcie teraz.** Noga CLOSED z werdyktem „S4 FAIL(b)
po literze; zdolność zmierzona, dowód pokrywa 11/12". KSIĘGA §5,
KIERUNKI §6, raport programu aktualizuje CC poza repo.

**Droga K5 — cykl naprawczy (budżet +7: noga ≤ 52, do ratyfikacji).**
Mechanizm: obwiednię trzeba zdjąć z lotów SIECI, nie nauczyciela.
1. Przy biurku (0 bootów): `freeze` obwiedni sieci kanonicznym
   analizatorem z 12 cięć S4 (reguła PRE §3 bez zmian: 1.5 × max per
   koszyk; Δ_D5_net = 1.5 × max δ zejść = 1.394); wstępna arytmetyka
   CC (metoda zgrubna): **T*_net ≈ 10–13 s** — nad progiem śmierci
   10 s, ale wyraźnie mniej niż 22. Kanoniczne przeliczenie może
   wyjść pod 10 ⇒ wtedy zamknięcie liczbami Z bez lotów (prereg).
2. P9_kont od nowa na obwiedni sieci (nowy cert obok, stary zostaje).
3. Loty świeże (nie te, z których zdjęto obwiednię — bez cyrkularności):
   **4 cięcia potwierdzające** (c11 ×2 + dwie komórki losowane
   z siatki) sądzone kryteriami (a)–(e) z (b) na obwiedni sieci
   i T*_net, plus **1 boot nominalny nom_b2** (domyka ramię (−) do
   24). Śmierć: jakiekolwiek naruszenie nowej obwiedni w świeżym
   locie ⇒ CLOSED liczbami Z; inaczej noga CLOSED PASS z T*_net.
4. Budżet: 4 + 1 + 2 rezerwy = 7; limit nogi 45 → 52 (wymaga
   ratyfikacji — PRE przekroczone, nazwane wprost).

**Rekomendacja CC: droga Z.** Uzasadnienie: wynik nogi już istnieje
i jest mocny w obu wersjach (12/12 zmierzone end-to-end, mechanizm yaw
nazwany i usunięty, T* = 22 s jako liczba charakteryzacji); K5 wymienia
„zmierzone" na „dowiedzione", ale przy T* zbitym do ~10–13 s — słabsza
liczba za ~2 wieczory i podniesienie limitu PRE. Przeciw Z: luka nom_b2
zostaje luką, a dowód luką 1/12. Decyzja należy do sygnału.

## §5. KSIĘGA (append-only; przy CO-Z pełna, przy CO-K5 bez P-KONT-5/6
— te rozliczy zamknięcie K5)

```
## KONT S4 i zamknięcie nogi (ANEKS_KONT-5, 8.11.2026)
- Drabina S4: FAIL przez (b) w c11_s01 (ε/ε_b 1.113, 548/1411 ticków,
  od 14.9 s) — obwiednia nauczyciela (n=8) za ciasna dla sieci w 1/12;
  pozostałe 11/12 ratio ≤ 0.999. (a)(c)(d)(e) 12/12; ramię (−) 20/24
  czyste (nom_b2 brak — wada kolejki f: lista z `pozostało` przerwanej
  kolejki zamiast siatka−ważne).
- P-KONT-5 (0.60, S4 PASS) — ✗. P-KONT-6 (0.90, breach 0) — ✓
  (45 bootów, 0 naruszeń w całej nodze).
- Wady wykonawcy (seria S4): ROOT w kopii drivera (1 boot); kontrola
  yaw po starcie intruder_motion (sieroty); kolejka bez kontroli V2′
  i V2′ liczona niekanonicznie; próbnik zegara dopisuje zamiast
  nadpisać (fałszywy STOP); lista pozycji z `pozostało` (utrata
  nom_b2). Każda nazwana w swoim STOP-ie, żadna nie skaziła liczb.
- Stanowisko: przyczyną spowolnień był tryb zasilania Windows
  (cichy → wydajny: 0.86–0.89 → 0.97–0.98) — znalazła Olga; launcher
  s2y (gz przed PX4) leczy 14/14 FAIL drugiego bootu, ale psuje
  inicjalizację estymatora w ~połowie bootów (bias/yaw) — mitygacja:
  wymuszony reinit EKF2 w preflight + kontrola kierunku ≤ 10°
  (skuteczna 15/15); watchdog biasu nie wykrywa złego yaw (mierzy
  nie tę obserwowablę).
- Lekcja nogi: obwiednia błędu zdjęta z nauczyciela nie jest
  obwiednią sieci — założenie o rozkładzie błędu musi być mierzone
  na tym samym sterowniku, którego dotyczy dowód (kuzyn „zadany ≠
  faktyczny", piąta instancja w programie).
```

## §6. KIERUNKI (append-only; wersja drogi Z — przy K5 dopisek pisze
zamknięcie K5)

```
## Dopisek stanu katalogu — 8.11.2026 (CO-KONT-Z, ANEKS_KONT-5)
- **2d KONTYNUACJA PO UTRACIE GNSS — CLOSED.** Zdolność zmierzona
  end-to-end w SITL: sieć pod odcięciem GNSS prowadzi zadanie na
  przepływie optycznym pełne 22 s w 12/12 epizodów (REFUSE w deadline,
  offboard do końca, zero natywnego failsafe, zero naruszeń R_E przy
  marginesie ≥ 8.5 m, zero fałszywych wejść w 20 epizodach ramienia
  nominalnego). Dowód zawierania P9_kont (+P1/P5/P7_kont, replikacja
  CC) obowiązuje przy założeniu A-kont, spełnionym w 11/12 — w c11_s01
  obwiednia nauczyciela za ciasna o 11.3% ⇒ S4 formalnie FAIL(b),
  epizod zmierzony, nie dowiedziony. Mechanizmy nazwane po drodze:
  skok yaw akcji D5 pod przepływem (usunięty trzymaniem yaw),
  ściana natywna 4 s na samym IMU, obwiednia nauczyciel≠sieć.
  Liczby: T* = 22 s (obwiednia nauczyciela), Δ_D5 1.524, R_nom 27.30,
  koszt bariery 0/48. Budżet 45/45. Kierunek ewentualnego powrotu
  (nowa pozycja, nieotwarta): obwiednia sieci + świeże potwierdzenie
  (szac. T*_net 10–13 s, +7 bootów).
- Katalog: 6 pozycji, 2d zamknięta. Breach 0 / REFUSE(POS) fałszywych 0
  programowo bez zmian (45 bootów nogi, łącznie ~185 bootów programu).
```

## §CO-Z (sygnał „zamykamy")

Bramka: origin/master == **0f4e6a25**. Jeden commit: korzeń
`ANEKS_KONT-5.md` (verbatim, byte-check sha256 z wiadomości CC),
`KIERUNKI_PO_PLANIE.md` += §6, `results/KSIEGA_PREDYKCJI.md` += §5.
Raport płaski, STOP. Push = Olga; CC sprawdza byte-check i append-only,
potem aktualizuje raport programu (poza repo).

## §CO-K5 (sygnał „ratyfikuję K5")

Bramka jak wyżej. Commit 1: aneks verbatim + KSIĘGA §5 (bez P-KONT-5/6).
Potem §4 K5 pkt 1 (desk; wynik < 10 s ⇒ przejście na §CO-Z bez lotów),
pkt 2 (cert), pkt 3 (loty), raport STOP-KONT5, push, werdykt CC
w ANEKS_KONT-6.
