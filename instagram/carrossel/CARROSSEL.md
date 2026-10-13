# Carrossel (slides prontos para postar)

Transforma um texto (post, roteiro do vídeo, artigo) em slides PNG para Instagram, Threads, LinkedIn (PDF),
Stories/TikTok ou apresentação 16:9, **na marca do cliente**, sem clicar em nada. O texto de cada slide sai da
`ig-carousel-planner` (`../skills/ig-carousel-planner/SKILL.md`); aqui ele vira imagem.

## Passo a passo

1. **Planejar** os slides com a `ig-carousel-planner` (gancho no 1º slide, uma ideia por slide, CTA no último) e
   mostrar a lista ao usuário antes de gerar (uma linha por slide: tipo, título, destaque).
2. **Criar a cópia de trabalho** dentro da pasta do cliente/vídeo:
   `python3 SKILL_DIR/instagram/carrossel/carrossel.py novo "<pasta>/carrossel/_projeto"`
   (na 1ª vez instala as dependências sozinho, ~420 MB fora do git).
3. **Marca do cliente** em `src/slides.ts` > `MARCA`: fundo, texto, texto secundário, títulos e destaque a partir de
   `clientes/<empresa>/estilo.md` e `<pasta da empresa>/marca/identidade.json` (escolher pela identidade: o fundo é a
   cor dominante da marca ou um escuro/claro neutro; o destaque é a cor de ação do site). Fonte do cliente: copiar o
   .ttf/.otf para `public/fonts/marca.ttf` (texto) e `marca-titulo.ttf` (gancho, opcional); sem o arquivo, usa Inter.
   Logo ou foto: copiar para `public/images/` e usar um slide `image`.
4. **Conteúdo** em `SLIDES` (nunca mexer no motor `src/app/` nem em `src/lib/`), formato em `DEFAULT_FORMAT`.
5. **Exportar:** `python3 SKILL_DIR/instagram/carrossel/carrossel.py exportar "<pasta>/carrossel/_projeto" "<pasta>/carrossel" [--pdf]`
   gera `01-hook.png`, `02-list.png`... (e `carrossel.pdf` para LinkedIn). **Abrir os PNGs e conferir** (texto cortado,
   contraste, destaque) antes de entregar.
6. **Legenda do post** pela `ig-caption-writer` + `ig-humanizer --mode audit`, salva em `<pasta>/carrossel/legenda_post.txt`.
7. Quer ajustar o visual à mão? `carrossel.py previa <projeto>` sobe a prévia no navegador com a barra (fonte, fundo,
   destaque, decoração, formato) e os botões de exportar.

## Formatos (`DEFAULT_FORMAT`)

| Id | Tamanho | Onde |
|---|---|---|
| `threads-4x5` (padrão) | 1080x1350 | feed do Instagram e Threads |
| `instagram-square` | 1080x1080 | feed quadrado, Facebook |
| `linkedin-square` | 1080x1080 | documento do LinkedIn (`--pdf`) |
| `tiktok-9x16` / `story-9x16` | 1080x1920 | Stories, modo foto do TikTok |
| `wide-16x9` | 1920x1080 | apresentação, YouTube (com `DEFAULT_PURPOSE = "presentation"`) |

## Tipos de slide

| Tipo | Para quê | Campos |
|---|---|---|
| `hook` | gancho de abertura | `text` |
| `body` | título + parágrafo (ou `points` com ✓/✗) | `title`, `text` ou `points[]` |
| `list` | itens numerados | `title`, `items[]` |
| `stats` | números grandes | `title`, `stats[{value, label}]` |
| `quote` | citação | `text`, `author` |
| `checklist` | itens com check | `title`, `items[]` |
| `process` | passos ligados | `title`, `steps[]` |
| `comparison` | antes x depois | `leftLabel`, `leftItems[]`, `rightLabel`, `rightItems[]` |
| `cta` | chamada final | `text`, `handle` |
| `image` | título + imagem | `imageSrc`, `title?`, `imageCaption?` |
| `emoji` | emoji gigante | `emoji`, `title?`, `text` |
| `number` | número herói | `bigNumber`, `title?`, `text` |

Opcionais em todos: `badge` ("01", "DICA"), `highlight` (1-2 palavras na cor de destaque) e
`highlightStyle: "italic-box"` (a palavra em itálico sobre um bloco colorido).

## Regras

- Máximo 40 palavras e 5 linhas por slide; uma ideia por slide; misturar tipos (não fazer tudo `body`).
- 1º slide é o gancho (funciona sozinho como capa); último é o CTA com o @ do cliente.
- Sem travessão nos textos. Português do cliente, nomes com a grafia de `pronuncia.json`.
- Carrossel não tem mídia misturada: tudo imagem (o Instagram aceita até 20; pela API, 2 a 10).
