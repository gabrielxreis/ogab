# Preset POSTER (pôster editorial em movimento)

Cada frase vira um **pôster de design**: fundo cinza de estúdio com vinheta OU preto chapado, um **recorte em preto e
branco de alto contraste** no centro, uma **forma vermelha chapada** atrás (disco com órbita pontilhada, quadro com
moldura fina ou pedestal preto) e **microtipografia de pôster** (rótulos miúdos, número no círculo, código de barras,
"QR", fio fino de rodapé, grade de linhas arredondadas). O texto entra **palavra a palavra**: frase pequena em cima, a
palavra-chave grande e pesada embaixo; cada palavra nasce apagada e desfocada e "acende". Uma **palavra GIGANTE**
desfocada atravessa a tela (na frente no claro, cinza atrás no escuro). **Câmera sempre viva** (afasta, aproxima,
anda, gira) com paralaxe do recorte, **corte seco** entre pôsteres (dois quadradinhos brancos piscam no corte) e
**fecho com a marca** no preto, entrando pesada e assentando leve.

Serve para frase de efeito, reflexão, criatividade, portfólio de criador/estúdio, manifesto de marca, "o que eu
aprendi", conteúdo de design, arte, cinema e música. Não serve para dado com gráfico, interface de app nem conteúdo
alegre e colorido (é P&B + um vermelho).

**Diferença da COLAGEM:** a colagem é foto antiga em meio-tom com borda de tesoura em papel kraft, movimento em
degraus. O pôster é recorte P&B limpo com sombra macia, cinza de estúdio, movimento contínuo e tipografia suíça.
**Diferença do KINETIC:** o kinetic é só tipografia batendo na tela; no pôster a imagem é a protagonista e o texto é
discreto, palavra a palavra.

Estudado em 27/10/2026 num Reel de design (6 planos, média 2,53 s, câmera em 100% dos planos, 50% dos planos no preto,
saturação 0,07). Ficha em `exemplo/` não guarda nada da referência: só a linguagem.

Exemplo: `exemplo.mp4` / `exemplo.gif` (14,6 s, 1080x1920): "ninguém nasce sabendo criar / o segredo é absorver /
tudo que você vê / vira referência / e aplicando nas suas ideias / gabrielxreis". Plano em `exemplo/plano.json`.

## Como pedir
`/ogab faz um reels no preset poster sobre <tema>` (ou `preset: poster` no estilo.md do cliente).

## Processo (o que o Gab faz)
1. Roteiro curto (8-30 s), 1 ideia por pôster, 1,3-4 s por cena (média ~2,5 s), alternando claro e escuro
   (a referência fica meio a meio). Cada cena: **que imagem forte mostra isso?** (estátua, pessoa, objeto, planeta,
   ferramenta) + 2 linhas de texto (pequena + palavra-chave) + opcional uma palavra gigante.
2. Imagem: só com direito de uso. Fotos do próprio cliente, ou livres: `python3 SKILL_DIR/scripts/baixar_video.py
   buscar "<termos>" --fonte commons|nasa|met|aic --tipo imagem` (conferir a licença; crédito no `credito` e na
   legenda do post). **Nunca** personagem de filme/desenho, ator, celebridade ou marca de terceiros (a referência
   usava; nós não). Gerar por IA só perguntando (custa crédito). Assunto bem separado do fundo recorta melhor.
3. Recorte: `"recorte": "sujeito"` (Apple Vision, `scripts/sujeito.py`, local e grátis), `"escuro"` (objeto claro
   sobre fundo preto: planeta, produto em estúdio preto) ou `"nenhum"` (foto inteira). O P&B com curva em S sai
   pronto no PNG (`gerar.py`).
4. Plano (`gerar.py`, docstring): por cena `dur`, `fundo` (claro | escuro), `camera` (lista: afasta, aproxima,
   direita, esquerda, sobe, desce, gira) e `ritmo` (lenta | media | rapida), `foto`, `forma` (disco | quadro |
   pedestal), `texto` (`linhas`, `y`, `em`, `ate`, `grande`, `cor: "branco"` sobre imagem), `gigante` (`texto`, `y`,
   `linhas`, `frente`), `grade`, `micro`, `hud` (cantos e chip, para o escuro) e `fecho` (só a marca).
   Com referência: `"ref_plano"`/`"ref_o_que"` em cada cena e `"referencia"` no topo.
5. Prints ANTES do render: `python3 SKILL_DIR/scripts/prints_cenas.py <pasta> <plano com de/ate>` e o checklist do
   SKILL.md. No preset, ESCURO no fundo preto e BORDA no planeta/palavra gigante são esperados; texto nunca encosta em
   órbita, forma ou recorte.
6. `python3 SKILL_DIR/presets/poster/gerar.py plano.json <pasta>/motions/poster [--tema <marca>] --render <pasta>/motions/poster.mp4 [--gif]`
   no painel Terminal (o `renderizar` imprime a barra; ~25 s de render para 15 s).
7. Conferir: `scripts/revisor.py <mp4> [--referencia <referencia.json>]`. O primeiro quadro do `snapshot` às vezes
   sai preto: conferir no MP4.

## Tema (cor da marca)
`temas/padrao.json`: `claro`/`borda` (cinza do centro e da vinheta), `escuro`, `tinta` (texto no claro), `branco`
(texto no escuro), `acento` (disco, quadro, órbita, X: a cor da marca entra aqui), `acento2` (chip do HUD) e
`micro` (os textos miúdos: `topo`, `marca`, `lado`, `rodape`, `chip`, `numero`). Marca nova: copiar para
`temas/<marca>.json` e trocar acento e os textos miúdos (nome, ano, @, site). Nada de degradê colorido: P&B + 1 cor.

## Regras de bom gosto
- Um recorte por pôster, grande e centrado; a forma vermelha atrás dele, nunca atrás do texto.
- Texto curto: linha pequena até ~4 palavras, palavra-chave até ~2 palavras. Palavras entram uma a uma e acendem;
  nada de letra a letra, nada de quique.
- Palavra gigante: no claro vai NA FRENTE e desfocada, embaixo; no escuro vai ATRÁS em cinza, em 1 ou 2 linhas.
- Câmera nunca parada; o recorte anda um pouco mais que o fundo (paralaxe). Corte seco, sem transição de efeito.
- Primeira cena: o recorte já aparece no quadro 0 (gancho nunca vazio).
- Fecho: só a marca, no preto, sem logo grande nem CTA longo (CTA, se houver, vai na legenda do post).
- Som: whoosh curto no corte, tique seco a cada palavra-chave, sub grave na entrada do preto; música eletrônica
  minimal ou piano com batida (~120-135 BPM).

## Créditos
- Linguagem estudada num Reel de design (27/10/2026); nenhuma imagem, texto, marca ou personagem dele foi usado.
- Fonte: Inter Tight (Michael Rafailyk, SIL OFL 1.1), em `kit/fontes/`.
- Fotos do exemplo: `Roman_Marble_Statue_Bust_(27692473774).jpg` (Gary Todd, CC0, Wikimedia Commons);
  `The_Earth_seen_from_Apollo_17.jpg` (NASA, domínio público); "Marble statue of a kouros", 253370 (The Met, CC0);
  `Apollo_lunar_mapping_camera.jpg` (National Air and Space Museum, CC0); `Astronaut_Edward_White_Ready_For_Gemini_IV_Liftoff_-_GPN-2002-000029.jpg`
  (NASA, domínio público).
