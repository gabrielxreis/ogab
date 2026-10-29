"""SFX COMPLETO a partir do plano do motion (regra do usuário, 29/10/2026: "os sfx têm que ser completos sempre").
Nada de "um whoosh por corte + um som por cena": TODO movimento que o preset anima ganha som, pelo próprio plano.

  python3 sfx_plano.py <preset> <plano.json> <saida plano_sfx.txt> --lib <pasta de sfx> [--ofs 5.38] [--acrescentar]

preset: poster | colagem | mimic | grafico. --ofs: segundo da timeline em que esse motion começa (vídeo em partes).
--acrescentar: soma ao plano_sfx.txt que já existe (outra parte do mesmo vídeo). A saída é o formato do
`resolve_lib.colocar_plano_sfx` ('T.TTs A3 nome -NNdB D.Ds: o que acompanha'); colocar com trilhas=range(3, 13).

O que ganha som (pela linguagem de cada preset):
  poster  corte (whoosh) + quadradinhos (blip) + forma (swell) + foto (som do objeto pelo nome do arquivo, senão
          whoosh) + HUD (blip) + gigante (swell baixo) + CADA palavra que acende (blip; a linha grande, click)
          + CADA vela que nasce (tique) + toque no celular + logo do fecho (impacto)
  colagem folha nova (papel + whoosh) + forma, retalho de jornal e foto batendo (papel) + cada etiqueta (cartão)
  mimic   troca de telão (whoosh) + placa descendo (madeira) + boneco entrando (passos/swell) + cada ação
          (pose = whoosh curto, cai = queda, anda = passos) + adereço pelo tipo (saco cai = moedas, estouro = pop,
          chuva = cédulas, relógio, gráfico = tiques, quadro = caneta, calendário = papel, mesa = toque) + cortina
  grafico entrada (swell) + resultado assentando (impacto) + legenda dos itens (blip)
Os nomes dos sons são os da biblioteca do cliente (`--lib`); falta de arquivo = aviso e o som mais próximo (SUBST).
"""
import json, os, re, sys

SONS = {   # papel -> (arquivo, dB, duração s)
    "corte": ("whoosh_cena", -16, 0.9), "corte2": ("whoosh_curto", -16, 0.6), "quadradinho": ("blip", -26, 0.25),
    "forma": ("crescer", -22, 1.0), "foto": ("whoosh_curto", -20, 0.5), "hud": ("blip", -24, 0.3),
    "gigante": ("whoosh_curto", -24, 0.6), "palavra": ("blip", -26, 0.25), "palavra_forte": ("click", -17, 0.3),
    "vela": ("vela_grafico", -19, 0.19), "toque": ("toque_tela", -12, 0.5), "fecho": ("impacto", -12, 1.6),
    "folha": ("papel", -15, 0.8), "bate": ("papel", -13, 0.8), "retalho": ("papel", -20, 0.6), "etiqueta": ("cartao", -14, 0.3),
    "telao": ("whoosh_cena", -17, 0.9), "placa": ("placa_madeira", -15, 1.0), "entra": ("passos", -21, 0.8),
    "surge": ("whoosh_curto", -22, 0.5), "pose": ("whoosh_curto", -23, 0.4), "cai": ("bola_queda", -14, 1.0),
    "anda": ("passos", -18, 0.9), "cortina": ("whoosh_cena", -14, 1.2), "estouro": ("balao", -12, 1.0),
    "entrada": ("crescer", -16, 1.2), "assenta": ("impacto", -16, 1.2),
}
ADERECO = {"saco": ("moedas", -14, 1.2), "nota": ("cedula", -16, 0.8), "chuva": ("cedula", -14, 2.0), "relogio": ("relogio", -14, 2.0),
           "quadro": ("risco_caneta", -14, 0.6), "calendario": ("papel", -14, 0.8), "seta": ("whoosh_curto", -18, 0.5),
           "mesa": ("toque_tela", -14, 0.5), "trono": ("impacto", -18, 1.0), "urna": ("click", -14, 0.3), "pomba": ("whoosh_curto", -20, 0.6),
           "pedra": ("bola_queda", -16, 0.8), "balao": ("blip", -22, 0.3), "grafico": ("vela_grafico", -18, 0.19)}
