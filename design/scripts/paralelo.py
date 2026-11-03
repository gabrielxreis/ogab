"""Produção de design do Gab em paralelo com trava de segurança (pedido do usuário, 30/10/2026: "cria o sistema de fork para
ir mais rápido, tipo o que o Gab faz"). Cada frente (marca, textos, imagens, uma página por agente...) roda ao mesmo
tempo que as outras, mas só quando o que ela precisa já existe, sem gastar crédito duas vezes, sem dois agentes no
mesmo navegador, com o Photoshop só no Gab principal e cada frente escrevendo só na sua pasta.
Estado em <pasta da peça>/paralelo.json (mesmo formato do Gab).

  python3 paralelo.py liberar <pasta> briefing|mapa|motor|montado   (SÓ o Gab principal, depois do ok do usuário)
  python3 paralelo.py pode <pasta>                       (o que já pode começar agora, o que espera e por quê)
  python3 paralelo.py iniciar <pasta> <frente>[:<n>] [--quem <agente>] [--refazer "motivo"]
  python3 paralelo.py concluir <pasta> <frente>[:<n>] --saida <arq> [--saida <arq> ...]
  python3 paralelo.py falhou <pasta> <frente>[:<n>] --erro "motivo curto"
  python3 paralelo.py dispensar <pasta> <frente>[:<n>] --motivo "..."   (tirar da peça, SÓ com o ok do usuário)
  python3 paralelo.py recurso <pasta> pegar|soltar navegador|photoshop --quem <agente>
  python3 paralelo.py status <pasta>
  python3 paralelo.py juntar <pasta>                     (OBRIGATÓRIO antes de montar: sai 0 = PODE_MONTAR)
  python3 paralelo.py painel <pasta da peça|do lote> [...] (painel ao vivo no Terminal; OBRIGATÓRIO aberto para `iniciar`)

Frentes: marca, textos, imagens, pagina:<n> (uma página do carrossel, um post da série ou uma versão de gancho por
agente), legenda, motion. Sai 1 com o motivo quando a frente não pode.
"""
import contextlib, json, os, shutil, subprocess, sys, time

# depende: portões (liberar) e/ou frentes concluídas; pasta: a ÚNICA onde a frente escreve; credito: gasta crédito;
# recurso: o que só um agente usa por vez (navegador = o Chrome do usuário). O Photoshop nunca é de uma frente.
FRENTES = {
    "marca":   {"depende": ["briefing"], "pasta": "marca"},            # identidade do site, paleta medida, fonte faltando
    "textos":  {"depende": ["mapa"], "pasta": "textos"},               # copy de cada página (+ humanizer)
    "imagens": {"depende": ["mapa", "motor"], "pasta": "imagens", "credito": True},   # IA conectada, banco, upscale
    "pagina":  {"depende": ["mapa", "motor", "textos"], "pasta": "paginas/p{n}"},     # arte.jsx, prompt ou plano do Canva
    "legenda": {"depende": ["textos"], "pasta": "legenda"},           # legenda do post, hashtags
    "motion":  {"depende": ["montado"], "pasta": "motion"},            # animar a peça montada (ferramentas do Gab)
}
PORTOES = ("briefing", "mapa", "motor", "montado")
MAX_AGENTES = 3          # frentes rodando ao mesmo tempo (cada agente custa tokens)
TRAVADA_MIN = 30         # rodando há mais que isso sem concluir = travada (conferir antes de esperar mais)
MIDIA = (".mp4", ".mov", ".webm")
IMAGEM = (".png", ".jpg", ".jpeg", ".webp", ".psd")


def arq(pasta): return os.path.join(pasta, "paralelo.json")


@contextlib.contextmanager
def _trava(caminho):
    """Trava de arquivo entre processos (Mac/Linux: fcntl; Windows: msvcrt)."""
    with open(caminho, "a+") as lk:
        if os.name == "nt":
            import msvcrt
            lk.seek(0)
            while True:
                try:
                    msvcrt.locking(lk.fileno(), msvcrt.LK_LOCK, 1); break
                except OSError:
                    time.sleep(0.1)
            try:
                yield
            finally:
                lk.seek(0); msvcrt.locking(lk.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lk, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lk, fcntl.LOCK_UN)


