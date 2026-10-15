"""Recria no CapCut a timeline ATUAL do DaVinci (só lê o DaVinci, nunca mexe nele).

    python3 ~/.claude/skills/ogab/capcut/davinci_para_capcut.py            # lê a timeline aberta no DaVinci
    python3 ~/.claude/skills/ogab/capcut/davinci_para_capcut.py retrato.json  # ou de um retrato salvo antes

O que vai: clipes de vídeo/imagem de todas as trilhas (trecho, zoom, pan/tilt, rotação, opacidade, desligado),
Cross Dissolve (vira Dissolve), áudio (o que casa com o vídeo fica no próprio clipe; o resto vira trilha de
áudio, Cross Fade vira fade), legendas (texto na Y 724). Não vai: compound clip, Fusion/lettering, cor, efeitos
do DaVinci. A mídia de fora de ~/Movies é COPIADA inteira para ~/Movies/Gab CapCut/<rascunho>/ (take nunca é
re-renderizado, regra do usuário). Relatório do que entrou e do que ficou de fora: relatorio_capcut.json na
pasta do rascunho.
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import capcut_lib as C


def ler_davinci():
    import resolve_lib as R
    r = R.conectar(abrir=False)
    p = r.GetProjectManager().GetCurrentProject()
    t = p.GetCurrentTimeline()
    F = float(t.GetSetting("timelineFrameRate"))
    S0 = t.GetStartFrame()
    out = {"projeto": p.GetName(), "timeline": t.GetName(), "fps": F, "w": t.GetSetting("timelineResolutionWidth"),
           "h": t.GetSetting("timelineResolutionHeight"), "fim": (t.GetEndFrame() - S0) / F, "trilhas": []}
    for tipo in ("video", "audio", "subtitle"):
        for k in range(1, t.GetTrackCount(tipo) + 1):
            tr = {"tipo": tipo, "n": k, "nome": t.GetTrackName(tipo, k), "ligada": t.GetIsTrackEnabled(tipo, k), "itens": []}
            for x in t.GetItemListInTrack(tipo, k) or []:
                d = {"nome": x.GetName(), "ini": (x.GetStart() - S0) / F, "dur": x.GetDuration() / F}
                mpi = x.GetMediaPoolItem()
                if mpi:
                    d["arq"] = mpi.GetClipProperty("File Path")
                    d["tipo_clip"] = mpi.GetClipProperty("Type")
                    try:
                        d["src_ini"] = x.GetSourceStartFrame() / F
                    except Exception:
                        d["src_ini"] = x.GetLeftOffset() / F
                if tipo == "video":
                    d["on"] = x.GetClipEnabled()
                    for q in ("ZoomX", "Pan", "Tilt", "RotationAngle", "Opacity"):
                        d[q] = x.GetProperty(q)
                tr["itens"].append(d)
            out["trilhas"].append(tr)
    return out


d = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else ler_davinci()

F = d["fps"]
W, H = int(d["w"]), int(d["h"])
NOME = f'{d["projeto"]} - {d["timeline"]}'


def probe(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=r_frame_rate,width,height", "-of", "json", f], capture_output=True, text=True)
    s = (json.loads(r.stdout or "{}").get("streams") or [{}])[0]
    n, q = (s.get("r_frame_rate") or f"{int(F)}/1").split("/")
    return float(n) / float(q), s.get("width"), s.get("height")


INFO = {}
def info(f):
    if f not in INFO:
        INFO[f] = probe(f)
    return INFO[f]


def src_seg(x):
    """Entrada no arquivo em segundos (o json guardou quadros do arquivo / fps da timeline)."""
    fps = info(x["arq"])[0] if x.get("tipo_clip") != "Audio" else F
    return x["src_ini"] * F / fps


def eh_transicao(x):
    return not x.get("arq") and ("Dissolve" in x["nome"] or "Cross Fade" in x["nome"])


rel = {"ok": [], "pulado": [], "aviso": []}
dr = C.novo(NOME, W, H, int(F), substituir=True)

# áudio: o que casa com um clipe de vídeo (mesmo arquivo, início e duração) fica no próprio vídeo
audios = [(t["n"], x) for t in d["trilhas"] if t["tipo"] == "audio" for x in t["itens"]]
usado = set()
def audio_do_video(v):
    for i, (n, a) in enumerate(audios):
        if i not in usado and a.get("arq") == v.get("arq") and abs(a["ini"] - v["ini"]) < 0.05 and abs(a["dur"] - v["dur"]) < 0.05:
            usado.add(i)
            return True
    return False

ids_video = {}
for t in [t for t in d["trilhas"] if t["tipo"] == "video"]:
    itens = t["itens"]
    for i, x in enumerate(itens):
        if eh_transicao(x):
            ant = ids_video.get((t["n"], i - 1))
            if ant:
                dr.transicao(ant, "Dissolve", x["dur"])
                rel["ok"].append(f'V{t["n"]} transição Dissolve {x["dur"]:.2f}s em {x["ini"]:.2f}s')
            continue
        if not x.get("arq"):
            rel["pulado"].append(f'V{t["n"]} {x["ini"]:.2f}s "{x["nome"]}" ({x.get("tipo_clip")}): sem arquivo, o CapCut não abre compound clip')
            continue
        # zoom 1.0 no DaVinci = encaixar no quadro, igual ao 1.0 do CapCut: o zoom passa direto
        com_som = audio_do_video(x)
        de = src_seg(x)
        sid = dr.video(x["arq"], x["ini"], de=de, ate=de + x["dur"], trilha=t["n"] - 1,
                       mudo=not com_som, escala=x.get("ZoomX") or 1.0,
                       x=W / 2 + (x.get("Pan") or 0), y=H / 2 + (x.get("Tilt") or 0),
                       rotacao=x.get("RotationAngle") or 0.0, opacidade=(x.get("Opacity") or 100) / 100)
        if x.get("on") is False:
            dr.desligar(sid)
        ids_video[(t["n"], i)] = sid
        rel["ok"].append(f'V{t["n"]} {x["ini"]:6.2f}s {x["nome"][:38]} zoom {x.get("ZoomX") or 1:.2f}'
                         + (" (desligado)" if x.get("on") is False else "") + ("" if com_som else " mudo"))

# áudios que sobraram (música, trechos soltos) nas trilhas de áudio, com fades onde havia cross fade
trilha_a = {}
for t in [t for t in d["trilhas"] if t["tipo"] == "audio"]:
    itens = t["itens"]
    for i, x in enumerate(itens):
        idx = audios.index((t["n"], x))
        if idx in usado or eh_transicao(x):
            continue
        if not x.get("arq"):
            rel["pulado"].append(f'A{t["n"]} {x["ini"]:.2f}s "{x["nome"]}": áudio de compound clip, sem arquivo')
            continue
        fin = next((c["dur"] / 2 for c in itens[i - 1:i] if eh_transicao(c)), 0)
        fout = next((c["dur"] / 2 for c in itens[i + 1:i + 2] if eh_transicao(c)), 0)
        de = src_seg(x)
        n = trilha_a.setdefault(t["n"], len(trilha_a))
        dr.audio(x["arq"], x["ini"], de=de, ate=de + x["dur"], trilha=n, fade_in=fin, fade_out=fout)
        rel["ok"].append(f'A{t["n"]} {x["ini"]:6.2f}s {x["nome"][:38]}' + (f" fades {fin:.2f}/{fout:.2f}" if fin or fout else ""))

for t in [t for t in d["trilhas"] if t["tipo"] == "subtitle"]:
    for x in t["itens"]:
        dr.texto(x["nome"], x["ini"], x["dur"], tamanho=8, cor="#FFFFFF", contorno="#000000", negrito=True, y=724)
        rel["ok"].append(f'Legenda {x["ini"]:6.2f}s {x["nome"]}')

dr.salvar(projeto_fechado=True)
json.dump(rel, open(os.path.join(dr.pasta, "relatorio_capcut.json"), "w"), ensure_ascii=False, indent=1)
print(dr.pasta)
print("ok", len(rel["ok"]), "| pulado", rel["pulado"])
for tr in dr.retrato():
    print(tr["tipo"], tr["trilha"], [(s["nome"][:14], round(s["inicio"], 2), round(s["fim"], 2)) for s in tr["segmentos"]][:14])
