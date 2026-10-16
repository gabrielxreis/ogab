"""Preset GLASS: movimentos de câmera na V1 do DaVinci, sincronizados com as cenas que entram com slide.

  python camera_davinci.py camera.json            -> aplica (refaz o nó CamGab do zero em cada clipe até "ate")
  python camera_davinci.py camera.json --tirar    -> remove o nó CamGab (clipes voltam ao original)

camera.json:
  { "timeline": "Minha Timeline", "ate": 48.4, "rosto": [0.47, 0.62],
    "zoom":   [[0, 1.18], [2.2, 1.0], [2.85, 1.0], [3.05, 1.12], ...],     tempo da timeline (s), zoom
    "slides": [[4.15, 9.80, 1], [15.0, 25.75, -1], ...] }                  início e fim da cena com slide, direção
  rosto = posição do rosto no quadro (x da esquerda, y de BAIXO, 0-1): o zoom acontece em volta dele, sem borda preta.
  Cada slide: a câmera sai 60% para o lado oposto em 0,4 s (power3, igual ao GSAP das cenas) com respiro de zoom +6%,
  fica escondida pela cena e volta do outro lado no fim. Motion blur no nó Transform do Fusion de cada clipe.
Precisa do resolve_lib.py do Gab (ou de DaVinciResolveScript no PYTHONPATH) e do DaVinci aberto no projeto.
Render de prova: MOV ProRes 422 LT (no Windows o MP4 H.264 da Media Foundation derrubou o DaVinci com Fusion pesado).
"""
import json, math, sys

SL, DESLOC, RESPIRO = 0.4, 0.6, 0.06


def ease2(u):
    return 2 * u * u if u < .5 else 1 - (-2 * u + 2) ** 2 / 2


def ease3(u):
    return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2


def main(a):
    cfg = json.load(open(a[0], encoding="utf-8"))
    chaves, slides, rosto = cfg["zoom"], cfg.get("slides", []), cfg.get("rosto", (.5, .6))

    def zoom_base(t):
        if t <= chaves[0][0]:
            return chaves[0][1]
        for (x0, z0), (x1, z1) in zip(chaves, chaves[1:]):
            if x0 <= t <= x1:
                return z0 + (z1 - z0) * (ease2((t - x0) / (x1 - x0)) if x1 > x0 else 1)
        return chaves[-1][1]

    def valor(t):
        z, s = zoom_base(t), 0.0
        for x0, x1, d in slides:
            if x0 <= t <= x0 + SL:
                u = (t - x0) / SL; s = -d * DESLOC * ease3(u); z *= 1 + RESPIRO * math.sin(math.pi * u)
            elif x0 + SL < t < x1 - SL:
                s = -d * DESLOC
            elif x1 - SL <= t <= x1:
                u = (t - (x1 - SL)) / SL; s = d * DESLOC * (1 - ease3(u)); z *= 1 + RESPIRO * math.sin(math.pi * u)
        return z, s

    try:
        import resolve_lib as R
        r = R.conectar()
        comp_de, quadro = R._comp_do_clipe, R._quadro_comp
    except ImportError:
        import DaVinciResolveScript as dvr
        r = dvr.scriptapp("Resolve")
        comp_de = lambda it: it.GetFusionCompByIndex(1) if it.GetFusionCompCount() else it.AddFusionComp()
        quadro = lambda comp, t_arq, fps: round(t_arq * fps + comp.GetAttrs()["COMPN_GlobalStart"])
    p = r.GetProjectManager().GetCurrentProject()
    t = [p.GetTimelineByIndex(i + 1) for i in range(p.GetTimelineCount()) if p.GetTimelineByIndex(i + 1).GetName() == cfg["timeline"]][0]
    p.SetCurrentTimeline(t)
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame()
    clipes = [x for x in sorted(t.GetItemListInTrack("video", 1), key=lambda x: x.GetStart()) if (x.GetStart() - S) / F < cfg["ate"] - .01]
    for it in clipes:
        comp = comp_de(it)
        mi, mo = comp.FindTool("MediaIn1"), comp.FindTool("MediaOut1")
        x = comp.FindTool("CamGab")
        if x:
            x.Delete()
        mo.Input = mi.Output
        if "--tirar" in a:
            continue
        fs = float(it.GetMediaPoolItem().GetClipProperty("FPS") or F)
        a_tl, b_tl = (it.GetStart() - S) / F, (it.GetEnd() - S) / F
        a_arq = it.GetSourceStartFrame() / fs
        comp.Lock(); tf = comp.AddTool("Transform", -32768, -32768); tf.SetAttrs({"TOOLS_Name": "CamGab"}); comp.Unlock()
        tf.Input = mi.Output; mo.Input = tf.Output
        tf.SetInput("MotionBlur", 1); tf.SetInput("Quality", 3); tf.SetInput("ShutterAngle", 180)
        tf.AddModifier("Size", "BezierSpline"); tf.AddModifier("Center", "XYPath")
        tt, n = a_tl, 0
        while tt <= b_tl + 1e-6:
            z, s = valor(tt)
            cx = .5 + (rosto[0] - .5) * (1 - z) + s; cy = .5 + (rosto[1] - .5) * (1 - z)
            f = quadro(comp, a_arq + (tt - a_tl), fs)
            tf.SetInput("Size", z, f); tf.SetInput("Center", {1: cx, 2: cy}, f); n += 1
            perto = any(x0 - .05 <= tt <= x0 + SL + .05 or x1 - SL - .05 <= tt <= x1 + .05 for x0, x1, _ in slides)
            tt += (1 if perto else 2) / F
        print(f"{a_tl:7.2f}-{b_tl:7.2f}s  {n} chaves")
    r.GetProjectManager().SaveProject()
    print("ok", len(clipes), "clipes")


if __name__ == "__main__":
    main(sys.argv[1:])