@contextlib.contextmanager
def estado(pasta, gravar=True):
    """Lê e grava o paralelo.json com trava: vários agentes chamando ao mesmo tempo não se atropelam."""
    os.makedirs(pasta, exist_ok=True)
    with _trava(os.path.join(pasta, ".paralelo.lock")):
        try:
            st = json.load(open(arq(pasta), encoding="utf-8"))
        except FileNotFoundError:
            st = {}
        st.setdefault("portoes", {}); st.setdefault("frentes", {}); st.setdefault("recursos", {})
        yield st
        if gravar:
            tmp = arq(pasta) + ".tmp"
            json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            os.replace(tmp, arq(pasta))   # gravação atômica: nunca fica um JSON pela metade


def tipo(nome): return nome.split(":")[0]


def faltando(st, nome):
    f = []
    for d in FRENTES[tipo(nome)]["depende"]:
        if d in PORTOES:
            if not st["portoes"].get(d): f.append(f"portão '{d}' não liberado")
        elif st["frentes"].get(d, {}).get("estado") != "concluida":
            f.append(f"frente '{d}' não concluída")
    return f


def pasta_da(nome):
    n = nome.split(":")[1] if ":" in nome else ""
    return FRENTES[tipo(nome)]["pasta"].format(n=n)


def minutos(t): return (time.time() - t) / 60


def validar_saida(p):
    """Saída que conta como pronta: existe, não está vazia; imagem abre; vídeo tem duração."""
    if not os.path.isfile(p): return "não existe"
    if os.path.getsize(p) == 0: return "arquivo vazio"
    low = p.lower()
    if low.endswith(IMAGEM) and not low.endswith(".psd"):
        try:
            from PIL import Image
            with Image.open(p) as im: im.verify()
        except ImportError:
            pass
        except Exception:
            return "imagem não abre (corrompida ou baixando ainda)"
    if low.endswith(MIDIA) and shutil.which("ffprobe"):
        o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                           capture_output=True, text=True)
        try:
            if float(o.stdout.strip()) < 0.3: return "duração quase zero"
        except ValueError:
            return "ffprobe não lê (arquivo corrompido ou baixando ainda)"
    return None


def cmd_liberar(pasta, portao):
    if portao not in PORTOES: raise SystemExit(f"portão desconhecido: {portao} (use {', '.join(PORTOES)})")
    with estado(pasta) as st:
        st["portoes"][portao] = time.strftime("%Y-%m-%d %H:%M")
    print(f"LIBERADO {portao}")


def cmd_pode(pasta):
    with estado(pasta, gravar=False) as st:
        for t in FRENTES:
            if t == "pagina":
                f = faltando(st, "pagina:1")
                print(f"  pagina:<n> {'PODE (um agente por página/post/versão)' if not f else 'espera: ' + '; '.join(f)}")
                continue
            e = st["frentes"].get(t, {}).get("estado")
            f = faltando(st, t)
            print(f"  {t:<10} " + (e.upper() if e else ("PODE" if not f else "espera: " + "; ".join(f))))


def cmd_iniciar(pasta, nome, quem, refazer):
    if tipo(nome) not in FRENTES: raise SystemExit(f"frente desconhecida: {nome} (use {', '.join(FRENTES)})")
    import painel_paralelo   # painel ao vivo obrigatório (igual ao Gab); ORICK_SEM_PAINEL=1 só sem painel Terminal
    if not painel_paralelo.vivo(pasta) and os.environ.get("ORICK_SEM_PAINEL") != "1":
        raise SystemExit("PAINEL_FECHADO: abra antes o painel ao vivo no painel Terminal (run_in_terminal, aba "
                         "\"Progresso: <peça>\"): python3 SKILL_DIR/scripts/paralelo.py painel <pasta da peça ou do lote>, "
                         "mande o link [Progresso: <peça>](#terminal/<tab_id>) na conversa e tente de novo. "
                         "Sem painel Terminal (outro app): ORICK_SEM_PAINEL=1 e dizer onde acompanhar.")
    if tipo(nome) == "pagina" and ":" not in nome: raise SystemExit("pagina precisa do número: pagina:1, pagina:2...")
    with estado(pasta) as st:
        atual = st["frentes"].get(nome)
        if atual and atual["estado"] == "rodando":
            raise SystemExit(f"NAO: {nome} já está rodando ({atual.get('quem')}, há {minutos(atual['inicio']):.0f} min)")
        if atual and atual["estado"] in ("concluida", "dispensada") and not refazer:
            raise SystemExit(f"NAO: {nome} já foi concluída. Refazer só com --refazer \"motivo\""
                             + (" e o OK do usuário (gasta crédito de novo)" if FRENTES[tipo(nome)].get("credito") else ""))
        f = faltando(st, nome)
        if f: raise SystemExit(f"NAO: {nome} espera: " + "; ".join(f))
        rodando = [k for k, v in st["frentes"].items() if v["estado"] == "rodando"]
        if len(rodando) >= MAX_AGENTES:
            raise SystemExit(f"NAO: já tem {len(rodando)} frentes rodando ({', '.join(rodando)}); máximo {MAX_AGENTES}")
        minha = pasta_da(nome)
        for k in rodando:   # pasta exclusiva: nenhuma frente escreve dentro da pasta de outra
            p = pasta_da(k)
            if minha == p or minha.startswith(p + "/") or p.startswith(minha + "/"):
                raise SystemExit(f"NAO: a pasta {minha} cruza com a de {k} ({p})")
        os.makedirs(os.path.join(pasta, minha), exist_ok=True)
        for k, v in st["frentes"].items():   # refez uma base: quem foi feito em cima dela fica desatualizado
            if v["estado"] == "concluida" and nome in FRENTES[tipo(k)]["depende"]:
                v["estado"] = "desatualizada"; v["erro"] = f"{nome} foi refeita depois"
        st["frentes"][nome] = {"estado": "rodando", "quem": quem or "?", "inicio": time.time(), "pasta": minha,
                               "refazer": refazer, "saidas": {}}
    print(f"INICIADA {nome} -> escreve SÓ em {minha}/"
          + ("; se for usar o Chrome (ChatGPT, Gemini, site de IA): `recurso pegar navegador` antes e soltar logo depois")
          + ("; GASTA CRÉDITO: custo e saldo aprovados pelo usuário antes" if FRENTES[tipo(nome)].get("credito") else "")
          + "; NUNCA abrir o Photoshop (é do Gab principal)")


