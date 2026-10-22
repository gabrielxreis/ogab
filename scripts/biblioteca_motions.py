"""Biblioteca de motions do Gab: modelos prontos (After Effects) que o dono cria e todo usuário recebe no update.

  python3 biblioteca_motions.py listar [--tag lista]
  python3 biblioteca_motions.py ver <modelo>
  python3 biblioteca_motions.py aplicar <modelo> valores.json [--saida spec.json]     # spec pronto para ae_lib.motion
  python3 biblioteca_motions.py salvar modelo.json [--previa previa.png] [--pasta <pasta do motion>]   # guarda (e publica, no dono)

Onde ficam:
  biblioteca_motions/<nome>/modelo.json (+ previa.png)  -> no GitHub, criados pelo dono (config.json "dono_biblioteca": true)
  biblioteca_motions_local/<nome>/...                    -> criados por outros usuários, só na máquina deles (fora do git)

Formato do modelo.json:
  {"nome", "descricao", "tags": [...], "autor", "criado", "dur": s, "dur_por_item": s,
   "campos": {"titulo": {"tipo": "texto", "exemplo": "..."}, "itens": {"tipo": "lista", "exemplo": [...], "max": 6},
              "valor": {"tipo": "numero", "exemplo": 141000}},
   "spec": {"w": 1080, "h": 1920, "fps": 30, "elementos": [ ...elementos do ae_lib...,
            {"repetir": "itens", "passo": {"y": 150, "inicio": 0.95}, "elementos": [ ... ]} ]}}
  Textos com {{campo}}; dentro do repetir: {{item}}, {{n}} (1, 2...) e {{n2}} (01, 02...).
  Números podem vir de campo ("ate": "{{valor}}") e tempos relativos ao fim ("saida_em": "fim-0.5").
  O bloco é centralizado em y = h/2 automaticamente ("centralizar": false no spec desliga).
  As cores NÃO ficam no modelo: vêm do cliente na hora de aplicar (principal, destaque, texto, fundo).

Modelo HyperFrames ("motor": "hyperframes"): o motion é a PASTA (PRESET.md, gerar.py, kit/*.css|js, index.html,
hyperframes.json), não um spec. Salvar SEMPRE com --pasta <pasta do preset/projeto>: os arquivos vão para dentro do
modelo (sem node_modules, renders, snapshots nem vídeo). Sem eles o modelo não pode ser recriado e o salvar recusa.
"""
import copy, json, os, re, shutil, subprocess, sys, datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLICA = os.path.join(RAIZ, "biblioteca_motions")
LOCAL = os.path.join(RAIZ, "biblioteca_motions_local")


