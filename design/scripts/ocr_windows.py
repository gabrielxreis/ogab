"""OCR nativo do Windows (Windows.Media.Ocr), no mesmo JSON do swift/ocr do Mac. Uso: ocr_windows.py imagem.png [pt-BR]
Cada linha: texto, caixa em px, palavras (p, i, n, x, y, w, h), angulo. O Windows não dá confiança: conf = 1.
Imagem pequena é ampliada antes (o OCR do Windows erra letra com menos de ~20 px) e as caixas voltam para a escala original."""
import asyncio
import json
import os
import sys
import tempfile

from PIL import Image
from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage import FileAccessMode, StorageFile


async def ler(caminho, idioma):
    arq = await StorageFile.get_file_from_path_async(caminho)
    stream = await arq.open_async(FileAccessMode.READ)
    bmp = await (await BitmapDecoder.create_async(stream)).get_software_bitmap_async()
    motor = OcrEngine.try_create_from_language(Language(idioma)) or OcrEngine.try_create_from_user_profile_languages()
    return await motor.recognize_async(bmp)


def main():
    img = os.path.abspath(sys.argv[1]); idioma = sys.argv[2].split(",")[0] if len(sys.argv) > 2 else "pt-BR"
    im = Image.open(img).convert("RGB"); W, H = im.size
    k = min(2.0, max(1.0, 2000 / W), (OcrEngine.max_image_dimension - 1) / max(W, H))
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = f.name
    try:
        (im.resize((round(W * k), round(H * k)), Image.LANCZOS) if k != 1 else im).save(tmp)
        res = asyncio.run(ler(tmp, idioma))
    finally:
        os.unlink(tmp)
    ang = float(res.text_angle) if res.text_angle is not None else 0.0
    out = []
    for linha in res.lines:
        palavras, texto = [], ""
        for w in linha.words:
            r = w.bounding_rect
            ini = len(texto) + (1 if texto else 0); texto = (texto + " " if texto else "") + w.text
            palavras.append({"p": w.text, "i": ini, "n": len(w.text),
                             "x": int(r.x / k), "y": int(r.y / k), "w": int(r.width / k), "h": int(r.height / k)})
        if not palavras:
            continue
        x1 = min(p["x"] for p in palavras); y1 = min(p["y"] for p in palavras)
        x2 = max(p["x"] + p["w"] for p in palavras); y2 = max(p["y"] + p["h"] for p in palavras)
        out.append({"texto": texto, "conf": 1.0, "palavras": palavras, "angulo": ang, "x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1})
    out.sort(key=lambda o: o["y"])
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
