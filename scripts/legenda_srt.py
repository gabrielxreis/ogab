"""Legenda do DaVinci pelo SRT, tudo pela API (regra do usuário, 04/11/2026: "toda vez que for tratar a legenda no
DaVinci, não precisa exportar o vídeo inteiro: exporta só o SRT, trata o SRT e importa de novo").

  python3 legenda_srt.py exportar "<timeline>" <saida.srt> [--trilha 1]
        -> lê os itens da trilha de legenda (texto, entrada e saída no tempo da timeline) e grava o SRT.
  python3 legenda_srt.py importar "<timeline>" <arquivo.srt>
        -> troca só os itens da trilha de legenda (o estilo da trilha fica), confere quantidade e texto pela API.

Fluxo: exportar > corrigir texto e quebras no SRT (ou frases.txt + legendas.py sincronizar) > `legendas.py metrica`
com 0 problema > importar. Nada de render de vídeo para conferir texto ou tempo: a API devolve os dois. Render de
quadro com legenda gravada só para ver estilo/posição (e só os quadros necessários, `conferir.py trecho`).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as R


def _tc(s):
    h, m = int(s // 3600), int(s % 3600 // 60); sec = s % 60
    return f"{h:02d}:{m:02d}:{int(sec):02d},{int(round((sec - int(sec)) * 1000)) % 1000:03d}"


def _timeline(p, nome):
    for i in range(1, p.GetTimelineCount() + 1):
        t = p.GetTimelineByIndex(i)
        if t.GetName() == nome: return t
    raise SystemExit(f"timeline não encontrada: {nome!r}")


def ler(t, trilha=1):
    """[(início s, fim s, texto)] da trilha de legenda, no tempo da timeline."""
    F, S = R.fps_tl(t), t.GetStartFrame()
    its = sorted(t.GetItemListInTrack("subtitle", trilha) or [], key=lambda x: x.GetStart())
    return [((x.GetStart() - S) / F, (x.GetEnd() - S) / F, x.GetName()) for x in its]


def exportar(t, saida, trilha=1):
    itens = ler(t, trilha)
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        for k, (a, b, txt) in enumerate(itens, 1):
            f.write(f"{k}\n{_tc(a)} --> {_tc(b)}\n{txt}\n\n")
    return len(itens)


def textos_srt(arq):
    blocos = re.split(r"\n\s*\n", open(arq, encoding="utf-8").read().strip())
    return [" ".join(b.splitlines()[2:]).strip() for b in blocos if len(b.splitlines()) >= 3]


def main(a):
    if len(a) < 3 or a[0] not in ("exportar", "importar"):
        raise SystemExit(__doc__)
    r = R.conectar(); p = r.GetProjectManager().GetCurrentProject(); t = _timeline(p, a[1])
    if a[0] == "exportar":
        trilha = int(a[a.index("--trilha") + 1]) if "--trilha" in a else 1
        print(f"{exportar(t, a[2], trilha)} legendas -> {a[2]}")
        return
    R.colocar_legendas(t, p.GetMediaPool(), a[2], p=p)
    novos, esperado = [x[2] for x in ler(t)], textos_srt(a[2])
    if novos != esperado:
        raise SystemExit(f"CONFERIR: {len(novos)} legendas na trilha x {len(esperado)} no SRT (texto diferente)")
    R.salvar(r); print(f"{len(novos)} legendas importadas em {a[1]!r}, texto conferido")


if __name__ == "__main__":
    main(sys.argv[1:])