def _cfg():
    p = os.path.join(RAIZ, "config.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def modelos():
    r = {}
    for base, origem in ((PUBLICA, "biblioteca"), (LOCAL, "local")):
        if not os.path.isdir(base):
            continue
        for n in sorted(os.listdir(base)):
            f = os.path.join(base, n, "modelo.json")
            if os.path.exists(f):
                m = json.load(open(f, encoding="utf-8"))
                m["_pasta"], m["_origem"] = os.path.dirname(f), origem
                r[m.get("nome", n)] = m
    return r


def _subst(v, ctx):
    if isinstance(v, str):
        inteiro = re.fullmatch(r"\{\{(\w+)\}\}", v)
        if inteiro and inteiro.group(1) in ctx and not isinstance(ctx[inteiro.group(1)], str):
            return ctx[inteiro.group(1)]                      # "{{valor}}" sozinho vira número
        v = re.sub(r"\{\{(\w+)\}\}", lambda m: str(ctx.get(m.group(1), m.group(0))), v)
        m = re.fullmatch(r"fim\s*([+-]\s*[\d.]+)?", v.strip())
        if m and "dur" in ctx:
            return round(ctx["dur"] + float((m.group(1) or "0").replace(" ", "")), 3)
        return v
    if isinstance(v, list):
        return [_subst(x, ctx) for x in v]
    if isinstance(v, dict):
        return {k: _subst(x, ctx) for k, x in v.items()}
    return v


def _desloca(e, k, d):
    """Soma d na chave k do elemento e de todos os elementos dentro dele (grupos)."""
    if isinstance(e.get(k), (int, float)):
        e[k] = round(e[k] + d, 3)
    for f in e.get("elementos", []) or []:
        _desloca(f, k, d)


def _expandir(elementos, ctx, valores):
    out = []
    for e in elementos:
        if "repetir" in e:
            lista = valores.get(e["repetir"]) or []
            passo = e.get("passo", {})
            for i, item in enumerate(lista):
                sub = dict(ctx, item=item, n=i + 1, n2=f"{i + 1:02d}")
                for nome, regra in (e.get("vars") or {}).items():     # valores que mudam por item
                    if "alterna" in regra:
                        sub[nome] = regra["alterna"][i % len(regra["alterna"])]
                    elif "lista" in regra:
                        sub[nome] = regra["lista"][min(i, len(regra["lista"]) - 1)]
                    else:
                        sub[nome] = round(regra.get("de", 0) + regra.get("passo", 0) * i, 3)
                for filho in _expandir(e["elementos"], sub, valores):
                    for k, d in passo.items():
                        _desloca(filho, k, d * i)
                    out.append(filho)
        else:
            out.append(_subst(copy.deepcopy(e), ctx))
    return out


def aplicar(nome, valores, cores=None, nome_comp=None):
    """Spec pronto para ae_lib.motion a partir do modelo + valores do vídeo + cores do cliente."""
    m = modelos().get(nome)
    if not m:
        raise SystemExit(f"modelo não encontrado: {nome}. Disponíveis: {', '.join(modelos())}")
    if m.get("motor") == "hyperframes":
        raise SystemExit(f"modelo HyperFrames: copiar a pasta {m['_pasta']} para o projeto e seguir o PRESET.md dela")
    for c, d in m.get("campos", {}).items():
        if c not in valores:
            raise SystemExit(f"falta o campo '{c}' ({d.get('tipo')}), ex.: {d.get('exemplo')}")
    n = max([len(v) for v in valores.values() if isinstance(v, list)] or [0])
    dur = round(m.get("dur", 5) + m.get("dur_por_item", 0) * max(0, n - 1), 3)
    ctx = dict(valores, dur=dur, n_itens=n)
    for var, expr in (m.get("calc") or {}).items():           # contas simples com n_itens e dur
        ctx[var] = round(eval(expr, {"__builtins__": {}}, {"n": n, "dur": dur}), 3)
    spec = copy.deepcopy(m["spec"])
    spec["elementos"] = _expandir(spec["elementos"], ctx, valores)
    if spec.pop("centralizar", True):          # regra do Gab: o bloco do motion fica centrado em y = h/2
        fundos = ("fundo", "fundo_rico")
        ys = [e["y"] for e in spec["elementos"] if isinstance(e.get("y"), (int, float)) and e.get("tipo") not in fundos]
        if ys:
            d = round(spec.get("h", 1920) / 2 - (min(ys) + max(ys)) / 2, 1)
            for e in spec["elementos"]:
                if e.get("tipo") not in fundos:
                    _desloca(e, "y", d)
    spec["nome"] = nome_comp or nome
    spec["dur"] = valores.get("dur", dur)
    if cores:
        spec["cores"] = cores
    return spec


PULAR_DIRS = {"node_modules", "renders", "snapshots", ".git", "__pycache__", ".hyperframes", "dist"}
PULAR_EXT = {".mp4", ".mov", ".webm", ".mkv", ".wav", ".mp3", ".aac", ".m4a", ".pyc", ".zip"}
CODIGO_HF = (".html", ".js", ".css", ".py")


def _copiar_pasta(origem, destino):
    """Copia a pasta do motion HyperFrames para dentro do modelo (sem dependências, renders, vídeos nem arquivos >5 MB)."""
    n = 0
    for raiz, dirs, arqs in os.walk(origem):
        dirs[:] = [d for d in dirs if d not in PULAR_DIRS and not d.startswith(".")]
        for a in arqs:
            f = os.path.join(raiz, a)
            if a.startswith(".") or a == "modelo.json" or os.path.splitext(a)[1].lower() in PULAR_EXT \
                    or os.path.getsize(f) > 5_000_000:
                continue
            alvo = os.path.join(destino, os.path.relpath(f, origem))
            os.makedirs(os.path.dirname(alvo), exist_ok=True)
            shutil.copy(f, alvo); n += 1
    return n


def _tem_codigo(pasta):
    return any(a.endswith(CODIGO_HF) for _, _, arqs in os.walk(pasta) for a in arqs)


def salvar(modelo, previa=None, pasta_motion=None, publicar=True):
    """Guarda o modelo. No dono (config "dono_biblioteca": true) vai para biblioteca_motions/ e é publicado
    (commit + push); nos outros usuários fica em biblioteca_motions_local/ (fora do git, não trava o update).
    HyperFrames ("motor": "hyperframes"): pasta_motion é copiada para dentro do modelo (é ela que recria o motion).
    publicar=False (no dono): só grava, sem commit/push."""
    hf = modelo.get("motor") == "hyperframes"
    if hf:
        modelo.setdefault("spec", {})
    for k in ("nome", "descricao", "campos", "spec"):
        if k not in modelo:
            raise SystemExit(f"modelo sem '{k}'")
    if hf and pasta_motion and not os.path.isdir(pasta_motion):
        raise SystemExit(f"pasta do motion não existe: {pasta_motion}")
    nome = re.sub(r"[^a-z0-9-]", "-", modelo["nome"].lower()).strip("-")
    modelo["nome"] = nome
    modelo.setdefault("criado", datetime.date.today().isoformat())
    dono = bool(_cfg().get("dono_biblioteca"))
    pasta = os.path.join(PUBLICA if dono else LOCAL, nome)
    if hf and not ((pasta_motion and _tem_codigo(pasta_motion)) or (os.path.isdir(pasta) and _tem_codigo(pasta))):
        raise SystemExit("modelo HyperFrames sem os arquivos do motion: salvar com --pasta <pasta do preset/projeto> "
                         "(PRESET.md, gerar.py, kit/*.css|js, index.html)")
    os.makedirs(pasta, exist_ok=True)
    if hf and pasta_motion:
        _copiar_pasta(pasta_motion, pasta)
    json.dump(modelo, open(os.path.join(pasta, "modelo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if previa and os.path.exists(previa):
        shutil.copy(previa, os.path.join(pasta, "previa.png"))
    if dono and not publicar:   # quem chamou faz o commit (banco_presets.py aceitar: junto com o catálogo)
        return f"{pasta} (salvo, sem commit)"
    if dono:
        g = ["git", "-C", RAIZ]
        subprocess.run(g + ["add", pasta], check=True)
        subprocess.run(g + ["commit", "-q", "-m", f"biblioteca de motions: {nome}\n\n{modelo['descricao']}\n\n"
                            "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"], check=True)
        ok = subprocess.run(g + ["push", "-q"]).returncode == 0
        return f"{pasta} (publicado{'' if ok else ': push falhou, publicar depois'})"
    try:   # relato anônimo do motion novo (só sai da máquina com consentimento; ver scripts/relatar.py)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import relatar
        relatar.registrar_preset(pasta)
    except Exception:
        pass
    return f"{pasta} (só nesta máquina)"


def main(a):
    if not a:
        raise SystemExit(__doc__)
    cmd = a[0]
    if cmd == "listar":
        tag = a[a.index("--tag") + 1] if "--tag" in a else None
        for n, m in modelos().items():
            if tag and tag not in m.get("tags", []):
                continue
            campos = ", ".join(f"{c} ({d.get('tipo')})" for c, d in m.get("campos", {}).items())
            motor = " hyperframes" if m.get("motor") == "hyperframes" else ""
            print(f"- {n} [{m['_origem']}{motor}] {m.get('descricao', '')}\n    campos: {campos}  tags: {', '.join(m.get('tags', []))}")
    elif cmd == "ver":
        m = modelos()[a[1]]
        print(json.dumps({k: v for k, v in m.items() if not k.startswith("_")}, ensure_ascii=False, indent=1))
        print("prévia:", os.path.join(m["_pasta"], "previa.png"))
    elif cmd == "aplicar":
        valores = json.load(open(a[2], encoding="utf-8"))
        spec = aplicar(a[1], valores, valores.pop("cores", None) if isinstance(valores, dict) else None)
        texto = json.dumps(spec, ensure_ascii=False, indent=1)
        if "--saida" in a:
            open(a[a.index("--saida") + 1], "w", encoding="utf-8").write(texto)
        else:
            print(texto)
    elif cmd == "salvar":
        previa = a[a.index("--previa") + 1] if "--previa" in a else None
        pasta_motion = a[a.index("--pasta") + 1] if "--pasta" in a else None
        print(salvar(json.load(open(a[1], encoding="utf-8")), previa, pasta_motion))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
