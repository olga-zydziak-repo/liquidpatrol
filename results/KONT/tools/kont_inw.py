#!/usr/bin/env python3
"""results/KONT/tools/kont_inw.py — sygnał po PID z inwentarza /proc zamiast pkill -f po wzorcu (ANEKS_KONT-1b §2.3, 1c §5). Dopasowanie wyłącznie po pozycji programu w argv, więc powłoka z nazwą w poleceniu nie pasuje.
Użycie: kont_inw.py <TERM|KILL|LIST> <nazwa> [<nazwa> ...]. Wypisuje trafione PID-y."""
import os
import signal
import sys


def trafia(argv, nazwy):
    if not argv or not argv[0]:
        return None
    prog = os.path.basename(argv[0].split()[0])
    if prog in nazwy:
        return prog
    if prog.startswith(("python", "ruby")):
        for a in argv[1:5]:
            b = os.path.basename(a)
            b = b[:-3] if b.endswith(".py") else b
            b = b.rsplit(".", 1)[-1]
            if b in nazwy:
                return b
    return None


def main():
    sig, nazwy = sys.argv[1], set(sys.argv[2:])
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) == os.getpid():
            continue
        try:
            argv = open(f"/proc/{d}/cmdline", "rb").read().decode(errors="replace").split("\0")
        except OSError:
            continue
        n = trafia(argv, nazwy)
        if n:
            print(d, n)
            if sig != "LIST":
                try:
                    os.kill(int(d), getattr(signal, "SIG" + sig))
                except ProcessLookupError:
                    pass


if __name__ == "__main__":
    main()
