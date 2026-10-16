"""Preset GLASS (16:9, YouTube): motions premium em vidro escuro com aurora violeta, grão de filme, título metálico,
destaque em Playfair itálico, números em Inter fina, revelações por máscara com desfoque, cenas que entram com SLIDE
(empurrão de câmera sincronizado com a V1 no DaVinci, ver camera_davinci.py), stingers de capítulo e cartão de
like + inscreva-se com a foto do canal.

  python gerar.py plano.json <pasta_saida> [--render] [--so id1,id2] [--fps 24]

plano.json: { "fps": 24, "cor": "#8b5cf6" (opcional: troca o violeta pela cor da marca), "motions": [ ... ] }
Tempos ABSOLUTOS da timeline em segundos (já ancorados na palavra falada); cada evento "t*" = início da palavra.
Imagens ("img", "img2", "avatar") com caminho absoluto ou relativo à pasta do plano.json.

TELA CHEIA com BG animado (MP4; com "slide": true sai MOV com alfa e entra/sai empurrando):
  numero      t, valor, prefixo, sufixo, legenda, t_leg, rotulo, icone, [slide, dir]
  frase       palavras [{p, t, d (destaque em serifa)}], icone, tam
  lista       titulo, rotulo, itens [{txt, t}] (até 7)
  passos      titulo, rotulo, itens [{txt, t, icone}] (3 ou 4)
  versus      a {rot, txt, t, icone, cor, img}, b {...}   (img = print/foto no lugar do ícone, com X carimbado)
  stinger     rotulo, texto        (transição de capítulo de 1,2 s: painéis diagonais cobrem e revelam)
CENAS COM SLIDE (MOV com alfa; "dir": 1 entra pela direita, -1 pela esquerda):
  print_destaque  img, anel (x0,y0,x1,y1 em fração), caixa (idem), proporcao (altura/largura do print), img2 (troca),
                  rotulo, titulo, destaque, frase, frase_serif, t_conv (print entra), t_ic (título + anel),
                  t_assim (destaque + caixa), t_agulha (troca para img2 + frase)
  dois_problemas  rotulo1, titulo1, serif1, sub1, rotulo2, titulo2, serif2, sub2, t_longa, t_desist1, t_troca, t_curta,
                  t_entender, t_desist2    (página infinita sem chegar ao botão -> página curta com "?")
  montagem        rotulo, titulo, titulo_serif, pilula, img, anel, t_estr (blocos montando), t_lt, t_ic
LATERAIS SEM BG (MOV com alfa, faixa livre da direita; "pos": "tela" = abaixo do facecam):
  callout     t, titulo, sub, t_sub, icone, rotulo
  numero_lado t, valor, prefixo, sufixo, legenda, t_leg
  lista_lado  titulo, t_tit, itens [{txt, t}]
  palavra     t, texto, rotulo, tam
  chip        itens [{t, icone, txt, sub, ruim}]
  blocos      t, rotulo, (7 numerais 01..07 estourando)
  foto_lado   img, anel, t, t_anel, rotulo
  inscreva    avatar, canal ("@seucanal"), sub, t_like, t_insc, txt_like, txt_inscrever, txt_inscrito
Ícones: check dinheiro grafico carrinho pagina raio alvo foguete pessoas relogio alerta celular estrela x
"""
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "kit"))
import base, cenas  # noqa: E402

BG = ("numero", "frase", "lista", "passos", "versus")
CENAS = ("print_destaque", "dois_problemas", "montagem", "chip", "blocos", "foto_lado", "funil", "paginas", "estrutura")


def main(a):
    if len(a) < 2:
        print(__doc__); return
    plano_arq, saida = os.path.abspath(a[0]), os.path.abspath(a[1])
    plano = json.load(open(plano_arq, encoding="utf-8"))
    base.IMG_BASE = os.path.dirname(plano_arq)
    base.OUT = os.path.join(saida, "_hf"); os.makedirs(base.OUT, exist_ok=True)
    so = set(a[a.index("--so") + 1].split(",")) if "--so" in a else None
    fps = a[a.index("--fps") + 1] if "--fps" in a else str(plano.get("fps", 24))
    for m in plano["motions"]:
        if so and m["id"] not in so:
            continue
        m["_cor"] = plano.get("cor")
        pasta = cenas.montar(m) if m["tipo"] in CENAS else base.gerar(m)
        ext = "mp4" if m["tipo"] in BG and not m.get("slide") else "mov"
        print(f'{m["id"]:<22} {m["tipo"]:<15} {m["ini"]:8.2f}s  {pasta}')
        if "--render" in a:
            out = os.path.join(saida, f'{m["id"]}.{ext}')
            cmd = f'npx --yes hyperframes@0.8.151 render --fps {fps} --format {ext} -o "{out}"' + (" -q delivery" if ext == "mp4" else "")
            r = subprocess.run(cmd, shell=True, cwd=pasta, capture_output=True, text=True, encoding="utf-8", errors="replace")
            print("   render:", "OK" if r.returncode == 0 and os.path.exists(out) else "ERRO\n" + r.stdout[-600:] + r.stderr[-600:])


if __name__ == "__main__":
    main(sys.argv[1:])
