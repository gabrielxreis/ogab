#!/usr/bin/env python3
"""Arte estática (PSD, PDF do Canva/Illustrator ou imagem achatada) -> camadas -> animação HyperFrames.

Fluxo (detalhes em docs/etapas/arte_animada.md):
    python3 arte_animada.py ler <arte.psd|.psb|.pdf|.png|.jpg> <pasta_projeto> [--prancheta N|nome] [--pagina N]
                                [--motor auto|psdtools|photoshop]
    python3 arte_animada.py plano <pasta_projeto>          # tabela: camada, papel, animação, tempo (para revisar)
    python3 arte_animada.py montar <pasta_projeto> [--duracao 10] [--largura 1080] [--particulas "#ff8a3c"]
                                [--sem-final-exato]
    npx hyperframes render --format mp4 -o <saida.mp4>     # dentro da pasta_projeto

`ler` grava <pasta>/camadas/*.png (uma por bloco animável, recortada) + <pasta>/camadas.json (posição, papel, blend,
texto) + camadas/_final.png (a arte inteira, para a trava final). O agente pode editar papel/anim/t no camadas.json
antes do `montar` (o `montar` respeita o que estiver escrito).
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

import numpy as np
from PIL import Image

AQUI = Path(__file__).resolve().parent
OYOSHI = Path.home() / ".claude/skills/oyoshi/scripts"

# ---------------------------------------------------------------- utilidades

NOMES = {
    "fundo": r"\b(bg|fundo|background|plano de fundo|backdrop)\b",
    "textura": r"(textur|texture|grain|gr[aã]o|noise|ru[ií]do|overlay|luz|light|flare|poeira|dust|gradient|degrad)",
    "pessoa": r"(foto|photo|pessoa|person|people|modelo|model|pastor|cantor|preletor|retrato|portrait|rosto|face|recorte)",
    "logo": r"(logo|marca|brand|selo)",
}
BLEND_CSS = {"NORMAL": "normal", "PASS_THROUGH": "normal", "MULTIPLY": "multiply", "SCREEN": "screen",
             "OVERLAY": "overlay", "DARKEN": "darken", "LIGHTEN": "lighten", "COLOR_DODGE": "color-dodge",
             "COLOR_BURN": "color-burn", "HARD_LIGHT": "hard-light", "SOFT_LIGHT": "soft-light",
             "DIFFERENCE": "difference", "EXCLUSION": "exclusion", "HUE": "hue", "SATURATION": "saturation",
             "COLOR": "color", "LUMINOSITY": "luminosity", "LINEAR_DODGE": "plus-lighter",
             "LINEAR_LIGHT": "hard-light", "VIVID_LIGHT": "hard-light", "PIN_LIGHT": "hard-light",
             "LINEAR_BURN": "multiply", "DARKER_COLOR": "darken", "LIGHTER_COLOR": "lighten",
             "HARD_MIX": "hard-light", "SUBTRACT": "difference", "DIVIDE": "color-dodge", "DISSOLVE": "normal"}


def slug(s, n=28):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower()).strip("-")
    return (s or "camada")[:n]


def recortar(img):
    """Recorta pelo alfa. Devolve (img_recortada, (x, y)) ou (None, None) se vazia."""
    a = np.array(img.getchannel("A"))
    ys, xs = np.where(a > 3)
    if not len(xs):
        return None, None
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    return img.crop((x0, y0, x1, y1)), (int(x0), int(y0))


def salvar_unidade(pasta, idx, nome, img_full, extra):
    img, pos = recortar(img_full)
    if img is None:
        return None
    arq = f"camadas/{idx:02d}-{slug(nome)}.png"
    img.save(pasta / arq, optimize=True)
    u = {"id": f"u{idx:02d}", "nome": nome, "png": arq, "x": pos[0], "y": pos[1], "w": img.width, "h": img.height}
    a = np.array(img.getchannel("A"))
    u["cobertura"] = round(float((a > 20).mean()), 3)  # quanto da própria caixa é opaco
    u.update(extra)
    return u


# ---------------------------------------------------------------- PSD

AJUSTES = ("brightnesscontrast", "levels", "curves", "exposure", "vibrance", "huesaturation", "colorbalance",
           "blackandwhite", "photofilter", "channelmixer", "colorlookup", "invert", "posterize", "threshold",
           "selectivecolor", "gradientmap")


def _so_ajuste(b):
    folhas = [x for c in b["camadas"] for x in ([c] if not c.is_group() else [d for d in c.descendants() if not d.is_group()])]
    return bool(folhas) and all(x.kind in AJUSTES for x in folhas)


def _ids_bloco(b):
    s = set()
    for c in b["camadas"]:
        for x in [c, *_ancestrais(c), *(c.descendants() if c.is_group() else [])]:
            if x.kind != "psdimage":
                s.add(x)
    return s


def _ancestrais(l):
    out = []
    p = l.parent
    while p is not None and p.kind != "psdimage":
        out.append(p)
        p = p.parent
    return out


def _unidades_psd(raiz):
    """Decide os blocos animáveis: filhos diretos da prancheta/raiz; grupo vira um bloco só, exceto quando é um grupo
    'comum' (não fundo/textura) com até 12 filhos, que é aberto um nível. Camadas com máscara de corte (clip) vão junto
    com a base; ajuste sem clip vai junto com a camada de baixo."""
    blocos = []

    def abrir(container, profundidade):
        filhos = [c for c in container if c.is_visible()]
        for c in filhos:
            nome = c.name or c.kind
            ajuste = c.kind in ("brightnesscontrast", "levels", "curves", "exposure", "vibrance", "huesaturation",
                                "colorbalance", "blackandwhite", "photofilter", "channelmixer", "colorlookup",
                                "invert", "posterize", "threshold", "selectivecolor", "gradientmap",
                                "solidcolorfill", "gradientfill", "patternfill")
            if c.clipping or (ajuste and blocos and c.kind not in ("solidcolorfill", "gradientfill", "patternfill")):
                if blocos:
                    blocos[-1]["camadas"].append(c)
                    continue
            if (c.kind == "group" and profundidade < 2 and len(list(c)) <= 12
                    and not re.search(NOMES["fundo"] + "|" + NOMES["textura"], nome.lower())):
                abrir(c, profundidade + 1)
                continue
            blocos.append({"nome": nome, "camadas": [c], "raiz": c})

    abrir(raiz, 0)
    return blocos


def _info_texto(l):
    try:
        txt = l.text.replace("\r", "\n").strip()
    except Exception:
        return None
    info = {"conteudo": txt}
    try:
        fs = l.resource_dict["FontSet"]
        runs = l.engine_dict["StyleRun"]["RunArray"]
        st = runs[0]["StyleSheet"]["StyleSheetData"]
        info["fonte"] = str(fs[st.get("Font", 0)]["Name"]).strip("'\"")
        tam = float(st.get("FontSize", 0))
        try:  # tamanho real = FontSize * escala vertical da transformação
            tam *= float(l.transform[3])
        except Exception:
            pass
        info["tamanho"] = round(tam, 1)
        cor = st.get("FillColor", {}).get("Values")
        if cor:
            info["cor"] = "#%02x%02x%02x" % tuple(int(float(v) * 255) for v in list(cor)[1:4])
    except Exception:
        pass
    return info


def ler_psd(arq, pasta, prancheta=None, motor="auto"):
    from psd_tools import PSDImage
    psd = PSDImage.open(arq)
    pranchetas = [l for l in psd if l.kind == "artboard" and l.is_visible()]
    raiz, caixa = psd, (0, 0, psd.width, psd.height)
    if pranchetas:
        if prancheta is None:
            ab = pranchetas[0]
        elif str(prancheta).isdigit():
            ab = pranchetas[int(prancheta) - 1]
        else:
            ab = next(a for a in pranchetas if a.name.lower() == str(prancheta).lower())
        raiz, caixa = ab, ab.bbox
        if len(pranchetas) > 1:
            print(f"PSD com {len(pranchetas)} pranchetas: usando '{ab.name}' (--prancheta para outra): "
                  + ", ".join(a.name for a in pranchetas))
    W, H = caixa[2] - caixa[0], caixa[3] - caixa[1]
    blocos = _unidades_psd(raiz)
    # ajuste global (grade de cor sem clip): não vira bloco; entra em cada bloco que está ABAIXO dele, para a cor
    # de cada camada já sair igual à da arte final
    for j in [j for j, b in enumerate(blocos) if _so_ajuste(b)][::-1]:
        for i in range(j):
            blocos[i].setdefault("extra", set()).update(_ids_bloco(blocos[j]))
        print(f"grade global aplicada nos blocos de baixo: {blocos[j]['nome']}")
        blocos.pop(j)

    tem_efeito = any(l.has_effects() for b in blocos for c in b["camadas"] for l in [c, *list(c.descendants())] if hasattr(l, "has_effects"))
    if motor == "auto":
        motor = "photoshop" if (tem_efeito and sys.platform == "darwin" and _tem_photoshop()) else "psdtools"
    print(f"{len(blocos)} blocos animáveis; motor de pixels: {motor}" + (" (há estilos de camada)" if tem_efeito else ""))

    (pasta / "camadas").mkdir(parents=True, exist_ok=True)
    imgs = _pixels_photoshop(arq, blocos, caixa) if motor == "photoshop" else None
    unidades = []
    for i, b in enumerate(blocos):
        keep = set()
        for c in b["camadas"]:
            keep.add(id(c)); keep.update(id(x) for x in _ancestrais(c))
            if c.is_group():
                keep.update(id(x) for x in c.descendants())
        keep.update(id(x) for x in b.get("extra", ()))
        if imgs is not None:
            full = imgs[i]
        else:
            full = psd.composite(viewport=caixa, layer_filter=lambda l: id(l) in keep and l.is_visible(),
                                 force=False)
        if full is None:
            continue
        full = full.convert("RGBA")
        r = b["raiz"]
        modo = str(r.blend_mode).split(".")[-1]
        if r.is_group() and modo == "PASS_THROUGH":
            # grupo "atravessar": vale o modo das camadas de dentro (ex.: textura em Tela dentro do grupo)
            modos = [str(x.blend_mode).split(".")[-1] for x in r if x.is_visible() and not x.clipping and x.kind not in AJUSTES]
            fora = [m for m in modos if m not in ("NORMAL", "PASS_THROUGH")]
            if fora and len(fora) >= len(modos) / 2:
                modo = max(set(fora), key=fora.count)
        extra = {"tipo": r.kind, "blend": BLEND_CSS.get(modo, "normal"),
                 "opacidade": round(r.opacity / 255, 3) if r.opacity is not None else 1}
        if extra["blend"] != "normal":
            extra["opacidade"] = 1  # o composite já aplicou a opacidade; blend fica para o CSS
        if r.kind == "type":
            t = _info_texto(r)
            if t:
                extra["texto"] = t
        if extra["blend"] != "normal":
            # composite isolado escurece/clareia diferente; refaz só a camada, sem blend, para o CSS misturar
            pass
        u = salvar_unidade(pasta, i, b["nome"], full, extra)
        if u:
            unidades.append(u)
    if imgs is None:
        tudo = {id(x) for x in raiz.descendants()} | {id(raiz)}
        final = psd.composite(viewport=caixa, layer_filter=lambda l: id(l) in tudo and l.is_visible())
    else:
        final = imgs[-1]
    final.convert("RGBA").save(pasta / "camadas/_final.png", optimize=True)
    return W, H, unidades


def _tem_photoshop():
    r = subprocess.run(["osascript", "-e", 'id of application id "com.adobe.Photoshop"'], capture_output=True, text=True)
    return r.returncode == 0


def _ps_arquivo(caminho, timeout=1800):
    """Roda um .jsx no Photoshop (usa a ponte da /oyoshi se existir; senão, a mesma chamada por AppleScript)."""
    if (OYOSHI / "ps_lib.py").exists():
        sys.path.insert(0, str(OYOSHI))
        import ps_lib
        return ps_lib.arquivo(caminho, timeout=timeout)
    c = os.path.abspath(caminho).replace("'", "\\'")
    r = subprocess.run(["osascript", "-e", f"with timeout of {timeout} seconds",
                        "-e", f"tell application id \"com.adobe.Photoshop\" to do javascript \"$.evalFile('{c}')\"",
                        "-e", "end timeout"], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr)
    return r.stdout.strip()


JSX_PIXELS = r"""
app.displayDialogs = DialogModes.NO;
app.preferences.rulerUnits = Units.PIXELS;
var ARQ = %(arq)s, SAIDA = %(saida)s, BLOCOS = %(blocos)s, REF = %(ref)s;
var src = null, jaAberto = false;
for (var i = 0; i < app.documents.length; i++) { try { if (app.documents[i].fullName.fsName == new File(ARQ).fsName) { src = app.documents[i]; jaAberto = true; } } catch (e) {} }
if (!src) src = app.open(new File(ARQ));
app.activeDocument = src;
var doc = src.duplicate("arte_animada_tmp", false);
if (!jaAberto) src.close(SaveOptions.DONOTSAVECHANGES);  // arquivo que o usuário já tinha aberto fica como estava
app.activeDocument = doc;
function vis(id, v){var d=new ActionDescriptor(),l=new ActionList(),r=new ActionReference();
  r.putIdentifier(charIDToTypeID("Lyr "),id);l.putReference(r);d.putList(charIDToTypeID("null"),l);
  try{executeAction(charIDToTypeID(v?"Shw ":"Hd  "),d,DialogModes.NO);}catch(e){}}
