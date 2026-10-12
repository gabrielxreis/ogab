"""Status do vídeo (regra 1m e 9): lê a pasta + a timeline, gera a barra de 3 linhas e atualiza o PROJETO.md.

  python3 projeto.py status <pasta_do_video> [--timeline "<nome>"]
  python3 projeto.py marcar <pasta_do_video> <etapa> [--pular "motivo"] [--desmarcar]

Etapas (edição): cortes, legenda, legenda_validada, broll, motions, musica, sfx, qc, export.
Na criação (existe roteiro.txt) entram antes: roteiro, voz.
O que dá para ver na timeline é detectado sozinho; o que depende do usuário (legenda_validada, roteiro, voz, qc, export
fora da pasta) é marcado com `marcar`. Estado em <pasta>/status.json. O bloco "## Status" do PROJETO.md é reescrito.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROTULO = {"roteiro": "roteiro", "voz": "voz", "cortes": "cortes", "legenda": "legenda", "legenda_validada": "validar a legenda",
          "broll": "b-roll/takes", "motions": "motions", "musica": "música", "sfx": "efeitos sonoros", "qc": "QC final", "export": "export"}
DEPENDE_DO_USUARIO = {"roteiro", "voz", "legenda_validada"}
MOTION = re.compile(r"(^x\d\d-|motion|cta|lettering)", re.I)


def etapas(pasta):
    base = ["cortes", "legenda", "legenda_validada", "broll", "motions", "musica", "sfx", "qc", "export"]
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
    acima = [x for k in range(2, t.GetTrackCount("video") + 1) for x in itens("video", k)]
    if any(not MOTION.search(x.GetName()) for x in acima): ok.add("broll")
    if any(MOTION.search(x.GetName()) for x in acima): ok.add("motions")
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


def main():
    a = sys.argv[1:]
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
