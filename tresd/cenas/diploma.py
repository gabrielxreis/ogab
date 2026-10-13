"""Cena 3D: diploma com selo de ouro (exemplo de OBJETO 3D; testado com a Calverstone em 12/10/2026).

  python3 tresd/tresd.py cena tresd/cenas/diploma.py saida.mov --dur 4
P (params, opcionais): titulo, subtitulo, linha, fonte_titulo, fonte_texto, cor_papel, cor_texto, cor_fita, cor_ouro.
Roda dentro do Blender: recebe `base` (cena_base) e `P`. Objetos "GEO-..." entram no enquadramento e na luz.
"""
import math, os
import bpy

P = globals().get("P") or {}
FONTES = os.path.join(os.path.dirname(base.__file__), "..", "assets", "fontes")
f_tit = P.get("fonte_titulo") or os.path.join(FONTES, "Cardo", "Cardo-Bold.ttf")
f_txt = P.get("fonte_texto") or os.path.join(FONTES, "Cardo", "Cardo-Regular.ttf")

base.mundo("#3a3a40", 0.9)   # ambiente mais claro: o ouro reflete o ambiente
m_papel = base.material("MAT-papel", P.get("cor_papel", "#F3EFE4"), rugosidade=0.55)
m_texto = base.material("MAT-texto", P.get("cor_texto", "#0B1F3A"), rugosidade=0.6)
m_fita = base.material("MAT-fita", P.get("cor_fita", "#0D2547"), rugosidade=0.45)
m_ouro = base.ouro("MAT-ouro", P.get("cor_ouro", "#E8C25A"), 0.22)

# ---- papel (de pé no plano XZ, de frente para a câmera em -Y), com leve curvatura
W, H = 2.1, 1.5
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
papel = bpy.context.object; papel.name = "GEO-papel"; papel.scale = (W, H, 1)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.subdivide(number_cuts=24); bpy.ops.object.mode_set(mode="OBJECT")
sol = papel.modifiers.new("espessura", "SOLIDIFY"); sol.thickness = 0.006
dobra = papel.modifiers.new("curva", "SIMPLE_DEFORM"); dobra.deform_method = "BEND"; dobra.angle = math.radians(12); dobra.deform_axis = "Z"
papel.data.materials.append(m_papel)

# ---- moldura dourada (barras finas um pouco à frente do papel)
def barra(nome, x, z, sx, sz):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -0.012, z)); b = bpy.context.object
    b.name = nome; b.scale = (sx, 0.004, sz); b.data.materials.append(m_ouro); return b
m = 0.09
moldura = [barra("GEO-moldura-cima", 0, H / 2 - m, W - 2 * m, 0.012), barra("GEO-moldura-baixo", 0, -H / 2 + m, W - 2 * m, 0.012),
           barra("GEO-moldura-esq", -W / 2 + m, 0, 0.012, H - 2 * m), barra("GEO-moldura-dir", W / 2 - m, 0, 0.012, H - 2 * m)]

# ---- textos
def texto(nome, corpo, fonte, tam, z, mat, extr=0.003, espaco=1.0):
    bpy.ops.object.text_add(location=(0, -0.016, z), rotation=(math.radians(90), 0, 0)); t = bpy.context.object
    t.name = nome; t.data.body = corpo; t.data.font = bpy.data.fonts.load(fonte); t.data.size = tam
    t.data.align_x = t.data.align_y = "CENTER"; t.data.extrude = extr; t.data.space_character = espaco
    t.data.materials.append(mat); return t
textos = [texto("GEO-txt-sub", P.get("subtitulo", "BACHARELADO"), f_txt, 0.075, 0.42, m_texto, espaco=1.45),
          texto("GEO-txt-titulo", P.get("titulo", "DIPLOMA"), f_tit, 0.30, 0.18, m_texto, extr=0.006, espaco=1.15),
          texto("GEO-txt-linha", P.get("linha", "Bacharel em Enfermagem"), f_txt, 0.10, -0.12, m_texto)]
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.014, -0.30)); risco = bpy.context.object
risco.name = "GEO-risco"; risco.scale = (0.9, 0.002, 0.004); risco.data.materials.append(m_ouro)