var n=(function(){var r=new ActionReference();r.putEnumerated(charIDToTypeID("Dcmn"),charIDToTypeID("Ordn"),charIDToTypeID("Trgt"));
  return executeActionGet(r).getInteger(charIDToTypeID("NmbL"));})();
var ids=[], orig={};
var base=0; try{doc.backgroundLayer; base=0;}catch(e){base=1;}
for(var i=1-base+base;i<=n;i++){try{var r=new ActionReference();r.putIndex(charIDToTypeID("Lyr "),i);
  var d=executeActionGet(r);var id=d.getInteger(stringIDToTypeID("layerID"));ids.push(id);
  orig[id]=d.getBoolean(charIDToTypeID("Vsbl"));}catch(e){}}
// pranchetas viram camadas comuns na cópia (senão o PNG sai só da prancheta e com fundo opaco)
for(var k=0;k<ids.length;k++){try{var r=new ActionReference();r.putIdentifier(charIDToTypeID("Lyr "),ids[k]);
  var d=executeActionGet(r);if(d.hasKey(stringIDToTypeID("artboardEnabled"))&&d.getBoolean(stringIDToTypeID("artboardEnabled"))){
    var s=new ActionDescriptor();var rr=new ActionReference();rr.putIdentifier(charIDToTypeID("Lyr "),ids[k]);s.putReference(charIDToTypeID("null"),rr);
    executeAction(charIDToTypeID("slct"),s,DialogModes.NO);
    var u=new ActionDescriptor();var ur=new ActionReference();ur.putEnumerated(charIDToTypeID("Lyr "),charIDToTypeID("Ordn"),charIDToTypeID("Trgt"));
    u.putReference(charIDToTypeID("null"),ur);executeAction(stringIDToTypeID("ungroupLayersEvent"),u,DialogModes.NO);}}catch(e){}}
