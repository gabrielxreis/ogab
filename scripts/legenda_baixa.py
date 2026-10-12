"""Legenda desce para Y 390 sob motion/CTA/lettering, SEM clicar (regra do usuário, 12/10/2026).

  python3 legenda_baixa.py "<timeline>" <pasta_do_video> [--y 390] [--simular]
  python3 legenda_baixa.py "<timeline>" <pasta_do_video> --desfazer

Por que assim: a API do DaVinci 21 sempre põe SRT na trilha de legenda 1 (trackIndex, lock e trilha desligada não
mudam isso) e InsertFusionTitleIntoTimeline cai na V1. Então cada legenda que cruza um motion vira um CLIPE
TRANSPARENTE (ProRes 4444) com o texto no estilo GAB USA (Poppins Bold, caixa alta, branca, mesmo tamanho medido no
render: 414 px para "NÃO FOI O MOVIMENTO"), centralizado em y = 1920 - Y, na trilha de vídeo do topo "LEGENDA BAIXA",
e o item original sai da trilha de legenda. --desfazer recoloca tudo na trilha 1 (estilo da trilha mantido).
Rodar `retrato.py antes` e `depois --alvo subtitle1,video<N>` em volta.
"""
import json, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as R
from projeto import MOTION

FONTE = os.path.expanduser("~/Library/Fonts/Poppins-Bold.ttf")
TAM = 35.5          # px na timeline 1080x1920 (calibrado contra o preset GAB USA)
TRILHA = "LEGENDA BAIXA"


def png(texto, y_centro, arq, W=1080, H=1920, k=4):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(FONTE, int(TAM * k)); im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    t = texto.upper(); b = d.textbbox((0, 0), t, font=f, anchor="mm")
    d.text((W * k / 2 + 2 * k, y_centro * k + 2 * k), t, font=f, fill=(0, 0, 0, 70), anchor="mm")   # sombra leve
    d.text((W * k / 2, y_centro * k), t, font=f, fill=(255, 255, 255, 255), anchor="mm")
    im.resize((W, H), Image.LANCZOS).save(arq)


def clipe(texto, dur, fps, y, pasta, i):
    os.makedirs(pasta, exist_ok=True)
    p = os.path.join(pasta, f"lb_{i:03d}.png"); m = os.path.join(pasta, f"lb_{i:03d}_{re.sub(r'[^a-z0-9]+', '_', texto.lower())[:24]}.mov")
    png(texto, 1920 - y, p)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", p, "-t", f"{dur + 0.2:.3f}", "-r", str(fps),
                    "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", m], check=True)
    os.remove(p); return m


def cobertos(t, minimo=0.3):
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame(); sec = lambda f: (f - S) / F
    tampa = [(sec(x.GetStart()), sec(x.GetEnd())) for k in range(2, t.GetTrackCount("video") + 1) if t.GetTrackName("video", k) != TRILHA
             for x in t.GetItemListInTrack("video", k) or [] if MOTION.search(x.GetName())
             or not (x.GetMediaPoolItem() and x.GetMediaPoolItem().GetClipProperty("File Path"))]
    out = []
    for x in t.GetItemListInTrack("subtitle", 1) or []:
        if not x.GetClipEnabled(): continue   # desativada sob motion (estilo do cliente): fica desativada, não desce
        a, b = sec(x.GetStart()), sec(x.GetEnd())
        if any(min(b, d) - max(a, c) >= minimo * (b - a) for c, d in tampa): out.append((x, a, b))
    return out


def srt_de(itens):
    tc = lambda s: f"{int(s // 3600):02d}:{int(s // 60 % 60):02d}:{int(s % 60):02d},{int(round(s * 1000)) % 1000:03d}"
    return "\n".join(f"{i + 1}\n{tc(a)} --> {tc(b)}\n{txt}\n" for i, (a, b, txt) in enumerate(itens))


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); sys.exit(2)
    nome, pasta = a[0], a[1]; y = int(a[a.index("--y") + 1]) if "--y" in a else 390
    r = R.conectar(); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool()
    t = next((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome), None)
    if not t: sys.exit(f"timeline não encontrada: {nome}")
    p.SetCurrentTimeline(t); time.sleep(0.5)
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame(); sec = lambda f: (f - S) / F
    reg = os.path.join(pasta, "legendas", "legenda_baixa.json")
    trilha = next((k for k in range(1, t.GetTrackCount("video") + 1) if t.GetTrackName("video", k) == TRILHA), None)

    if "--desfazer" in a:
        if not os.path.exists(reg): sys.exit("nada para desfazer")
        movidas = [tuple(x) for x in json.load(open(reg))]
        atuais = [(sec(x.GetStart()), sec(x.GetEnd()), x.GetName()) for x in t.GetItemListInTrack("subtitle", 1) or []]
        todas = sorted(atuais + movidas)
        srt = os.path.join(pasta, "legendas", "legendas_restauradas.srt"); open(srt, "w").write(srt_de(todas))
        if trilha: t.DeleteClips(t.GetItemListInTrack("video", trilha) or [])
        R.colocar_legendas(t, mp, srt, p=p); os.remove(reg); print(f"desfeito: {len(todas)} legendas na trilha 1"); return

    alvo = cobertos(t)
    for x, s0, s1 in alvo: print(f"  {s0:6.2f}-{s1:6.2f}  {x.GetName()}")
    if "--simular" in a or not alvo: print(f"{len(alvo)} legenda(s) para descer"); return
    if not trilha:
        t.AddTrack("video"); trilha = t.GetTrackCount("video"); t.SetTrackName("video", trilha, TRILHA)
    dest = os.path.join(pasta, "legendas", "legenda_baixa"); movidas = json.load(open(reg)) if os.path.exists(reg) else []
    for i, (x, s0, s1) in enumerate(alvo):
        m = clipe(x.GetName(), s1 - s0, int(round(F)), y, dest, len(movidas) + i)
        it = R.importar(mp, m, "Legendas")
        ok = mp.AppendToTimeline([{"mediaPoolItem": it, "mediaType": 1, "trackIndex": trilha, "recordFrame": x.GetStart(),
                                   "startFrame": 0, "endFrame": x.GetEnd() - x.GetStart() - 1}])
        if not ok: sys.exit(f"não entrou o clipe de '{x.GetName()}': nada foi apagado dessa legenda")
        movidas.append((round(s0, 3), round(s1, 3), x.GetName()))
    if not t.DeleteClips([x for x, _, _ in alvo]): sys.exit("clipes entraram, mas as legendas originais não saíram (timeline atual?)")
    json.dump(movidas, open(reg, "w"), ensure_ascii=False, indent=1)
    print(f"{len(alvo)} legenda(s) desceram para Y {y} na trilha V{trilha} '{TRILHA}'")
    r.GetProjectManager().SaveProject()


if __name__ == "__main__":
    main()
