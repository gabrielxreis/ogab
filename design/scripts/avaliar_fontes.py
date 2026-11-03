"""Bancada de teste do reconhecimento de fonte: PSDs com camadas de texto viram verdade conhecida.

    .venv/bin/python avaliar_fontes.py pasta_com_psds [--max 40] [--filtro ""]

Para cada camada de texto visível (psd-tools): recorta a linha no composto achatado, roda o comparar_fonte e
confere se a fonte verdadeira (PostScript) está em 1º / no top 5, e se pelo menos a FAMÍLIA bate.
Só conta fontes instaladas (senão não tem como acertar). Relatório no fim + avaliacao_fontes.json.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

from psd_tools import PSDImage

AQUI = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
sys.path.insert(0, AQUI); import comparar_fonte as CF  # noqa


def main():
    pasta = sys.argv[1]; mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 40
    filtro = sys.argv[sys.argv.index("--filtro") + 1] if "--filtro" in sys.argv else ""
    idx = CF.indice(); tmp = tempfile.mkdtemp(prefix="aval_"); res = []
    for f in sorted(glob.glob(os.path.join(pasta, "**", "*.psd"), recursive=True)):
        try:
            psd = PSDImage.open(f); comp = psd.composite()
        except Exception as e:
            print("falhou abrir", os.path.basename(f), e); continue
        png = os.path.join(tmp, os.path.basename(f) + ".png"); comp.convert("RGB").save(png)
        for l in psd.descendants():
            if l.kind != "type" or not l.is_visible(): continue
            try:
                fontes = [str(x["Name"]).strip("'\x22") for x in l.resource_dict["FontSet"]]
                rs = l.engine_dict["StyleRun"]["RunArray"]; f0 = fontes[rs[0]["StyleSheet"]["StyleSheetData"].get("Font", 0)]
            except Exception:
                continue
            ss = rs[0]["StyleSheet"]["StyleSheetData"]
            txt = l.text.replace("\r", " ").strip()
            if ss.get("FontCaps", 0) == 2: txt = txt.upper()   # Caixa alta no estilo: a tela mostra maiúsculas
            fc = ss.get("FillColor", {}).get("Values", [1, 1, 1, 1]); cor = "#%02X%02X%02X" % tuple(round(v * 255) for v in fc[1:4])
            if abs(l.transform[1]) > 0.01 if hasattr(l, "transform") else False: continue   # texto girado fica fora
            efeitos_cor = any(type(e).__name__ in ("GradientOverlay", "ColorOverlay", "PatternOverlay") for e in (l.effects or []))
            if len(set(fontes[r["StyleSheet"]["StyleSheetData"].get("Font", 0)] for r in rs)) > 1 or "\r" in l.text or "\x03" in l.text or len(txt) < 3 or efeitos_cor:
                continue   # só linha única de uma fonte (o teste é da fonte, não da quebra)
            if f0 not in idx:
                continue
            x1, y1, x2, y2 = l.bbox
            if x2 - x1 < 20 or y2 - y1 < 8 or x1 < 0 or y1 < 0 or x2 > comp.width or y2 > comp.height: continue
            args = [PY, os.path.join(AQUI, "comparar_fonte.py"), png, str(x1), str(y1), str(x2), str(y2), txt, "--top", "5", "--cor", cor]
            if filtro: args += ["--filtro", filtro]
            if "--sem-fino" in sys.argv: args += ["--sem-fino"]
            out = subprocess.run(args, capture_output=True, text=True, timeout=900).stdout.strip().splitlines()
            cands = [ln.split()[-1] for ln in out if ln[:1].isdigit()]
            fam = lambda s: s.split("-")[0]
            r = {"psd": os.path.basename(f), "txt": txt[:30], "real": f0, "top": cands, "acerto1": bool(cands) and cands[0] == f0,
                 "acerto5": f0 in cands, "familia": bool(cands) and fam(cands[0]) == fam(f0), "alt": y2 - y1}
            res.append(r)
            print(f"{'OK ' if r['acerto1'] else ('5  ' if r['acerto5'] else ('FAM' if r['familia'] else 'X  '))} {f0:<28} -> {cands[:2]}  '{txt[:24]}'", flush=True)
            if len(res) >= mx: break
        if len(res) >= mx: break
    n = max(1, len(res))
    print(f"\n{len(res)} linhas: 1º {sum(r['acerto1'] for r in res) / n:.0%} | top5 {sum(r['acerto5'] for r in res) / n:.0%} | família {sum(r['familia'] for r in res) / n:.0%}")
    json.dump(res, open(os.path.join(AQUI, "..", "docs", "catalogo", "local", "avaliacao_fontes.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