// desfazer prancheta aumenta a tela: mede onde a camada de referência foi parar (o Python ajusta o recorte)
var off="0 0";try{var r=new ActionReference();r.putIdentifier(charIDToTypeID("Lyr "),REF);var bd=executeActionGet(r).getObjectValue(stringIDToTypeID("boundsNoEffects"));
  off=bd.getUnitDoubleValue(charIDToTypeID("Left"))+" "+bd.getUnitDoubleValue(charIDToTypeID("Top "));}catch(e){}
var opt=new PNGSaveOptions(); var estado={};
for(var k=0;k<ids.length;k++) estado[ids[k]]=orig[ids[k]];
function aplicar(mostrar){var m={};for(var j=0;j<mostrar.length;j++)m[mostrar[j]]=1;
  for(var k=0;k<ids.length;k++){var id=ids[k];var quer=(m[id]===1)&&orig[id];if(estado[id]!==quer){vis(id,quer);estado[id]=quer;}}}
for(var b=0;b<BLOCOS.length;b++){aplicar(BLOCOS[b]);
  doc.saveAs(new File(SAIDA+"/b"+(b<10?"0":"")+b+".png"),opt,true,Extension.LOWERCASE);}
var todos=[];for(var k=0;k<ids.length;k++)todos.push(ids[k]);aplicar(todos);
doc.saveAs(new File(SAIDA+"/final.png"),opt,true,Extension.LOWERCASE);
doc.close(SaveOptions.DONOTSAVECHANGES);
"ok " + ids.length + " " + off;
"""


def _pixels_photoshop(arq, blocos, caixa):
    """Exporta cada bloco pelo Photoshop (estilos de camada, smart objects e ajustes fiéis), numa cópia do PSD."""
    tmp = Path(tempfile.mkdtemp(prefix="arte_ps_"))
    lista = []
    for b in blocos:
        lista.append(sorted({int(x.layer_id) for x in _ids_bloco(b) | set(b.get("extra", ()))}))
    ref = next((l for b in blocos for c in b["camadas"] for l in [c, *(c.descendants() if c.is_group() else [])]
                if l.kind in ("pixel", "shape", "smartobject", "type") and l.width > 0 and l.height > 0), None)
    jsx = tmp / "pixels.jsx"
    jsx.write_text(JSX_PIXELS % {"arq": json.dumps(str(Path(arq).resolve())), "saida": json.dumps(str(tmp)),
                                 "blocos": json.dumps(lista), "ref": int(ref.layer_id) if ref else -1}, encoding="utf-8")
    print("Photoshop exportando os blocos (cópia do arquivo; o original não é tocado)...")
    res = _ps_arquivo(str(jsx)).split()
    dx = dy = 0
    if ref is not None and len(res) >= 4:
        dx, dy = round(float(res[2])) - ref.left, round(float(res[3])) - ref.top
    x0, y0, x1, y1 = caixa[0] + dx, caixa[1] + dy, caixa[2] + dx, caixa[3] + dy
    out = [Image.open(tmp / f"b{i:02d}.png").convert("RGBA").crop((x0, y0, x1, y1)) for i in range(len(blocos))]
    out.append(Image.open(tmp / "final.png").convert("RGBA").crop((x0, y0, x1, y1)))
    if not os.environ.get("ARTE_DEBUG"):
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        print("debug:", tmp)
    return out


# ---------------------------------------------------------------- PDF (Canva, Illustrator, InDesign)

def _render_sem(doc_bytes, pagina, zoom, tirar_texto, tirar_imagens, tirar_formas):
    import fitz
    d = fitz.open("pdf", doc_bytes)
    p = d[pagina]
    p.add_redact_annot(p.rect)
    p.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE if tirar_imagens else fitz.PDF_REDACT_IMAGE_NONE,
                       graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED if tirar_formas else fitz.PDF_REDACT_LINE_ART_NONE,
                       text=fitz.PDF_REDACT_TEXT_REMOVE if tirar_texto else fitz.PDF_REDACT_TEXT_NONE)
    pix = p.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
    return Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)


def _componentes(img, dil, min_area):
    """Separa uma camada em pedaços (cada pedaço = um elemento) pelo alfa, juntando o que está a até `dil` px."""
    import cv2
    a = (np.array(img.getchannel("A")) > 8).astype(np.uint8)
    if dil:
        a2 = cv2.dilate(a, np.ones((dil, dil), np.uint8))
    else:
        a2 = a
    n, lab, st, _ = cv2.connectedComponentsWithStats(a2, 8)
    out = []
    for k in range(1, n):
        x, y, w, h, area = st[k]
        if area < min_area:
            continue
        m = (lab == k) & (a > 0)
        arr = np.array(img).copy()
        arr[..., 3] = np.where(m, arr[..., 3], 0)
        out.append((Image.fromarray(arr), (x, y, w, h)))
    return out


def _desenhar(paths, rect, zoom):
    """Redesenha só estes vetores numa página vazia e devolve a imagem com transparência."""
    import fitz
    d = fitz.open()
    pg = d.new_page(width=rect.width, height=rect.height)
    for pa in paths:
        sh = pg.new_shape()
        for it in pa["items"]:
            if it[0] == "l":
                sh.draw_line(it[1], it[2])
            elif it[0] == "re":
                sh.draw_rect(it[1])
            elif it[0] == "qu":
                sh.draw_quad(it[1])
            elif it[0] == "c":
                sh.draw_bezier(it[1], it[2], it[3], it[4])
        sh.finish(fill=pa.get("fill"), color=pa.get("color"), width=pa.get("width") or 1,
                  even_odd=pa.get("even_odd") or False, closePath=pa.get("closePath") or False,
                  fill_opacity=pa.get("fill_opacity") if pa.get("fill_opacity") is not None else 1,
                  stroke_opacity=pa.get("stroke_opacity") if pa.get("stroke_opacity") is not None else 1,
                  lineCap=max(pa.get("lineCap") or (0,)) if isinstance(pa.get("lineCap"), (tuple, list)) else (pa.get("lineCap") or 0),
                  lineJoin=pa.get("lineJoin") or 0, dashes=pa.get("dashes") or None)
        sh.commit()
    pix = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
    return Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)


def _agrupar_vetores(paths, folga):
    """Junta só vetores que são o MESMO elemento (preenchimento + contorno da mesma pílula, partes coladas de um
    ícone): caixas quase iguais ou uma pequena encostada noutra de tamanho parecido. Formas diferentes que só se
    sobrepõem (pílula em cima de um círculo de luz) ficam separadas."""
    def area(c):
        return max(c[2] - c[0], 0) * max(c[3] - c[1], 0)

    def mesmo(c, r):
        ix = max(0, min(c[2], r[2]) - max(c[0], r[0])); iy = max(0, min(c[3], r[3]) - max(c[1], r[1]))
        inter = ix * iy
        uni = area(c) + area(r) - inter
        if uni <= 0:
            return False
        if inter / uni > .6:
            return True
        pequeno, grande = sorted([area(c), area(r)])
        perto = not (r[2] + folga < c[0] or r[0] - folga > c[2] or r[3] + folga < c[1] or r[1] - folga > c[3])
        return perto and grande > 0 and pequeno / grande > .25 and grande < 40000  # pedaços de um ícone pequeno

    grupos = []
    for pa in sorted(paths, key=lambda x: x.get("seqno", 0)):
        r = [pa["rect"].x0, pa["rect"].y0, pa["rect"].x1, pa["rect"].y1]
        alvo = next((g for g in grupos if mesmo(g["caixa"], r)), None)
        if alvo is None:
            grupos.append({"paths": [pa], "caixa": r, "seq": pa.get("seqno", 0)})
        else:
            alvo["paths"].append(pa)
            c = alvo["caixa"]
            alvo["caixa"] = [min(c[0], r[0]), min(c[1], r[1]), max(c[2], r[2]), max(c[3], r[3])]
    return grupos


def ler_pdf(arq, pasta, pagina=0, largura=1080):
    import fitz
    dados = Path(arq).read_bytes()
    d = fitz.open("pdf", dados)
    pg = d[pagina]
    zoom = largura / pg.rect.width
    W, H = round(pg.rect.width * zoom), round(pg.rect.height * zoom)
    (pasta / "camadas").mkdir(parents=True, exist_ok=True)
    if not pg.get_text("text").strip():
        print("AVISO: o PDF não tem texto (foi exportado 'achatado' ou com texto em contorno). No Canva: Compartilhar > "
              "Baixar > PDF Impressão, SEM marcar 'Achatar PDF'. Seguindo com o que tem.")
    so_imagens = _render_sem(dados, pagina, zoom, True, False, True)
    so_texto = _render_sem(dados, pagina, zoom, False, True, True)
    full = pg.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=True)
    Image.frombytes("RGBA", (full.width, full.height), full.samples).save(pasta / "camadas/_final.png", optimize=True)

    unidades, idx = [], 0
    area_pg = pg.rect.width * pg.rect.height
    vet = pg.get_drawings()
    grandes = [v for v in vet if v["rect"].width * v["rect"].height > area_pg * .5]
    pequenos = [v for v in vet if v not in grandes]
    print(f"PDF: {len(vet)} vetores ({len(grandes)} de fundo), texto em {len(pg.get_text('dict')['blocks'])} blocos")
    if grandes:
        u = salvar_unidade(pasta, idx, "fundo", _desenhar(grandes, pg.rect, zoom),
                           {"tipo": "shape", "blend": "normal", "opacidade": 1, "papel": "fundo"})
        if u:
            unidades.append(u); idx += 1
    for img, (x, y, w, h) in sorted(_componentes(so_imagens, 0, 400), key=lambda c: -c[1][2] * c[1][3]):
        u = salvar_unidade(pasta, idx, f"imagem{idx}", img, {"tipo": "smartobject", "blend": "normal", "opacidade": 1})
        if u:
            unidades.append(u); idx += 1
    for g in _agrupar_vetores(pequenos, 2):
        u = salvar_unidade(pasta, idx, f"forma{idx}", _desenhar(g["paths"], pg.rect, zoom),
                           {"tipo": "shape", "blend": "normal", "opacidade": 1})
        if u:
            unidades.append(u); idx += 1
    # texto: um bloco por linha (o PDF diz onde cada linha está), pixels do render só-texto
    for bloco in pg.get_text("dict")["blocks"]:
        for linha in bloco.get("lines", []):
            spans = [s for s in linha["spans"] if s["text"].strip()]
            if not spans:
                continue
            x0, y0, x1, y1 = (v * zoom for v in linha["bbox"])
            pad = 6
            caixa = (max(0, int(x0) - pad), max(0, int(y0) - pad), min(W, int(x1) + pad), min(H, int(y1) + pad))
            m = Image.new("RGBA", so_texto.size, (0, 0, 0, 0))
            m.paste(so_texto.crop(caixa), caixa[:2])
            s0 = max(spans, key=lambda s: s["size"])
            txt = "".join(s["text"] for s in spans).strip()
            info = {"conteudo": txt, "fonte": s0["font"], "tamanho": round(s0["size"] * zoom, 1),
                    "cor": "#%06x" % s0["color"]}
            u = salvar_unidade(pasta, idx, txt[:24], m, {"tipo": "type", "blend": "normal", "opacidade": 1, "texto": info})
            if u:
                unidades.append(u); idx += 1
    return W, H, unidades


# ---------------------------------------------------------------- imagem achatada (PNG/JPG)

SWIFT_SEG = r"""
import Vision
import CoreImage
let a = CommandLine.arguments
let h = VNImageRequestHandler(url: URL(fileURLWithPath: a[1]))
let q = VNGenerateForegroundInstanceMaskRequest()
try h.perform([q])
guard let r = q.results?.first else { print("0"); exit(0) }
let ctx = CIContext()
for i in r.allInstances {
  let b = try r.generateMaskedImage(ofInstances: IndexSet(integer: i), from: h, croppedToInstancesExtent: false)
  try ctx.writePNGRepresentation(of: CIImage(cvPixelBuffer: b), to: URL(fileURLWithPath: a[2] + "/p\(i).png"),
    format: .RGBA8, colorSpace: CGColorSpaceCreateDeviceRGB())
}
print(r.allInstances.count)
"""


def ler_imagem(arq, pasta, largura=1080):
    import cv2
    im = Image.open(arq).convert("RGBA")
    W = largura
    H = round(im.height * largura / im.width)
    im = im.resize((W, H), Image.LANCZOS)
    (pasta / "camadas").mkdir(parents=True, exist_ok=True)
    im.save(pasta / "camadas/_final.png")
    tmp = Path(tempfile.mkdtemp(prefix="arte_seg_"))
    im.save(tmp / "in.png")
    pessoas = []
    if sys.platform == "darwin":
        bin_ = Path.home() / ".cache/ogab/seg_vision"
        if not bin_.exists():
            bin_.parent.mkdir(parents=True, exist_ok=True)
            (tmp / "seg.swift").write_text(SWIFT_SEG)
            subprocess.run(["swiftc", "-O", str(tmp / "seg.swift"), "-o", str(bin_)], check=True, capture_output=True)
        subprocess.run([str(bin_), str(tmp / "in.png"), str(tmp)], check=True, capture_output=True)
        pessoas = sorted(tmp.glob("p*.png"))
    else:
        print("Recorte automático de pessoas só no Mac (Vision); no Windows o fundo vai inteiro.")
    arr = np.array(im)
    masc = np.zeros(arr.shape[:2], np.uint8)
    for p in pessoas:
        masc |= (np.array(Image.open(p).getchannel("A")) > 30).astype(np.uint8) * 255
    unidades = []
    if masc.any():
        m = cv2.dilate(masc, np.ones((15, 15), np.uint8))
        rgb = cv2.inpaint(np.ascontiguousarray(arr[..., :3]), m, 12, cv2.INPAINT_TELEA)
        rgb = cv2.GaussianBlur(rgb, (0, 0), 3) * (m[..., None] > 0) + rgb * (m[..., None] == 0)
        fundo = Image.fromarray(np.dstack([rgb.astype(np.uint8), arr[..., 3]]))
    else:
        fundo = im
    u = salvar_unidade(pasta, 0, "fundo", fundo, {"tipo": "pixel", "blend": "normal", "opacidade": 1, "papel": "fundo"})
    unidades.append(u)
    for i, p in enumerate(pessoas, 1):
        u = salvar_unidade(pasta, i, f"pessoa{i}", Image.open(p).convert("RGBA"),
                           {"tipo": "pixel", "blend": "normal", "opacidade": 1, "papel": "pessoa"})
        if u:
            unidades.append(u)
    shutil.rmtree(tmp, ignore_errors=True)
    print("Imagem achatada: os TEXTOS continuam colados no fundo. Para animar o texto, refazer cada texto em HTML "
          "por cima (fonte parecida, mesma posição) e apagar do fundo; ver docs/etapas/arte_animada.md, 'Só imagem'.")
    return W, H, unidades


# ---------------------------------------------------------------- papéis e plano

def classificar(W, H, unidades):
    area_tela = W * H
    textos = [u for u in unidades if u.get("texto") or u.get("tipo") == "type"]
    maior_txt = max(textos, key=lambda u: (u.get("texto", {}).get("tamanho") or 0, u["h"]), default=None)
    for u in unidades:
        if u.get("papel"):
            continue
        n = u["nome"].lower()
        frac = u["w"] * u["h"] / area_tela
        if re.search(NOMES["logo"], n):
            p = "logo"
        elif u.get("tipo") == "type" or u.get("texto"):
            p = "titulo" if u is maior_txt else "texto"
        elif re.search(NOMES["fundo"], n) or (frac > .75 and u["cobertura"] > .9):
            p = "fundo"
        elif u["blend"] not in ("normal",) and frac > .3 or re.search(NOMES["textura"], n):
            p = "textura"
        elif re.search(NOMES["pessoa"], n) or (u.get("tipo") in ("smartobject", "pixel") and u["h"] > H * .22
                                                and u["cobertura"] < .85):
            p = "pessoa"
        elif min(u["w"], u["h"]) <= max(6, W * .008):
            p = "linha"
        elif u.get("tipo") == "shape" and u["w"] / max(u["h"], 1) > 2.6:
            p = "pilula"
        elif frac < .012:
            p = "icone"
        elif frac > .5:
            p = "fundo"
        else:
            p = "forma"
        u["papel"] = p
    # títulos: textos com tamanho perto do maior também ganham destaque
    if maior_txt and maior_txt.get("texto", {}).get("tamanho"):
        tmax = maior_txt["texto"]["tamanho"]
        for u in textos:
            if u.get("papel") == "texto" and (u.get("texto", {}).get("tamanho") or 0) >= tmax * .7:
                u["papel"] = "titulo"
    return unidades


ANIM_PAPEL = {"fundo": "zoom_fundo", "textura": "fade", "pessoa": "sobe_blur", "titulo": "slam", "texto": "sobe_blur_curto",
              "pilula": "abre_x", "linha": "risca", "icone": "pop", "logo": "gira_pop", "forma": "pop_suave"}


def planejar(unidades, dur):
    """Tempo de entrada de cada bloco: fundo e texturas no 0; pessoas primeiro; o resto de cima para baixo.
    Toda a entrada termina em ~55% da duração; o resto é respiro com movimento."""
    fim_entrada = dur * .55
    fixos = [u for u in unidades if u["papel"] in ("fundo", "textura")]
    pessoas = sorted([u for u in unidades if u["papel"] == "pessoa"], key=lambda u: (u["y"], u["x"]))
    resto = sorted([u for u in unidades if u["papel"] not in ("fundo", "textura", "pessoa")],
                   key=lambda u: (round(u["y"] / 40), u["x"]))
    for i, u in enumerate(fixos):
        u.setdefault("t", round(.0 + i * .08, 2))
    t = .35
    for i, u in enumerate(pessoas):
        u.setdefault("t", round(t + i * .18, 2))
    t0 = .35 + (len(pessoas) * .18 + .5 if pessoas else 0)
    passo = max(.07, min(.28, (fim_entrada - t0 - .6) / max(len(resto), 1)))
    for i, u in enumerate(resto):
        u.setdefault("t", round(t0 + i * passo, 2))
    for u in unidades:
        u.setdefault("anim", ANIM_PAPEL.get(u["papel"], "fade"))
    return unidades


# ---------------------------------------------------------------- HyperFrames

ANIM_JS = r"""
const A = {
  zoom_fundo: (el, t) => { tl.fromTo(el, {opacity: 0, scale: 1.12}, {opacity: 1, scale: 1, duration: 1.6, ease: "power2.out"}, t); },
  fade: (el, t) => { tl.fromTo(el, {opacity: 0}, {opacity: 1, duration: 1, ease: "power1.out"}, t); },
  sobe_blur: (el, t) => { tl.fromTo(el, {opacity: 0, y: 90*S, scale: 1.05, filter: "blur(14px)"}, {opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 1.1, ease: "power3.out"}, t); },
  sobe_blur_curto: (el, t) => { tl.fromTo(el, {opacity: 0, y: 26*S, filter: "blur(8px)"}, {opacity: 1, y: 0, filter: "blur(0px)", duration: .6, ease: "power3.out"}, t); },
  desce_blur: (el, t) => { tl.fromTo(el, {opacity: 0, y: -40*S, filter: "blur(8px)"}, {opacity: 1, y: 0, filter: "blur(0px)", duration: .6, ease: "power3.out"}, t); },
  esquerda: (el, t) => { tl.fromTo(el, {opacity: 0, x: -160*S}, {opacity: 1, x: 0, duration: .7, ease: "power3.out"}, t); },
  direita: (el, t) => { tl.fromTo(el, {opacity: 0, x: 160*S}, {opacity: 1, x: 0, duration: .7, ease: "power3.out"}, t); },
  slam: (el, t) => { tl.fromTo(el, {opacity: 0, scale: 1.7, filter: "blur(10px)"}, {opacity: 1, scale: 1, filter: "blur(0px)", duration: .5, ease: "power4.out"}, t);
                     tl.fromTo("#palco", {x: 0, y: 0}, {keyframes: [{x: 5*S, y: -4*S, duration: .04}, {x: -4*S, y: 3*S, duration: .04}, {x: 0, y: 0, duration: .05}]}, t + .45); },
  wipe: (el, t) => { tl.fromTo(el, {clipPath: "inset(0% 100% 0% 0%)"}, {clipPath: "inset(0% 0% 0% 0%)", duration: .8, ease: "power2.inOut"}, t);
                     tl.fromTo(el, {x: -20*S}, {x: 0, duration: .8, ease: "power3.out"}, t); },
  revela_baixo: (el, t) => { tl.fromTo(el, {clipPath: "inset(100% 0% 0% 0%)", y: 20*S}, {clipPath: "inset(0% 0% 0% 0%)", y: 0, duration: .7, ease: "power3.out"}, t); },
  abre_x: (el, t) => { tl.fromTo(el, {opacity: 0, scaleX: 0}, {opacity: 1, scaleX: 1, duration: .6, ease: "power3.out"}, t); },
  risca: (el, t) => { tl.fromTo(el, {clipPath: "inset(0% 100% 0% 0%)"}, {clipPath: "inset(0% 0% 0% 0%)", duration: .7, ease: "power3.out"}, t); },
  pop: (el, t) => { tl.fromTo(el, {opacity: 0, scale: 0, rotation: -25}, {opacity: 1, scale: 1, rotation: 0, duration: .55, ease: "back.out(2)"}, t); },
  pop_suave: (el, t) => { tl.fromTo(el, {opacity: 0, scale: .85, filter: "blur(6px)"}, {opacity: 1, scale: 1, filter: "blur(0px)", duration: .7, ease: "power3.out"}, t); },
  gira_pop: (el, t) => { tl.fromTo(el, {opacity: 0, scale: .3, rotation: -120}, {opacity: 1, scale: 1, rotation: 0, duration: .8, ease: "back.out(1.6)"}, t); },
};
"""

HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=%(W)d, height=%(H)d">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  body{margin:0;background:#000}
  #root{position:relative;width:%(W)dpx;height:%(H)dpx;overflow:hidden;background:%(bg)s}
  #push,#palco{position:absolute;inset:0;transform-origin:50%% 50%%}
  .u{position:absolute;transform-origin:50%% 50%%}
  .u img{display:block;width:100%%;height:100%%}
  .brilho{position:absolute;inset:0;pointer-events:none;mix-blend-mode:overlay;
    background:linear-gradient(105deg,rgba(255,255,255,0) 40%%,rgba(255,255,255,.95) 50%%,rgba(255,255,255,0) 60%%);
    background-size:300%% 100%%;background-repeat:no-repeat;background-position:130%% 0}
  #final{position:absolute;inset:0;width:100%%;height:100%%;opacity:0}
  #particulas i{position:absolute;border-radius:50%%;background:%(pcor)s;box-shadow:0 0 8px 2px %(pcor)s}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="%(W)d" data-height="%(H)d" data-duration="%(dur)s">
 <div id="push"><div id="palco">
%(camadas)s
  <img id="final" src="camadas/_final.png">
%(brilhos)s
  <div id="particulas"></div>
 </div></div>
</div>
<script>
(function(){
  const T = %(dur)s, S = %(S)s, FIM = %(fim)s, FINAL_EXATO = %(final_exato)s, PART = %(part)s;
  let seed = 11; const rnd = () => (seed = (seed * 16807) %% 2147483647) / 2147483647;
  const tl = gsap.timeline({paused: true});
  %(anim_js)s
  const U = %(plano)s;
  U.forEach(u => { const el = document.getElementById(u.id); (A[u.anim] || A.fade)(el, u.t); });
  // respiro: câmera e parallax depois da entrada
  tl.fromTo("#push", {scale: 1.05}, {scale: 1, duration: FIM, ease: "power2.out"}, 0);
  tl.to("#push", {scale: 1.03, duration: T - FIM, ease: "none"}, FIM);
  U.filter(u => u.papel === "pessoa").forEach((u, i) => tl.to("#" + u.id, {y: (i %% 2 ? -8 : -14) * S, duration: T - FIM, ease: "sine.inOut"}, FIM));
  U.filter(u => u.papel === "fundo" || u.papel === "textura").forEach(u => tl.to("#" + u.id, {scale: 1.04, duration: T - 1.6, ease: "none"}, 1.6));
  // brilho passando nos títulos (mascarado pelo próprio PNG)
  document.querySelectorAll(".brilho").forEach((b, i) => {
    tl.fromTo(b, {backgroundPosition: "130%% 0"}, {backgroundPosition: "-30%% 0", duration: 1.1, ease: "power2.inOut", immediateRender: false}, FIM + .2 + i * .15);
    tl.fromTo(b, {backgroundPosition: "130%% 0"}, {backgroundPosition: "-30%% 0", duration: 1.2, ease: "power2.inOut", immediateRender: false}, T - 2.2 + i * .15);
  });
  // ícones e pílulas: pulso leve no respiro
  U.filter(u => u.papel === "icone").forEach((u, i) => tl.to("#" + u.id, {scale: 1.12, duration: .5, ease: "sine.inOut", repeat: 3, yoyo: true}, FIM + .5 + i * .2));
  // trava final: a arte exata por cima, sem o leitor perceber (corrige qualquer diferença de blend/efeito)
  if (FINAL_EXATO) tl.fromTo("#final", {opacity: 0}, {opacity: 1, duration: .9, ease: "sine.inOut"}, FIM - .2);
  if (PART) { const box = document.getElementById("particulas");
    for (let i = 0; i < 34; i++) { const e = document.createElement("i"); const sz = (2 + rnd() * 4) * S;
      e.style.width = e.style.height = sz + "px"; e.style.left = rnd() * %(W)d + "px"; e.style.top = (%(H)d * .45 + rnd() * %(H)d * .6) + "px";
      box.appendChild(e); const st = rnd() * 3, du = 4 + rnd() * 4;
      tl.fromTo(e, {y: 0, x: 0, opacity: 0}, {y: -(300 + rnd() * 500) * S, x: (rnd() - .5) * 120 * S, duration: du, ease: "none"}, st);
      tl.to(e, {opacity: .3 + rnd() * .7, duration: .6, ease: "none"}, st);
      tl.to(e, {opacity: 0, duration: 1, ease: "none"}, st + du - 1); } }
  tl.set({}, {}, T);
  window.__timelines = window.__timelines || {};
  window.__timelines["main"] = tl;
})();
</script>
</body>
</html>
"""