# ---- fitas e selo de ouro (canto inferior direito)
sx, sz = 0.62, -0.48
for i, ang in enumerate((-18, 14)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(sx + 0.08 * (1 if i else -1), -0.03, sz - 0.25), rotation=(0, math.radians(ang), 0))
    f = bpy.context.object; f.name = f"GEO-fita-{i+1}"; f.scale = (0.09, 0.006, 0.36); f.data.materials.append(m_fita)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.24, depth=0.05, location=(sx, -0.05, sz), rotation=(math.radians(90), 0, 0))
selo = bpy.context.object; selo.name = "GEO-selo"; selo.data.materials.append(m_ouro)
bv = selo.modifiers.new("chanfro", "BEVEL"); bv.width = 0.012; bv.segments = 4
bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.012, location=(sx, -0.078, sz), rotation=(math.radians(90), 0, 0))
anel = bpy.context.object; anel.name = "GEO-selo-anel"; anel.data.materials.append(m_ouro)
bpy.ops.object.text_add(location=(sx, -0.08, sz), rotation=(math.radians(90), 0, 0)); ls = bpy.context.object
ls.name = "GEO-selo-letra"; ls.data.body = P.get("letra_selo", "C"); ls.data.font = bpy.data.fonts.load(f_tit); ls.data.size = 0.2
ls.data.align_x = ls.data.align_y = "CENTER"; ls.data.extrude = 0.008; ls.data.materials.append(m_ouro)

# ---- grupos para animar
bpy.ops.object.empty_add(location=(0, 0, 0)); diploma = bpy.context.object; diploma.name = "DIPLOMA"
for o in [papel, risco] + moldura + textos + [o for o in bpy.data.objects if o.name.startswith("GEO-fita")]:
    o.parent = diploma
bpy.ops.object.empty_add(location=(sx, -0.05, sz)); grupo_selo = bpy.context.object; grupo_selo.name = "SELO"
for o in (selo, anel, ls):
    o.parent = grupo_selo; o.location = o.location - grupo_selo.location
grupo_selo.parent = diploma

# ---- luz (perfil metal: realça o ouro sem lavar o papel) e câmera
base.tres_pontos("metal")
cam, centro, tam = base.camera(lente=50, altura=0.05, ocupar=0.86)

# ---- animação (4 s a 30 fps)
fim = bpy.context.scene.frame_end
base.chave(diploma, "rotation_euler", 1, (math.radians(-65), 0, math.radians(25)))
base.chave(diploma, "location", 1, (0, 0, -0.35))
base.chave(diploma, "rotation_euler", int(fim * 0.42), (math.radians(4), 0, math.radians(-6)))
base.chave(diploma, "location", int(fim * 0.42), (0, 0, 0.02))
base.chave(diploma, "rotation_euler", fim, (0, 0, math.radians(-3)))
base.chave(diploma, "location", fim, (0, 0, 0))
base.chave(grupo_selo, "scale", 1, (0, 0, 0)); base.chave(grupo_selo, "scale", int(fim * 0.45), (0, 0, 0))
base.chave(grupo_selo, "scale", int(fim * 0.6), (1.15, 1.15, 1.15)); base.chave(grupo_selo, "scale", int(fim * 0.68), (1, 1, 1))
base.chave(grupo_selo, "rotation_euler", int(fim * 0.45), (0, math.radians(-200), 0)); base.chave(grupo_selo, "rotation_euler", int(fim * 0.66), (0, 0, 0))
p0 = cam.location.copy()
base.chave(cam, "location", 1, (p0.x + 0.25, p0.y * 1.18, p0.z + 0.1)); base.chave(cam, "location", fim, p0)
