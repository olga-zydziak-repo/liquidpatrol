# ANEKS_REAKW-1 — dźwignia sfalsyfikowana deskiem: zamknięcie pozycji RE-AKW + erratum CC + dwie nowe pozycje katalogu (CO-REAKW)

CC · 12.10.2026 · łańcuch RE-AKW (po STOP-REAKWR, commit 5a16f029 na origin). Aneks
zamykający POZYCJĘ na etapie recon, samowykonalny (§5): zero bootów wydanych, zero
bootów do wydania. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-REAKWR

Przyjęte po weryfikacji CC z repo wykonaniem: zakres commitu = wyłącznie
results/REAKW_RECON/** (5 plików); rozbiór 14 porażek odtworzony z SUROWYCH rekordów
dir_replay.json: **5 bez żadnej utraty tracku** (c09_s02/s03, c10_s01/s03, c11_s03 —
co do sidów), **6 fantom-startów** (t_loss ≈ 0.92–1.07 s, ψ_pred 91.5–169.8° OD celu,
ślepe 9.5–26.8 s), **2 vel-śmiecie** (gate_ok=false, 7.6–16.8 m/s), **1 ślepy 0.31 s**;
krótkie re-admisje śródepizodowe (0.05–0.41 s) bez znaczenia. vel_quality
i maneuver.json spójne z raportem (jakość kierunku dobra przy żywym tracku, manewr
tnie okno ekstrapolacji). Wykonanie wzorcowe — recon z prerejestrowaną możliwością
zabicia nogi zabił ją uczciwie.

## §2. WERDYKT: pozycja RE-AKW ZAMKNIĘTA wynikiem recon (opcja c)

**Dźwignia „pamięć kierunku z trk_vel_ned" jest SFALSYFIKOWANA przy biurku: górna
granica konwersji 0/14** — 5 porażek nie ma utraty (strategia ich nie dotyka), w 6
pamięć kierunku to ANTYSYGNAŁ (wskazuje fantom stagingu), 2 odrzuca konieczna brama
plauzybilności, 1 jest bez znaczenia. Kampania w dowolnym wariancie potwierdziłaby
zero z desku za ≥24 booty — nie jest uzasadniona. Pozycja zamyka się kosztem
**0 bootów** (pierwsze pełne zabicie kierunku deskiem w programie; dla porównania:
śmierć AKW kosztowała 29). KSIĘGA bez rozliczenia — PRE nie powstało, predykcji nie
zarejestrowano; reguła 9 zadziałała w najtańszej możliwej formie.

## §3. ERRATUM CC (do rejestru; klasa: rekomendacja roadmapowa na niezmierzonym mechanizmie)

ANEKS_AKW-3 §8 nazwał trk_vel_ned „nazwaną drogą dalej" — to była moja inferencja
z mechanizmu regresji c08, NIE pomiar. Desk mierzy ją jako fałszywą w większości
przypadków: regresje c08 to w danych **interakcja fantom×skan** (ostatni ważny track
przed utratą był fantomem stagingu), nie brak pamięci kierunku. Werdykt AKW (Δ=12,
ŚMIERĆ-AKW) NIETKNIĘTY — erratum dotyczy wyłącznie uzasadnienia pozycji katalogowej.
Rozszerzenie reguły kalibracyjnej (obowiązuje od teraz): **pozycja katalogowa, której
dźwignia opiera się na niezmierzonym mechanizmie, nosi jawną flagę [MECHANIZM
NIEZMIERZONY] do czasu desku lub sondy** — i recon takiej pozycji zaczyna od pomiaru
dźwigni, co niniejszy łańcuch właśnie wykonał wzorcowo.

## §4. Dwie NOWE pozycje katalogu (z aktywami z desku; NIE otwierane tym aneksem)

- **FANTOM-START** — jeden mechanizm niesie 6/9 utrat: lock F2 na stagingu przed
  startem epizodu → expire → ślepy start 9.5–26.8 s. Dźwignia musi być po stronie
  KONSUMENTA/choreografii (percepcja FROZEN): kandydaci do recon — ignorowanie przez
  konsumenta tracków zaadmitowanych przed startem epizodu; choreografia stagingu
  w narzędziu-driverze. Trigger: przed kampanią wymagającą czystego startu epizodu.
  Aktywa: 6 nazwanych epizodów + rekordy dir_replay. Flaga: mechanizm ZMIERZONY
  (ten desk).
- **POŚCIG-V1** — 5/14 porażek przy TRZYMANYM tracku + obie porażki ramienia B
  (wyrocznia pada tak samo) ⇒ deficyt pościgu za celem v=1.0, liga sieci/egzekutora —
  nie percepcji i nie skanu. Trigger: przed roszczeniem pełnej siatki z celem szybkim.
  Aktywa: 5+2 epizodów z telemetrią obu kampanii. Flaga: mechanizm nazwany danymi
  (track żywy, D6 pada), dźwignia NIEZMIERZONA — recon od niej zacznie.

## §5. Zlecenie CO-REAKW — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista
zamknięta): korzeń `ANEKS_REAKW-1.md` (ARCH-1, verbatim, pierwszy w commicie);
EDYCJA `KIERUNKI_PO_PLANIE.md`: pozycja RE-AKW → **CLOSED-BY-RECON** z odsyłaczem do
`results/REAKW_RECON/RECON_REAKW.md` i jednozdaniowym werdyktem §2; nota-erratum §3
dopisana przy wpisie AKW (odsyłacz, bez edycji RAPORT_AKW — raporty wstecz
nietykalne); dopisane pozycje **FANTOM-START** i **POŚCIG-V1** wg §4 (trigger +
aktywa + flagi mechanizmu). ŻADNYCH edycji KSIĘGI ani raportów. Raport płaski:
diff-stat, pełna treść zmian KIERUNKÓW, porcelain. STOP. Push = Olga („wypchnięte").

## §6. Status i dalej

Pozycja RE-AKW: CLOSED (0 bootów, 1 sesja deskowa). Program w trybie katalogu; stan
po dzisiejszym: **FANTOM-START** (najkrótszy recon — mechanizm jeden i zmierzony,
dane leżą), **POŚCIG-V1** (cięższa — dotyka ligi uczonej), 1b(ii) weryfikacja sieci,
2d VIO, 2c adwersarz; warstwa 0 bez zmian. Mapa rezyduum Δ=12 jest kompletna:
6 fantom-start + 5(+2B) pościg + 3 drobne — każda przyszła noga wie, po co leci.
Breach 0 / REFUSE 0 pozostaje prawdą o wszystkim, co kiedykolwiek poleciało uzbrojone.
