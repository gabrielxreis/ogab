"""Prova de fogo da fonte: monta a arte de verdade no Photoshop com cada fonte candidata e mede qual bate com a
referência na região do texto (nota de bordas do sobrepor.py). Decide quando o comparar_fonte.py fica em dúvida
(referência pequena/comprimida, traço fino, pesos vizinhos da mesma família).

    python3 provar_fontes.py arte.jsx ref.png VAR "Fonte-A,Fonte-B,Fonte-C" X1 Y1 X2 Y2 MARCA=... [OUTRA=...]

- No arte.jsx a fonte testada vem de uma variável:  fonte: (typeof VAR !== "undefined") ? VAR : "Padrão"
- X1 Y1 X2 Y2 = região do texto em pixels do documento (1080). O texto precisa ter `alvo` (medido), senão a
  posição muda junto e a comparação perde sentido.
- Saída: ranking pela nota; as sobreposições ficam na pasta temporária para conferir no olho.
"""
import os
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(AQUI, "..", ".venv", "bin", "python")


def main():
    arte, ref, var, fontes = sys.argv[1:5]; regiao = sys.argv[5:9]; extras = sys.argv[9:]
    tmp = tempfile.mkdtemp(prefix="provar_"); res = []
    for f in [x.strip() for x in fontes.split(",") if x.strip()]:
        subprocess.run([sys.executable, os.path.join(AQUI, "montar.py"), arte, f"SAIDA={tmp}", f"{var}={f}", *extras],
                       capture_output=True, text=True)
        pngs = [p for p in os.listdir(tmp) if p.endswith(".png") and not p.startswith("ov_")]
        if not pngs:
            print(f"{f}: falhou"); continue
        out = subprocess.run([PY, os.path.join(AQUI, "sobrepor.py"), ref, os.path.join(tmp, pngs[0]),
                              os.path.join(tmp, f"ov_{f}.png"), "--regiao", *regiao], capture_output=True, text=True).stdout
        try:
            nota = float(out.split(":")[1].split()[0])
        except Exception:
            nota = 0
        res.append((nota, f)); print(f"{nota:.3f}  {f}", flush=True)
    print("\nRANKING:"); [print(f"  {n:.3f}  {f}") for n, f in sorted(res, reverse=True)]; print(tmp)


if __name__ == "__main__":
    main()
