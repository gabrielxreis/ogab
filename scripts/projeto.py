"""Status do vídeo (regra 1m e 9): lê a pasta + a timeline, gera a barra de 3 linhas e atualiza o PROJETO.md.

  python3 projeto.py status <pasta_do_video> [--timeline "<nome>"]
  python3 projeto.py marcar <pasta_do_video> <etapa> [--pular "motivo"] [--desmarcar]
  python3 projeto.py lote <pasta_da_empresa>          (barra de TODOS os vídeos do lote, com a timeline gravada de cada um)
  python3 projeto.py checklist <pasta_do_video>|<pasta_da_empresa>   (OBRIGATÓRIO antes de dizer "pronto"/entregar)

Etapas (edição): cortes, legenda, legenda_validada, broll, cor, letterings, motions, musica, sfx, abas, qc, export.
cor = todos os takes da V1 com PowerGrade (nó > 1, detectado); letterings = título Fusion acima da V1 (detectado);
motions = item na trilha MOTIONS ou nome de motion (detectado); abas = timelines abertas em abas (marcar depois de abrir_em_abas).
Na criação (existe roteiro.txt) entram antes: roteiro, voz.
O que dá para ver na timeline é detectado sozinho; o que depende do usuário (legenda_validada, roteiro, voz, qc, export
fora da pasta) é marcado com `marcar`. Estado em <pasta>/status.json. O bloco "## Status" do PROJETO.md é reescrito.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROTULO = {"roteiro": "roteiro", "voz": "voz", "cortes": "cortes", "legenda": "legenda", "legenda_validada": "validar a legenda",
          "broll": "b-roll/takes", "cor": "cor (PowerGrade)", "letterings": "letterings", "abas": "abas abertas", "motions": "motions", "musica": "música", "sfx": "efeitos sonoros", "qc": "QC final", "export": "export"}
DEPENDE_DO_USUARIO = {"roteiro", "voz", "legenda_validada"}
MOTION = re.compile(r"(^x\d\d-|motion|cta|lettering)", re.I)


def etapas(pasta):
    base = ["cortes", "legenda", "legenda_validada", "broll", "cor", "letterings", "motions", "musica", "sfx", "abas", "qc", "export"]
    return (["roteiro", "voz"] if os.path.exists(os.path.join(pasta, "roteiro.txt")) else []) + base


def estado(pasta):
    f = os.path.join(pasta, "status.json")
    return json.load(open(f)) if os.path.exists(f) else {"feitas": [], "puladas": {}, "timeline": None}


def salvar(pasta, st): json.dump(st, open(os.path.join(pasta, "status.json"), "w"), ensure_ascii=False, indent=1)


def detectar(nome_tl):
    try:
        import resolve_lib as R
        p = R.conectar().GetProjectManager().GetCurrentProject()
        t = next((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome_tl), None)
    except Exception:
        return set()
    if not t: return set()
    ok = set(); itens = lambda tipo, k: t.GetItemListInTrack(tipo, k) or []
    if len(itens("video", 1)) > 1: ok.add("cortes")
    if t.GetTrackCount("subtitle") and itens("subtitle", 1): ok.add("legenda")
    tracks = range(2, t.GetTrackCount("video") + 1)
    nome_trilha = {k: (t.GetTrackName("video", k) or "").upper() for k in tracks}
    acima = [(k, x) for k in tracks for x in itens("video", k)]
    eh_titulo = lambda x: x.GetMediaPoolItem() is None          # Fusion Title (não abre a composição)
    eh_motion = lambda k, x: nome_trilha[k] == "MOTIONS" or bool(MOTION.search(x.GetName()))
    v1 = [x for x in itens("video", 1) if x.GetMediaPoolItem() is not None]
    if any(not eh_titulo(x) and not eh_motion(k, x) for k, x in acima) or len(v1) >= 2: ok.add("broll")
    if any(eh_titulo(x) for k, x in acima): ok.add("letterings")
    if any(eh_motion(k, x) and not eh_titulo(x) for k, x in acima): ok.add("motions")
    try:
        if v1 and all(x.GetNodeGraph().GetNumNodes() > 1 for x in v1): ok.add("cor")
    except Exception:
        pass
    if t.GetTrackCount("audio") >= 2 and itens("audio", 2): ok.add("musica")
    if t.GetTrackCount("audio") >= 3 and itens("audio", 3): ok.add("sfx")
    return ok


def status(pasta, nome_tl=None):
    st = estado(pasta)
    if nome_tl: st["timeline"] = nome_tl
    E = etapas(pasta); vistos = detectar(st["timeline"]) if st.get("timeline") else set()
    if glob.glob(os.path.join(pasta, "videos", "*.mp4")): vistos.add("export")
    feitas = [e for e in E if e in vistos or e in st["feitas"]]
    puladas = {e: m for e, m in st["puladas"].items() if e in E and e not in feitas}
    falta = [e for e in E if e not in feitas and e not in puladas]
    n = len(feitas) + len(puladas); tot = len(E)
    nome = os.path.basename(os.path.normpath(pasta)).split(" - ")[0]
    prox = falta[0] if falta else None
    linhas = [f"{nome} {'▰' * n}{'▱' * (tot - n)} {n} de {tot}",
              "Falta: " + (", ".join(ROTULO[e] for e in falta) if falta else "nada, pronto para entregar"),
              "Próximo: " + ((ROTULO[prox] + (" (esperando seu ok)" if prox in DEPENDE_DO_USUARIO else "")) if prox else "entregar")]
    if puladas: linhas.insert(2, "Pulado: " + ", ".join(f"{ROTULO[e]} ({m})" for e, m in puladas.items()))
    salvar(pasta, st); atualizar_md(pasta, E, feitas, puladas, st.get("timeline"))
    return "\n".join(linhas)


def atualizar_md(pasta, E, feitas, puladas, tl):
    md = os.path.join(pasta, "PROJETO.md")
    bloco = "## Status (gerado por projeto.py)\n" + (f"Timeline: {tl}\n" if tl else "") + "".join(
        f"- [{'x' if e in feitas else ('-' if e in puladas else ' ')}] {ROTULO[e]}" + (f" (pulado: {puladas[e]})" if e in puladas else "") + "\n" for e in E)
    txt = open(md).read() if os.path.exists(md) else f"# {os.path.basename(os.path.normpath(pasta))}\n\n"
    if "## Status (gerado por projeto.py)" in txt:
        txt = re.sub(r"## Status \(gerado por projeto\.py\)\n(?:.*\n)*?(?=\n## |\Z)", bloco, txt, count=1)
    else:
        txt = txt.rstrip("\n") + "\n\n" + bloco
    open(md, "w").write(txt)


CONFERIR = [  # o que a API não vê: conferir de olho (prévia/screenshot) antes de entregar
    "takes: nenhum ilegível/cortado errado (horizontal virando vertical) e nenhum quadro preto entre takes",
    "cor: 2-3 quadros conferidos depois do PowerGrade (nada estourado)",
    "SFX: cada som = o que o motion/take MOSTRA (foley real); HUD só em interface",
    "legenda: regra do estilo.md do cliente sob motion/lettering/CTA (desce p/ 390 ou desativada)",
    "letterings: entram animados na prévia (quadros +1, +7, +19)",
    "música: termina junto com o vídeo, -10 dB; narração +5 dB",
    "abas: todas as timelines do lote abertas (abrir_em_abas) e Stacked ligado",
    "barra de progresso (projeto.py lote) no fim da resposta",
]


def pastas_do_lote(base):
    return sorted(d for d in glob.glob(os.path.join(base, "*")) if os.path.isdir(d) and os.path.exists(os.path.join(d, "status.json")))


def checklist(alvo):
    ps = pastas_do_lote(alvo) or [alvo]; falta_algo = False
    for d in ps:
        print(status(d)); st = estado(d); E = etapas(d)
        feitas = set(st["feitas"]) | detectar(st["timeline"]) if st.get("timeline") else set(st["feitas"])
        pend = [ROTULO[e] for e in E if e not in feitas and e not in st["puladas"] and e not in ("qc", "export")]
        if pend: falta_algo = True; print("  PENDENTE antes do QC:", ", ".join(pend))
        print()
    print("Conferir de olho antes de entregar:"); [print("  [ ]", c) for c in CONFERIR]
    return 1 if falta_algo else 0


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "lote":
        for d in pastas_do_lote(a[1]): print(status(d)); print()
        return
    if len(a) >= 2 and a[0] == "checklist": sys.exit(checklist(a[1]))
    if len(a) < 2 or a[0] not in ("status", "marcar"): print(__doc__); sys.exit(2)
    pasta = a[1]; st = estado(pasta)
    if a[0] == "marcar":
        e = a[2]
        if e not in ROTULO: sys.exit(f"etapa inválida: {e} (use {', '.join(ROTULO)})")
        if "--desmarcar" in a: st["feitas"] = [x for x in st["feitas"] if x != e]; st["puladas"].pop(e, None)
        elif "--pular" in a: st["puladas"][e] = a[a.index("--pular") + 1]
        elif e not in st["feitas"]: st["feitas"].append(e)
        salvar(pasta, st)
    print(status(pasta, a[a.index("--timeline") + 1] if "--timeline" in a else None))


if __name__ == "__main__":
    main()
