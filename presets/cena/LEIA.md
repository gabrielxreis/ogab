# Motor CENA (comum aos presets de apresentador)

Família estudada em 16/10/2026 (página "Claude Creator Studio" + 6 reels do mesmo criador, ver `REFERENCIA.md`):
o apresentador falando no centro e tudo acontecendo em volta dele, como num palco. Cada efeito é um preset com
nome próprio, todos rodando por este motor:

| Preset | O que é | Pasta |
|---|---|---|
| **DESTAQUE** | legenda palavra por palavra: branca pequena, palavra-chave grande amarela ou em serifa itálica com brilhinhos, pílula com marca-texto, frase empilhada | `presets/destaque` |
| **PALCO** | palavra gigante ATRÁS da pessoa (recorte da pessoa por cima) | `presets/palco` |
| **ÓRBITA** | cartões em volta dele: checklist, barra "pronto 100%", caixa de comentário (CTA); próximos: prova social, parede de manchetes, cartões girando, janela do app, recibos e etiquetas | `presets/orbita` |
| **LENTE** | efeitos de câmera: zoom rápido no rosto; próximos: foco de luz, congelar com etiqueta, antes/depois, transição com desfoque, encolher para a janela | `presets/lente` |
| **BANCADA** | tela verde para comentário: ele recortado embaixo, o assunto atrás, gancho fixo no topo, número circulado à mão | `presets/bancada` |

Não confundir com VITRINE (já existia: cartões de produto) nem com TELA DIVIDIDA (painel de motion em cima).

## Como gerar
1. Transcrição com tempo por palavra (`palavras.json`: `[{"w","ini","fim"}]`).
2. Plano (formato completo no topo do `gerar.py`): só as chaves dos presets que o vídeo usa
   (`destaque`, `palco`, `orbita`, `lente`).
3. `python3 presets/cena/gerar.py plano.json <pasta>/cena` gera as camadas com alfa e a `previa.mp4`.
   `--sem-render` só monta os projetos HyperFrames (`proj_palco/`, `proj_frente/`) para revisar.

## Camadas (ordem na timeline)
V1 `base.mp4` (vídeo com a LENTE) · V2 `palco.mov` · V3 `recorte_lente.mov` (a pessoa) · V4 `frente.mov`
(DESTAQUE + ÓRBITA). Sem LENTE, V1 é o vídeo original e V3 é `recorte.mov`. A linha principal nunca é apagada.

## Regra do rosto (automática)
Texto e animação NUNCA na frente do rosto. O `gerar.py` detecta o rosto (`rosto.py`, Apple Vision, grátis; leva em
conta o zoom da LENTE) no tempo de cada elemento:
- legenda que bate no rosto desce para baixo do queixo;
- cartão/animação que bate vai para TRÁS da pessoa (camada `palco.mov`, com o recorte por cima);
- CTA desce se couber, senão vai para trás;
- sem espaço embaixo: imprime `AVISO ... reenquadre`. Aí tirar o zoom do trecho, afastar/baixar a pessoa ou mover o
  texto; nunca entregar com o aviso pendente. `"proteger_rosto": false` no plano desliga (só se o usuário pedir).

## Recorte da pessoa (`recorte.py`)
Mac: segmentação de pessoas da Apple (Vision), local e grátis, sem chave de IA. Cerca de 50 s para 30 s de vídeo
1080p em "equilibrada". Borda suavizada e estabilizada no tempo. Fora do Mac: rembg (mais lento).
Só é preciso quando há PALCO (ou BANCADA).

## Paleta e fontes
Amarelo `#F2D16B` (`"dest"` no plano troca pela cor do cliente), branco, vidro escuro. Poppins Bold/ExtraBold/Black
e Playfair Display Italic/SemiBold Italic (em `assets/fontes`, copiadas para cada projeto).

## Ritmo (do estudo)
Um efeito grande a cada 3-5 s, legenda sempre presente (DESTAQUE contínuo), CTA nos últimos 3-4 s.
O efeito nasce da fala: a palavra dita é a que aparece atrás, a lista falada é a que recebe os checks.
