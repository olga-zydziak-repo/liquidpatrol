#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_v8_en.py — sterownik montażu v8 EN (PROMPT_DEMOC_V8 §6). NOWY plik; democ_en_71 i przyrząd
democ_kolizje NIETKNIĘTE (importowane). Każdy krok w osobnym procesie: przyrząd kolizji (democ_kolizje.install z funkcją tożsamości —
teksty aktu 8 są wypalane wprost po angielsku), tabela paneli kroku, potem main() narzędzia democ_v8_overlay. Panel części B aktu 8
ma inny układ niż w akcie 7 — tabela „aktB8” dopisywana do słownika przyrządu w procesie kroku (plik przyrządu bez zmian).
Po krokach: agregacja kolizji aktu 8 w zegarze filmu (karta wejścia, A, B, karta zakresu, plansza) z asercją zera, montaż, kontaktówka.
Wyjście kroków: results/DEMO_C/clips_v8/; filmy w results/DEMO_C/.
Użycie: democ_v8_en.py all <take>      democ_v8_en.py step <nazwa> <take>
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
OUT = os.path.join(DC, "clips_v8")
V71 = os.path.join(DC, "DEMO_C_v71_EN.mp4")
PANELE_KROKU = {"akt8_A": ["std", "nadir", "brain"], "akt8_B": ["aktB8"], "karty": ["karta"]}
AKTB8 = {"top": (0, 0, 1920, 56), "speed": (1600, 56, 320, 52), "map": (280, 60, 720, 720), "legend": (0, 100, 280, 220),
         "graph": (100, 780, 920, 214), "right": (1060, 108, 860, 590), "mini": (1500, 690, 420, 280), "caption": (0, 1008, 1920, 72)}
ORDER = ["karty", "akt8_A", "akt8_B"]


def O(nm):
    return os.path.join(OUT, nm)


def instrument(name):
    os.environ["KOLIZJE_OUT"] = O(f"kolizje_{name}.json")
    os.environ["KOLIZJE_BAZA"] = ""
    sys.path.insert(0, HERE)
    import democ_kolizje
    democ_kolizje.PANELE["aktB8"] = AKTB8
    democ_kolizje.install(lambda s: s, PANELE_KROKU[name])


def step(name, take):
    instrument(name)
    sys.path.insert(0, HERE)
    import democ_v8_overlay as V
    argv = {"karty": ["karty", OUT], "akt8_A": ["aktA", take, O("akt8_A.mp4")], "akt8_B": ["aktB", O("akt8_B.mp4")]}[name]
    sys.argv = ["democ_v8_overlay.py"] + argv
    V.main()


def agreguj():
    wynik, t_film = [], 0.0
    film = [("karty", (0, 50)), ("akt8_A", None), ("akt8_B", None), ("karty", (50, 110)), ("karty", (110, 200))]
    for nm, rng in film:
        kl = json.load(open(O(f"kolizje_{nm}.json")))["klatki"]
        if rng:
            kl = kl[rng[0]:rng[1]]
        for k, f in enumerate(kl):
            for c in f["kolizje"]:
                wynik.append({"klip": nm, "klatka_klipu": k, "t_akt8": round(t_film + k / 10.0, 1), **c})
        t_film += len(kl) / 10.0
    out = {"dlugosc_aktu8_z_plansza_s": round(t_film, 1), "n_kolizji": len(wynik),
           "typy": {t: sum(1 for w in wynik if w["typ"] == t) for t in sorted({w["typ"] for w in wynik})}, "kolizje": wynik}
    json.dump(out, open(os.path.join(DC, "kolizje_v8.json"), "w"), ensure_ascii=False, indent=1)
    print(f"[kolizje v8] {out['n_kolizji']} kolizji {out['typy']}")
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1] == "step":
        step(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "agreguj":
        o = agreguj()
        assert o["n_kolizji"] == 0, "v8: kolizje niezerowe — montaż przerwany"
    elif sys.argv[1] == "cut":
        sys.path.insert(0, HERE)
        import democ_v8_overlay as V
        r = V.cut(V71, OUT)
        V.kontaktowka(OUT, os.path.join(DC, "kontaktowka_v8.jpg"))
        json.dump(r, open(O("cut_v8.json"), "w"), ensure_ascii=False, indent=1)
        print(json.dumps(r, ensure_ascii=False)[:1500])
    elif sys.argv[1] == "all":
        take = sys.argv[2]
        for nm in ORDER:
            r = subprocess.run([sys.executable, __file__, "step", nm, take], cwd=DC)
            assert r.returncode == 0, f"krok {nm} rc={r.returncode}"
        for a in ("agreguj", "cut"):
            r = subprocess.run([sys.executable, __file__, a], cwd=DC)
            assert r.returncode == 0, f"{a} rc={r.returncode}"


if __name__ == "__main__":
    main()
