"""Preset MIMIC: teatrinho de bonecos de papel num palco de cortina azul. Cada frase vira uma PLACA de papel que
desce do urdimento pendurada em dois barbantes e balança até parar; bonecos de papel sobem do alçapão, mudam de
pose, andam e caem; o cenário pintado (telão) desce de cima na troca de cena. Linguagem estudada num Reels de
teatro bíblico de papel (27/10/2026); desenho e código nossos.

  python3 gerar.py plano.json <pasta_saida> [--tema padrao|<marca>|caminho/tema.json] [--render saida.mp4 --gif]

plano.json (x/y em px a partir do CENTRO da tela 540,960; vertical 1080x1920):
{ "w": 1080, "h": 1920, "fps": 30,
  "transcricao": "transcricao.json",          # opcional: aí todo "em" pode ser uma palavra da fala
  "cenas": [
    { "dur": 3.2,
      "cenario": "noite" | "jardim" | "por_do_sol" | "dia" | "palacio" | "creme" | "campo" | "deserto",
      "plateia": true,                        # cabeças da plateia na frente (bom no gancho)
      "cortina": "fecha",                     # só na última cena: a cortina fecha e a placa (CTA) desce na frente
      "auto": false,                          # tira a lua automática da noite/jardim
      "placas": [{"texto": "O que Davi faria|diante do gigante?", "ref": "1 Samuel 17", "em": 0.1,
                  "empilha": false, "y": 0, "x": 0, "rot": -2, "cor": "#hex", "tam1": 44, "tam2": 80}],
      "bonecos": [{"personagem": "povo|jesus|discipulo|soldado|rei|diabo|menino|pessoa|gigante",
                   "x": -200, "y": 0, "escala": 1, "olha": -1, "em": 0.15, "entra": "baixo|esquerda|direita",
                   "pose": "repouso", "sai": 2.4,
                   "roupa": "#hex", "pele": "#hex", "cabelo": "#hex", "calca": "#hex", "faixa": "#hex",
                   "manto": true, "barba": true, "cabelo_longo": true, "chapeu": "coroa|capacete|chifres",
                   "objeto": "espada|lanca|tocha|funda|cajado|cetro|tridente",
                   "acoes": [{"em": 1.2, "pose": "aponta"}, {"em": 0.8, "anda": 160, "dur": 0.9},
                             {"em": 2.0, "cai": "direita"}]}],
      "aderecos": [{"tipo": "sol|lua|nuvem|estrela|balao|trono|urna|pomba|pedra|saco|nota|chuva|relogio|grafico|quadro|calendario|seta|mesa", "x": 220, "y": 200, "em": 0.3,
                    "raio": 80, "escala": 1, "texto": "ira", "cor": "#hex", "fio_ate": [0, 260],
                    "pendurado": true, "de": [-500, -200], "ate": [500, -300], "dur": 1.6}] } ] }

  em negativo (ex.: -0.25) = já entra no meio do movimento no quadro 0 (bom no gancho).
  texto: "linha pequena|linha grande" (sem "|" vira só a linha grande, ex.: "2º"). ref: plaquinha da passagem
  pendurada embaixo. empilha: a placa nova entra NA FRENTE da anterior, um pouco abaixo (sem empilha, a anterior
  sobe antes). Poses: repouso, aponta, abertos, levanta, vitoria, acena, mao_alta, bencao, ora, triste, golpe, gira.
  Sol/lua/nuvem/estrela descem pendurados no barbante; trono/urna sobem do alçapão; balão flutua; pomba voa de->ate.
Trava de ritmo (regra "tela sempre mudando"): dentro de uma cena, nada pode ficar mais de 4,5 s sem algo novo entrar
(placa, boneco, ação ou adereço); a última cena (CTA) pode ir a 7 s. Passou disso o gerar.py recusa (CENA_PARADA).
"""
import json, os, shutil, sys, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "..", "scripts"))
from hf_preset import renderizar, args_render  # noqa: E402

CENARIOS = {"noite", "jardim", "por_do_sol", "dia", "palacio", "creme", "campo", "deserto"}
LIMITE, LIMITE_CTA = 4.5, 7.0


def _norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    return "".join(c for c in s if c.isalnum() and unicodedata.category(c) != "Mn")


def palavras(transcricao, base):
    arq = transcricao if os.path.isabs(transcricao) else os.path.join(base, transcricao)
    j = json.load(open(arq, encoding="utf-8"))
    return [{"t": w.get("text", w.get("word", "")), "s": float(w.get("start", 0))}
            for s in j.get("segments", []) for w in s.get("words", [])]


