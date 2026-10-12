"""Legendas: rascunho automático por frase + sincronização de frases escritas à mão com a transcrição.

Comandos:
  python3 legendas.py rascunho  transcricao.json frases.txt [--cliente pasta_cliente] [--max 25]
      -> gera um frases.txt (uma legenda por linha, UMA linha cada, cortada em ponto natural),
         já com as correções de grafia do cliente. Revise/ajuste à mão se precisar.
  python3 legendas.py sincronizar transcricao.json frases.txt saida.srt
      -> casa cada legenda com o tempo das palavras faladas e grava o SRT.
  python3 legendas.py reflow transcricao.json frases.txt [--cliente pasta]  (reparte para passar na métrica)
  python3 legendas.py metrica saida.srt [--max 25]
      -> métrica obrigatória: uma linha, tamanho, palavra fraca no fim, duração mínima, número separado. Tem que dar 0 problema.

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
    equilibrar(saida); equilibrar(saida)   # 2ª passada pega o que a cadeia deixou


def equilibrar(srt, min_s=0.7, max_shift=0.35):
    """Fala rápida deixa legenda curta demais. Empresta tempo das vizinhas (no máximo max_shift s de deslocamento
    em relação à fala e sem a vizinha ficar abaixo de min_s). Reescreve o SRT."""
    def s(tc): h, m, r = tc.split(':'); sec, ms = r.split(','); return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
    tc = lambda x: f"{int(x//3600):02d}:{int(x//60%60):02d}:{int(x%60):02d},{int(round(x*1000))%1000:03d}"
    bl = [b.split('\n') for b in open(srt).read().strip().split('\n\n')]
    T = [[s(x.strip()) for x in b[1].split('-->')] for b in bl]; orig = [list(x) for x in T]
    for k in range(len(T)):
        falta = min_s - (T[k][1] - T[k][0])
        if falta <= 0: continue
        if k + 1 < len(T):                       # empurra o início da próxima, em cadeia (até 3 vizinhas)
            for _ in range(2):
                folga = min(T[k + 1][1] - T[k + 1][0] - min_s, max_shift - (T[k + 1][0] - orig[k + 1][0]), falta)
                if folga > 0: T[k][1] += folga; T[k + 1][0] += folga; falta -= folga
                if falta <= 0: break
                for m in range(k + 1, min(k + 3, len(T) - 1)):   # a vizinha repõe empurrando a seguinte
                    sobra = min(T[m + 1][1] - T[m + 1][0] - min_s, max_shift - (T[m + 1][0] - orig[m + 1][0]), falta)
                    if sobra > 0: T[m][1] += sobra; T[m + 1][0] += sobra
        elif falta > 0: T[k][1] += falta; falta = 0   # última: estende o fim
        if falta > 0 and k == 0:                 # primeira: começa um pouco antes da fala
            ant = min(falta, max_shift, T[0][0]); T[0][0] -= ant; falta -= ant
        if falta > 0 and k > 0:                  # adianta o início dela, encurtando a anterior
            folga = min(T[k - 1][1] - T[k - 1][0] - min_s, max_shift - (orig[k][0] - T[k][0]), falta)
            if folga > 0: T[k - 1][1] -= folga; T[k][0] -= folga
    for k in range(1, len(T)):                   # nunca sobrepor (o DaVinci recusa SRT sobreposto)
        if T[k][0] < T[k - 1][1]: T[k - 1][1] = T[k][0]
    out = [f"{b[0]}\n{tc(T[k][0])} --> {tc(T[k][1])}\n" + '\n'.join(b[2:]) + '\n' for k, b in enumerate(bl)]
    open(srt, 'w').write('\n'.join(out))


def sem_legenda(srt_ent, srt_sai, intervalos):
    """Tira do SRT as legendas que encostam nos intervalos [(ini, fim), ...] em que há palavra-chave na tela."""
    def s(tc): h, m, r = tc.split(':'); sec, ms = r.split(','); return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
    blocos = open(srt_ent).read().strip().split('\n\n'); out = []
    for b in blocos:
        l = b.split('\n'); a, z = [s(x.strip()) for x in l[1].split('-->')]
        if any(a < fim and z > ini for ini, fim in intervalos): continue
        out.append(f"{len(out)+1}\n{l[1]}\n" + '\n'.join(l[2:]) + '\n')
    open(srt_sai, 'w').write('\n'.join(out)); print(len(blocos) - len(out), 'legendas tiradas ->', srt_sai)


JUNTOS = {("estados", "unidos"), ("final", "action"), ("action", "date"), ("green", "card"), ("visa", "bulletin"), ("priority", "date"),
          ("jogar", "fora")}
# além das FRACAS, palavras que pedem a seguinte (determinante, adjetivo antes do nome, pronome antes do verbo)
NAO_FECHA = {'essa', 'esse', 'esta', 'este', 'essas', 'esses', 'estas', 'estes', 'aquele', 'aquela', 'aqueles', 'aquelas',
             'novo', 'nova', 'novos', 'novas', 'boa', 'bom', 'grande', 'minha', 'meu', 'seus', 'suas', 'nossa', 'nosso',
             'era', 'como', 'quanto', 'qual', 'quais', 'eu', 'ele', 'ela', 'próprio', 'própria', 'cada', 'outro', 'outra'}


def reflow(transc, saida, cliente=None, maxc=25, min_s=0.7, fps=30):
    """Reparte cada frase (de ponto a ponto) em legendas que passam na métrica: até maxc caracteres, sem palavra
    fraca no fim, sem separar número de 'de/anos' nem nomes compostos, e com duração >= min_s sempre que possível.
    Programação dinâmica por frase: minimiza (legendas curtas demais, cortes fora de vírgula, nº de legendas)."""
    ws = aplicar(palavras(transc, fps), correcoes(cliente))
    frases, cur = [], []
    for w in ws:
        cur.append(w)
        if re.search(r'[.?!]$', w[0]): frases.append(cur); cur = []
    if cur: frases.append(cur)
    linhas = []
    for fi, fr in enumerate(frases):
        prox_ini = frases[fi + 1][0][1] if fi + 1 < len(frases) else fr[-1][2] + 1.0
        n = len(fr); INF = (10 ** 9, 0, 0, 0)
        best = [INF] * (n + 1); best[0] = (0, 0, 0, 0); corte = [0] * (n + 1)
        for j in range(1, n + 1):
            for i in range(j - 1, -1, -1):
                txt = ' '.join(w[0] for w in fr[i:j])
                if len(txt) > maxc: break
                if best[i] == INF: continue
                ult = re.sub(r'[,;:]$', '', fr[j - 1][0]).lower(); prox = fr[j][0].lower() if j < n else ''
                if j < n:
                    ant = fr[j - 2][0].lower() if j >= 2 else ''
                    if fraca(ult) and not re.fullmatch(r'[\d.,º]+', ult) and not (ult == 'que' and ant == 'por'): continue
                    if re.sub(r'[,.]$', '', prox) == 'de' and j + 1 < n and re.match(r'\d', fr[j + 1][0]): continue   # '15 de maio | de 2024'
                    if re.fullmatch(r'[\d.,º]+', ult) and re.sub(r'[,.]$', '', prox) in ('de', 'anos', 'mil', 'milhões'): continue
                    if (ult, re.sub(r'[,.]$', '', prox)) in JUNTOS: continue
                fim_tela = fr[j][1] if j < n else min(max(fr[j - 1][2], fr[i][1] + 0.8), prox_ini)
                curta = 1 if fim_tela - fr[i][1] < min_s - 0.02 else 0
                fecha_mal = 1 if (j < n and ult in NAO_FECHA and not fr[j - 1][0].endswith(',')) else 0
                sem_virg = 0 if (j == n or fr[j - 1][0].endswith(',')) else 1
                c = (best[i][0] + curta, best[i][1] + fecha_mal, best[i][2] + sem_virg, best[i][3] + 1)
                if c < best[j]: best[j] = c; corte[j] = i
        j, pedacos = n, []
        while j > 0: i = corte[j]; pedacos.append(fr[i:j]); j = i
        linhas += reversed(pedacos)
    with open(saida, 'w') as f:
        for c in linhas:
            txt = ' '.join(w[0] for w in c); nf = sum(w[3] for w in c)
            f.write(txt + (f' #{nf}' if nf != len(txt.split()) else '') + '\n')
    print(len(linhas), 'legendas (reflow) ->', saida)


def metrica(srt, maxc=25, min_s=0.7):
    """Métrica da legenda (regra do usuário): roda logo depois de gerar e tem que dar 0 problema.
    Confere: uma linha, até maxc caracteres, final sem palavra fraca (mesmo com vírgula), duração mínima
    e número/data cortado da legenda seguinte."""
    def s(tc): h, m, r = tc.split(':'); sec, ms = r.split(','); return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
    bl = [b.split('\n') for b in open(srt).read().strip().split('\n\n')]
    probs = []; ant_fim = 0
    for k, b in enumerate(bl):
        a, z = [s(x.strip()) for x in b[1].split('-->')]; txt = b[2:]; linha = ' '.join(txt); d = z - a
        tag = f"#{b[0]} [{linha}]"
        if len(txt) > 1: probs.append(f"{tag} mais de uma linha")
        if len(linha) > maxc: probs.append(f"{tag} {len(linha)} caracteres (máx {maxc})")
        ult = re.sub(r'[,;:]$', '', linha.split()[-1]) if linha.split() else ''
        pen = linha.split()[-2].lower() if len(linha.split()) > 1 else ''
        if k + 1 < len(bl) and not re.search(r'[.?!]$', linha) and fraca(ult) and not re.fullmatch(r'[\d.,º]+', ult) and not (ult.lower() == 'que' and pen == 'por') and not (ult.lower() == 'mais' and pen == 'que'):
            probs.append(f"{tag} termina em palavra fraca '{ult}'")
        if d < min_s - 0.02: probs.append(f"{tag} dura {d:.2f}s (mín {min_s})")
        if k and a < ant_fim - 0.001: probs.append(f"{tag} começa antes do fim da anterior (sobreposta)")
        ant_fim = z
        if k + 1 < len(bl):
            prox = bl[k + 1][2:]; p1 = prox[0].split()[0].lower() if prox and prox[0].split() else ''
            if re.search(r'\d$', linha) and p1 in ('de', 'anos', 'mil', 'milhões', '%'): probs.append(f"{tag} número separado de '{p1}'")
    for x in probs: print('PROBLEMA', x)
    print(f"{len(bl)} legendas, {len(probs)} problema(s) -> {'OK' if not probs else 'CORRIGIR antes de seguir'}")
    return probs


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == 'rascunho': rascunho(a[1], a[2], opt('--cliente'), int(opt('--max', 25)))
    elif a[0] == 'sincronizar': sincronizar(a[1], a[2], a[3])
    elif a[0] == 'reflow': reflow(a[1], a[2], opt('--cliente'), int(opt('--max', 25)))
    elif a[0] == 'metrica': sys.exit(1 if metrica(a[1], int(opt('--max', 25))) else 0)
    else: print(__doc__)


def picotado(srt, compostos=()):
    """Frase/palavra picotada (o que a métrica não pega, regra do usuário 12/10/2026). Devolve a lista de problemas:
    - legenda termina em determinante/possessivo/pronome que pede a palavra seguinte ("os seus / limites.");
    - palavra órfã: a seguinte é UMA palavra só fechando a frase ("ganhou / ontem.") e a atual não terminou frase;
    - termo composto partido entre duas legendas (compostos + termos com espaço do pronuncia.json do cliente)."""
    bl = [b.split('\n') for b in open(srt).read().strip().split('\n\n')]
    txt = [' '.join(b[2:]).strip() for b in bl]; probs = []
    norm = lambda s: re.sub(r'[^\wà-ú ]', '', s.lower())
    base = {'gestão de risco', 'centros financeiros', 'estados unidos', 'nova york', 'wall street', 'world trade center'} | {c.lower() for c in compostos}
    for k in range(len(txt) - 1):
        a, b = txt[k], txt[k + 1]; ult = norm(a.split()[-1]) if a.split() else ''
        fecha = bool(re.search(r'[.?!,;:]$', a))
        if not fecha and ult in NAO_FECHA: probs.append(f"#{k + 1} [{a}] termina em '{ult}' (pede a palavra seguinte)")
        if not re.search(r'[.?!]$', a) and len(b.split()) == 1 and re.search(r'[.?!]$', b) and k + 1 < len(txt) - 1:
            probs.append(f"#{k + 2} [{b}] palavra órfã depois de [{a}]")
        junta = norm(a + ' ' + b)
        for c in base:
            if c in junta and c not in norm(a) and c not in norm(b) and len(c.split()) > 1:
                probs.append(f"#{k + 1}-{k + 2} termo '{c}' partido: [{a}] / [{b}]")
    return probs
