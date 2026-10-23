"""Gab no Final Cut Pro: plano do Gab -> projeto FCPXML (o Final Cut importa pronto).

  python3 fcpxml.py plano.json saida.fcpxml [--importar] [--validar]

plano.json:
{ "evento": "Calverstone", "projeto": "Reels 13",          # "biblioteca": "~/Movies/X.fcpbundle" só se quiser outra
  "w": 1080, "h": 1920, "fps": 30,
  "v1": [ {"arquivo": "talking.mp4", "de": 0.0, "ate": 4.2, "no": 0.0}, ... ],  # linha principal ("no" opcional: buraco vira gap)
  "dur": 63.0,                                                                  # opcional: estende a timeline até aqui
  "camadas": [ {"arquivo": "broll.mp4", "no": 2.0, "de": 0, "dur": 2.5, "mudo": true} ],   # b-roll/motion acima (lane 1, 2...)
  "audios":  [ {"arquivo": "musica.wav", "no": 0, "de": 0, "dur": 30, "db": -18, "fade_in": 0.5, "fade_out": 2.5} ],   # música, SFX (abaixo)
  "titulos": [ {"texto": "LICENÇA", "no": 1.0, "dur": 2.0, "fonte": "Poppins", "estilo": "Bold", "tamanho": 120,
                "cor": "#FFFFFF", "y": 400} ],    # lettering simples (Basic Title); tamanho em px do quadro, y em px a partir do centro (+ = acima)
  "legenda": [ {"texto": "VOCÊ PRECISA", "no": 0.2, "dur": 1.1} ],              # legenda queimada no estilo do Gab
  "legenda_preset": "a-grande-missao",          # finalcut/presets/legenda/<nome>.json (legenda medida do DaVinci)
  "legenda_estilo": {"fonte": "Poppins", "estilo": "Bold", "tamanho": 64, "cor": "#FFFFFF", "y": -520, "caixa_alta": true} }   # sobrepõe o preset
Tempos em segundos da timeline (no) e do arquivo (de/ate/dur). Tudo vira múltiplo exato do quadro de cada mídia.
--importar abre no Final Cut (Apple Event "open": ele importa o .fcpxml na biblioteca do plano).
--validar confere contra o DTD oficial que vem dentro do Final Cut (FCPXMLv1_11.dtd).
"""
import json, os, subprocess, sys, urllib.parse
from fractions import Fraction
from xml.sax.saxutils import escape, quoteattr

VERSAO = "1.11"
APP = "/Applications/Final Cut Pro Creator Studio.app"
DTD_REL = "/Contents/Frameworks/Interchange.framework/Versions/A/Resources/FCPXMLv1_11.dtd"   # o app pode ser "Final Cut Pro" ou "... Creator Studio"
# Final Cut mede tamanho E posição do título numa escala de 1080 de altura: no vertical 1080x1920 tudo é x1080/1920.
BASIC_TITLE = ".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"
POS_KEY = "9999/999166631/999166633/1/100/101"   # parâmetro Position do Basic Title


def app_fcp():
    for c in (APP, "/Applications/Final Cut Pro.app"):
        if os.path.exists(c):
            return c
    raise SystemExit("Final Cut Pro não encontrado em /Applications")


def sonda(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,sample_rate,channels",
                        "-show_entries", "format=duration", "-of", "json", arq], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout); v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    fr = Fraction(v["r_frame_rate"]) if v else None
    return {"dur": float(d["format"]["duration"]), "w": v and v["width"], "h": v and v["height"], "fps": fr,
            "audio": bool(a), "canais": int(a["channels"]) if a else 0, "hz": int(a["sample_rate"]) if a else 48000}


def t(seg, fps):
    """Segundos -> tempo FCPXML exato em quadros de `fps` (ex.: '45/30s')."""
    fps = Fraction(fps); q = round(Fraction(seg).limit_denominator(100000) * fps)
    v = Fraction(q) / fps
    return f"{v.numerator}/{v.denominator}s" if v.denominator != 1 else f"{v.numerator}s"


def cor(h, a=1):
    h = h.lstrip("#"); return " ".join(f"{int(h[i:i + 2], 16) / 255:.4f}" for i in (0, 2, 4)) + f" {a}"