def montar(pasta, dur=10.0, largura=1080, particulas=None, final_exato=True):
    meta = json.loads((pasta / "camadas.json").read_text())
    W0, H0, U = meta["largura"], meta["altura"], meta["camadas"]
    s = largura / W0
    W, H = largura, round(H0 * s / 2) * 2
    planejar(U, dur)
    linhas, brilhos = [], []
    for u in U:
        st = (f"left:{u['x'] * s:.1f}px;top:{u['y'] * s:.1f}px;width:{u['w'] * s:.1f}px;height:{u['h'] * s:.1f}px;"
              f"opacity:{u.get('opacidade', 1)};mix-blend-mode:{u.get('blend', 'normal')}")
        linhas.append(f'  <div class="u" id="{u["id"]}" data-papel="{u["papel"]}" style="{st}"><img src="{u["png"]}"></div>')
        if u["papel"] == "titulo":
            m = f"-webkit-mask:url({u['png']}) center/100% 100% no-repeat;mask:url({u['png']}) center/100% 100% no-repeat"
            brilhos.append(f'  <div class="brilho" style="left:{u["x"] * s:.1f}px;top:{u["y"] * s:.1f}px;width:{u["w"] * s:.1f}px;'
                           f'height:{u["h"] * s:.1f}px;inset:auto;{m}"></div>')
    fim = round(max([u["t"] for u in U] + [0]) + 1.0, 2)
    plano = [{"id": u["id"], "papel": u["papel"], "anim": u["anim"], "t": u["t"]} for u in U]
    html = HTML % {"W": W, "H": H, "dur": dur, "S": round(s, 4), "fim": fim, "bg": meta.get("cor_fundo", "#000"),
                   "final_exato": "true" if final_exato else "false", "part": "true" if particulas else "false",
                   "pcor": particulas or "#ffb070", "camadas": "\n".join(linhas), "brilhos": "\n".join(brilhos),
                   "anim_js": ANIM_JS, "plano": json.dumps(plano)}
    (pasta / "index.html").write_text(html, encoding="utf-8")
    if not (pasta / "hyperframes.json").exists():
        (pasta / "hyperframes.json").write_text(json.dumps({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}))
    meta["camadas"] = U
    (pasta / "camadas.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"index.html pronto: {W}x{H}, {dur}s, {len(U)} camadas, entrada termina em {fim}s"
          + (" + trava final na arte exata" if final_exato else ""))


