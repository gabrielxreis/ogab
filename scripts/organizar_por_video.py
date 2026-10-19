"""Organiza o Media Pool do projeto: uma pasta por vídeo ("NN Nome"), cada uma com Takes, Motions, Audio e Timelines.

  python3 organizar_por_video.py [--simular]

O vídeo de cada mídia vem de qual timeline a usa ("NN ..." -> vídeo NN); sem uso, do caminho do arquivo
("<Assunto> - <Empresa>/..."). O que não é de nenhum vídeo vai para "00 Geral". Só move entre pastas do Media Pool:
nenhuma timeline nem clipe muda.
"""
import os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as L

SIM = "--simular" in sys.argv
SUB = ("Takes", "Motions", "Audio", "Timelines")
r = L.conectar(abrir=False); p = r.GetProjectManager().GetCurrentProject(); mp = p.GetMediaPool(); root = mp.GetRootFolder()
tls = [p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1)]
num = lambda n: (re.match(r"^(\d{2}) (.+?)(?: - com silencios| - YouTube| - Curso| \(backup.*\))*$", n) or [None, None, None])
videos = {}   # "NN" -> nome base
for t in tls:
    m = num(t.GetName())
    if m and m[1]: videos.setdefault(m[1], m[2])
# uso: id do item -> vídeo
uso = collections.defaultdict(set)
for t in tls:
    m = num(t.GetName()); v = m[1] if m and m[1] else "00"
    for k in ("video", "audio", "subtitle"):
        for n in range(1, t.GetTrackCount(k) + 1):
            for c in t.GetItemListInTrack(k, n) or []:
                it = c.GetMediaPoolItem()
                if it: uso[it.GetUniqueId()].add(v)
assunto_v = {re.sub(r"[^a-z0-9]", "", nome.lower()): v for v, nome in videos.items()}


def video_do_item(it):
    if "timeline" in (it.GetClipProperty("Type") or "").lower():
        m = num(it.GetName() or ""); return m[1] if m and m[1] else "00"
    u = uso.get(it.GetUniqueId())
    if u: return sorted(u)[-1] if len(u) == 1 or "00" not in u else sorted(u - {"00"})[-1]
    fp = it.GetClipProperty("File Path") or ""
    m = re.search(r"/([^/]+) - A Grande Missao/", fp)
    if m:
        k = re.sub(r"[^a-z0-9]", "", m.group(1).lower())
        for a, v in assunto_v.items():
            if k and (k in a or a in k): return v
    return "00"


def tipo(it):
    ty = (it.GetClipProperty("Type") or "").lower(); fp = (it.GetClipProperty("File Path") or "").lower(); nm = (it.GetName() or "").lower()
    if "timeline" in ty: return "Timelines"
    if "/motions" in fp or "_motions" in fp or "/overlays/" in fp or "lettering" in fp or "fusion" in ty or "title" in ty: return "Motions"
    if ty.startswith("audio") or fp.endswith((".wav", ".mp3", ".aif", ".aiff", ".m4a", ".flac")): return "Audio"
    if "subtitle" in ty or fp.endswith(".srt"): return "Timelines"
    return "Takes"


todos = []
def coleta(f):
    for it in f.GetClipList() or []: todos.append(it)
    for s in f.GetSubFolderList() or []: coleta(s)
coleta(root)
plano = collections.defaultdict(list)
for it in todos:
    plano[(video_do_item(it), tipo(it))].append(it)
nomes = dict(videos); nomes["00"] = "Geral"
for (v, k), its in sorted(plano.items()):
    print(f"{v} {nomes.get(v, '?'):32} {k:10} {len(its)}")
if SIM: sys.exit()
pastas = {}
def pasta(nome, pai):
    for s in pai.GetSubFolderList() or []:
        if s.GetName() == nome: return s
    return mp.AddSubFolder(pai, nome)
for (v, k), its in plano.items():
    pv = pasta(f"{v} {nomes.get(v, 'Geral')}", root)
    for s in SUB: pasta(s, pv)
    alvo = pasta(k, pv)
    if not mp.MoveClips(its, alvo): print("não moveu:", v, k, len(its))
# garante as 4 subpastas em todo vídeo e apaga pastas antigas que ficaram vazias
for v, nome in nomes.items():
    pv = pasta(f"{v} {nome}", root)
    for s in SUB: pasta(s, pv)
vazias = [s for s in root.GetSubFolderList() or [] if not re.match(r"^\d{2} ", s.GetName()) and not (s.GetClipList() or []) and not (s.GetSubFolderList() or [])]
if vazias: mp.DeleteFolders(vazias)
L.salvar(r)
print("ok; pastas antigas vazias removidas:", [s.GetName() for s in vazias] if vazias else [])