class Projeto:
    def __init__(s, p):
        s.p, s.fps = p, Fraction(p.get("fps", 30)); s.res, s.ids, s.n, s.info = [], {}, 0, {}
        s.fmt = s._formato(p.get("w", 1080), p.get("h", 1920), s.fps)
        s.titulo_ref = s._id(); s.res.append(f'<effect id="{s.titulo_ref}" name="Basic Title" uid="{BASIC_TITLE}"/>')

    def _id(s):
        s.n += 1; return f"r{s.n}"

    def _formato(s, w, h, fps):
        k = ("fmt", w, h, fps)
        if k not in s.ids:
            i = s._id(); s.ids[k] = i
            fd = 1 / Fraction(fps)
            s.res.append(f'<format id="{i}" frameDuration="{fd.numerator}/{fd.denominator}s" width="{w}" height="{h}" '
                         f'colorSpace="1-1-1 (Rec. 709)"/>')
        return s.ids[k]

    def asset(s, arq):
        arq = os.path.abspath(os.path.expanduser(arq))
        if arq in s.ids:
            return s.ids[arq], s.info[arq]
        info = sonda(arq); i = s._id(); s.ids[arq] = i; s.info[arq] = info
        fps = info["fps"] or s.fps
        fmt = f' format="{s._formato(info["w"], info["h"], fps)}"' if info["w"] else ""
        aud = (f' hasAudio="1" audioSources="1" audioChannels="{info["canais"]}" audioRate="{info["hz"]}"' if info["audio"] else "")
        vid = ' hasVideo="1" videoSources="1"' if info["w"] else ""
        url = "file://" + urllib.parse.quote(arq)
        s.res.append(f'<asset id="{i}" name={quoteattr(os.path.splitext(os.path.basename(arq))[0])} start="0s" '
                     f'duration="{t(info["dur"], fps)}"{vid}{aud}{fmt}><media-rep kind="original-media" src={quoteattr(url)}/></asset>')
        return i, info

    # -------------------------------------------------- montagem
    def montar(s):
        p, F = s.p, s.fps
        spine, pos = [], Fraction(0)
        q = lambda x, r: Fraction(round(Fraction(x).limit_denominator(100000) * r)) / r   # alinha no quadro
        for c in p["v1"]:
            ref, info = s.asset(c["arquivo"]); fa = info["fps"] or F
            if c.get("no") is not None and q(c["no"], F) > pos:   # buraco na linha principal: gap
                g = q(c["no"], F) - pos
                spine.append({"gap": True, "offset": pos, "start": Fraction(0), "dur": g, "fa": F, "filhos": []}); pos += g
            ini = q(c["de"], fa)
            dur = q(c["ate"] - c["de"], F)
            spine.append({"ref": ref, "offset": pos, "start": ini, "dur": dur, "fa": fa, "nome": os.path.basename(c["arquivo"]),
                          "filhos": [], "db": c.get("db")})
            pos += dur
        fim = q(p.get("dur", 0), F)
        if fim > pos:
            spine.append({"gap": True, "offset": pos, "start": Fraction(0), "dur": fim - pos, "fa": F, "filhos": []}); pos = fim
        s.total = pos

        def pai(no):
            for c in spine:
                if c["offset"] <= no < c["offset"] + c["dur"]:
                    return c
            return spine[-1]

        def local(c, no):   # tempo da timeline -> tempo local do clipe-pai (offset dos conectados é no tempo do pai)
            return c["start"] + (no - c["offset"])

        def anexar(no, xml_fn):
            no = Fraction(no).limit_denominator(100000); c = pai(no); c["filhos"].append(xml_fn(local(c, no), c["fa"]))

        for k, cam in enumerate(p.get("camadas", [])):
            ref, info = s.asset(cam["arquivo"]); fa = info["fps"] or F; lane = cam.get("lane", 1)
            vol = '<adjust-volume amount="-96dB"/>' if cam.get("mudo", True) and info["audio"] else ""
            anexar(cam["no"], lambda off, pfa, ref=ref, cam=cam, fa=fa, lane=lane, vol=vol:
                   f'<asset-clip ref="{ref}" lane="{lane}" offset="{t(off, pfa)}" start="{t(cam.get("de", 0), fa)}" '
                   f'duration="{t(cam["dur"], F)}" name="broll">{vol}</asset-clip>')
        for k, au in enumerate(p.get("audios", [])):
            ref, info = s.asset(au["arquivo"]); lane = au.get("lane", -(k + 1))
            fades = "".join([f'<fadeIn type="easeIn" duration="{t(au["fade_in"], F)}"/>' if au.get("fade_in") else "",
                             f'<fadeOut type="easeOut" duration="{t(au["fade_out"], F)}"/>' if au.get("fade_out") else ""])
            vol = (f'<adjust-volume amount="{au.get("db", 0)}dB">' + (f'<param name="amount">{fades}</param>' if fades else "")
                   + '</adjust-volume>')
            anexar(au.get("no", 0), lambda off, pfa, ref=ref, au=au, lane=lane, vol=vol:
                   f'<asset-clip ref="{ref}" lane="{lane}" offset="{t(off, pfa)}" start="{t(au.get("de", 0), 48000)}" '
                   f'duration="{t(au["dur"], F)}" srcEnable="audio" name="audio">{vol}</asset-clip>')
        pre = {}
        if p.get("legenda_preset"):   # finalcut/presets/legenda/<nome>.json (medido do DaVinci)
            pre = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets", "legenda",
                                              p["legenda_preset"] + ".json"), encoding="utf-8"))
            pre = {k: v for k, v in pre.items() if not k.startswith("_")}
        est = {"fonte": "Poppins", "estilo": "Bold", "tamanho": 64, "cor": "#FFFFFF", "y": -520, "caixa_alta": True,
               **pre, **p.get("legenda_estilo", {})}
        topo = max([c.get("lane", 1) for c in p.get("camadas", [])] + [0])   # títulos e legenda sempre acima dos motions
        itens = [(ti, ti.get("lane", topo + 2)) for ti in p.get("titulos", [])]
        itens += [({**est, **lg, "texto": lg["texto"].upper() if est.get("caixa_alta") else lg["texto"]}, topo + 1) for lg in p.get("legenda", [])]
        for k, (ti, lane) in enumerate(itens):
            sid = f"ts{k + 1}"
            txt = escape(ti["texto"])
            anexar(ti["no"], lambda off, pfa, ti=ti, sid=sid, txt=txt, lane=lane:
                   f'<title ref="{s.titulo_ref}" lane="{lane}" offset="{t(off, pfa)}" start="3600s" duration="{t(ti["dur"], F)}" '
                   f'name={quoteattr(ti["texto"][:30])}><param name="Position" key="{POS_KEY}" value="0 {round(ti.get("y", 0) * 1080 / s.p.get("h", 1080), 1)}"/>'
                   f'<text><text-style ref="{sid}">{txt}</text-style></text>'
                   f'<text-style-def id="{sid}"><text-style font={quoteattr(ti.get("fonte", "Poppins"))} fontSize="{round(ti.get("tamanho", 100) * 1080 / s.p.get("h", 1080), 1)}" '
                   f'fontFace={quoteattr(ti.get("estilo", "Bold"))} fontColor="{cor(ti.get("cor", "#FFFFFF"))}" alignment="center"/>'
                   f'</text-style-def></title>')
        corpo = []
        for c in spine:
            if c.get("gap"):
                corpo.append(f'<gap offset="{t(c["offset"], F)}" start="0s" duration="{t(c["dur"], F)}" name="Gap">{"".join(c["filhos"])}</gap>')
                continue
            vol = f'<adjust-volume amount="{c["db"]}dB"/>' if c.get("db") is not None else ""
            corpo.append(f'<asset-clip ref="{c["ref"]}" offset="{t(c["offset"], F)}" start="{t(c["start"], c["fa"])}" '
                         f'duration="{t(c["dur"], F)}" name={quoteattr(c["nome"])}>{vol}{"".join(c["filhos"])}</asset-clip>')
        return "".join(corpo)

    def xml(s):
        corpo = s.montar(); p = s.p
        lib = p.get("biblioteca")   # sem biblioteca: entra na biblioteca aberta no Final Cut (o normal)
        ev = (f'<event name={quoteattr(p.get("evento", "Gab"))}>\n<project name={quoteattr(p.get("projeto", "Gab"))}>\n'
              f'<sequence format="{s.fmt}" duration="{t(s.total, s.fps)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">\n'
              f'<spine>{corpo}</spine>\n</sequence>\n</project>\n</event>\n')
        if lib:
            lib = os.path.abspath(os.path.expanduser(lib))
            ev = f'<library location={quoteattr("file://" + lib + "/")}>\n{ev}</library>\n'
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n<fcpxml version="{VERSAO}">\n<resources>\n'
                + "\n".join(s.res) + f'\n</resources>\n{ev}</fcpxml>\n')


def validar(arq):
    import shutil, tempfile
    dtd = os.path.join(tempfile.gettempdir(), "FCPXMLv1_11.dtd"); shutil.copy(app_fcp() + DTD_REL, dtd)   # xmllint não aceita espaço no caminho
    r = subprocess.run(["xmllint", "--noout", "--dtdvalid", dtd, arq], capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


def importar(arq):
    subprocess.run(["open", "-a", app_fcp(), arq], check=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    plano = json.load(open(a[0], encoding="utf-8")); x = Projeto(plano).xml()
    open(a[1], "w", encoding="utf-8").write(x); print("ok", a[1])
    if "--validar" in a:
        ok, err = validar(a[1]); print("DTD ok" if ok else "DTD FALHOU:\n" + err)
    if "--importar" in a:
        importar(a[1]); print("importando no Final Cut")