FOTO = [(r"calend", ("papel", -14, 0.8)), (r"dard|alvo", ("dardo", -12, 1.0)), (r"despert|relog", ("relogio", -14, 1.6)),
        (r"mouse|clique", ("click", -12, 0.3)), (r"cadeado|cofre", ("cofre", -12, 0.7)), (r"ficha|dado", ("dado", -13, 1.2)),
        (r"moeda", ("moedas", -14, 1.2)), (r"calcul", ("risco_caneta", -14, 0.6)), (r"aberto|placa", ("placa_madeira", -14, 1.0)),
        (r"dono|saindo|atrasad", ("passos", -18, 1.2)), (r"stress|vendad", ("impacto", -18, 1.2)), (r"lupa", ("crescer", -18, 0.8)),
        (r"notebook|laptop", ("toque_tela", -14, 0.4)), (r"microfone", ("click", -16, 0.3)), (r"semaforo", ("blip", -16, 0.4)),
        (r"global|logo", ("impacto", -12, 1.6))]
SUBST = {"cartao": "papel", "crescer": "whoosh_curto", "blip": "click", "passos": "whoosh_curto", "cofre": "click",
         "risco_caneta": "papel", "placa_madeira": "impacto", "bola_queda": "impacto", "balao": "impacto", "cedula": "papel",
         "moedas": "impacto", "dado": "click", "dardo": "impacto", "relogio": "click", "vela_grafico": "click", "toque_tela": "click"}


class Plano:
    def __init__(self, lib, ofs):
        self.lib, self.ofs, self.ev, self.faltou = lib, ofs, [], set()

    def som(self, t, papel_ou_trio, nota, dmax=None):
        nome, db, dur = SONS[papel_ou_trio] if isinstance(papel_ou_trio, str) else papel_ou_trio
        while not os.path.exists(os.path.join(self.lib, nome + ".wav")) and nome in SUBST:
            self.faltou.add(nome); nome = SUBST[nome]
        if not os.path.exists(os.path.join(self.lib, nome + ".wav")):
            self.faltou.add(nome); return
        if dmax: dur = min(dur, dmax)
        self.ev.append((round(self.ofs + t, 2), nome, db, dur, nota))

    def linhas(self):
        out, ult = [], {}
        for t, nome, db, dur, nota in sorted(self.ev):
            if t < 0 or t - ult.get(nome, -9) < 0.09: continue   # mesmo som colado no anterior soa como um só
            ult[nome] = t; out.append(f"{t:.2f}s A3 {nome} {db}dB {dur}s: {nota}")
        return out


def poster(P, plano):
    t = 0.0
    for i, c in enumerate(plano["cenas"]):
        S = c.get("de", t) if "de" in c else t; t = S + c["dur"]
        if i: P.som(S - 0.04, "corte" if i % 2 else "corte2", f"corte para a cena {i + 1}"); P.som(S + 0.03, "quadradinho", "quadradinhos do corte")
        fo = c.get("foto") or {}
        if c.get("fecho") or re.search(r"global|logo", fo.get("arquivo", ""), re.I):
            P.som(S, "fecho", "logo do fecho"); continue
        if c.get("forma"): P.som(S, "forma", f"forma {c['forma'].get('tipo')} entra")
        if fo:
            trio = next((v for k, v in FOTO if re.search(k, os.path.basename(fo["arquivo"]), re.I)), None)
            P.som(S + 0.05, trio or "foto", f"foto {os.path.basename(fo['arquivo'])} entra")
        if c.get("hud"): P.som(S + 0.05, "hud", "HUD entra")
        if c.get("gigante"): P.som(S, "gigante", f"palavra gigante {c['gigante'].get('texto')}")
        tx = c.get("texto") or {}; linhas = tx.get("linhas") or []
        palavras = [(li, w) for li, l in enumerate(linhas) for w in l.split()]
        grande = tx.get("grande", len(linhas) - 1)
        tempos = tx.get("tempos") or [tx.get("em", .1) + k * (tx.get("ate", 1) - tx.get("em", .1)) / max(1, len(palavras)) for k in range(len(palavras))]
        for (li, w), q in zip(palavras, tempos):
            if q is not None and q < c["dur"]: P.som(S + q, "palavra_forte" if li == grande else "palavra", f"'{w}' acende")
        v = c.get("velas")
        if v:
            n = v.get("n", 12); em = v.get("em", .3); ate = v.get("ate", c["dur"] * .75); passo = (ate - em) / n
            for k in range(n): P.som(S + em + k * passo, "vela", f"vela {k + 1} nasce")
        cel = c.get("celular")
        if cel: P.som(S + cel.get("em", 1.4), "toque", "dedo toca em Seguir")


