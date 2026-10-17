"""Layout do preset TELA DIVIDIDA (Reels 1080x1920): painel de motion em cima, apresentador embaixo, legenda-etiqueta na emenda.

Medidas tiradas das 4 "Edições Brabas" (13/10/2026): emenda em 46,5 % da altura -> painel 0-893 px, apresentador 893-1920 px.

  python3 layout.py guia [saida.png]                  -> guia 1080x1920 com as zonas (para conferir motion e enquadramento)
  python3 layout.py medir <video_do_apresentador>     -> zoom, pan, tilt e crop_top para o rosto ficar na metade de baixo
  python3 layout.py aplicar "<timeline>" [trilha=1]   -> mede o 1º clipe da trilha e aplica em todos os pedaços (DaVinci)
No DaVinci: Tilt positivo sobe a imagem; CropTop em pixels da fonte (1920). Conferir com 1 quadro de render.
"""
import os, sys
W, H = 1080, 1920
EMENDA = 893                 # y da divisão (46,5 %)
ROSTO_Y = 1330               # onde o centro do rosto fica (terço de cima da metade de baixo, olhar acima do meio)
ROSTO_LADO = 300             # tamanho do rosto desejado (px) para o enquadramento "do peito para cima"
LEGENDA_Y = EMENDA           # a etiqueta da legenda fica centrada na emenda


def guia(saida="guia_tela_dividida.png"):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, EMENDA), fill=(0, 160, 255, 50)); d.rectangle((0, EMENDA, W, H), fill=(255, 140, 0, 40))
    d.line((0, EMENDA, W, EMENDA), fill=(255, 255, 255, 255), width=4)
    d.rounded_rectangle((W / 2 - 250, LEGENDA_Y - 34, W / 2 + 250, LEGENDA_Y + 34), 10, outline=(255, 255, 255, 255), width=3)
    d.ellipse((W / 2 - ROSTO_LADO / 2, ROSTO_Y - ROSTO_LADO / 2 * 1.25, W / 2 + ROSTO_LADO / 2, ROSTO_Y + ROSTO_LADO / 2 * 1.25), outline=(255, 220, 0, 255), width=4)
    d.rectangle((60, 120, W - 60, EMENDA - 90), outline=(0, 200, 255, 255), width=3)          # área útil do painel
    d.rectangle((0, 0, W, 220), fill=(255, 0, 0, 40)); d.rectangle((0, 1600, W, H), fill=(255, 0, 0, 40))   # UI do Instagram
    for y, t in ((60, "PAINEL DE MOTION (0-893)"), (EMENDA + 50, "LEGENDA-ETIQUETA NA EMENDA"), (1760, "APRESENTADOR (893-1920) - UI do Instagram embaixo")):
        d.text((40, y), t, fill=(255, 255, 255, 255))
    im.save(saida); print("guia ->", saida); return saida


def calcular(face):
    """face = resolve_lib.medir_rosto(): {"cx","cy","lado"} no quadro 1080x1920 sem zoom."""
    z = max(1.0, round(ROSTO_LADO / max(1, face["lado"]), 3))
    pan = round(W / 2 - (W / 2 + (face["cx"] - W / 2) * z))
    fy = H / 2 + (face["cy"] - H / 2) * z
    tilt = round(fy - ROSTO_Y)                         # positivo sobe; aqui normalmente negativo (desce o apresentador)
    crop_top = max(0, round((EMENDA + tilt - H / 2) / z + H / 2))   # tudo acima da emenda some (o painel fica limpo)
    return {"zoom": z, "pan": pan, "tilt": tilt, "crop_top": crop_top}


def aplicar(t, enq, trilha=1):
    for x in t.GetItemListInTrack("video", trilha) or []:
        for k, v in (("ZoomX", enq["zoom"]), ("ZoomY", enq["zoom"]), ("Pan", enq["pan"]), ("Tilt", enq["tilt"]), ("CropTop", enq["crop_top"])):
            x.SetProperty(k, v)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: raise SystemExit(__doc__)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scripts"))
    if a[0] == "guia":
        guia(a[1] if len(a) > 1 else "guia_tela_dividida.png")
    elif a[0] == "medir":
        import resolve_lib as L
        f = L.medir_rosto(a[1]); print("rosto", f); print(calcular(f) if f else "rosto não encontrado")
    elif a[0] == "aplicar":
        import resolve_lib as L
        r = L.conectar(); p = r.GetProjectManager().GetCurrentProject()
        t = next(p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == a[1])
        trilha = int(a[2]) if len(a) > 2 else 1; it = t.GetItemListInTrack("video", trilha)[0]
        f = L.medir_rosto(it.GetMediaPoolItem().GetClipProperty("File Path"))
        if not f: sys.exit("rosto não encontrado: nada aplicado (medir à mão num quadro com grade)")
        enq = calcular(f); aplicar(t, enq, trilha); print("aplicado", enq)
