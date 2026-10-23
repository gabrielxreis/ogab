"""Acessibilidade (AX) do Final Cut: inventário da interface e "chamadas" por ação (base da ponte do Gab).

  python3 ax.py arvore [--max 4000] [--filtro timeline]   # inventário: papel, subpapel, título, descrição, valor, ações
  python3 ax.py timeline                                  # clipes da timeline aberta (o que a AX expõe de cada um)

Precisa da permissão de Acessibilidade para o Terminal/Claude (Ajustes > Privacidade > Acessibilidade).
"""
import json, subprocess, sys
from ApplicationServices import (AXUIElementCreateApplication, AXUIElementCopyAttributeNames, AXUIElementCopyAttributeValue,
                                 AXUIElementCopyActionNames, AXUIElementSetAttributeValue, AXUIElementPerformAction,
                                 AXValueGetValue, kAXValueCGPointType, kAXValueCGSizeType)

BUNDLE = "com.apple.FinalCutApp"


def pid():
    r = subprocess.run(["pgrep", "-f", "Final Cut Pro.app/Contents/MacOS/Final Cut Pro|Creator Studio.app/Contents/MacOS/Final Cut Pro"],
                       capture_output=True, text=True).stdout.split()
    if not r:
        raise SystemExit("Final Cut Pro não está aberto")
    return int(r[0])


def attr(e, nome):
    err, v = AXUIElementCopyAttributeValue(e, nome, None)
    return v if err == 0 else None


def ponto(v, tipo):
    try:
        ok, p = AXValueGetValue(v, tipo, None)
        return p if ok else None
    except Exception:
        return None


def info(e):
    d = {}
    for k in ("AXRole", "AXSubrole", "AXTitle", "AXDescription", "AXHelp", "AXIdentifier", "AXRoleDescription"):
        v = attr(e, k)
        if v:
            d[k[2:]] = str(v)
    v = attr(e, "AXValue")
    if v is not None and not hasattr(v, "__len__") or isinstance(v, str):
        d["Value"] = str(v)[:120] if v is not None else None
    p, s = attr(e, "AXPosition"), attr(e, "AXSize")
    if p is not None:
        p = ponto(p, kAXValueCGPointType); s = ponto(s, kAXValueCGSizeType) if s is not None else None
        if p is not None:
            d["pos"] = [round(p.x), round(p.y)] + ([round(s.width), round(s.height)] if s is not None else [])
    err, acoes = AXUIElementCopyActionNames(e, None)
    if err == 0 and acoes:
        d["acoes"] = [str(a) for a in acoes]
    err, nomes = AXUIElementCopyAttributeNames(e, None)
    if err == 0 and nomes:
        d["attrs"] = [str(n) for n in nomes if str(n) not in ("AXRole", "AXSubrole", "AXTitle", "AXDescription", "AXParent",
                                                              "AXChildren", "AXWindow", "AXTopLevelUIElement", "AXPosition", "AXSize")]
    return d


def arvore(maxn=4000, filtro=None):
    app = AXUIElementCreateApplication(pid()); out = []; pilha = [(app, 0, "")]
    while pilha and len(out) < maxn:
        e, nivel, caminho = pilha.pop()
        d = info(e); d["nivel"] = nivel
        rotulo = d.get("Description") or d.get("Title") or d.get("Role", "")
        d["caminho"] = (caminho + "/" + rotulo)[-220:]
        if not filtro or filtro.lower() in d["caminho"].lower():
            out.append(d)
        filhos = attr(e, "AXChildren") or []
        for f in reversed(list(filhos)):
            pilha.append((f, nivel + 1, d["caminho"]))
    return out


# ------------------------------------------------------------ timeline: chamadas por item
def _timeline():
    """O AXLayoutArea "Project Timeline" (busca em largura, para na 1ª)."""
    fila = [AXUIElementCreateApplication(pid())]
    while fila:
        e = fila.pop(0)
        if attr(e, "AXRole") == "AXLayoutArea" and attr(e, "AXDescription") in ("Project Timeline", "Linha do Tempo do Projeto"):   # Final Cut em inglês ou português
            return e
        fila.extend(list(attr(e, "AXChildren") or []))
    raise SystemExit("timeline não encontrada (abra um projeto)")


