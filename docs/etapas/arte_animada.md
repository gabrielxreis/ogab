# Arte animada: PSD, Canva (PDF) ou imagem → camadas → animação

Pedido típico: "anima essa arte", "faz esse flyer/post virar vídeo", "anima o PSD", "anima meu design do Canva".
Script: `scripts/arte_animada.py`. Saída: projeto HyperFrames (um `index.html` por arte) + MP4 (ou MOV com alfa).

## 1. Pedir a melhor fonte (nesta ordem)

| O usuário tem | Qualidade | Como chega |
|---|---|---|
| **PSD/PSB** | máxima: cada camada original em alta, no lugar exato | arquivo |
| **Canva** | alta: textos, fotos e formas separados (vetor) | PDF: no Canva, *Compartilhar > Baixar > PDF Impressão*, **sem** marcar "Achatar PDF". Com o conector do Canva autorizado, exportar o design como PDF por ele. O Canva não exporta PSD. |
| Illustrator / InDesign / Figma | alta | PDF (mesmo caminho do Canva) |
| Só PNG/JPG | média: só pessoas viram camada; o texto fica colado no fundo | arquivo |

Imagem chegou pequena (ex.: print do WhatsApp) e o template é de banco (Freepik/Envato, "photo not included"): perguntar se ele tem o PSD do template antes de seguir pela imagem.

## 2. Ler as camadas

```bash
python3 SKILL_DIR/scripts/arte_animada.py ler "<arte.psd|.pdf|.png>" "<projeto>" [--prancheta N|nome] [--pagina N] [--motor auto|psdtools|photoshop]
```
Projeto em `<pasta_saida>/<Empresa>/_motions/<arte>-anim/` (ou na pasta do vídeo, se a arte for parte de um vídeo).
Grava `camadas/NN-nome.png` (cada bloco recortado), `camadas/_final.png` (arte inteira) e `camadas.json`, e imprime o plano.

- **PSD:** cada filho da prancheta vira um bloco. Grupo comum com até 12 filhos é aberto um nível; grupo de fundo/textura fica inteiro. Camada com máscara de corte (clip) vai junto com a base. **Ajuste global** (grade de cor sem clip) não vira bloco: entra em todo bloco abaixo dele, para a cor de cada camada já sair igual à final. Grupo "atravessar" herda o modo de mesclagem das camadas de dentro.
  - `--motor photoshop` (Mac com Photoshop; o `auto` escolhe sozinho quando há estilo de camada): exporta cada bloco pelo próprio Photoshop numa CÓPIA do arquivo (sombras, traços, smart objects e ajustes fiéis). Usa a ponte da /oyoshi (`~/.claude/skills/oyoshi/scripts/ps_lib.py`) se existir. Arquivo que o usuário já tinha aberto continua aberto e intacto.
  - `--motor psdtools`: sem Photoshop (Windows também). Estilos de camada podem sair diferentes; a trava final corrige o último quadro.
  - Várias pranchetas (feed + story no mesmo PSD): usa a 1ª e lista as outras; `--prancheta 2` ou pelo nome. Uma animação por prancheta.
- **PDF:** vetor de fundo (>50% da página) = fundo; cada foto = um bloco; formas = um bloco por elemento (preenchimento + contorno da mesma pílula juntos); texto = um bloco por linha (pixels exatos do PDF, com conteúdo, fonte, tamanho e cor no json). Pilha: fundo < fotos < formas < texto. PDF sem texto = foi exportado achatado: pedir de novo sem achatar.
- **Imagem:** recorta as pessoas com o Vision da Apple (local, sem crédito) e apaga elas do fundo. **O texto continua no fundo.** Para animar texto, refazer à mão: cada texto em HTML na mesma posição (fonte parecida do Google Fonts), apagar o texto do fundo/recorte com inpaint (OpenCV) e escurecer onde o título novo cobre. Foi assim no flyer "Fevereiro Profético" (16/10/2026).

## 3. Revisar o plano (o Gab decide, o usuário vê)

`arte_animada.py plano <projeto>` mostra a tabela (id, tempo, papel, animação, caixa, texto). Papéis automáticos: `fundo`, `textura`, `pessoa`, `titulo` (maior texto e os de tamanho parecido), `texto`, `pilula`, `linha`, `icone`, `logo`, `forma`. Corrigir no `camadas.json` o que estiver errado (`papel`, `anim`, `t`) e só então montar. Animações disponíveis: `zoom_fundo`, `fade`, `sobe_blur`, `sobe_blur_curto`, `desce_blur`, `esquerda`, `direita`, `slam` (com tremor), `wipe`, `revela_baixo`, `abre_x`, `risca`, `pop`, `pop_suave`, `gira_pop`.

Ordem padrão: fundo e texturas no 0 s; pessoas a partir de 0,35 s; o resto de cima para baixo; toda a entrada em ~55% da duração; depois respiro (câmera leve, pessoas com parallax, brilho passando nos títulos, ícones pulsando).

## 4. Montar, conferir, renderizar

```bash
python3 SKILL_DIR/scripts/arte_animada.py montar "<projeto>" [--duracao 10] [--largura 1080] [--particulas "#ff9a3c"] [--sem-final-exato] [--cinema suave] [--cinema-cor "#ffb070"]
cd "<projeto>" && npx hyperframes lint && npx hyperframes snapshot --at 0.5,1.5,3,5,9
npx hyperframes render --format mp4 --fps 30 -o "<pasta do vídeo>/videos/<arte>.mp4"     # ou --format mov (alfa)
```
- **Trava final** (padrão): no fim da entrada, a arte exata (`_final.png`) entra por cima em 0,9 s. Corrige o que o navegador mistura diferente do Photoshop (modos Luz linear/Luz intensa, grupos atravessar). Desligar com `--sem-final-exato` só se os blocos já baterem com a arte (comparar o quadro final com `_final.png` lado a lado).
- **Cinema** (`--cinema suave`, padrão para arte animada; ver `fx.md`): bloom, grão, aberração e luz nos cantos por cima de tudo, inclusive da trava final.
- Conferir no contact sheet: nada piscando antes da hora, pessoa sem faixa cortada, título legível, último quadro igual à arte.
- Depois do automático, dá para refinar à mão no `index.html` (é GSAP normal): ex. título letra a letra refazendo o texto em HTML, estrelas girando, elipse se desenhando (`stroke-dashoffset`).
- SFX e música: seguir `sfx.md` (whoosh na pessoa, impacto no `slam`, brilho no chime) e a música bruta como sempre.

## Armadilhas (testadas em 16/10/2026)
- Photoshop: `saveAs` PNG de documento com prancheta salva só a prancheta e com fundo OPACO. O script desfaz as pranchetas na cópia (`ungroupLayersEvent` com referência `Trgt`) e mede o deslocamento da tela (a tela cresce, ex.: 3716x9120) pela `boundsNoEffects` de uma camada de referência.
- psd-tools: `psd.composite(viewport=...)` sem filtro mistura as outras pranchetas; o final usa filtro só com a prancheta escolhida.
- PDF: agrupar vetores só por "caixas se tocam" junta a pílula com o círculo de luz atrás; o agrupamento usa sobreposição alta (mesmo elemento) e não proximidade.
- Rodar os scripts com `python3 -P` quando o diretório atual for de arquivos baixados (nunca `-I`, que esconde o psd-tools instalado com `--user`).
