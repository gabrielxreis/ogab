# Novidades do Gab (/ogab)

O Gab mostra aqui o que mudou desde a última vez que você usou (ele se atualiza sozinho ao abrir).
Mais novo em cima. Cada versão é uma linha `## <versão> (<data>)` seguida dos itens.

## 2026.10.12-12 (12/10/2026)
- **Efeitos sonoros que preenchem:** o Gab monta o som em camadas (base contínua, ambiente do lugar que aparece na imagem, transições do tamanho do movimento, impactos e detalhes), cada camada na sua trilha com nome.
- **Som conferido sem chute:** cada efeito é identificado por um classificador de áudio antes de entrar (não vale mais o título do banco), e o Gab confere se o vídeo tem som o tempo todo, se cada cena soa como o que mostra e se os sons batem com os movimentos. Na 1ª vez baixa o modelo (~600 MB).

## 2026.10.12-11 (12/10/2026)
- **B-roll real achado no trecho certo:** o Gab lê a legenda, os capítulos e a descrição do vídeo e acha onde a pessoa fala o que você pediu ("um corte do Powell falando de juros"), sem chutar o tempo.
- **Folha de quadros antes de baixar:** o Gab olha uma grade com os quadros do trecho (e o tempo de cada um) antes de pôr na timeline; pega marca d'água, legenda queimada e cena errada.
- **Novas fontes de b-roll:** acervo da NASA e Wikimedia Commons (domínio público, seguro para anúncio, com a licença anotada no links.txt), posts recentes de um perfil do TikTok sem login e print vertical de site ou notícia.

## 2026.10.12-11 (12/10/2026)
- **Objetos 3D de verdade:** além de logo e texto, o Gab monta objetos em 3D (diploma com selo de ouro, troféu, avião...) no Blender, com luz de estúdio para metal e fundo transparente. Vem junto o pacote **cc-blender-skill** (30 skills de Blender), instalado pelo instalador.

## 2026.10.12-10 (12/10/2026)
- **Logo em 3D de verdade:** a logo ou um texto com volume, metal na cor da marca, luz e câmera, renderizado no Blender com fundo transparente (o instalador agora instala o Blender).
- **Morph de formas complexas:** a logo se formando, com uma forma virando a letra e a letra virando a palavra da marca.

## 2026.10.12-9 (12/10/2026)
- **Novas técnicas de motion no After Effects:** linhas de luz (glow lines), letras que esticam (letter stretch), texto cinético, formas que se transformam (morphing), elementos 3D e câmera fluida com parallax e desfoque de movimento.
- **Tracking no After Effects:** o texto fica preso a um null "RASTREIO"; para ajustar a distância é só arrastar o texto.

## 2026.10.12-8 (12/10/2026)
- **Texto que segue a pessoa ou o objeto (tracking)** no DaVinci, no Premiere e no After Effects: o Gab rastreia o rosto ou o objeto e o texto acompanha, com keyframes editáveis. Peça: "coloca o nome em cima da cabeça dele" ou "o texto segue o produto".
- **Animação no editor:** punch-in, zoom, pan, giro e opacidade com keyframes direto no DaVinci (pelo Fusion do clipe) e no Premiere.
- **Premiere:** lettering com o texto do vídeo (o After Effects gera o MOGRT com o texto em segundos e o Premiere insere; continua editável).
- **Doctor mais completo:** confere o Python e cada pacote que os recursos usam (e instala o que faltar), o ffmpeg completo, versões do DaVinci, Premiere e After Effects, MOGRTs, espaço em disco e a ponte do After Effects.

## 2026.10.12-7 (12/10/2026)
- **Motions no After Effects com acabamento de verdade:** fundo animado (degradê, grade que desliza, brilhos e vinheta), cartões de vidro com brilho atravessando, divisor dourado, check que gira e curvas de movimento iguais às do HyperFrames. O motion de lista da biblioteca (e o MOGRT dele) foi refeito assim.
- Fonte **Cardo** agora vem junto (usada nos motions da Calverstone).

## 2026.10.12-6 (12/10/2026)
- **Gasta menos tokens:** o Gab avisa quando trocar para Sonnet (ou esforço baixo) nas fases mecânicas e quando voltar para Opus nas decisões. Downloads em lote (Envato, Artlist), conversões e conferências vão para um ajudante mais barato, que devolve só o resultado. Os motions começam pela biblioteca de modelos.
- **Docker não é mais instalado:** o Gab não usa. Se o `hyperframes doctor` avisar "Docker: not found", pode ignorar. Quem já instalou pode manter ou desinstalar, tanto faz.

## 2026.10.12-5 (12/10/2026)
- **Novidades ao abrir:** o Gab se atualiza sozinho e agora mostra o que mudou (é esta mensagem).
- **`/ogab doctor`:** confere a instalação inteira (ferramentas, Docker, DaVinci, Premiere, After Effects, fontes) e corrige sozinho o que der; o que sobrar ele te guia passo a passo. Roda também no fim do instalador e no `/ogab comecar`.
- **Biblioteca de motions:** modelos prontos (lista com checks, contador com barra, frase em duas linhas) que se ajustam ao seu vídeo e às cores do cliente. Cresce a cada motion novo aprovado e chega para você no update.
- **MOGRTs para o Premiere:** cada modelo da biblioteca também vira um template do Premiere, com texto e cores editáveis no Essential Graphics (já instalados pelo instalador).

## 2026.10.12-4 (12/10/2026)
- **Motions no After Effects:** na instalação você escolhe se os motions são automáticos (HyperFrames) ou montados no After Effects como camadas editáveis: cada texto, número, check e cor dá para mudar no AE. Uma camada CONTROLES troca as cores da marca do motion inteiro. Trocar depois: `/ogab config motion aftereffects` ou `hyperframes`.
- **O instalador agora instala tudo** (DaVinci, Premiere e After Effects) em qualquer máquina. As perguntas da instalação só escolhem qual app o Gab usa.

## 2026.10.12-3 (12/10/2026)
- **Docker Desktop instalado automaticamente** (o HyperFrames pede). Se você já tinha instalado o Gab, rode o instalador de novo.
- **Inspiração para motions:** antes de criar um motion novo, o Gab procura referências de movimento numa coleção com mais de 850 vídeos feitos em código.

## 2026.10.12-2 (12/10/2026)
- **Adobe Premiere Pro:** o Gab agora edita também no Premiere 2026 (projeto, sequência, takes, narração, música, SFX, transcrição do próprio Premiere, Enhance Speech e o LUT DO GAB). Na instalação você escolhe DaVinci ou Premiere. Trocar depois: `/ogab config editor premiere` ou `davinci`.
- No Premiere, a legenda (SRT) fica no bin "Legendas": arraste uma vez para a timeline.

## 2026.10.12-1 (12/10/2026)
- **Windows:** o Gab funciona no Windows (instalador próprio em PowerShell). Diferenças em `windows/README.md`.
