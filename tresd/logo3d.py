"""Logo/texto em 3D DE VERDADE no Blender (roda sem abrir a janela). Chamado por tresd/tresd.py.

  blender -b -P logo3d.py -- plano.json

plano.json:
  {"texto": "CALVERSTONE", "fonte": "/caminho/Cardo-Regular.ttf", "tamanho": 1.0, "espaco": 0.12,
   "profundidade": 0.10, "chanfro": 0.012, "cor": "#C9A657", "metal": 1.0, "rugosidade": 0.28,
   "losango": true, "linhas": true, "fundo": null | "#0B1F3A",
   "w": 1080, "h": 1920, "fps": 30, "dur": 3.0, "anim": "entrada" | "giro" | "orbita",
   "amostras": 32, "saida": "/pasta/quadros_"}
Gera PNG com alfa por quadro (fundo transparente) para virar MOV ProRes 4444 (tresd.py junta com ffmpeg).
Tudo fica editável no .blend salvo junto (saida + "cena.blend").
"""
import json, math, sys
import bpy

plano = json.load(open(sys.argv[sys.argv.index("--") + 1]))


def hex_rgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]   # sRGB -> linear


bpy.ops.wm.read_factory_settings(use_empty=True)
cena = bpy.context.scene
cena.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
cena.render.resolution_x, cena.render.resolution_y = plano.get("w", 1080), plano.get("h", 1920)
cena.render.fps = plano.get("fps", 30)
cena.frame_start, cena.frame_end = 1, int(round(plano.get("dur", 3.0) * cena.render.fps))
cena.render.film_transparent = plano.get("fundo") is None
cena.render.image_settings.file_format = "PNG"
cena.render.image_settings.color_mode = "RGBA"
cena.view_settings.view_transform = "AgX" if "AgX" in [v.name for v in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
try:
    cena.eevee.taa_render_samples = plano.get("amostras", 32)
except Exception:
    pass

# ---- material metálico (dourado por padrão)
mat = bpy.data.materials.new("Metal Gab"); mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = hex_rgb(plano.get("cor", "#C9A657"))
bsdf.inputs["Metallic"].default_value = plano.get("metal", 1.0)
bsdf.inputs["Roughness"].default_value = plano.get("rugosidade", 0.28)

# ---- texto extrudado
bpy.ops.object.text_add(location=(0, 0, 0))
txt = bpy.context.object; txt.name = "TEXTO 3D"
txt.data.body = plano.get("texto", "LOGO")
if plano.get("fonte"):
    txt.data.font = bpy.data.fonts.load(plano["fonte"])
txt.data.size = plano.get("tamanho", 1.0)
txt.data.space_character = 1.0 + plano.get("espaco", 0.12)
txt.data.align_x, txt.data.align_y = "CENTER", "CENTER"
txt.data.extrude = plano.get("profundidade", 0.10)
txt.data.bevel_depth = plano.get("chanfro", 0.012)
txt.data.bevel_resolution = 4
txt.data.materials.append(mat)
txt.rotation_euler = (math.radians(90), 0, 0)          # de pé, de frente para a câmera (eixo -Y)
largura = None
bpy.context.view_layer.update()
largura = txt.dimensions.x

pecas = [txt]
# ---- losango e linhas (assinatura da marca)
if plano.get("losango", False):
    bpy.ops.mesh.primitive_cube_add(size=0.16, location=(0, 0, -0.55))
    los = bpy.context.object; los.name = "LOSANGO 3D"
    los.rotation_euler = (0, math.radians(45), 0); los.scale = (1, 0.35, 1)
    bpy.ops.object.modifier_add(type="BEVEL"); los.modifiers["Bevel"].width = 0.012; los.modifiers["Bevel"].segments = 3
    los.data.materials.append(mat); pecas.append(los)
    if plano.get("linhas", True):
        for lado in (-1, 1):
            bpy.ops.mesh.primitive_cube_add(size=1, location=(lado * 0.42, 0, -0.55))
            ln = bpy.context.object; ln.name = "LINHA 3D"; ln.scale = (0.30, 0.02, 0.012)
            ln.data.materials.append(mat); pecas.append(ln)

# ---- grupo (empty) para animar tudo junto
bpy.ops.object.empty_add(location=(0, 0, 0)); grupo = bpy.context.object; grupo.name = "LOGO"
for p in pecas:
    p.parent = grupo

# ---- luz: ambiente suave + key quente + rim que desenha o chanfro
mundo = bpy.data.worlds.new("Mundo"); cena.world = mundo; mundo.use_nodes = True
bg = mundo.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = hex_rgb(plano["fundo"]) if plano.get("fundo") else (0.02, 0.03, 0.05, 1)
bg.inputs["Strength"].default_value = 0.6
for nome, loc, energia, cor in (("KEY", (2.5, -3.5, 2.5), 900, (1.0, 0.92, 0.8)), ("RIM", (-3, 2.5, 1.5), 1200, (0.75, 0.85, 1.0)),
                                ("FILL", (-2.5, -3, -1), 250, (1, 1, 1))):
    bpy.ops.object.light_add(type="AREA", location=loc)
    lz = bpy.context.object; lz.name = nome; lz.data.energy = energia; lz.data.color = cor; lz.data.size = 3
    alvo = lz.constraints.new("TRACK_TO"); alvo.target = grupo; alvo.track_axis = "TRACK_NEGATIVE_Z"; alvo.up_axis = "UP_Y"

# ---- câmera enquadrando a largura do logo (vertical 9:16)
bpy.ops.object.camera_add(location=(0, -6, 0)); cam = bpy.context.object; cena.camera = cam
cam.data.lens = 50
alvo = cam.constraints.new("TRACK_TO"); alvo.target = grupo; alvo.track_axis = "TRACK_NEGATIVE_Z"; alvo.up_axis = "UP_Y"
sensor_w = cam.data.sensor_width * cena.render.resolution_x / max(cena.render.resolution_x, cena.render.resolution_y)
dist = (largura * 1.25) * cam.data.lens / sensor_w        # logo ocupa ~80% da largura do quadro
cam.location = (0, -dist, 0)

# ---- animação
fim = cena.frame_end
anim = plano.get("anim", "entrada")
def chave(obj, campo, quadro, valor):
    setattr(obj, campo, valor); obj.keyframe_insert(data_path=campo, frame=quadro)
if anim == "entrada":            # vem girando de lado e assenta de frente, a câmera aproxima devagar
    chave(grupo, "rotation_euler", 1, (0, 0, math.radians(-70)))
    chave(grupo, "rotation_euler", int(fim * 0.55), (0, 0, math.radians(4)))
    chave(grupo, "rotation_euler", fim, (0, 0, 0))
    chave(cam, "location", 1, (0.6, -dist * 1.25, 0.25)); chave(cam, "location", fim, (0, -dist, 0))
elif anim == "giro":             # gira 360 sobre o próprio eixo
    chave(grupo, "rotation_euler", 1, (0, 0, 0)); chave(grupo, "rotation_euler", fim, (0, 0, math.radians(360)))
else:                            # orbita: câmera passeia em arco em volta do logo parado
    for q, ang in ((1, -35), (fim, 35)):
        a = math.radians(ang)
        chave(cam, "location", q, (math.sin(a) * dist, -math.cos(a) * dist, 0.4 * math.sin(a)))
for obj in (grupo, cam):
    if obj.animation_data and obj.animation_data.action:
        try:
            for fc in obj.animation_data.action.fcurves:
                for k in fc.keyframe_points:
                    k.interpolation = "BEZIER"; k.easing = "EASE_IN_OUT"
        except Exception:
            pass

cena.render.filepath = plano["saida"]
bpy.ops.wm.save_as_mainfile(filepath=plano["saida"] + "cena.blend")
bpy.ops.render.render(animation=True)
print("GAB_OK", cena.frame_end)
