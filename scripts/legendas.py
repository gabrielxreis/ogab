"""Legendas: rascunho automático por frase + sincronização de frases escritas à mão com a transcrição.

Comandos:
  python3 legendas.py rascunho  transcricao.json frases.txt [--cliente pasta_cliente] [--max 25]
      -> gera um frases.txt (uma legenda por linha, UMA linha cada, cortada em ponto natural),
         já com as correções de grafia do cliente. Revise/ajuste à mão se precisar.
  python3 legendas.py sincronizar transcricao.json frases.txt saida.srt
      -> casa cada legenda com o tempo das palavras faladas e grava o SRT.

Formato do frases.txt: uma legenda por linha. '#n' no fim força o nº de palavras faladas quando a grafia
corrigida tem nº de palavras diferente da transcrição (ex.: "na Marca X. #4" quando a transcrição ouviu "na Mar ca X", 4 palavras).

transcricao.json = saída de MediaPoolItem.GetTranscription() do Resolve (segments[].words[] com start/end em
timecode HH:MM:SS:FF) ou do ElevenLabs/Whisper convertida para {"segments":[{"words":[{"text","start","end"}]}]} em segundos.
"""
import json, os, re, sys

FRACAS = {'a', 'o', 'as', 'os', 'um', 'uma', 'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos', 'que',
          'com', 'por', 'para', 'pra', 'se', 'é', 'ao', 'à', 'mas', 'ou', 'seu', 'sua', 'te', 'não', 'mais', 'nem', 'todo',
          'toda', 'pode', 'vai', 'só', 'quem', 'muito', 'the', 'of', 'to', 'and'}


def t_seg(v, fps):
    if isinstance(v, (int, float)): return float(v)
    h, m, s, f = map(int, v.split(':')); return h * 3600 + m * 60 + s + f / fps


def palavras(transc, fps=30):
    tr = json.load(open(transc))
    return [[w['text'].strip(), t_seg(w['start'], fps), t_seg(w['end'], fps)]
            for s in tr['segments'] for w in s['words'] if w['text'].strip() not in ('', '(...)')]


def correcoes(pasta_cliente):
    """pronuncia.json do cliente: {"termos": [{"grafia": "Marca X", "erros_transcricao": ["Mar ca X"], "fala": "Marca X"}]}"""
    fix = []
    p = os.path.join(pasta_cliente, 'pronuncia.json') if pasta_cliente else None
    if p and os.path.exists(p):
        for t in json.load(open(p)).get('termos', []):
            for e in t.get('erros_transcricao', []):
                fix.append(([w.lower() for w in e.split()], t['grafia']))
    return fix


def aplicar(ws, fix):
    out, i = [], 0
    while i < len(ws):
        for seq, rep in fix:
            n = len(seq)
            cand = [re.sub(r'[,.?!]$', '', w[0].lower()) for w in ws[i:i + n]]
            if cand == seq:
                pont = re.search(r'[,.?!]$', ws[i + n - 1][0]); rep2 = rep + (pont.group(0) if pont else '')
                out.append([rep2, ws[i][1], ws[i + n - 1][2], n]); i += n; break
        else:
            out.append(ws[i] + [1]); i += 1
    return out


def fraca(w):
    t = w.lower().strip(',.?!"'); return t in FRACAS or bool(re.fullmatch(r'[\d.,º]+', t))


def rascunho(transc, saida, cliente=None, maxc=25, fps=30):
    ws = aplicar(palavras(transc, fps), correcoes(cliente))
    txt = lambda c: ' '.join(w[0] for w in c)
    caps, cur = [], []
    for w in ws:
        if cur and len(txt(cur + [w])) > maxc:
            virg = [j for j in range(1, len(cur)) if cur[j - 1][0].endswith(',')]
            boas = [j for j in range(1, len(cur) + 1) if not fraca(cur[j - 1][0])]
            k = virg[-1] if virg and virg[-1] >= len(cur) // 2 else (boas[-1] if boas else len(cur))
            caps.append(cur[:k]); cur = cur[k:]
        cur.append(w)
        if re.search(r'[.?!,]$', w[0]) and len(txt(cur)) >= maxc * 0.45: caps.append(cur); cur = []
        elif re.search(r'[.?!]$', w[0]): caps.append(cur); cur = []
    if cur: caps.append(cur)
    with open(saida, 'w') as f:
        for c in caps:
            n_falado = sum(w[3] for w in c); n_escrito = len(txt(c).split())
            f.write(txt(c) + (f' #{n_falado}' if n_falado != n_escrito else '') + '\n')
    print(len(caps), 'legendas no rascunho ->', saida)


def sincronizar(transc, frases, saida, fps=30):
    ws = palavras(transc, fps)
    cont = []
    for l in open(frases):
        l = l.strip()
        if not l: continue
        if ' #' in l: f, n = l.rsplit(' #', 1); cont.append((f.strip(), int(n)))
        else: cont.append((l, len(l.replace(' / ', ' ').split())))
    tot = sum(n for _, n in cont)
    if tot != len(ws): raise SystemExit(f"nº de palavras não bate: legendas {tot} x narração {len(ws)} (ajuste #n)")
    tc = lambda t: f"{int(t//3600):02d}:{int(t//60%60):02d}:{int(t%60):02d},{int(round(t*1000))%1000:03d}"
    out, i = [], 0
    for k, (f, n) in enumerate(cont):
        st, en = ws[i][1], ws[i + n - 1][2]; i += n
        if k + 1 < len(cont): en = max(en, min(st + 0.8, ws[i][1]))
        out.append(f"{k + 1}\n{tc(st)} --> {tc(en)}\n{f.replace(' / ', chr(10))}\n")
    open(saida, 'w').write('\n'.join(out)); print(len(out), 'legendas ->', saida)


def sem_legenda(srt_ent, srt_sai, intervalos):
    """Tira do SRT as legendas que encostam nos intervalos [(ini, fim), ...] em que há palavra-chave na tela."""
    def s(tc): h, m, r = tc.split(':'); sec, ms = r.split(','); return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
    blocos = open(srt_ent).read().strip().split('\n\n'); out = []
    for b in blocos:
        l = b.split('\n'); a, z = [s(x.strip()) for x in l[1].split('-->')]
        if any(a < fim and z > ini for ini, fim in intervalos): continue
        out.append(f"{len(out)+1}\n{l[1]}\n" + '\n'.join(l[2:]) + '\n')
    open(srt_sai, 'w').write('\n'.join(out)); print(len(blocos) - len(out), 'legendas tiradas ->', srt_sai)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == 'rascunho': rascunho(a[1], a[2], opt('--cliente'), int(opt('--max', 25)))
    elif a[0] == 'sincronizar': sincronizar(a[1], a[2], a[3])
    else: print(__doc__)
