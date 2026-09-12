# NOTA_UNROLL — desk-note O4/L3: weryfikacja wnętrza sieci CfC (status: częściowy)

CC · 11.09.2026 · noga FV, S3, PRE_FV §3/O4 + F6 + prerejestracja P-CC2-1. **BEZ instalacji narzędzi,
BEZ biegu.** Statusy narzędzi = z dokumentacji, z zastrzeżeniem weryfikacji (nie sprawdzone empirycznie
w tej nodze). Zakres tej noty: wyłącznie wnętrze sieci; ZŁOŻENIE (O4/L1+L2) domknięte osobno w
RAPORT_FV §3 na kodzie i modelu.

## 1. Co dowiedliśmy bez unrollu (i dlaczego to wystarcza bramce)
Bramka nogi (PRE_FV §5) NIE zależy od wnętrza CfC. O4 jako stretch (ii) domyka się na **złożeniu**:
- **L1** — głowa `y = tanh(·)·V_MAX` (net/models.py:12 CfC, :57 MLP), |tanh|≤1 ⇒ |y_net| ≤ V_MAX
  ARCHITEKTONICZNIE, niezależnie od wag i historii stanu ukrytego.
- **L2** — `clip_v` (r03/controllers/common.py:10-16) wymusza |v_cmd| ≤ v_max BEZWARUNKOWO (nawet gdyby
  L1 zawiodło); dalej O3 (P8, jeśli używane) + P2 dają pr ≤ R_E na domenie clampu.
Te własności są własnościami KODU (głowa, klamp, koperta), nie wnętrza rekurencji — i to one wiążą
wyjście sieci z obwiednią. Wnętrze CfC (dynamika stanu ukrytego h przez T kroków) NIE jest potrzebne
do żadnego twierdzenia bramkowego ani do O4.

## 2. Czego wymagałaby weryfikacja feedforwardowa wnętrza (unroll-T)
CfC per krok (net/models.py:11-12, dt=1 zaszyte w wagach):
`bb=tanh(Wb·[x,h]+bb0); g=tanh(Wg·bb+bg); hh=tanh(Wh·bb+bh); gate=σ(−(Wt·bb+bt)); h'=gate⊙g+(1−gate)⊙hh; y=tanh(Wo·h'+bo)·V_MAX`.
Aby dowieść własności NIEtrywialnej wnętrza (np. ograniczenie/monotoniczność `h` albo `y` po historii,
albo brak trybu ucieczki stanu), trzeba:
1. **Rozwinąć T kopii** rekurencji (T = horyzont epizodu; okno realne rzędu setek ticków) — każda kopia
   wnosi warstwy `tanh`/`σ` i mnożenie `Wb·[x,h]`.
2. **Zakodować funkcje przestępne** `tanh`, `σ` — brak dokładnej teorii w SMT liniowym/wielomianowym;
   wymaga albo solvera δ-zupełnego nad ℝ z funkcjami przestępnymi, albo relaksacji liniowych/Taylora.
3. **Związać wagi liczbowe** (NCP20: 1903 parametry `float`, numpy; RECON_FV R5) z modelem dowodowym —
   ekstrakcja + kontrola prowieniencji wag (analog `certs_selfcheck` dla numpy).
4. **Zdefiniować własność wnętrza wartą dowodu** — a te, które mają znaczenie dla bezpieczeństwa
   (|y|≤V_MAX), są JUŻ zamknięte architektonicznie (L1) bez unrollu.

## 3. Kandydackie klasy narzędzi (z nazwy; status z dokumentacji, do weryfikacji)
- **SMT δ-zupełne nad ℝ z przestępnymi** — klasa dReal: obsługa `tanh`/`exp`/`σ` przez δ-osłabienie;
  koszt rośnie z T i szerokością; brak instalacji w tej nodze (F7).
- **Propagacja granic / abstrakcyjna interpretacja** — klasa CROWN/auto_LiRPA: relaksacje liniowe dla
  `tanh`/`σ`; skaluje do dużych sieci, ale daje GRANICE (nie równości), więc twierdzenia = ograniczenia.
- **Osiągalność pętli zamkniętej NN-controlled** — klasa Verisig / NNV / POLAR / ReachNN: modele Taylora
  / Bernsteina dla aktywacji przestępnych na horyzoncie T; celowane w reachability sterowania, nie w
  składnię SMT.
- **Weryfikatory NN oparte o MILP/simplex** — klasa Marabou/Reluplex: natywnie ReLU; `tanh`/`σ` wymagają
  rozszerzeń/relaksacji — dopasowanie do CfC niepewne.
Wszystkie: NOWA zależność (łamie F7/SR-FV-3), część wymaga GPU/toolchainu poza budżetem nogi.

## 4. Dlaczego poza budżetem nogi (F6, P-CC2-1)
F6 zamraża stretch (ii) jako **dowód ZŁOŻENIA**, a wnętrze CfC jako WYŁĄCZNIE desk-note „częściowy",
zero instalacji (F7/SR-FV-3). Budżet nogi ≤4 sesje, bez GPU/instalacji (PRE_FV §6). Weryfikacja unroll-T
wnętrza wymaga nowej zależności i modelu przestępnego — poza zakresem. Prerejestrowana **P-CC2-1**
(p≈0.7: część (ii) „własności samej sieci CfC narzędziem off-the-shelf" → wynik **częściowy** albo śmierć
na pokryciu narzędzi) — realizuje się jako **CZĘŚCIOWY**: złożenie dowiedzione (L1/L2), wnętrze CfC
pozostaje niedowiedzione.

## 5. Status
**CZĘŚCIOWY** — złożenie osłona∘sieć domknięte na kodzie i modelu (O4/L1+L2, RAPORT_FV §3); wnętrze CfC
(unroll-T) niedowodzone, poza budżetem i zakresem narzędziowym nogi (F6/F7). Zero twierdzeń o locie.