def cmd_concluir(pasta, nome, saidas):
    if not saidas: raise SystemExit("concluir precisa de --saida <arquivo> (o que a frente entregou)")
    with estado(pasta) as st:
        fr = st["frentes"].get(nome)
        if not fr or fr["estado"] != "rodando": raise SystemExit(f"NAO: {nome} não está rodando")
        ruins = []
        for s in saidas:
            p = s if os.path.isabs(s) else os.path.join(pasta, s)
            rel = os.path.relpath(p, pasta).replace("\\", "/")
            if not (rel == fr["pasta"] or rel.startswith(fr["pasta"] + "/")):
                ruins.append(f"{rel}: fora da pasta da frente ({fr['pasta']}/)"); continue
            erro = validar_saida(p)
            if erro: ruins.append(f"{rel}: {erro}")
            else: fr["saidas"][rel] = os.path.getsize(p)
        if ruins:
            fr["saidas"] = {}
            raise SystemExit("NAO concluída (continua rodando):\n  " + "\n  ".join(ruins))
        fr["estado"] = "concluida"; fr["fim"] = time.time()
    soltar_da_frente(pasta, nome)
    print(f"CONCLUIDA {nome} ({len(saidas)} arquivo(s) conferido(s))")


def cmd_falhou(pasta, nome, erro):
    with estado(pasta) as st:
        fr = st["frentes"].get(nome)
        if not fr: raise SystemExit(f"NAO: {nome} nunca foi iniciada")
        fr["estado"] = "falhou"; fr["erro"] = erro; fr["fim"] = time.time()
    soltar_da_frente(pasta, nome)
    print(f"FALHOU {nome}: {erro} (o Gab principal decide: refazer, outra fonte ou seguir sem)")


def soltar_da_frente(pasta, nome):
    """Frente terminou (bem ou mal): solta o navegador SÓ se ainda está com o mesmo agente dela."""
    with estado(pasta) as st:
        dono = st["recursos"].get("navegador"); quem = st["frentes"][nome].get("quem")
        if dono and dono["quem"] == quem: st["recursos"].pop("navegador")


def cmd_dispensar(pasta, nome, motivo):
    if not motivo: raise SystemExit("dispensar precisa de --motivo (e do ok do usuário)")
    with estado(pasta) as st:
        fr = st["frentes"].get(nome)
        if not fr: raise SystemExit(f"NAO: {nome} nunca foi iniciada")
        if fr["estado"] == "rodando": raise SystemExit(f"NAO: {nome} ainda está rodando; parar o agente antes")
        fr["estado"] = "dispensada"; fr["erro"] = motivo; fr["saidas"] = {}
    soltar_da_frente(pasta, nome)
    print(f"DISPENSADA {nome}: {motivo}")


