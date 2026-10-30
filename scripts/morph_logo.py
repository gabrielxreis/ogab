"""Morph de forma complexa para logo (HyperFrames + GSAP MorphSVG): forma inicial -> letra grande -> palavra da marca.

  python3 morph_logo.py plano.json <pasta_projeto_hyperframes> [--render saida.mp4|.mov]

plano.json:
  {"palavra": "CALVERSTONE", "fonte": ".../Cardo-Regular.ttf", "tamanho": 98, "espaco": 0.2,
   "forma": "losango" | "circulo" | "<d de um path SVG>", "letra": "C" (padrão: 1ª letra da palavra), "tamanho_letra": 560,
   "cores": {"claro": "#f1dfa6", "meio": "#c9a657", "escuro": "#a8853a", "fundo": "#0B1F3A"},
   "divisor": true, "dur": 5, "id": "morph-logo", "fundo_animado": true}
A forma vira a letra grande e a letra grande vira a 1ª letra da palavra, enquanto as outras entram em cascata (sem
"bolha": cada letra tem o seu path, ver svg_texto.letras). Gera <projeto>/motions/<id>/index.html; --render chama o
HyperFrames (mov = com alfa, sem fundo).
"""
import json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from svg_texto import caminho, letras
from componentes import hf  # noqa: E402

FORMAS = {"losango": "M540,780 L690,930 L540,1080 L390,930 Z",
          "circulo": "M540,780 C622.8,780 690,847.2 690,930 C690,1012.8 622.8,1080 540,1080 C457.2,1080 390,1012.8 390,930 C390,847.2 457.2,780 540,780 Z"}

FUNDO = """
const cv = document.getElementById("bg"), cx = cv.getContext("2d");
function draw(t) {
  const g = cx.createRadialGradient(540, 920, 80, 540, 960, 1300);
  g.addColorStop(0, "#14345f"); g.addColorStop(0.5, "%(fundo)s"); g.addColorStop(1, "#050f1d");
  cx.fillStyle = g; cx.fillRect(0, 0, 1080, 1920);
  cx.strokeStyle = "%(grade)s"; cx.lineWidth = 1; const off = (t * 10) %% 60;
  for (let x = -60 + off; x < 1140; x += 60) { cx.beginPath(); cx.moveTo(x, 0); cx.lineTo(x, 1920); cx.stroke(); }
  for (let y = -60 + off; y < 1980; y += 60) { cx.beginPath(); cx.moveTo(0, y); cx.lineTo(1080, y); cx.stroke(); }
  const v = cx.createRadialGradient(540, 960, 700, 540, 960, 1250);
  v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,0.55)"); cx.fillStyle = v; cx.fillRect(0, 0, 1080, 1920);
}
const st = { t: 0 }; draw(0);
tl.to(st, { t: %(dur)s, duration: %(dur)s, ease: "none", onUpdate: () => draw(st.t) }, 0);
"""


def gerar(plano, projeto):
    p = dict(plano)
    cores = {"claro": "#f1dfa6", "meio": "#c9a657", "escuro": "#a8853a", "fundo": "#0B1F3A", **(p.get("cores") or {})}
    pal, fonte, dur, ident = p["palavra"], p["fonte"], p.get("dur", 5), p.get("id", "morph-logo")
    ls = letras(pal, fonte, p.get("tamanho", 98), p.get("espaco", 0.2), centro=(540, 930))
    dLetra, _, _ = caminho(p.get("letra", ls[0][0]), fonte, p.get("tamanho_letra", 560), centro=(540, 930))
    forma = FORMAS.get(p.get("forma", "losango"), p.get("forma"))
    outras = "".join(f'<path class="lt" d="{d}" fill="url(#ouro)"/>' for _, d in ls[1:])
    divisor = ('<g id="div" opacity="0"><rect x="380" y="1029" width="110" height="3" fill="%(meio)s"/>'
               '<rect x="530" y="1020.5" width="20" height="20" fill="%(meio)s" transform="rotate(45 540 1030.5)"/>'
               '<rect x="590" y="1029" width="110" height="3" fill="%(meio)s"/></g>' % cores) if p.get("divisor", True) else ""
    m = cores["meio"].lstrip("#"); grade = f"rgba({int(m[0:2], 16)},{int(m[2:4], 16)},{int(m[4:6], 16)},0.06)"
    fundo_js = (FUNDO % {"fundo": cores["fundo"], "dur": dur, "grade": grade}) if p.get("fundo_animado", True) else ""
    html = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="UTF-8" /><meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/MorphSVGPlugin.min.js"></script>
<style>* {{ margin: 0; padding: 0; box-sizing: border-box; }} html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: transparent; }}
#root {{ position: relative; width: 100%; height: 100%; }} #bg {{ position: absolute; inset: 0; }} svg {{ position: absolute; inset: 0; }}</style>
</head><body>
<div id="root" data-composition-id="{ident}" data-start="0" data-duration="{dur}" data-width="1080" data-height="1920" data-fps="30">
<canvas id="bg" width="1080" height="1920"></canvas>
<svg width="1080" height="1920" viewBox="0 0 1080 1920">
  <defs><linearGradient id="ouro" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{cores['claro']}"/><stop offset=".55" stop-color="{cores['meio']}"/><stop offset="1" stop-color="{cores['escuro']}"/></linearGradient></defs>
  <path id="m" d="{forma}" fill="url(#ouro)"/>
  <path id="alvoL" d="{dLetra}" style="visibility:hidden"/>
  <path id="alvoP" d="{ls[0][1]}" style="visibility:hidden"/>
  <g id="resto">{outras}</g>
  {divisor}
</svg>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{fundo_js}
gsap.registerPlugin(MorphSVGPlugin);
gsap.set("#m", {{ transformOrigin: "50% 50%" }});
tl.from("#m", {{ scale: 0, rotation: -90, duration: 0.7, ease: "power3.out" }}, 0.1);
tl.to("#m", {{ morphSVG: {{ shape: "#alvoL", type: "rotational" }}, duration: 1.1, ease: "power3.inOut" }}, 0.9);
tl.to("#m", {{ morphSVG: {{ shape: "#alvoP" }}, duration: 1.0, ease: "power3.inOut" }}, 2.3);
tl.from(".lt", {{ opacity: 0, x: 40, filter: "blur(6px)", duration: 0.55, stagger: 0.06, ease: "power3.out" }}, 2.75);
if (document.getElementById("div")) tl.fromTo("#div", {{ opacity: 0, scaleX: 0, transformOrigin: "50% 50%" }}, {{ opacity: 1, scaleX: 1, duration: 0.6, ease: "power3.out" }}, 3.4);
window.__timelines = window.__timelines || {{}};
window.__timelines["{ident}"] = tl;
</script>
</body></html>'''
    pasta = os.path.join(projeto, "motions", ident); os.makedirs(pasta, exist_ok=True)
    arq = os.path.join(pasta, "index.html"); open(arq, "w", encoding="utf-8").write(html)
    return arq


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    plano = json.load(open(a[0])); arq = gerar(plano, a[1]); print(arq)
    if "--render" in a:
        saida = os.path.abspath(a[a.index("--render") + 1]); fmt = "mov" if saida.endswith(".mov") else "mp4"
        import progresso   # LEI do usuário (30/10/2026): render de motion sempre com a barra e o link para acompanhar
        progresso.hf(["npx", "--yes", hf(), "render", os.path.abspath(os.path.join(a[1], "motions", plano.get("id", "morph-logo"))),
                      "--format", fmt, "-o", saida], "morph-logo")
        print(saida)