def tc(v, fps):
    """'00:00:01:05' -> segundos."""
    h, m, s_, f = [int(x) for x in str(v).replace(";", ":").split(":")]
    return round(h * 3600 + m * 60 + s_ + f / fps, 4)


def itens(fps=24):
    """Todos os itens da timeline aberta: tipo, nome (texto do título), início/fim/duração (s), y/altura (camada), selecionado."""
    out = []
    for e in list(attr(_timeline(), "AXChildren") or []):
        if attr(e, "AXSubrole") != "AXTimeline":
            continue
        desc = str(attr(e, "AXDescription") or ""); tipo, _, nome = desc.partition(":")
        bordas = {str(attr(h, "AXDescription")): attr(h, "AXValue") for h in (attr(e, "AXHandles") or [])}
        p = ponto(attr(e, "AXPosition"), kAXValueCGPointType); sz = ponto(attr(e, "AXSize"), kAXValueCGSizeType)
        it = {"tipo": tipo, "nome": nome, "dur": tc(attr(e, "AXValue"), fps) if attr(e, "AXValue") else None,
              "ini": tc(bordas.get("Leading Edge") or bordas.get("Margem Principal"), fps) if (bordas.get("Leading Edge") or bordas.get("Margem Principal")) else None,
              "fim": tc(bordas.get("Trailing Edge") or bordas.get("Margem Posterior"), fps) if (bordas.get("Trailing Edge") or bordas.get("Margem Posterior")) else None,
              "y": round(p.y) if p else None, "h": round(sz.height) if sz else None, "selecionado": bool(attr(e, "AXSelected")), "_e": e}
        out.append(it)
    return out


def achar(tipo=None, nome=None, fps=24):
    for it in itens(fps):
        if (tipo is None or it["tipo"] == tipo) and (nome is None or nome.lower() in it["nome"].lower()):
            return it
    return None


def selecionar(lista):
    """Seleciona exatamente estes itens (lista de dicts de itens()). AXSelected de cada clipe é só leitura; quem aceita
    escrita é a timeline (AXSelectedChildren). Depois disso os comandos/teclas do Final Cut agem neles."""
    lista = lista if isinstance(lista, list) else [lista]
    return AXUIElementSetAttributeValue(_timeline(), "AXSelectedChildren", [i["_e"] for i in lista]) == 0


# ------------------------------------------------------------ Inspetor: cada controle tem nome fixo na AX
def controle(descricao, papel=None):
    """Acha um controle do Inspetor pelo nome AX (ex.: "size scrubber", "y scrubber", "Font Family")."""
    pilha = [AXUIElementCreateApplication(pid())]
    while pilha:
        e = pilha.pop()
        if str(attr(e, "AXDescription") or "") == descricao and (papel is None or attr(e, "AXRole") == papel):
            return e
        pilha.extend(list(attr(e, "AXChildren") or []))
    return None


def inspetor(descricao, valor):
    """Escreve um valor num campo do Inspetor e confirma (vale para TODOS os itens selecionados).
    Números no formato do sistema (pt-BR usa vírgula: 43,3)."""
    e = controle(descricao, "AXTextField")
    if e is None:
        raise SystemExit(f"controle '{descricao}' não encontrado (Inspetor aberto na aba certa?)")
    if isinstance(valor, float):
        valor = f"{valor:.1f}".replace(".", ",")
    AXUIElementSetAttributeValue(e, "AXFocused", True)
    err = AXUIElementSetAttributeValue(e, "AXValue", str(valor))
    AXUIElementPerformAction(e, "AXConfirm")
    return err == 0, attr(controle(descricao, "AXTextField"), "AXValue")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["arvore"]:
        mx = int(a[a.index("--max") + 1]) if "--max" in a else 4000
        fl = a[a.index("--filtro") + 1] if "--filtro" in a else None
        print(json.dumps(arvore(mx, fl), ensure_ascii=False, indent=0))
    elif a[:1] == ["timeline"]:
        for it in itens(float(a[1]) if len(a) > 1 else 24):
            it.pop("_e"); print(json.dumps(it, ensure_ascii=False))
    else:
        raise SystemExit(__doc__)
