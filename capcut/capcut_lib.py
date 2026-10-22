"""Gab no CapCut (Mac): edita o rascunho do CapCut direto no JSON.

O CapCut não tem API de script nem porta local (engenharia reversa de 14/10/2026,
CapCut 9.4.0, rascunho new_version 181). O que ele tem é o rascunho em JSON puro:
  ~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<nome>/draft_info.json
Esta lib lê e escreve esse arquivo. Regra de ouro: o CapCut precisa estar FECHADO
(ou fora do projeto) na hora de salvar, senão ele sobrescreve na próxima gravação.

    import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/ogab/capcut")); import capcut_lib as C
    d = C.novo("Reels 01 - Cliente", 1080, 1920, 30)
    v = d.video("/caminho/take.mp4", 0)                  # V1
    d.audio("/caminho/musica.wav", 0, db=-10, fade_out=2)
    d.texto("OLÁ", 1.0, 2.0, y=1200)
    d.salvar(); C.abrir_capcut()

Tempos em segundos. Posição em pixels do quadro (x a partir da esquerda, y a partir
de BAIXO, igual à convenção da /ogab no DaVinci: legenda Y 724).
"""
import copy, difflib, hashlib, json, math, os, re, shutil, subprocess, time, uuid

RAIZ = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")
MIDIA = os.path.expanduser("~/Movies/Gab CapCut")   # o CapCut é sandboxed: só lê ~/Movies sem pedir
AQUI = os.path.dirname(os.path.abspath(__file__))
MOLDE = json.load(open(os.path.join(AQUI, "molde.json")))
# transições, animações, efeitos e máscaras do CapCut internacional (ids do VectCutAPI, Apache 2.0).
# O caminho do efeito não vai no JSON: o CapCut baixa pelo resource_id ao abrir o projeto.
CATALOGO = json.load(open(os.path.join(AQUI, "catalogo.json")))


# loja do CapCut tirada do cache local dos painéis (Cache/ressdk_db/*/rp.db, tabela http_cache = respostas da API
# /artist/v1/panel/get_panel_info). effect_type: 12 filtro, 2 adesivo, 48 modelo de texto, 18 animação de texto
# (Entrada/Saída/Loop/Legenda), 13 animação de vídeo, 26 efeito de voz, 7/19 efeito de vídeo, 10 fonte.
LOJA_ARQ = os.path.join(AQUI, "loja.json")
TIPOS_LOJA = {12: "filtros", 2: "adesivos", 48: "modelos_texto", 18: "texto_anim", 13: "video_anim", 26: "voz",
              7: "efeitos_loja", 19: "efeitos_loja", 10: "fontes"}
CAT_ANIM = {"entrada": "in", "in": "in", "saída": "out", "out": "out", "loop": "loop", "legenda": "caption",
            "caption": "caption", "combinação": "group", "combo": "group"}


def atualizar_loja():
    """Relê o cache do CapCut e regrava loja.json (abrir um painel no CapCut põe os itens dele no cache)."""
    import glob, sqlite3
    base = os.path.join(os.path.dirname(RAIZ), "..", "Cache", "ressdk_db")
    loja = {g: {} for g in set(TIPOS_LOJA.values())}
    for db in glob.glob(os.path.join(base, "*", "rp.db")):
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        for (corpo,) in con.execute("select response_body from http_cache where url like '/artist/v1/%'"):
            try:
                dados = json.loads(corpo)["data"]
            except Exception:
                continue
            cats = {str(c["category_id"]): c.get("category_name", "") for c in dados.get("categories") or []}
            blocos = (dados.get("category_resources") or {}).items() if "category_resources" in dados else [("", dados)]
            for cid, b in blocos:
                for it in (b or {}).get("effect_item_list") or []:
                    ca = it.get("common_attr") or {}
                    g = TIPOS_LOJA.get(ca.get("effect_type"))
                    if not g or not ca.get("effect_id"):
                        continue
                    e = loja[g].setdefault(ca["effect_id"], {"nome": ca.get("title", ""), "resource_id": ca.get("id"),
                                                           "effect_id": ca["effect_id"], "vip": False, "tipos": []})
                    e["vip"] = e["vip"] or '\\"is_vip\\":true' in json.dumps(ca.get("business_info") or {}) \
                        or '"is_vip": true' in json.dumps(ca.get("business_info") or {})
                    k = CAT_ANIM.get(cats.get(cid, "").strip().lower())
                    if k and k not in e["tipos"]:
                        e["tipos"].append(k)
    json.dump(loja, open(LOJA_ARQ, "w"), ensure_ascii=False, separators=(",", ":"))
    return {g: len(v) for g, v in loja.items()}


LOJA = json.load(open(LOJA_ARQ)) if os.path.exists(LOJA_ARQ) else {}


def loja(grupo, busca="", tipo=None):
    """Itens da loja: filtros, adesivos, modelos_texto, texto_anim (tipo in/out/loop/caption), video_anim, voz,
    efeitos_loja, fontes."""
    return sorted({v["nome"].strip() + (" (pro)" if v.get("vip") else "") for v in LOJA.get(grupo, {}).values()
                   if busca.lower() in v["nome"].lower() and (tipo is None or tipo in v.get("tipos", []))})


def _loja(grupo, nome, tipo=None):
    g = {k: v for k, v in LOJA.get(grupo, {}).items() if tipo is None or not v.get("tipos") or tipo in v["tipos"]}
    alvo = nome.replace(" (pro)", "").strip().lower()
    for v in g.values():
        if v["nome"].strip().lower() == alvo or v["resource_id"] == nome:
            return v
    perto = difflib.get_close_matches(nome, [v["nome"] for v in g.values()], 5, 0.4)
    raise KeyError(f"'{nome}' não está na loja ({grupo}). Parecidos: {perto}. Lista: loja('{grupo}')")


def catalogo(grupo, busca=""):
    """Nomes disponíveis: grupo = transicoes, video_entrada, video_saida, video_combo,
    texto_entrada, texto_saida, texto_loop, efeitos, efeitos_pessoa, mascaras."""
    return sorted(v["nome"] + (" (pro)" if v.get("vip") else "") for v in CATALOGO[grupo].values()
                  if busca.lower() in v["nome"].lower())


def _cat(grupo, nome):
    g = CATALOGO[grupo]
    alvo = nome.lower().replace(" (pro)", "").strip()
    for k, v in g.items():
        if k.lower() == alvo.replace(" ", "_") or v["nome"].lower() == alvo:
            return v
    perto = difflib.get_close_matches(nome, [v["nome"] for v in g.values()], 5, 0.4)
    raise KeyError(f"'{nome}' não está em {grupo}. Parecidos: {perto}. Lista: catalogo('{grupo}')")
US = 1_000_000
FOTO_DUR = 10_800_000_000  # o CapCut guarda foto com 3 h de duração


def _id():
    return str(uuid.uuid4()).upper()


def _us(seg):
    return int(round(seg * US))


def _novo(chave, **campos):
    m = copy.deepcopy(MOLDE[chave])
    m["id"] = _id()
    m.update(campos)
    return m