def colagem(P, plano):
    t = 0.0
    for i, c in enumerate(plano["cenas"]):
        S = t; t += c["dur"]
        if i: P.som(S - 0.05, "folha", f"folha nova da cena {i + 1}"); P.som(S - 0.08, "corte2", "folha deitando")
        f = c.get("forma")
        if f: P.som(S + f.get("em", .1), "retalho", f"{f.get('tipo')} colado")
        for j in c.get("jornal", []): P.som(S + j.get("em", .05), "retalho", "retalho de jornal")
        for fo in c.get("fotos", []):
            P.som(S + fo.get("em", .25), "bate", f"foto {os.path.basename(fo['arquivo'])} bate na página")
            trio = next((v for k, v in FOTO if re.search(k, os.path.basename(fo["arquivo"]), re.I)), None)
            if trio: P.som(S + fo.get("em", .25) + 0.12, trio, f"som do objeto {os.path.basename(fo['arquivo'])}")
        for r in c.get("rotulos", []):
            for k, _ in enumerate(str(r["texto"]).split("|")): P.som(S + r.get("em", .6) + k * 0.17, "etiqueta", f"etiqueta '{r['texto']}'")


def mimic(P, plano):
    t = 0.0
    for i, c in enumerate(plano["cenas"]):
        S = t; t += c["dur"]
        if i: P.som(S - 0.3, "telao", f"telão da cena {i + 1} desce")
        if c.get("cortina") == "fecha": P.som(S, "cortina", "cortina fecha")
        for pl in c.get("placas", []): P.som(S + (pl.get("em") if pl.get("em") is not None else .1), "placa", f"placa '{pl.get('texto')}' desce")
        for k, b in enumerate(c.get("bonecos", [])):
            t0 = S + (b.get("em") if b.get("em") is not None else .12 + k * .1)
            P.som(t0, "entra" if b.get("entra") in ("esquerda", "direita") else "surge", f"{b.get('personagem', 'povo')} entra")
            for a in b.get("acoes", []):
                q = S + a.get("em", 0)
                if a.get("cai"): P.som(q + 0.4, "cai", "boneco cai")
                elif a.get("anda") is not None: P.som(q, "anda", "boneco anda")
                elif a.get("pose"): P.som(q, "pose", f"pose {a['pose']}")
        for a in c.get("aderecos", []):
            tipo = a.get("tipo"); q = S + (a.get("em") if a.get("em") is not None else .15)
            if tipo in ("sol", "lua", "nuvem", "estrela"): P.som(q, "quadradinho", f"{tipo} aparece"); continue
            if tipo == "grafico":
                for k in range(9): P.som(q + 0.25 + k * a.get("dur_velas", 1.6) / 9, ADERECO["grafico"], "vela do quadro nasce")
                continue
            if tipo in ADERECO: P.som(q + (0.5 if a.get("cai") else 0), ADERECO[tipo], f"{tipo} {'cai' if a.get('cai') else 'entra'}")
            if a.get("estoura_em") is not None: P.som(S + a["estoura_em"], "estouro", f"{tipo} estoura")
            if a.get("some_em") is not None: P.som(S + a["some_em"], "surge", f"{tipo} some")
            if tipo == "relogio" and a.get("check") is not None: P.som(q + a["check"], "palavra_forte", "selo de confirmado")


def grafico(P, plano):
    P.som(0.05, "entrada", "gráfico entra"); P.som(0.9, "quadradinho", "itens aparecem"); P.som(1.8, "assenta", "valor assenta")


def main():
    a = sys.argv[1:]
    if len(a) < 3 or "--lib" not in a: raise SystemExit(__doc__)
    preset, plano, saida = a[0], json.load(open(a[1])), a[2]
    P = Plano(a[a.index("--lib") + 1], float(a[a.index("--ofs") + 1]) if "--ofs" in a else 0.0)
    {"poster": poster, "colagem": colagem, "mimic": mimic, "grafico": grafico}[preset](P, plano)
    L = P.linhas()
    antes = open(saida).read().splitlines() if "--acrescentar" in a and os.path.exists(saida) else []
    open(saida, "w").write("\n".join(antes + L) + "\n")
    if P.faltou: print("AVISO: sem estes sons na biblioteca (troquei pelo mais próximo):", ", ".join(sorted(P.faltou)))
    print(f"{len(L)} sons de movimento -> {saida}")


if __name__ == "__main__":
    main()
