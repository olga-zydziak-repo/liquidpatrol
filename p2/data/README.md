# p2/data — zrzut etykiet Anti-UAV (wariant B, IR)

Zgodnie z ratyfikacją (opcja 1 + rider prowieniencji): **wrzuć TYLKO etykiety IR** (kilka MB), nie wideo.

## Co wrzucić
Etykiety per-sekwencja z oryginalnego Anti-UAV (ZhaoJ9014, MIT), wersja **challenge (per-klatka)**:
- pliki **`IR_label.json`** dla każdej sekwencji (pole `exist` + `gt_rect`/`get_rect`).

## Układ (jeden z dwóch — loader obsłuży oba)
**Wariant per-sekwencja (preferowany):**
```
p2/data/antiuav_B/<split>/<nazwa_sekwencji>/IR_label.json
   gdzie <split> ∈ {train, val, test}
```
**Wariant spłaszczony (jeśli wygodniej):**
```
p2/data/antiuav_B/<split>/<nazwa_sekwencji>.json
```
Jeśli układ per-sekwencja okaże się niepraktyczny do wrzucenia → przechodzimy na opcję 2 (ja pobieram gdown), bez kombinowania (ustalenie z ratyfikacji).

## Rider prowieniencji (wymagany)
Dla KAŻDEGO wrzuconego pliku/archiwum zapiszę w `p2/frozen/provenance.json`:
- **sha256**, dokładna **nazwa z paczki źródłowej**, **URL źródłowy** (Google Drive / repo).
Podaj URL źródłowy (link do paczki, z której pochodzą etykiety) — wpiszę go do prowieniencji. Domyślnie: https://github.com/ZhaoJ9014/Anti-UAV (MIT).

## RGB — NIE teraz
Etykiety RGB pomijamy (opcjonalny osobny split, ta sama ścieżka później, jeśli wejdzie). Kanoniczny werdykt = IR (A1).

## Po wrzuceniu
Uruchomię: parser → statystyki (długości, ≥T_min drabina, hole-rate „duch G2") → **commit zamrażający** (split/maski/statystyki/baseline) → Ty push przed treningiem.