def cmd_recurso(pasta, acao, rec, quem, silencioso=False):
    if rec not in ("navegador", "photoshop"): raise SystemExit("recurso: navegador ou photoshop")
    with estado(pasta) as st:
        dono = st["recursos"].get(rec)
        if acao == "pegar":
            if rec == "photoshop" and quem != "principal":
                raise SystemExit("NAO: o Photoshop é só do Gab principal (uma página por vez), nunca de uma frente")
            if dono and dono["quem"] != quem and minutos(dono["desde"]) < TRAVADA_MIN:
                raise SystemExit(f"NAO: o {rec} está com {dono['quem']} há {minutos(dono['desde']):.0f} min; esperar soltar")
            st["recursos"][rec] = {"quem": quem, "desde": time.time()}
        else:
            st["recursos"].pop(rec, None)
    if not silencioso: print(f"{rec.upper()} {'com ' + quem if acao == 'pegar' else 'livre'}")


def problemas(st, pasta):
    p = []
    for k, v in st["frentes"].items():
        if v["estado"] == "rodando":
            p.append(f"{k} {'TRAVADA' if minutos(v['inicio']) > TRAVADA_MIN else 'rodando'} há {minutos(v['inicio']):.0f} min ({v.get('quem')})")
        elif v["estado"] == "falhou":
            p.append(f"{k} FALHOU: {v.get('erro')} (refazer com `iniciar`, ou `dispensar` com o ok do usuário)")
        elif v["estado"] == "desatualizada":
            p.append(f"{k} DESATUALIZADA: {v.get('erro')} (refazer com `iniciar --refazer`)")
        for rel, tam in v.get("saidas", {}).items():   # saída sumiu ou mudou depois de conferida
            f = os.path.join(pasta, rel)
            if not os.path.isfile(f): p.append(f"{k}: {rel} sumiu depois de concluída")
            elif os.path.getsize(f) != tam: p.append(f"{k}: {rel} mudou depois de concluída (conferir e concluir de novo)")
    return p


def cmd_status(pasta):
    with estado(pasta, gravar=False) as st:
        print("portões: " + ", ".join(f"{g} {'ok' if st['portoes'].get(g) else '-'}" for g in PORTOES))
        for k, v in sorted(st["frentes"].items()):
            extra = f" há {minutos(v['inicio']):.0f} min" if v["estado"] == "rodando" else ""
            print(f"  {k:<10} {v['estado']}{extra} ({v.get('quem')}) -> {', '.join(v.get('saidas', {})) or v['pasta'] + '/'}")
        for r, d in st["recursos"].items(): print(f"  {r}: com {d['quem']} há {minutos(d['desde']):.0f} min")
        for x in problemas(st, pasta): print("  ATENCAO " + x)


def cmd_juntar(pasta):
    with estado(pasta, gravar=False) as st:
        p = [x for x in problemas(st, pasta) if not x.startswith("motion")]   # motion vem depois da montagem
        if st["recursos"].get("navegador"): p.append(f"navegador ainda com {st['recursos']['navegador']['quem']}")
    if p:
        print("NAO_MONTAR: resolver antes de montar:\n  " + "\n  ".join(p)); return 1
    print("PODE_MONTAR: frentes concluídas e conferidas; só o Gab principal monta (Photoshop: uma página por vez; "
          "Canva/IA: na ordem das páginas). Depois de montar e conferir: `liberar <pasta> montado`.")
    return 0


def main(a):
    if len(a) < 2: raise SystemExit(__doc__)
    def opt(n, varios=False):
        v = [a[i + 1] for i, x in enumerate(a[:-1]) if x == n]
        return v if varios else (v[0] if v else None)
    c, pasta = a[0], a[1]
    if c == "painel":
        import painel_paralelo; return painel_paralelo.main(a[1:])
    if c == "liberar": cmd_liberar(pasta, a[2])
    elif c == "pode": cmd_pode(pasta)
    elif c == "iniciar": cmd_iniciar(pasta, a[2], opt("--quem"), opt("--refazer"))
    elif c == "concluir": cmd_concluir(pasta, a[2], opt("--saida", True))
    elif c == "falhou": cmd_falhou(pasta, a[2], opt("--erro") or "sem motivo")
    elif c == "dispensar": cmd_dispensar(pasta, a[2], opt("--motivo"))
    elif c == "recurso": cmd_recurso(pasta, a[2], a[3], opt("--quem"))
    elif c == "status": cmd_status(pasta)
    elif c == "juntar": return cmd_juntar(pasta)
    else: raise SystemExit(__doc__)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main(sys.argv[1:]))
