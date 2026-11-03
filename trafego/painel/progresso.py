#!/usr/bin/env python3
"""Barra de progresso ao vivo no Terminal para o trabalho do Gab no painel.

  python3 progresso.py mostrar                 # deixa rodando numa aba do Terminal (redesenha a cada 0,5 s)
  python3 progresso.py etapas "A" "B" "C"      # começa a lista de etapas (a primeira fica em andamento)
  python3 progresso.py etapa 2                 # marca as anteriores como feitas e a 2 em andamento (1 = primeira)
  python3 progresso.py item 7 26 "C5 | Relógio"  # sub-barra da etapa atual: 7 de 26
  python3 progresso.py fim                     # tudo concluído

O estado fica em painel/.progresso.json (fora do git).
"""
import json
import os
import sys
import time

ARQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".progresso.json")


def ler():
    try:
        return json.load(open(ARQ, encoding="utf-8"))
    except Exception:
        return {"etapas": [], "atual": 0, "item": None, "inicio": time.time(), "fim": False}


def gravar(d):
    tmp = ARQ + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, ARQ)


def barra(frac, larg=34):
    cheio = int(round(frac * larg))
    return "█" * cheio + "░" * (larg - cheio)


def mostrar():
    giro = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    k = 0
    while True:
        d = ler(); k += 1
        et, at = d.get("etapas", []), d.get("atual", 0)
        feitas = len(et) if d.get("fim") else at
        frac = feitas / len(et) if et else 0
        seg = int(time.time() - d.get("inicio", time.time()))
        linhas = ["\033[H\033[2J", "\033[1m  O GAB · painel\033[0m   " + time.strftime("%H:%M:%S") + f"   ({seg // 60:02d}:{seg % 60:02d})", ""]
        linhas.append(f"  {barra(frac)}  \033[1m{int(frac * 100):3d}%\033[0m  {feitas}/{len(et)} etapas")
        linhas.append("")
        for i, t in enumerate(et):
            if d.get("fim") or i < at:
                linhas.append(f"  \033[32m✔\033[0m  {t}")
            elif i == at:
                linhas.append(f"  \033[33m{giro[k % len(giro)]}\033[0m  \033[1m{t}\033[0m")
                it = d.get("item")
                if it and it.get("total"):
                    f2 = it["n"] / it["total"]
                    linhas.append(f"       {barra(f2, 24)} {it['n']}/{it['total']}  \033[2m{(it.get('txt') or '')[:48]}\033[0m")
            else:
                linhas.append(f"  \033[2m○  {t}\033[0m")
        if d.get("fim"):
            linhas += ["", "  \033[32m\033[1mPronto.\033[0m"]
        sys.stdout.write("\n".join(linhas) + "\n"); sys.stdout.flush()
        time.sleep(0.5)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "mostrar":
        return mostrar()
    cmd, args = sys.argv[1], sys.argv[2:]
    d = ler()
    if cmd == "etapas":
        d = {"etapas": args, "atual": 0, "item": None, "inicio": time.time(), "fim": False}
    elif cmd == "etapa":
        d["atual"] = max(0, int(args[0]) - 1); d["item"] = None; d["fim"] = False
    elif cmd == "item":
        d["item"] = {"n": int(args[0]), "total": int(args[1]), "txt": " ".join(args[2:])}
    elif cmd == "fim":
        d["fim"] = True; d["item"] = None
    gravar(d)


if __name__ == "__main__":
    main()