def _sonda(arq):
    """Duração (s), largura, altura e se tem áudio, via ffprobe."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,width,height:stream_side_data=rotation", "-of", "json", arq],
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    vid = [s for s in j.get("streams", []) if s.get("codec_type") == "video"]
    aud = any(s.get("codec_type") == "audio" for s in j.get("streams", []))
    dur = float(j.get("format", {}).get("duration") or 0)
    w, h = (vid[0].get("width", 0), vid[0].get("height", 0)) if vid else (0, 0)
    rot = next((abs(int(x.get("rotation", 0))) for x in (vid[0].get("side_data_list") or []) if "rotation" in x), 0) if vid else 0
    if rot in (90, 270):   # celular/câmera na vertical: o arquivo é 16:9 com rotação nos metadados
        w, h = h, w
    return dur, w, h, aud


def _hex(cor):
    cor = cor.lstrip("#")
    return [int(cor[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def capcut_aberto():
    return subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0


def fechar_capcut(espera=20):
    """Fecha o CapCut (ele salva o que estiver aberto). Necessário antes de salvar()."""
    subprocess.run(["osascript", "-e", 'tell application "CapCut" to quit'], capture_output=True)
    for _ in range(espera * 2):
        if not capcut_aberto():
            return True
        time.sleep(0.5)
    return False


def abrir_capcut():
    """Abre o CapCut na tela inicial. Abrir o projeto é 1 clique na miniatura
    (não há deep link para rascunho; com o computer-use o Gab clica sozinho)."""
    subprocess.run(["open", "-a", "CapCut"])


def rascunhos():
    """Lista os rascunhos: [(nome, duração s, modificado)]."""
    out = []
    for n in sorted(os.listdir(RAIZ)):
        f = os.path.join(RAIZ, n, "draft_info.json")
        if os.path.isfile(f):
            d = json.load(open(f))
            out.append((n, d.get("duration", 0) / US, time.strftime("%d/%m %H:%M", time.localtime(os.path.getmtime(f)))))
    return out


def novo(nome, w=1080, h=1920, fps=30, substituir=False):
    """Cria um rascunho vazio a partir do esqueleto real do CapCut 9.4 e registra na tela inicial."""
    pasta = os.path.join(RAIZ, nome)
    if os.path.exists(pasta):
        if not substituir:
            raise FileExistsError(f"Já existe o rascunho '{nome}'. Use abrir('{nome}') ou substituir=True")
        shutil.rmtree(pasta)
    shutil.copytree(os.path.join(AQUI, "esqueleto"), pasta)
    # ids do esqueleto trocados por novos em todos os arquivos
    velho_tl = json.load(open(os.path.join(pasta, "Timelines", "project.json")))
    trocas = {velho_tl["main_timeline_id"]: _id(), velho_tl["id"]: _id(),
              json.load(open(os.path.join(pasta, "draft_meta_info.json")))["draft_id"]: _id()}
    os.rename(os.path.join(pasta, "Timelines", velho_tl["main_timeline_id"]),
              os.path.join(pasta, "Timelines", trocas[velho_tl["main_timeline_id"]]))
    agora = int(time.time() * US)
    for base, _, arqs in os.walk(pasta):
        for a in arqs:
            f = os.path.join(base, a)
            try:
                t = open(f, encoding="utf-8").read()
            except UnicodeDecodeError:
                continue
            for v, n in trocas.items():
                t = t.replace(v, n)
            open(f, "w", encoding="utf-8").write(t)
    d = Rascunho(nome)
    d.j.update(fps=float(fps), duration=0, tracks=[])
    # ímã da trilha principal desligado: senão o CapCut gruda os clipes da V1 ao abrir e some com os buracos
    d.j["config"]["maintrack_adsorb"] = False
    d.j["canvas_config"].update(width=w, height=h, ratio="original")
    m = d.meta
    m.update(draft_name=nome, draft_fold_path=pasta, draft_root_path=RAIZ, draft_cover="",
             tm_draft_create=agora, tm_draft_modified=agora, draft_materials=[{"type": t, "value": []} for t in (0, 1, 2, 3, 6, 7, 8)])
    d.salvar(forcar=True)
    return d


def abrir(nome):
    return Rascunho(nome)


class Rascunho:
    def __init__(self, nome):
        self.nome = nome
        self.pasta = os.path.join(RAIZ, nome)
        if not os.path.isdir(self.pasta):
            raise FileNotFoundError(f"Rascunho '{nome}' não existe. rascunhos() lista os que existem")
        bruto = open(os.path.join(self.pasta, "draft_info.json"), "rb").read()
        self._digital = hashlib.sha256(bruto).hexdigest()   # se mudar até o salvar(), alguém mexeu no CapCut
        self.j = json.loads(bruto)
        self.meta = json.load(open(os.path.join(self.pasta, "draft_meta_info.json")))
        self._backup_feito = False

    # ---------- leitura ----------
    @property
    def W(self):
        return self.j["canvas_config"]["width"]

    @property
    def H(self):
        return self.j["canvas_config"]["height"]

    def _mat(self, mid):
        for lista in self.j["materials"].values():
            if isinstance(lista, list):
                for m in lista:
                    if isinstance(m, dict) and m.get("id") == mid:
                        return m
        return None

    def retrato(self, salvar_em=None):
        """Retrato da timeline (regra 1g): trilhas, segmentos, início/fim, origem, texto."""
        out = []
        for i, t in enumerate(self.j["tracks"]):
            segs = []
            for s in t["segments"]:
                m = self._mat(s["material_id"]) or {}
                tr, sr = s["target_timerange"], s.get("source_timerange") or {}
                nome = m.get("material_name") or m.get("name") or ""
                if m.get("text_info_resources"):   # texto dentro de modelo
                    m = self._mat(m["text_info_resources"][0]["text_material_id"]) or m
                if m.get("type") == "text":
                    nome = json.loads(m["content"]).get("text", "")
                segs.append({"id": s["id"], "nome": nome, "inicio": tr["start"] / US,
                             "fim": (tr["start"] + tr["duration"]) / US,
                             "de": sr.get("start", 0) / US, "velocidade": s.get("speed", 1),
                             "volume": s.get("volume", 1), "visivel": s.get("visible", True)})
            out.append({"trilha": i, "tipo": t["type"], "nome": t.get("name", ""), "segmentos": segs})
        if salvar_em:
            json.dump(out, open(salvar_em, "w"), ensure_ascii=False, indent=1)
        return out

    def segmento(self, sid):
        for t in self.j["tracks"]:
            for s in t["segments"]:
                if s["id"] == sid:
                    return t, s
        raise KeyError(sid)

    # ---------- trilhas ----------
    def _trilha(self, tipo, n):
        """n-ésima trilha do tipo (0 = primeira). Cria as que faltarem."""
        doTipo = [t for t in self.j["tracks"] if t["type"] == tipo]
        while len(doTipo) <= n:
            t = copy.deepcopy(MOLDE["trilha"])
            t.update(id=_id(), type=tipo, segments=[], flag=0, attribute=0, name="", is_default_name=True)
            self.j["tracks"].append(t)
            doTipo.append(t)
        return doTipo[n]

    def _ordem(self, trilha):
        return self.j["tracks"].index(trilha)

    def _livre(self, trilha, ini, dur):
        for s in trilha["segments"]:
            a, b = s["target_timerange"]["start"], s["target_timerange"]["start"] + s["target_timerange"]["duration"]
            if ini < b and ini + dur > a:
                return False
        return True

    def _por(self, trilha, seg):
        trilha["segments"].append(seg)
        trilha["segments"].sort(key=lambda s: s["target_timerange"]["start"])
        fim = max((s["target_timerange"]["start"] + s["target_timerange"]["duration"]
                   for t in self.j["tracks"] for s in t["segments"]), default=0)
        self.j["duration"] = fim

    def _seg(self, mat_id, ini, dur, de=None, velocidade=1.0, volume=1.0, refs=(), render=0):
        s = copy.deepcopy(MOLDE["segmento"])
        s.update(id=_id(), material_id=mat_id, speed=velocidade, volume=volume, last_nonzero_volume=volume or 1.0,
                 target_timerange={"start": ini, "duration": dur},
                 source_timerange=None if de is None else {"start": de, "duration": int(round(dur * velocidade))},
                 extra_material_refs=list(refs), render_index=render, track_render_index=render,
                 common_keyframes=[], keyframe_refs=[])
        return s

    def _apoio(self, velocidade):
        """Materiais de apoio que o CapCut cria junto com todo clipe de vídeo/áudio."""
        mats = self.j["materials"]
        sp = _novo("speeds", speed=velocidade)
        mats["speeds"].append(sp)
        refs = [sp["id"]]
        for k in ("placeholder_infos", "canvases", "sound_channel_mappings", "material_colors", "vocal_separations"):
            m = _novo(k)
            mats[k].append(m)
            refs.append(m["id"])
        return refs

    # ---------- mídia ----------
    def _trazer(self, arq):
        """Garante que o arquivo está em ~/Movies (sandbox do CapCut). Fora disso, copia (hardlink se der)."""
        arq = os.path.abspath(os.path.expanduser(arq))
        if not os.path.isfile(arq):
            raise FileNotFoundError(arq)
        if arq.startswith(os.path.expanduser("~/Movies/")):
            return arq
        destino_dir = os.path.join(MIDIA, self.nome)
        os.makedirs(destino_dir, exist_ok=True)
        destino = os.path.join(destino_dir, os.path.basename(arq))
        if not os.path.exists(destino) or os.path.getsize(destino) != os.path.getsize(arq):
            try:
                if os.path.exists(destino):
                    os.remove(destino)
                os.link(arq, destino)
            except OSError:
                shutil.copy2(arq, destino)
        return destino

    def _no_pool(self, arq, tipo, dur, w, h):
        pool = self.meta.setdefault("draft_materials", [])
        grupo = next((g for g in pool if g["type"] == 0), None)
        if grupo is None:
            grupo = {"type": 0, "value": []}
            pool.insert(0, grupo)
        if any(v.get("file_Path") == arq for v in grupo["value"]):
            return
        agora = int(time.time())
        grupo["value"].append({"ai_group_type": "", "create_time": agora, "duration": dur, "enter_from": 0,
                               "extra_info": os.path.basename(arq), "file_Path": arq, "height": h, "width": w,
                               "id": str(uuid.uuid4()), "import_time": agora, "import_time_ms": agora * US,
                               "item_source": 1, "material_color_tag": "", "md5": "", "metetype": tipo,
                               "roughcut_time_range": {"duration": dur, "start": 0},
                               "sub_time_range": {"duration": -1, "start": -1}, "type": 0})

    def video(self, arquivo, tempo, de=0.0, ate=None, trilha=0, velocidade=1.0, volume=1.0, mudo=False,
              escala=1.0, x=None, y=None, rotacao=0.0, opacidade=1.0, dur=None):
        """Vídeo ou imagem na trilha de vídeo `trilha` (0 = principal, V1). Devolve o id do segmento.
        de/ate: trecho do arquivo (s). dur: só para imagem. x/y em px (y de baixo); None = centro."""
        arq = self._trazer(arquivo)
        total, w, h, tem_audio = _sonda(arq)
        foto = os.path.splitext(arq)[1].lower() in (".png", ".jpg", ".jpeg", ".webp", ".heic", ".bmp", ".gif") and total < 0.5
        if foto:
            dur_us = _us(dur or 3.0)
            de_us, mat_dur, tipo = 0, FOTO_DUR, "photo"
        else:
            fim = total if ate is None else min(ate, total)
            de_us = _us(de)
            dur_us = int(round((_us(fim) - de_us) / velocidade))
            mat_dur, tipo = _us(total), "video"
        mat = _novo("video", type=tipo, path=arq, material_name=os.path.basename(arq), duration=mat_dur,
                    width=w, height=h, has_audio=bool(tem_audio and not foto))
        self.j["materials"]["videos"].append(mat)
        t = self._trilha("video", trilha)
        ini = _us(tempo)
        if not self._livre(t, ini, dur_us):
            raise ValueError(f"Trilha de vídeo {trilha} ocupada em {tempo:.2f}s. Use outra trilha (V1 é intocável)")
        s = self._seg(mat["id"], ini, dur_us, de_us, velocidade, 0.0 if mudo else volume,
                      self._apoio(velocidade), render=self._ordem(t))
        self._transformar(s, escala, x, y, rotacao, opacidade)
        self._por(t, s)
        self._no_pool(arq, "photo" if foto else "video", mat_dur if not foto else 5 * US, w, h)
        return s["id"]

    def imagem(self, arquivo, tempo, dur, trilha=1, **kw):
        return self.video(arquivo, tempo, trilha=trilha, dur=dur, **kw)

    def audio(self, arquivo, tempo, de=0.0, ate=None, trilha=0, db=0.0, fade_in=0.0, fade_out=0.0, velocidade=1.0):
        """Áudio (narração, música, SFX) na trilha de áudio `trilha`. Música bruta: WAV original, corte e fade aqui."""
        arq = self._trazer(arquivo)
        total = _sonda(arq)[0]
        fim = total if ate is None else min(ate, total)
        de_us = _us(de)
        dur_us = int(round((_us(fim) - de_us) / velocidade))
        mat = {"app_id": 0, "category_id": "", "category_name": "local", "check_flag": 1, "copyright_limit_type": "none",
               "duration": _us(total), "effect_id": "", "formula_id": "", "id": _id(), "intensifies_path": "",
               "is_ai_clone_tone": False, "is_text_edit_overdub": False, "is_ugc": False, "local_material_id": str(uuid.uuid4()),
               "music_id": str(uuid.uuid4()), "name": os.path.basename(arq), "path": arq, "query": "", "request_id": "",
               "resource_id": "", "search_id": "", "source_from": "", "source_platform": 0, "team_id": "", "text_id": "",
               "tone_category_id": "", "tone_category_name": "", "tone_effect_id": "", "tone_effect_name": "",
               "tone_platform": "", "tone_second_category_id": "", "tone_second_category_name": "", "tone_speaker": "",
               "tone_type": "", "type": "extract_music", "video_id": "", "wave_points": []}
        self.j["materials"]["audios"].append(mat)
        refs = self._apoio(velocidade)
        if fade_in or fade_out:
            fd = {"id": _id(), "fade_in_duration": _us(fade_in), "fade_out_duration": _us(fade_out),
                  "fade_type": 0, "type": "audio_fade"}
            self.j["materials"].setdefault("audio_fades", []).append(fd)
            refs.append(fd["id"])
        t = self._trilha("audio", trilha)
        ini = _us(tempo)
        if not self._livre(t, ini, dur_us):
            raise ValueError(f"Trilha de áudio {trilha} ocupada em {tempo:.2f}s")
        s = self._seg(mat["id"], ini, dur_us, de_us, velocidade, 10 ** (db / 20), refs, render=self._ordem(t))
        s["clip"] = None
        s["hdr_settings"] = None
        self._por(t, s)
        self._no_pool(arq, "music", _us(total), 0, 0)
        return s["id"]

    def texto(self, texto, tempo, dur, trilha=0, tamanho=10.0, cor="#FFFFFF", contorno=None, contorno_largura=0.08,
              negrito=False, fonte=None, x=None, y=None, escala=1.0, alinhamento=1, largura_max=0.82):
        """Texto simples. tamanho na escala do CapCut (legenda ~8-10, título ~15-20).
        contorno='#000000' liga a borda. fonte=caminho de .ttf/.otf (cópia vai para ~/Movies)."""
        estilo = {"fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": _hex(cor)}}},
                  "range": [0, len(texto)], "size": tamanho, "bold": negrito, "italic": False, "underline": False}
        mat = copy.deepcopy(MOLDE["texto"])
        mat.update(id=_id(), name=_id(), text_color=cor.upper() + ("FF" if len(cor) == 7 else ""), font_size=tamanho,
                   alignment=alinhamento, line_max_width=largura_max, use_effect_default_color=False)
        if contorno:
            estilo["strokes"] = [{"content": {"solid": {"alpha": 1.0, "color": _hex(contorno)}}, "width": contorno_largura}]
            mat.update(border_color=contorno, border_width=contorno_largura, border_alpha=1.0)
        if fonte:
            f = self._trazer(fonte)
            estilo["font"] = {"id": "", "path": f}
            mat.update(font_path=f, font_name=os.path.splitext(os.path.basename(f))[0],
                       fonts=[{"id": _id(), "path": f, "resource_id": "", "source_platform": 0, "title": os.path.basename(f)}])
        mat["content"] = json.dumps({"styles": [estilo], "text": texto}, ensure_ascii=False)
        self.j["materials"]["texts"].append(mat)
        anim = _novo("material_animations")
        self.j["materials"].setdefault("material_animations", []).append(anim)
        t = self._trilha("text", trilha)
        ini, dur_us = _us(tempo), _us(dur)
        if not self._livre(t, ini, dur_us):
            raise ValueError(f"Trilha de texto {trilha} ocupada em {tempo:.2f}s")
        s = copy.deepcopy(MOLDE["segmento_texto"])
        s.update(id=_id(), material_id=mat["id"], extra_material_refs=[anim["id"]], target_timerange={"start": ini, "duration": dur_us},
                 source_timerange=None, render_index=14000 + self._ordem(t), track_render_index=self._ordem(t),
                 common_keyframes=[], keyframe_refs=[])
        self._transformar(s, escala, x, y, 0.0, 1.0)
        self._por(t, s)
        return s["id"]

    def legenda_srt(self, srt, y=724, tamanho=8.0, cor="#FFFFFF", contorno="#000000", trilha=0, **kw):
        """Legenda a partir de .srt (o legendas.py da /ogab gera). Uma trilha de texto, um bloco por fala."""
        bloco = re.split(r"\n\s*\n", open(srt, encoding="utf-8-sig").read().strip())
        ids = []
        def seg(ts):
            h, m, r = ts.replace(",", ".").split(":")
            return int(h) * 3600 + int(m) * 60 + float(r)
        for b in bloco:
            linhas = b.strip().splitlines()
            tl = next(i for i, l in enumerate(linhas) if "-->" in l)
            a, z = [seg(x.strip()) for x in linhas[tl].split("-->")]
            ids.append(self.texto("\n".join(linhas[tl + 1:]), a, z - a, trilha=trilha, tamanho=tamanho, cor=cor,
                                  contorno=contorno, y=y, **kw))
        return ids

    # ---------- transformação e keyframes ----------
    def _px(self, x, y):
        tx = 0.0 if x is None else (x - self.W / 2) / (self.W / 2)
        ty = 0.0 if y is None else (y - self.H / 2) / (self.H / 2)
        return tx, ty

    def _transformar(self, s, escala, x, y, rotacao, opacidade):
        tx, ty = self._px(x, y)
        s["clip"] = {"scale": {"x": escala, "y": escala}, "rotation": rotacao, "transform": {"x": tx, "y": ty},
                     "flip": {"vertical": False, "horizontal": False}, "alpha": opacidade}
        s["uniform_scale"] = {"on": True, "value": escala}

    def transformar(self, sid, escala=None, x=None, y=None, rotacao=None, opacidade=None):
        s = self.segmento(sid)[1]
        c = s["clip"]
        if escala is not None:
            c["scale"] = {"x": escala, "y": escala}
            s["uniform_scale"] = {"on": True, "value": escala}
        if x is not None or y is not None:
            tx, ty = self._px(x, y)
            if x is not None: c["transform"]["x"] = tx
            if y is not None: c["transform"]["y"] = ty
        if rotacao is not None: c["rotation"] = rotacao
        if opacidade is not None: c["alpha"] = opacidade

    PROPS = {"x": "KFTypePositionX", "y": "KFTypePositionY", "escala": ("KFTypeScaleX", "KFTypeScaleY"),
             "rotacao": "KFTypeRotation", "opacidade": "KFTypeAlpha", "volume": "KFTypeVolume",
             "saturacao": "KFTypeSaturation", "contraste": "KFTypeContrast", "brilho": "KFTypeBrightness"}

    def keyframes(self, sid, prop, chaves):
        """Animação por keyframes. chaves = [(tempo_no_clipe_s, valor), ...].
        prop: x, y (px), escala (1 = 100%), rotacao (graus), opacidade (0-1), volume (dB), saturacao/contraste/brilho.
        Outras: qualquer nome KFType* do CapCut (lista no README)."""
        s = self.segmento(sid)[1]
        nomes = self.PROPS.get(prop, prop)
        nomes = nomes if isinstance(nomes, tuple) else (nomes,)
        for nome in nomes:
            lista = []
            for t, v in chaves:
                if prop == "x": v = self._px(v, None)[0]
                elif prop == "y": v = self._px(None, v)[1]
                elif prop == "volume": v = 10 ** (v / 20)
                lista.append({"curveType": "Line", "graphID": "", "id": _id(), "left_control": {"x": 0.0, "y": 0.0},
                              "right_control": {"x": 0.0, "y": 0.0}, "time_offset": _us(t), "values": [v]})
            s["common_keyframes"] = [k for k in s["common_keyframes"] if k["property_type"] != nome]
            s["common_keyframes"].append({"id": _id(), "keyframe_list": lista, "material_id": "", "property_type": nome})
        return sid

    def zoom(self, sid, de=1.0, para=1.15):
        """Zoom lento (Ken Burns) do começo ao fim do clipe."""
        dur = self.segmento(sid)[1]["target_timerange"]["duration"] / US
        return self.keyframes(sid, "escala", [(0, de), (dur, para)])

    # ---------- edição ----------
    def dividir(self, sid, tempo):
        """Corta o segmento no tempo (s, da timeline). Devolve o id da 2a metade."""
        t, s = self.segmento(sid)
        tr = s["target_timerange"]
        corte = _us(tempo) - tr["start"]
        if not 0 < corte < tr["duration"]:
            raise ValueError("Tempo fora do segmento")
        b = copy.deepcopy(s)
        b["id"] = _id()
        b["target_timerange"] = {"start": tr["start"] + corte, "duration": tr["duration"] - corte}
        s["target_timerange"]["duration"] = corte
        if s.get("source_timerange"):
            src = int(round(corte * s.get("speed", 1)))
            b["source_timerange"] = {"start": s["source_timerange"]["start"] + src,
                                     "duration": s["source_timerange"]["duration"] - src}
            s["source_timerange"]["duration"] = src
        b["common_keyframes"] = []
        self._por(t, b)
        return b["id"]

    def remover(self, sid, fechar_buraco=False):
        """Tira o segmento. Na regra da /ogab, preferir desligar(): V1 nunca se apaga."""
        t, s = self.segmento(sid)
        t["segments"].remove(s)
        if fechar_buraco:
            d = s["target_timerange"]["duration"]
            for o in t["segments"]:
                if o["target_timerange"]["start"] >= s["target_timerange"]["start"]:
                    o["target_timerange"]["start"] -= d
        self.j["duration"] = max((o["target_timerange"]["start"] + o["target_timerange"]["duration"]
                                  for tr in self.j["tracks"] for o in tr["segments"]), default=0)

    def _mat_texto(self, sid):
        m = self._mat(self.segmento(sid)[1]["material_id"])
        if not m or m.get("type") != "text":
            raise ValueError(f"{sid} não é texto simples")
        return m

    def trocar_texto(self, sid, texto):
        """Troca o texto mantendo estilo, posição e tempo."""
        m = self._mat_texto(sid)
        c = json.loads(m["content"])
        c["text"] = texto
        for st in c.get("styles", []):
            st["range"] = [0, len(texto)]
        m["content"] = json.dumps(c, ensure_ascii=False)
        return sid

    def estilo_texto(self, sid, tamanho=None, cor=None, contorno=None, contorno_largura=None, negrito=None,
                     fonte=None, y=None, x=None, largura_max=None):
        """Muda o estilo de um texto já na timeline (tamanho, cor, contorno, negrito, fonte .ttf, posição)."""
        m = self._mat_texto(sid)
        c = json.loads(m["content"])
        for st in c.get("styles", []) or [{}]:
            if tamanho is not None:
                st["size"] = tamanho
            if cor is not None:
                st.setdefault("fill", {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0}}})
                st["fill"]["content"]["solid"]["color"] = _hex(cor)
            if negrito is not None:
                st["bold"] = bool(negrito)
            if contorno is not None or contorno_largura is not None:
                if contorno == "" or contorno is False:
                    st.pop("strokes", None)
                else:
                    velho = (st.get("strokes") or [{}])[0]
                    st["strokes"] = [{"content": {"solid": {"alpha": 1.0, "color": _hex(contorno) if contorno else
                                      velho.get("content", {}).get("solid", {}).get("color", [0, 0, 0])}},
                                      "width": contorno_largura if contorno_largura is not None else velho.get("width", .08)}]
            if fonte:
                f = self._trazer(fonte)
                st["font"] = {"id": "", "path": f}
                m.update(font_path=f, font_name=os.path.splitext(os.path.basename(f))[0])
        m["content"] = json.dumps(c, ensure_ascii=False)
        if tamanho is not None:
            m["font_size"] = tamanho
        if cor is not None:
            m["text_color"] = cor.upper()
        if largura_max is not None:
            m["line_max_width"] = largura_max
        if x is not None or y is not None:
            self.transformar(sid, x=x, y=y)
        return sid

    def desligar(self, sid, ligado=False):
        """Esconde o clipe sem apagar (estilo do Gabriel: desligar em vez de apagar)."""
        self.segmento(sid)[1]["visible"] = ligado

    def volume(self, sid, db):
        s = self.segmento(sid)[1]
        s["volume"] = 10 ** (db / 20)
        s["last_nonzero_volume"] = s["volume"] or 1.0

    def mover(self, sid, tempo):
        s = self.segmento(sid)[1]
        s["target_timerange"]["start"] = _us(tempo)

    # ---------- efeitos da loja (ids do catalogo.json) ----------
    def transicao(self, sid, nome="Dissolve", dur=None):
        """Transição entre este clipe e o PRÓXIMO da mesma trilha. dur em s (padrão do efeito)."""
        s = self.segmento(sid)[1]
        m = _cat("transicoes", nome)
        tr = {"category_id": "", "category_name": "", "duration": _us(dur if dur is not None else m["duracao"]),
              "effect_id": m["effect_id"], "id": _id(), "is_overlap": m["sobrepor"], "name": m["nome"],
              "platform": "all", "resource_id": m["resource_id"], "type": "transition"}
        velhas = {t["id"] for t in self.j["materials"].setdefault("transitions", [])}
        s["extra_material_refs"] = [r for r in s["extra_material_refs"] if r not in velhas]
        self.j["materials"].setdefault("transitions", []).append(tr)
        s["extra_material_refs"].append(tr["id"])
        return tr["id"]

    def animar(self, sid, entrada=None, saida=None, combo=None, loop=None, dur_entrada=None, dur_saida=None, legenda=None):
        """Animação de entrada/saída. Vídeo/imagem: entrada, saida ou combo. Texto: entrada, saida e loop,
        ou legenda= (animação de legenda palavra a palavra, ocupa o texto inteiro).
        Nomes: catalogo('video_entrada'), catalogo('texto_entrada'), loja('texto_anim', tipo='caption')..."""
        t, s = self.segmento(sid)
        texto = t["type"] == "text"
        dur = s["target_timerange"]["duration"]
        ids = {a["id"] for a in self.j["materials"].setdefault("material_animations", [])}
        ref = next((r for r in s["extra_material_refs"] if r in ids), None)
        if ref is None:
            mat = _novo("material_animations")
            self.j["materials"].setdefault("material_animations", []).append(mat)
            s["extra_material_refs"].append(mat["id"])
        else:
            mat = next(a for a in self.j["materials"].setdefault("material_animations", []) if a["id"] == ref)
        lista = []

        def item(grupo, nome, tipo, ini, d):
            try:
                m = _cat(grupo, nome)
            except KeyError:   # não está no catálogo fixo: procura na loja (cache do CapCut)
                m = dict(_loja("texto_anim" if texto else "video_anim", nome, tipo))
                m["duracao"] = 0.5
            d = min(_us(d if d is not None else m["duracao"]), dur)
            ini = dur - d if ini is None else ini
            lista.append({"anim_adjust_params": None, "platform": "all", "panel": "" if texto else "video",
                          "material_type": "sticker" if texto else "video", "name": m["nome"], "id": m["effect_id"],
                          "type": tipo, "resource_id": m["resource_id"], "start": ini, "duration": d})
            return d
        pre = "texto" if texto else "video"
        d_in = d_out = 0
        if legenda:
            # 22/10/2026 (CapCut 9.4/9.5): gravada assim aparece como "Perda da animação" e o app não baixa o arquivo
            # (entrada/saída/loop de texto baixam). Deve precisar do tempo de cada palavra que só a legenda automática
            # do CapCut grava. Até descobrir o formato, recusa em vez de deixar o texto quebrado.
            raise NotImplementedError("animação de legenda (caption) ainda não carrega no CapCut: use entrada= ou loop=")
            if not texto:
                raise ValueError("Animação de legenda é só para texto")
            m = _loja("texto_anim", legenda, "caption")
            lista.append({"anim_adjust_params": None, "platform": "all", "panel": "", "material_type": "sticker",
                          "name": m["nome"], "id": m["effect_id"], "type": "caption", "resource_id": m["resource_id"],
                          "start": 0, "duration": dur})
            mat["animations"] = lista
            return mat["id"]
        if combo:
            if texto:
                raise ValueError("Texto não tem combo: use loop")
            item("video_combo", combo, "group", 0, dur / US)
        else:
            if entrada:
                d_in = item(f"{pre}_entrada", entrada, "in", 0, dur_entrada)
            if saida:
                d_out = item(f"{pre}_saida", saida, "out", None, dur_saida)
            if loop:
                if not texto:
                    raise ValueError("Loop é só para texto")
                item("texto_loop", loop, "loop", d_in, (dur - d_in - d_out) / US)
        mat["animations"] = lista
        return mat["id"]

    def _efeito_mat(self, nome, params, alvo):
        try:
            m, tipo = _cat("efeitos", nome), "video_effect"
        except KeyError:
            m, tipo = _cat("efeitos_pessoa", nome), "face_effect"
        ajustes = []
        for i, p in enumerate(m["params"]):
            v = p["default_value"]
            if params and i < len(params) and params[i] is not None:
                v = p["min_value"] + (p["max_value"] - p["min_value"]) * params[i] / 100
            ajustes.append({**p, "parameterIndex": i, "portIndex": 0, "value": v})
        mat = {"adjust_params": ajustes, "apply_target_type": alvo, "apply_time_range": None, "category_id": "",
               "category_name": "", "common_keyframes": [], "disable_effect_faces": [], "effect_id": m["effect_id"],
               "formula_id": "", "id": _id(), "name": m["nome"], "platform": "all", "render_index": 11000,
               "resource_id": m["resource_id"], "source_platform": 0, "time_range": None, "track_render_index": 0,
               "type": tipo, "value": 1.0, "version": ""}
        self.j["materials"].setdefault("video_effects", []).append(mat)
        return mat

    def efeito(self, nome, tempo, dur, params=None, trilha=0):
        """Efeito de tela inteira (trilha de efeitos, pega tudo que está embaixo). params em 0-100, na ordem do catálogo.
        Nomes: catalogo('efeitos', 'shake'), catalogo('efeitos_pessoa')."""
        mat = self._efeito_mat(nome, params, 2)
        t = self._trilha("effect", trilha)
        ini, d = _us(tempo), _us(dur)
        if not self._livre(t, ini, d):
            raise ValueError(f"Trilha de efeitos {trilha} ocupada em {tempo:.2f}s")
        s = self._seg(mat["id"], ini, d, render=10000 + self._ordem(t))
        s.update(clip=None, hdr_settings=None, volume=1.0)
        self._por(t, s)
        return s["id"]

    def efeito_no_clipe(self, sid, nome, params=None):
        """Efeito só neste clipe (acompanha o clipe se ele mudar de lugar)."""
        mat = self._efeito_mat(nome, params, 0)
        self.segmento(sid)[1]["extra_material_refs"].append(mat["id"])
        return mat["id"]

    def mascara(self, sid, nome="Circle", x=None, y=None, tamanho=0.5, suavizar=0.0, cantos=0.0, rotacao=0.0,
                inverter=False, largura=None):
        """Máscara: Split (linha), Filmstrip (espelho), Circle, Rectangle, Stars, Heart. x/y em px (y de baixo),
        tamanho = altura em fração do quadro, suavizar/cantos 0-100."""
        s = self.segmento(sid)[1]
        m = _cat("mascaras", nome)
        cx, cy = self._px(x, y)
        mat = {"config": {"aspectRatio": m["proporcao"], "centerX": cx, "centerY": cy, "feather": suavizar / 100,
                          "height": tamanho, "invert": inverter, "rotation": rotacao, "roundCorner": cantos / 100,
                          "width": largura or tamanho * self.H * m["proporcao"] / self.W},
               "category": "video", "category_id": "", "category_name": "", "id": _id(), "name": m["nome"],
               "platform": "all", "position_info": "", "resource_type": m["resource_type"],
               "resource_id": m["resource_id"], "type": "mask"}
        velhas = {k["id"] for k in self.j["materials"].setdefault("common_mask", [])}
        s["extra_material_refs"] = [r for r in s["extra_material_refs"] if r not in velhas]
        self.j["materials"].setdefault("common_mask", []).append(mat)
        s["extra_material_refs"].append(mat["id"])
        return mat["id"]

    def fundo(self, sid, desfoque=None, cor=None):
        """Fundo do quadro atrás do clipe (vídeo horizontal em 9x16): desfoque 0-1 ou cor '#RRGGBB'."""
        s = self.segmento(sid)[1]
        cv = next((c for c in self.j["materials"].setdefault("canvases", []) if c["id"] in s["extra_material_refs"]), None)
        if cv is None:
            cv = _novo("canvases")
            self.j["materials"].setdefault("canvases", []).append(cv)
            s["extra_material_refs"].append(cv["id"])
        if desfoque is not None:
            cv.update(type="canvas_blur", blur=desfoque, color="")
        else:
            cv.update(type="canvas_color", color=(cor or "#000000").upper() + "FF", blur=0.0)

    # ---------- itens da loja (loja.json, tirado do cache do CapCut) ----------
    def _filtro_mat(self, nome, intensidade):
        m = _loja("filtros", nome)
        mat = {"adjust_params": [], "algorithm_artifact_path": "", "apply_target_type": 0, "bloom_params": None,
               "category_id": "", "category_name": "", "color_match_info": {"source_feature_path": "",
               "target_feature_path": "", "target_image_path": ""}, "effect_id": m["effect_id"],
               "enable_skin_tone_correction": False, "exclusion_group": [], "face_adjust_params": [], "formula_id": "",
               "id": _id(), "intensity_key": "", "multi_language_current": "", "name": m["nome"], "panel_id": "",
               "platform": "all", "resource_id": m["resource_id"], "source_platform": 1, "sub_type": "none",
               "time_range": None, "type": "filter", "value": intensidade / 100, "version": ""}
        self.j["materials"].setdefault("effects", []).append(mat)
        return mat

    def filtro(self, sid, nome, intensidade=100):
        """Filtro de cor só neste clipe. Nomes: loja('filtros'). intensidade 0-100."""
        s = self.segmento(sid)[1]
        mat = self._filtro_mat(nome, intensidade)
        velhos = {e["id"] for e in self.j["materials"]["effects"] if e.get("type") == "filter" and e is not mat}
        s["extra_material_refs"] = [r for r in s["extra_material_refs"] if r not in velhos] + [mat["id"]]
        return mat["id"]

    def filtro_global(self, nome, tempo, dur, intensidade=100, trilha=0):
        """Filtro de cor numa trilha própria: pega tudo que está embaixo nesse intervalo."""
        mat = self._filtro_mat(nome, intensidade)
        mat["apply_target_type"] = 2
        t = self._trilha("filter", trilha)
        ini, d = _us(tempo), _us(dur)
        if not self._livre(t, ini, d):
            raise ValueError(f"Trilha de filtro {trilha} ocupada em {tempo:.2f}s")
        s = self._seg(mat["id"], ini, d, render=11000 + self._ordem(t))
        s.update(clip=None, hdr_settings=None)
        self._por(t, s)
        return s["id"]

    def adesivo(self, nome, tempo, dur, trilha=0, escala=1.0, x=None, y=None, rotacao=0.0, opacidade=1.0):
        """Adesivo (sticker) da loja. Nomes: loja('adesivos', 'emoji')."""
        m = _loja("adesivos", nome)
        mat = {"id": _id(), "resource_id": m["resource_id"], "sticker_id": m["effect_id"], "source_platform": 1,
               "type": "sticker", "name": m["nome"], "path": "", "unicode": "", "category_id": "", "category_name": "",
               "icon_url": "", "preview_cover_url": "", "radius": {"x": 0.0, "y": 0.0}, "global_alpha": 1.0}
        self.j["materials"].setdefault("stickers", []).append(mat)
        anim = _novo("material_animations")
        self.j["materials"].setdefault("material_animations", []).append(anim)
        t = self._trilha("sticker", trilha)
        ini, d = _us(tempo), _us(dur)
        if not self._livre(t, ini, d):
            raise ValueError(f"Trilha de adesivos {trilha} ocupada em {tempo:.2f}s")
        s = self._seg(mat["id"], ini, d, refs=[anim["id"]], render=14000 + self._ordem(t))
        s["hdr_settings"] = None
        self._transformar(s, escala, x, y, rotacao, opacidade)
        self._por(t, s)
        return s["id"]

    def voz(self, sid, nome, forca=100):
        """Efeito de voz (trocador de voz) num clipe de áudio ou vídeo. Nomes: loja('voz')."""
        s = self.segmento(sid)[1]
        m = _loja("voz", nome)
        mat = {"audio_adjust_params": [{"default_value": 1.0, "max_value": 1.0, "min_value": 0.0, "name": "strength",
                                        "parameterIndex": 0, "portIndex": 0, "value": forca / 100}],
               "category_id": "sound_effect", "category_name": "", "id": _id(), "is_ugc": False, "name": m["nome"],
               "production_path": "", "resource_id": m["resource_id"], "speaker_id": "", "sub_type": 1,
               "time_range": {"duration": 0, "start": 0}, "type": "audio_effect", "path": ""}
        velhos = {e["id"] for e in self.j["materials"].setdefault("audio_effects", [])}
        self.j["materials"]["audio_effects"].append(mat)
        s["extra_material_refs"] = [r for r in s["extra_material_refs"] if r not in velhos] + [mat["id"]]
        return mat["id"]

    def modelo_texto(self, nome, texto, tempo, dur, trilha=0, x=None, y=None, escala=1.0, legenda=False):
        """Texto num modelo pronto da loja (estilo + animação do próprio modelo). Nomes: loja('modelos_texto').
        legenda=True marca como modelo de legenda (como o CapCut faz nas legendas automáticas). Beta: o
        CapCut aplica o visual do modelo ao abrir; se vier texto simples, o modelo não aceitou a troca."""
        m = _loja("modelos_texto", nome)
        sid = self.texto(texto, tempo, dur, trilha=trilha, x=x, y=y, escala=escala)
        t, s = self.segmento(sid)
        txt_id = s["material_id"]
        anim = s["extra_material_refs"][0]
        tpl = copy.deepcopy(MOLDE["modelo_texto"])
        tpl.update(id=_id(), effect_id=m["effect_id"], resource_id=m["resource_id"], name=m["nome"], path="",
                   type="text_template_subtitle" if legenda else "text_template", resources=[])
        tpl["text_info_resources"] = [{**tpl["text_info_resources"][0], "id": _id(), "text_material_id": txt_id,
                                       "extra_material_refs": [anim],
                                       "attach_info": {**tpl["text_info_resources"][0]["attach_info"], "duration": _us(dur)}}]
        tpl["text_template_resource_type"] = "subtitle_template" if legenda else "text_template"
        self.j["materials"].setdefault("text_templates", []).append(tpl)
        s["material_id"] = tpl["id"]
        return sid

    # ---------- corte de silêncio (V1) ----------
    def _clonar(self, s):
        """Cópia do segmento com materiais de apoio próprios (o CapCut não gosta de apoio compartilhado)."""
        n = copy.deepcopy(s)
        n["id"] = _id()
        refs = []
        for r in s["extra_material_refs"]:
            for chave, lista in self.j["materials"].items():
                achado = next((m for m in lista if isinstance(m, dict) and m.get("id") == r), None) if isinstance(lista, list) else None
                if achado:
                    c = copy.deepcopy(achado)
                    c["id"] = _id()
                    lista.append(c)
                    refs.append(c["id"])
                    break
            else:
                refs.append(r)
        n["extra_material_refs"] = refs
        n["common_keyframes"] = []
        return n

    def religar(self, velho, novo, deslocamento=0.0):
        """Troca a mídia `velho` por `novo` em todos os clipes, somando `deslocamento` (s) ao ponto de entrada.
        Uso: trecho baixado à parte (começa em 1551 s do original) -> religar(trecho, original, 1551)."""
        novo = self._trazer(novo)
        total, w, h, aud = _sonda(novo)
        ids = set()
        for lista in ("videos", "audios"):
            for m in self.j["materials"].get(lista, []):
                if m.get("path") and os.path.basename(m["path"]) == os.path.basename(velho):
                    m.update(path=novo, duration=_us(total))
                    if "material_name" in m: m["material_name"] = os.path.basename(novo)
                    if "name" in m: m["name"] = os.path.basename(novo)
                    ids.add(m["id"])
        n = 0
        for t in self.j["tracks"]:
            for s in t["segments"]:
                if s["material_id"] in ids and s.get("source_timerange"):
                    s["source_timerange"]["start"] += _us(deslocamento)
                    n += 1
        self._no_pool(novo, "video", _us(total), w, h)
        return n

    def silencios(self, sid, ruido_db=-30, minimo=0.4):
        """Trechos de silêncio (s, no ARQUIVO) dentro do trecho usado pelo clipe."""
        s = self.segmento(sid)[1]
        m = self._mat(s["material_id"])
        sr = s["source_timerange"]
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{sr['start'] / US:.3f}", "-t",
                            f"{sr['duration'] / US:.3f}", "-i", m["path"], "-map", "0:a:0", "-vn", "-af",
                            f"silencedetect=noise={ruido_db}dB:d={minimo}", "-f", "null", "-"],
                           capture_output=True, text=True)
        ini = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
        fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
        fim += [sr["duration"] / US] * (len(ini) - len(fim))
        base = sr["start"] / US
        return [(base + max(a, 0), base + b) for a, b in zip(ini, fim)]

    def cortar_silencio(self, ruido_db=-30, minimo=0.4, folga=0.12, trilha=0):
        """Tira os silêncios dos clipes da trilha de vídeo `trilha` (padrão V1, a fala) e junta tudo (ripple).
        folga = respiro mantido antes/depois de cada fala. Só a trilha alvo anda: rodar ANTES de legenda e b-roll
        (ordem da /ogab: cortes > legenda > b-roll). Devolve os segundos removidos."""
        t = self._trilha("video", trilha)
        cabeca = t["segments"][0]["target_timerange"]["start"] if t["segments"] else 0
        novos, removido = [], 0
        for s in list(t["segments"]):
            if not s.get("source_timerange") or (self._mat(s["material_id"]) or {}).get("type") != "video":
                novos.append(s)
                continue
            sp = s.get("speed", 1)
            a0 = s["source_timerange"]["start"] / US
            a1 = a0 + s["source_timerange"]["duration"] / US
            manter, cur = [], a0
            for x, y in self.silencios(s["id"], ruido_db, minimo):
                x, y = x + folga, y - folga
                if y - x > 0.05:
                    if x > cur:
                        manter.append((cur, x))
                    cur = y
            if cur < a1:
                manter.append((cur, a1))
            for i, (x, y) in enumerate(manter):
                n = s if i == 0 else self._clonar(s)
                n["source_timerange"] = {"start": _us(x), "duration": _us(y - x)}
                n["target_timerange"] = {"start": 0, "duration": int(round(_us(y - x) / sp))}
                novos.append(n)
            removido += (a1 - a0 - sum(y - x for x, y in manter)) / sp
        pos = cabeca
        for n in novos:
            n["target_timerange"]["start"] = pos
            pos += n["target_timerange"]["duration"]
        t["segments"] = novos
        self.j["duration"] = max((o["target_timerange"]["start"] + o["target_timerange"]["duration"]
                                  for tr in self.j["tracks"] for o in tr["segments"]), default=0)
        return round(removido, 2)

    # ---------- gravar ----------
    def salvar(self, projeto_fechado=False, forcar=False):
        """Grava em todas as cópias que o CapCut 9.4 mantém. Faz backup na 1a gravação.
        O CapCut pode ficar aberto na tela inicial ou em OUTRO projeto: confirmar e passar projeto_fechado=True.
        Com este projeto aberto lá, o CapCut sobrescreve tudo na próxima gravação dele."""
        if capcut_aberto() and not (projeto_fechado or forcar):
            raise RuntimeError("O CapCut está aberto. Se este projeto NÃO estiver aberto nele (tela inicial ou outro "
                               "projeto), salve com projeto_fechado=True. Senão, feche o projeto ou C.fechar_capcut()")
        info = os.path.join(self.pasta, "draft_info.json")
        if not forcar and os.path.exists(info) and hashlib.sha256(open(info, "rb").read()).hexdigest() != self._digital:
            raise RuntimeError("O rascunho mudou no disco desde que foi aberto (edição no CapCut?). "
                               "Abra de novo com C.abrir() e refaça, para não apagar a edição manual")
        tl = json.load(open(os.path.join(self.pasta, "Timelines", "project.json")))["main_timeline_id"]
        self.j["id"] = tl
        dados = json.dumps(self.j, ensure_ascii=False, separators=(",", ":"))

        def gravar(f, texto):   # atômico: nunca deixa um JSON pela metade
            tmp = f + ".gabtmp"
            open(tmp, "w", encoding="utf-8").write(texto)
            os.replace(tmp, f)
        if not self._backup_feito:
            orig = os.path.join(self.pasta, "draft_info.json")
            if os.path.exists(orig):
                shutil.copy2(orig, os.path.join(self.pasta, f"draft_info.gab_{time.strftime('%Y%m%d-%H%M%S')}.json"))
            self._backup_feito = True
        tdir = os.path.join(self.pasta, "Timelines", tl)
        for f in (os.path.join(self.pasta, n) for n in ("draft_info.json", "draft_info.json.bak", "template-2.tmp")):
            gravar(f, dados)
        if os.path.isdir(tdir):
            for n in ("draft_info.json", "draft_info.json.bak", "template-2.tmp"):
                gravar(os.path.join(tdir, n), dados)
            patch = os.path.join(tdir, "attachment", "patch")
            if os.path.isdir(patch):
                open(os.path.join(patch, "patch.json"), "w").write('{"patch_data":[]}')
                mini = os.path.join(patch, "mini_draft.json")
                if os.path.exists(mini):
                    os.remove(mini)
        agora = int(time.time() * US)
        self.meta.update(tm_duration=self.j["duration"], tm_draft_modified=agora)
        gravar(os.path.join(self.pasta, "draft_meta_info.json"), json.dumps(self.meta, ensure_ascii=False))
        self._registrar(agora)
        self._digital = hashlib.sha256(dados.encode("utf-8")).hexdigest()
        return self.pasta

    def _registrar(self, agora):
        """Entrada na tela inicial do CapCut (root_meta_info.json)."""
        f = os.path.join(RAIZ, "root_meta_info.json")
        r = json.load(open(f))
        lista = r.setdefault("all_draft_store", [])
        e = next((x for x in lista if x.get("draft_fold_path") == self.pasta), None)
        if e is None:
            e = copy.deepcopy(lista[0]) if lista else {}
            lista.insert(0, e)
            e.update(draft_cover="", tm_draft_create=agora, draft_id=self.meta.get("draft_id", _id()))
        e.update(draft_fold_path=self.pasta, draft_json_file=os.path.join(self.pasta, "draft_info.json"),
                 draft_name=self.nome, draft_root_path=RAIZ, tm_draft_modified=agora, tm_duration=self.j["duration"],
                 draft_timeline_materials_size=0, tm_draft_removed=0, draft_is_invisible=False)
        json.dump(r, open(f, "w"), ensure_ascii=False)
