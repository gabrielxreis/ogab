# Preset SKETCH (desenho de marcador)

Estudado quadro a quadro de um reel de tutorial de apps (13/10/2026): **fundo preto com luz suave no centro e tudo
desenhado como se fosse marcador**. Os contornos se traçam na hora, um cursor "_" pisca dentro do cartão vazio e os
ícones surgem. Textos manuscritos entram digitados letra a letra, botões são pílulas com contorno à mão e setas se
desenham da esquerda para a direita. O traço "treme" levemente o tempo todo, como animação desenhada (line boil).
Cada bloco tem uma cor (laranja, azul, verde, roxo) com fundo translúcido da mesma cor, e o amarelo é o destaque.

Bom para: tutorial, "X apps/ferramentas que...", passo a passo, comparação "isto → aquilo", lista de recursos, explicar
um fluxo (ferramenta → resultado), conteúdo de tecnologia, IA, produtividade e educação. Não é para luxo nem para
dado oficial (use vitrine ou o motion do cliente).

Exemplo: `exemplos/exemplo.json` → `exemplos/exemplo.mp4` (vertical, 3 cenas) e `exemplo.gif`.

## Como gerar
`python3 presets/sketch/gerar.py plano.json <pasta>/motions/sketch --render <pasta>/motions/sketch.mp4`
(formato do plano e lista de blocos no topo do `gerar.py`). O layout é calculado no Python, medindo cada texto com a
própria fonte (Patrick Hand), então nada estoura a largura. O bloco todo fica centralizado na altura (regra do Gab).

## Blocos
| Bloco | O que é | Quando usar |
|---|---|---|
| `cabecalho` | linha "ícone + texto → destaque" (partes com `icone`, `texto`, `seta`, `grande`, `cor`) | título da cena, "GitHub → App Store", "antes → depois" |
| `grade` | cartões com cursor, 1 ícone grande ou 2 mini-cartões de ícone, rótulo e botão digitado | lista de apps, ferramentas, recursos (2-6) |
| `numero` | cartão com número grande + "projeto 1 de 5" + título em até 2 linhas | contagem, capítulo, passo N |
| `fluxo` | cartão-ícone com rótulo → seta → painel com esboço (`editor_video`, `grafico`, `lista`, `chat`) | "a ferramenta faz isto", entrada → resultado |
| `frase` | frase grande manuscrita com sublinhado ondulado no destaque | gancho, conclusão, CTA |
| `lista` | caixinhas que recebem check desenhado, com texto digitado | passos, benefícios, checklist |
| `espaco` | respiro vertical | separar blocos |

Ícones desenhados (`kit/icones.js`): video, play, tesoura, email, gmail, drive, instagram, tiktok, youtube, github,
claude, robo, codigo, terminal, chat, doc, pasta, grafico, subida, dolar, check, xis, pessoa, grupo, globo, raio,
estrela, engrenagem, lupa, casa, calendario, coracao, celular, link, foguete, cadeado, sino, carrinho, lampada,
relogio, alvo, ia. Faltou um? Desenhar o path (viewBox 24, só contorno) no `icones.js` e pôr aqui.

## Regras do estilo
- Fundo `#070707` com luz `#1b1b1d` no centro e grão leve; nada de fundo de cor.
- Paleta padrão: laranja `#f0884a`, azul `#4aa3f0`, verde `#3fcf6a`, roxo `#a07cf0`; destaque amarelo `#ffc83d`;
  texto `#f2f2f2`. Cliente com marca: `"cores": {"paleta": [...cores da marca...], "destaque": "#..."}`.
- Uma cor por cartão (a grade alterna a paleta sozinha); o rótulo fica branco e o botão na cor do cartão.
- Ritmo: o cartão seguinte começa enquanto o anterior ainda digita (cascata de ~0,35 s); a cena segura ~1,5 s montada.
- Com narração, a cena dura o tempo da fala (`"dur"` na cena) e a legenda do Gab continua embaixo, fora do bloco.
- Formatos: `"formato": "vertical"` (1080x1920, tudo 25% maior) ou `"horizontal"` (1920x1080).

## Som (desenho de som do Gab, `docs/etapas/sonorizacao.md`)
Marcador riscando papel quando o contorno se desenha, clique de teclado leve na digitação, "pop" curto no ícone,
whoosh fino na seta, nada de impacto pesado. Ambiente: sala silenciosa ou lo-fi baixo.

## Licenças
Fonte Patrick Hand (Patrick Wagesreiter, SIL Open Font License, `assets/fontes/PatrickHand/OFL.txt`). Ícones desenhados
para este preset (sem marca registrada copiada: são esboços simples). GSAP 3.14 (licença padrão GreenSock, gratuita).
