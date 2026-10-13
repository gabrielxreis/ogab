"""Cena 3D: claquete com o nome da marca (abertura de vídeo, hero do README).

  python3 -c "import sys; sys.path.insert(0,'tresd'); import tresd; tresd.cena('tresd/cenas/claquete.py', 'claquete.mov', dur=3.5, fps=24, w=1280, h=720, transparente=False)"
P (params, opcionais): texto ("/ogab"), linha ("CENA 01   TAKE 1"), cor (laranja da marca), fonte, fonte_linha.
Roda dentro do Blender: recebe `base` (cena_base) e `P`. Câmera própria (enquadramento horizontal ou vertical).
"""
import math, os
import bpy
from mathutils import Vector

P = globals().get("P") or {}
FONTES = os.path.join(os.path.dirname(base.__file__), "..", "assets", "fontes", "Poppins")
f_tit = P.get("fonte") or os.path.join(FONTES, "Poppins-ExtraBold.ttf")
f_lin = P.get("fonte_linha") or os.path.join(FONTES, "Poppins-SemiBold.ttf")
COR = P.get("cor", "#FF7A3D")
sc = bpy.context.scene
fim = sc.frame_end

base.eevee_qualidade(64, motion_blur=True)
base.mundo("#05070b", 0.35)

# ---- materiais
m_preto = base.material("MAT-verniz", "#0b0d12", metal=0.0, rugosidade=0.22)
m_marca = base.material("MAT-marca", COR, metal=1.0, rugosidade=0.25, emissao=COR, forca_emissao=0.6)
m_branco = base.material("MAT-giz", "#e9edf3", rugosidade=0.7)
m_chao = base.material("MAT-chao", "#07090d", metal=0.0, rugosidade=0.2)


def listrado(nome):
    """Listras diagonais pretas e na cor da marca (Wave Texture em faixas, rampa constante)."""
    m = bpy.data.materials.new(nome); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "DIAGONAL"
    wv.inputs["Scale"].default_value = 1.6; wv.wave_profile = "SAW"
    rp = nt.nodes.new("ShaderNodeValToRGB"); rp.color_ramp.interpolation = "CONSTANT"
    rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = base.hex_linear("#0b0d12")
    rp.color_ramp.elements[1].position = 0.5; rp.color_ramp.elements[1].color = base.hex_linear(COR)
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    nt.links.new(wv.outputs["Fac"], rp.inputs["Fac"])
    nt.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    return m


m_listra = listrado("MAT-listras")


def caixa(nome, loc, esc, mat, chanfro=0.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = nome; o.scale = esc
    bpy.ops.object.transform_apply(scale=True)
    bv = o.modifiers.new("chanfro", "BEVEL"); bv.width = chanfro; bv.segments = 3
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def texto(nome, corpo, fonte, tam, loc, mat, extr):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0, 0))
    t = bpy.context.object; t.name = nome; t.data.body = corpo
    t.data.font = bpy.data.fonts.load(fonte); t.data.size = tam
    t.data.align_x, t.data.align_y = "CENTER", "CENTER"
    t.data.extrude = extr; t.data.bevel_depth = extr * 0.35; t.data.bevel_resolution = 3
    t.data.materials.append(mat)
    return t


# ---- claquete: corpo, faixa listrada fixa, haste que bate (articulada na dobradiça da esquerda)
W, H, D = 2.0, 1.25, 0.12
raiz = bpy.data.objects.new("CLAQUETE", None); sc.collection.objects.link(raiz)
corpo = caixa("GEO-corpo", (0, 0, H / 2), (W, D, H), m_preto)
faixa = caixa("GEO-faixa", (0, 0, H + 0.11), (W, D, 0.22), m_listra)
tit = texto("GEO-titulo", P.get("texto", "/ogab"), f_tit, 0.52, (0, -D / 2 - 0.012, H * 0.56), m_marca, 0.03)
lin = texto("GEO-linha", P.get("linha", "CENA 01     TAKE 1"), f_lin, 0.12, (0, -D / 2 - 0.004, H * 0.2), m_branco, 0.004)
# linhas de giz entre os campos
for k, z in enumerate((H * 0.34, H * 0.08)):
    caixa(f"GEO-giz{k}", (0, -D / 2 - 0.004, z), (W * 0.86, 0.004, 0.012), m_branco, 0.002)

