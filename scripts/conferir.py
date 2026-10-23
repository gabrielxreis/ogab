#!/usr/bin/env python3
"""Conferência visual da timeline montada no DaVinci por QUADROS em PNG (regra do usuário, 23/10/2026).

  python3 conferir.py chave  [--timeline "<nome>"] [--pasta <saída>] [--max 24]
  python3 conferir.py trecho --em 12.5 [--raio 2] [--passo 0.25] [--timeline "<nome>"] [--pasta <saída>]

Em vez de renderizar o vídeo inteiro para conferir, o DaVinci exporta direto em PNG (meia resolução) só os quadros
que importam e eles viram UMA folha com o tempo de cada quadro (bem menos token que vídeo ou quadros soltos):
- chave: cada corte da V1 e começo/meio/fim de cada item das trilhas de cima (lettering, motion, b-roll), mais os
  marcadores da timeline;
- trecho: quadros a cada --passo segundos em volta de --em (o momento em que o usuário viu o problema).
Saída: <pasta>/conferir_<modo>/folha.png e os PNG soltos. A fila de render do usuário fica como estava.
"""
import glob, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def arg(nome, padrao=None):
    a = sys.argv
    return a[a.index(nome) + 1] if nome in a and a.index(nome) + 1 < len(a) else padrao


def timeline(p, nome):
    if not nome:
        return p.GetCurrentTimeline()
    for i in range(1, p.GetTimelineCount() + 1):
        t = p.GetTimelineByIndex(i)
        if t.GetName() == nome:
            p.SetCurrentTimeline(t); return t
    raise SystemExit(f"timeline não encontrada: {nome}")


def tempos_chave(t, F, S, maximo):
    """(segundo, rótulo) dos quadros que mostram o que foi montado."""
    prio, resto = [], []
    for k in range(1, t.GetTrackCount("video") + 1):
        if not t.GetIsTrackEnabled("video", k):
            continue
        for it in t.GetItemListInTrack("video", k) or []:
            a, b = (it.GetStart() - S) / F, (it.GetEnd() - S) / F
            if k == 1:
                resto.append((a + 2 / F, f"corte V1"))
            else:
                nome = (it.GetName() or f"V{k}")[:18]
                for s, r in ((min(b, a + .3), "entra"), ((a + b) / 2, "meio"), (max(a, b - .2), "sai")):
                    prio.append((s, f"V{k} {nome} {r}"))
    for f, m in sorted((t.GetMarkers() or {}).items()):
        prio.append((f / F, "marcador " + (m.get("name") or m.get("note") or "")[:16]))
    escolhidos = []
    for s, r in sorted(prio) + sorted(resto):   # trilhas de cima e marcadores primeiro; cortes completam até o máximo
        if len(escolhidos) >= maximo:
            break
        if all(abs(s - e) > .25 for e, _ in escolhidos):
            escolhidos.append((s, r))
    return sorted(escolhidos)


def exportar(p, t, tempos, pasta):
    """Um job PNG de 1 quadro por tempo, todos de uma vez; devolve [(png, segundo, rótulo)]."""
    from resolve_lib import fps_tl, pagina_edit
    F = fps_tl(t); S = t.GetStartFrame()
    w = int(t.GetSetting("timelineResolutionWidth")) // 2 // 2 * 2; h = int(t.GetSetting("timelineResolutionHeight")) // 2 // 2 * 2
    os.makedirs(pasta, exist_ok=True)
    for velho in glob.glob(os.path.join(pasta, "q_*.png")):
        os.remove(velho)
    ant = p.GetCurrentRenderFormatAndCodec() or {}
    p.SetCurrentRenderFormatAndCodec("png", "RGB8")
    jobs = []
    try:
        for i, (s, _) in enumerate(tempos):
            q = S + max(0, round(s * F))
            p.SetRenderSettings({"SelectAllFrames": False, "MarkIn": q, "MarkOut": q, "TargetDir": pasta, "CustomName": f"q_{i:03d}",
                                 "FormatWidth": w, "FormatHeight": h, "ExportVideo": True, "ExportAudio": False})
            jid = p.AddRenderJob()
            if jid:
                jobs.append(jid)
        if not jobs:
            raise SystemExit("o DaVinci não aceitou os jobs de PNG (página Deliver travada ou timeline vazia)")
        p.StartRendering(jobs)
        while p.IsRenderingInProgress():
            time.sleep(.5)
    finally:
        for jid in jobs:
            p.DeleteRenderJob(jid)   # só os jobs do Gab
        if ant.get("format") and ant.get("codec"):
            p.SetCurrentRenderFormatAndCodec(ant["format"], ant["codec"])
        pagina_edit()
    out = []
    for i, (s, r) in enumerate(tempos):
        achados = sorted(glob.glob(os.path.join(pasta, f"q_{i:03d}*.png")), key=os.path.getmtime)
        if achados:
            out.append((achados[-1], s, r))
    return out


def folha(quadros, saida, col=6, larg=180):
    from PIL import Image, ImageDraw
    if not quadros:
        raise SystemExit("nenhum quadro exportado")
    im0 = Image.open(quadros[0][0]); alt = round(larg * im0.height / im0.width); faixa = 30
    lin = (len(quadros) + col - 1) // col
    f = Image.new("RGB", (col * larg, lin * (alt + faixa)), (12, 12, 12)); d = ImageDraw.Draw(f)
    for k, (png, s, r) in enumerate(quadros):
        x, y = (k % col) * larg, (k // col) * (alt + faixa)
        f.paste(Image.open(png).convert("RGB").resize((larg, alt)), (x, y))
        d.text((x + 4, y + alt + 3), f"{int(s // 60)}:{s % 60:05.2f}", fill=(255, 255, 255))
        d.text((x + 4, y + alt + 15), r[:26], fill=(150, 220, 170))
    f.save(saida); return saida


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("chave", "trecho"):
        raise SystemExit(__doc__)
    from resolve_lib import conectar, fps_tl
    modo = sys.argv[1]
    r = conectar(); p = r.GetProjectManager().GetCurrentProject(); t = timeline(p, arg("--timeline"))
    if not t:
        raise SystemExit("sem timeline aberta")
    F = fps_tl(t); S = t.GetStartFrame(); dur = (t.GetEndFrame() - S) / F
    if modo == "chave":
        tempos = tempos_chave(t, F, S, int(arg("--max", 24)))
    else:
        em, raio, passo = float(arg("--em")), float(arg("--raio", 2)), float(arg("--passo", .25))
        n = int(2 * raio / passo) + 1
        tempos = [(round(em - raio + k * passo, 3), "") for k in range(n) if 0 <= em - raio + k * passo < dur]
    pasta = os.path.join(os.path.expanduser(arg("--pasta", "/tmp/ogab_conferir")), f"conferir_{modo}")
    quadros = exportar(p, t, tempos, pasta)
    print(folha(quadros, os.path.join(pasta, "folha.png")))
    print(f"{len(quadros)} de {len(tempos)} quadros ({t.GetName()})")


if __name__ == "__main__":
    main()