def gerar(plano, pasta, base, tema):
    plano = json.loads(json.dumps(plano))
    plano.setdefault("w", 1080); plano.setdefault("h", 1920); plano.setdefault("fps", 30)
    if (plano["w"], plano["h"]) != (1080, 1920):
        raise SystemExit("O preset mimic é vertical: use w 1080 e h 1920.")
    pal = palavras(plano["transcricao"], base) if plano.get("transcricao") else None
    S, erros = 0.0, []
    for k, c in enumerate(plano["cenas"]):
        if c.get("cenario", "noite") not in CENARIOS:
            raise SystemExit(f"cena {k + 1}: cenário '{c.get('cenario')}' não existe ({', '.join(sorted(CENARIOS))})")

        def quando(v):
            if isinstance(v, (int, float)) or v is None:
                return v
            if not pal:
                raise SystemExit(f'"em": "{v}" é palavra, mas o plano não tem "transcricao"')
            alvo = _norm(v)
            for w in pal:
                if w["s"] >= S - .3 and _norm(w["t"]) == alvo:
                    return round(w["s"] - S, 3)
            raise SystemExit(f'palavra "{v}" não achada depois de {S:.2f} s')
        momentos = [0.0]
        for grupo in ("placas", "bonecos", "aderecos"):
            for e in c.get(grupo, []):
                if "em" in e:
                    e["em"] = quando(e["em"])
                momentos.append(e.get("em") or 0)
                for a in e.get("acoes", []):
                    a["em"] = quando(a.get("em", 0))
                    momentos.append(a["em"])
        momentos = sorted(set(m for m in momentos if m is not None) | {c["dur"]})
        maior = max(b - a for a, b in zip(momentos, momentos[1:]))
        lim = LIMITE_CTA if k == len(plano["cenas"]) - 1 else LIMITE
        if maior > lim:
            erros.append(f"cena {k + 1} ({S:.1f}-{S + c['dur']:.1f} s): {maior:.1f} s sem nada novo (máx. {lim} s)")
        S += c["dur"]
    if erros:
        raise SystemExit("CENA_PARADA (regra tela sempre mudando):\n  " + "\n  ".join(erros)
                         + "\nQuebre a cena, ponha outra placa, uma ação de boneco ou um adereço no meio.")
    dur = round(S, 3)
    os.makedirs(pasta, exist_ok=True)
    tema = dict(tema)
    for chave in ("fonte_titulo_arquivo", "fonte_texto_arquivo"):   # fonte da marca fora do kit vai junto
        arq = tema.get(chave)
        if arq and os.path.isabs(arq):
            os.makedirs(os.path.join(pasta, "fontes"), exist_ok=True)
            shutil.copy(arq, os.path.join(pasta, "fontes", os.path.basename(arq)))
            tema[chave] = "fontes/" + os.path.basename(arq)
    plano["tema"] = tema
    for a in os.listdir(os.path.join(AQUI, "kit")):
        o = os.path.join(AQUI, "kit", a)
        if os.path.isdir(o):
            shutil.copytree(o, os.path.join(pasta, a), dirs_exist_ok=True)
        elif a != "index.html":
            shutil.copy(o, pasta)
    open(os.path.join(pasta, "plano.js"), "w", encoding="utf-8").write("window.PLANO = " + json.dumps(plano, ensure_ascii=False) + ";\n")
    html = open(os.path.join(AQUI, "kit", "index.html"), encoding="utf-8").read()
    for k, v in (("%W%", plano["w"]), ("%H%", plano["h"]), ("%FPS%", plano["fps"]), ("%DUR%", dur)):
        html = html.replace(k, str(v))
    open(os.path.join(pasta, "index.html"), "w", encoding="utf-8").write(html)
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}},
              open(os.path.join(pasta, "hyperframes.json"), "w"))
    print("ok", pasta, f"{len(plano['cenas'])} cenas, {dur} s, tema {tema.get('nome')}")
    return pasta


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    nome_tema = a[a.index("--tema") + 1] if "--tema" in a else "padrao"
    arq_tema = nome_tema if nome_tema.endswith(".json") else os.path.join(AQUI, "temas", nome_tema + ".json")
    tema = json.load(open(arq_tema, encoding="utf-8"))
    caminho_plano = os.path.abspath(a[0])
    pasta = gerar(json.load(open(caminho_plano, encoding="utf-8")), os.path.abspath(a[1]), os.path.dirname(caminho_plano), tema)
    saida, gif = args_render(a)
    if saida:
        renderizar(pasta, saida, gif)
