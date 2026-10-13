"""Base das cenas 3D do Gab no Blender (importado dentro do Blender pelo runner de tresd.py).

Receitas de luz e material adaptadas do pacote cc-blender-skill (MIT, RobLe3, github.com/RobLe3/cc-blender-skill):
três pontos com proporção por tipo de material (Recipe 0a de blender-lighting) e ouro polido (Recipe 2 de
blender-materials). Convenções: objetos do assunto com nome "GEO-...", luzes "LGT-...", câmera "CAM-principal".
"""
import math
import bpy
from mathutils import Vector


def limpar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def hex_linear(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c] + [1.0]


def render(w=1080, h=1920, fps=30, dur=4.0, transparente=True, amostras=32, motor="EEVEE"):
    cena = bpy.context.scene
    ids = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    cena.render.engine = "CYCLES" if motor == "CYCLES" else ("BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in ids else "BLENDER_EEVEE")
    cena.render.resolution_x, cena.render.resolution_y, cena.render.fps = w, h, fps
    cena.frame_start, cena.frame_end = 1, int(round(dur * fps))
    cena.render.film_transparent = transparente
    cena.render.image_settings.file_format = "PNG"; cena.render.image_settings.color_mode = "RGBA"
    vt = [v.name for v in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items]
    cena.view_settings.view_transform = "AgX" if "AgX" in vt else "Filmic"
    try:
        cena.eevee.taa_render_samples = amostras
    except Exception:
        pass
    if motor == "CYCLES":
        cena.cycles.samples = amostras; cena.cycles.use_denoising = True
    return cena


def mundo(cor="#06101e", forca=0.5):
    w = bpy.data.worlds.new("MUNDO"); bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = hex_linear(cor); bg.inputs["Strength"].default_value = forca
    return w


def material(nome, cor, metal=0.0, rugosidade=0.5, emissao=None, forca_emissao=0.0):
    m = bpy.data.materials.new(nome); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hex_linear(cor)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rugosidade
    if emissao:
        b.inputs["Emission Color"].default_value = hex_linear(emissao); b.inputs["Emission Strength"].default_value = forca_emissao
    return m


def ouro(nome="MAT-ouro", cor="#D4AF37", rugosidade=0.18):
    """Ouro polido (Recipe 2 do cc-blender-skill): metal 1, rugosidade baixa, cor ouro."""
    return material(nome, cor, metal=1.0, rugosidade=rugosidade)


def aim_at(obj, alvo):
    p = Vector(alvo.location) if hasattr(alvo, "location") else Vector(alvo)
    obj.rotation_euler = (p - obj.location).normalized().to_track_quat("-Z", "Y").to_euler()


def caixa_assunto():
    malhas = [o for o in bpy.data.objects if o.type in ("MESH", "FONT", "CURVE") and o.name.startswith("GEO-")]
    deps = bpy.context.evaluated_depsgraph_get(); pts = []
    for o in malhas:
        eo = o.evaluated_get(deps); em = eo.to_mesh()
        pts += [o.matrix_world @ v.co for v in em.vertices]; eo.to_mesh_clear()
    if not pts:
        return Vector((0, 0, 0)), 1.0
    xs, ys, zs = [v.x for v in pts], [v.y for v in pts], [v.z for v in pts]
    centro = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
    return centro, max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def tres_pontos(classe="metal"):
    """Luz de três pontos com proporção por tipo de material (Recipe 0a do cc-blender-skill)."""
    perfis = {"metal": ((4, 1, 2), (1, .95, .85), (.85, .9, 1), (.7, .85, 1)),
              "vidro": ((3, 1, 1.2), (1, .98, .95), (.95, .95, 1), (.95, .95, 1)),
              "madeira": ((4, 1, 1.5), (1, .92, .78), (.95, .95, 1), (.85, .92, 1)),
              "papel": ((3, 1, .8), (1, .97, .92), (.92, .95, 1), (.95, .95, 1)),
              "produto": ((5, 1, 1.5), (1, .98, .95), (.98, .98, 1), (.98, .98, 1))}
    razao, ck, cf, cr = perfis.get(classe, perfis["metal"])
    centro, tam = caixa_assunto()
    d = max(tam * 1.5, 1.0); base = 100 * (d / 1.5) ** 2
    for nome, (ox, oy, oz), r, cor in (("LGT-key", (1.2, -1.4, 1.1), razao[0], ck), ("LGT-fill", (-1.4, -1.0, 0.3), razao[1], cf),
                                       ("LGT-rim", (-0.6, 1.6, 1.3), razao[2], cr)):
        bpy.ops.object.light_add(type="AREA", location=centro + Vector((ox, oy, oz)) * d)
        l = bpy.context.object; l.name = nome; l.data.energy = base * r; l.data.color = cor; l.data.size = d * 0.8
        aim_at(l, centro)
    if classe in ("metal", "produto"):   # metal reflete o ambiente: um softbox grande acima dá o "brilho de ouro"
        bpy.ops.object.light_add(type="AREA", location=centro + Vector((0, -0.6, 1.8)) * d)
        sb = bpy.context.object; sb.name = "LGT-softbox"; sb.data.energy = base * 2.5; sb.data.size = d * 2.2
        sb.data.color = (1, .97, .92); aim_at(sb, centro)
        # rebatedor atrás da câmera: superfície de metal virada para a câmera (selo, moeda, logo) reflete ele e acende
        bpy.ops.object.light_add(type="AREA", location=centro + Vector((0.3, -3.2, 0.6)) * d)
        rb = bpy.context.object; rb.name = "LGT-rebatedor"; rb.data.energy = base * 3.0; rb.data.size = d * 3.0
        rb.data.color = (1, .95, .86); aim_at(rb, centro)
    return centro, tam


def largura_assunto():
    malhas = [o for o in bpy.data.objects if o.type in ("MESH", "FONT", "CURVE") and o.name.startswith("GEO-")]
    deps = bpy.context.evaluated_depsgraph_get(); xs = []
    for o in malhas:
        eo = o.evaluated_get(deps); em = eo.to_mesh(); xs += [(o.matrix_world @ v.co).x for v in em.vertices]; eo.to_mesh_clear()
    return (max(xs) - min(xs)) if xs else 1.0


def camera(dist_fator=None, lente=60, altura=0.15, ocupar=0.82):
    """Câmera de frente (-Y). Sem dist_fator: distância calculada para o objeto ocupar `ocupar` da LARGURA do quadro
    (no vertical 9:16 a largura é o limite: objeto horizontal cortava nas laterais)."""
    centro, tam = caixa_assunto()
    r = bpy.context.scene.render
    sensor_h = 36.0 * min(r.resolution_x, r.resolution_y) / max(r.resolution_x, r.resolution_y)   # largura útil do sensor
    dist = (largura_assunto() / ocupar) * lente / sensor_h if dist_fator is None else tam * dist_fator
    bpy.ops.object.camera_add(location=centro + Vector((0, -dist, tam * altura)))
    c = bpy.context.object; c.name = "CAM-principal"; c.data.lens = lente
    bpy.context.scene.camera = c; aim_at(c, centro)
    return c, centro, tam


def chave(obj, campo, quadro, valor, interp="BEZIER"):
    setattr(obj, campo, valor); obj.keyframe_insert(data_path=campo, frame=quadro)


def suavizar_tudo():
    for o in bpy.data.objects:
        ad = o.animation_data
        if ad and ad.action:
            try:
                for fc in ad.action.fcurves:
                    for k in fc.keyframe_points:
                        k.interpolation = "BEZIER"; k.easing = "EASE_IN_OUT"
            except Exception:
                pass


# ---------------- v2 (12/10/2026, pedido do usuário): qualidade de produto ----------------
# Cycles na GPU + HDRI de estúdio (Poly Haven, CC0) no lugar do EEVEE com luzes fortes (dava "aberração de luz"),
# render em TELA CHEIA 1080x1920 com alfa (nunca um quadrado colado por cima) e câmera deslocada para o objeto
# ficar abaixo do texto. Assets: tresd/polyhaven.py.

def gpu_cycles(motion_blur=True):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"
    try:
        pr = bpy.context.preferences.addons["cycles"].preferences
        pr.compute_device_type = "METAL" if bpy.app.build_platform == b"Darwin" else "CUDA"; pr.get_devices()
        for d in pr.devices: d.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("Cycles sem GPU:", e)
    sc.render.use_persistent_data = True   # ~5 s/quadro em 1080x1920 com 24 amostras no M1 Pro (sem isso, ~17 s)
    sc.cycles.use_denoising = True; sc.render.use_motion_blur = motion_blur; sc.render.motion_blur_shutter = 0.5


def hdri(arquivo, forca=1.0, rot=0.0):
    w = bpy.data.worlds.new("MUNDO"); bpy.context.scene.world = w; w.use_nodes = True; nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(arquivo)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value[2] = math.radians(rot)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    bg = nt.nodes["Background"]; nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = forca
    return w


def torno(nome, perfil, mat, eixo="Z", seg=96):
    """Sólido de revolução (martelo, taça, troféu, ampulheta): perfil = [(raio, altura)] de baixo para cima."""
    import bmesh
    bm = bmesh.new(); aneis = []
    for r, z in perfil:
        anel = []
        for i in range(seg):
            a = 2 * math.pi * i / seg; x, y = r * math.cos(a), r * math.sin(a)
            anel.append(bm.verts.new({"Z": (x, y, z), "X": (z, x, y), "Y": (x, z, y)}[eixo]))
        aneis.append(anel)
    for a, b in zip(aneis, aneis[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    bm.faces.new(list(reversed(aneis[0]))); bm.faces.new(aneis[-1])
    me = bpy.data.meshes.new(nome); bm.normal_update(); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nome, me); bpy.context.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat); sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = 1; sd.render_levels = 2
    return o


def deslocar_camera(cam, y_alvo_px, h=1920):
    """Põe o centro do objeto em y_alvo_px sem mudar a perspectiva. NÃO mexer no sensor_fit (VERTICAL estreita o
    campo e o objeto sai 1,5x maior e cortado)."""
    cam.data.shift_y = (y_alvo_px - h / 2) / h