dobradica = bpy.data.objects.new("DOBRADICA", None); sc.collection.objects.link(dobradica)
dobradica.location = (-W / 2, 0, H + 0.24)
haste = caixa("GEO-haste", (W / 2, 0, 0.11), (W, D, 0.22), m_listra)
haste.parent = dobradica
for o in (corpo, faixa, tit, lin, dobradica) + tuple(o for o in bpy.data.objects if o.name.startswith("GEO-giz")):
    if o.parent is None:
        o.parent = raiz

# ---- chão espelhado
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
chao = bpy.context.object; chao.name = "CHAO"; chao.data.materials.append(m_chao)

# ---- luz: três pontos de produto + contra-luz na cor da marca
base.tres_pontos("produto")
for l in bpy.data.objects:
    if l.type == "LIGHT":
        l.data.energy *= 0.55
bpy.ops.object.light_add(type="AREA", location=(0, 2.6, 2.4))
rim = bpy.context.object; rim.name = "LGT-marca"; rim.data.energy = 380; rim.data.size = 2.2
rim.data.color = tuple(base.hex_linear(COR)[:3]); base.aim_at(rim, Vector((0, 0, 1.6)))   # mira alta: contorna a claquete sem lavar o chão

# ---- câmera (lente 50 mm, arco lento da direita para a esquerda)
alvo = Vector((0, 0, 1.15))
bpy.ops.object.camera_add(location=(2.6, -8.4, 2.4))
cam = bpy.context.object; cam.name = "CAM-principal"; cam.data.lens = 54
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.8
sc.camera = cam
foco = bpy.data.objects.new("FOCO", None); sc.collection.objects.link(foco); foco.location = alvo
cam.data.dof.focus_object = foco
trk = cam.constraints.new("TRACK_TO"); trk.target = foco; trk.track_axis = "TRACK_NEGATIVE_Z"; trk.up_axis = "UP_Y"
base.chave(cam, "location", 1, (2.6, -8.4, 2.4))
base.chave(cam, "location", fim, (-1.7, -7.7, 1.7))

# ---- animação: a claquete cai girando e assenta; a haste abre e BATE; leve tremida no impacto
base.chave(raiz, "location", 1, (0, 0.4, 3.2)); base.chave(raiz, "rotation_euler", 1, (math.radians(-25), 0, math.radians(-40)))
q_assenta = int(fim * 0.36)
base.chave(raiz, "location", q_assenta, (0, 0, 0)); base.chave(raiz, "rotation_euler", q_assenta, (0, 0, math.radians(4)))
base.chave(raiz, "location", q_assenta + 3, (0, 0, 0.05)); base.chave(raiz, "location", q_assenta + 6, (0, 0, 0))
base.chave(raiz, "rotation_euler", fim, (0, 0, math.radians(-4)))
q_abre, q_bate = int(fim * 0.4), int(fim * 0.62)
base.chave(dobradica, "rotation_euler", 1, (0, math.radians(-8), 0))
base.chave(dobradica, "rotation_euler", q_abre, (0, math.radians(-26), 0))
base.chave(dobradica, "rotation_euler", q_bate - 3, (0, math.radians(-28), 0))
base.chave(dobradica, "rotation_euler", q_bate, (0, 0, 0))
base.chave(dobradica, "rotation_euler", q_bate + 2, (0, math.radians(-2.5), 0))
base.chave(dobradica, "rotation_euler", q_bate + 4, (0, 0, 0))
base.chave(raiz, "location", q_bate, (0, 0, 0)); base.chave(raiz, "location", q_bate + 1, (0, 0, -0.03))
base.chave(raiz, "location", q_bate + 3, (0, 0, 0))
# brilho da marca acende no impacto
em = m_marca.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
em.default_value = 0.2; em.keyframe_insert("default_value", frame=q_bate - 1)
em.default_value = 3.0; em.keyframe_insert("default_value", frame=q_bate + 1)
em.default_value = 0.7; em.keyframe_insert("default_value", frame=q_bate + 10)
