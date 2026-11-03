"""Extrai as imagens embutidas nos smart objects de um PSD (fotos, logos, vetores) para uma pasta.
    python3 extrair_so.py arquivo.psd pasta/
Útil para reaproveitar o material do próprio cliente (fotos de banco já licenciadas, logos)."""
import os, sys, hashlib
from psd_tools import PSDImage
psd = PSDImage.open(sys.argv[1]); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
vistos = set()
for l in psd.descendants():
    if l.kind != "smartobject": continue
    so = l.smart_object
    try: dados = so.data
    except Exception: continue
    if not dados: continue
    h = hashlib.md5(dados).hexdigest()
    if h in vistos: continue
    vistos.add(h)
    nome = so.filename or (l.name + "." + (so.filetype or "bin"))
    nome = nome.replace("/", "_")
    open(os.path.join(out, nome), "wb").write(dados)
    print(f"{len(dados)//1024:>7} KB  {nome}")