def mostrar_plano(pasta):
    meta = json.loads((pasta / "camadas.json").read_text())
    planejar(meta["camadas"], meta.get("duracao", 10))
    print(f"Arte {meta['largura']}x{meta['altura']} ({meta['origem']}), {len(meta['camadas'])} camadas:")
    print(f"{'id':4} {'t':>5}  {'papel':8} {'anim':16} {'caixa':22} nome")
    for u in sorted(meta["camadas"], key=lambda u: u["t"]):
        cx = f"{u['x']},{u['y']} {u['w']}x{u['h']}"
        txt = (" | " + u["texto"]["conteudo"][:30].replace("\n", " ")) if u.get("texto") else ""
        print(f"{u['id']:4} {u['t']:5.2f}  {u['papel']:8} {u['anim']:16} {cx:22} {u['nome'][:30]}{txt}")


def cor_media_borda(png):
    im = np.array(Image.open(png).convert("RGB"))
    b = np.concatenate([im[0], im[-1], im[:, 0], im[:, -1]])
    return "#%02x%02x%02x" % tuple(int(v) for v in np.median(b, 0))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("ler"); a.add_argument("arte"); a.add_argument("pasta")
    a.add_argument("--prancheta"); a.add_argument("--pagina", type=int, default=1)
    a.add_argument("--motor", default="auto", choices=["auto", "psdtools", "photoshop"])
    a.add_argument("--largura", type=int, default=1080, help="largura de trabalho para PDF/imagem")
    b = sp.add_parser("plano"); b.add_argument("pasta")
    c = sp.add_parser("montar"); c.add_argument("pasta"); c.add_argument("--duracao", type=float, default=10)
    c.add_argument("--largura", type=int, default=1080); c.add_argument("--particulas")
    c.add_argument("--sem-final-exato", action="store_true")
    g = ap.parse_args()
    pasta = Path(g.pasta).expanduser().resolve()
    if g.cmd == "ler":
        arte = Path(g.arte).expanduser().resolve()
        pasta.mkdir(parents=True, exist_ok=True)
        if (pasta / "camadas").exists():
            shutil.rmtree(pasta / "camadas")
        ext = arte.suffix.lower()
        if ext in (".psd", ".psb"):
            W, H, U = ler_psd(arte, pasta, g.prancheta, g.motor); origem = "psd"
        elif ext == ".pdf":
            W, H, U = ler_pdf(arte, pasta, g.pagina - 1, g.largura); origem = "pdf"
        elif ext in (".png", ".jpg", ".jpeg", ".webp"):
            W, H, U = ler_imagem(arte, pasta, g.largura); origem = "imagem"
        else:
            sys.exit(f"formato não suportado: {ext} (PSD, PSB, PDF, PNG, JPG)")
        classificar(W, H, U)
        meta = {"origem": origem, "arquivo": str(arte), "largura": W, "altura": H,
                "cor_fundo": cor_media_borda(pasta / "camadas/_final.png"), "camadas": U}
        (pasta / "camadas.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        mostrar_plano(pasta)
    elif g.cmd == "plano":
        mostrar_plano(pasta)
    else:
        montar(pasta, g.duracao, g.largura, g.particulas, not g.sem_final_exato)


if __name__ == "__main__":
    main()
