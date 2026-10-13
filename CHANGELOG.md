# Novidades do Gab (/ogab)

O Gab mostra aqui o que mudou desde a última vez que você usou (ele se atualiza sozinho ao abrir).
Mais novo em cima. Cada versão é uma linha `## 2026.10.13-8 (13/10/2026)
- **Motions colados continuam no tempo da fala:** ao fechar o vãozinho entre motions em sequência, o Gab estica o motion anterior em vez de puxar o seguinte; antes, numa sequência longa, os últimos entravam alguns quadros antes da palavra.

## 2026.10.13-7 (13/10/2026)
- **Motion sem fade embutido:** o motion sai do render sem fade de entrada e saída; a transição fica no DaVinci, onde você ajusta.
- **Motion com fundo próprio:** motion de tela cheia tem o fundo na identidade do assunto (nunca por cima do vídeo cru); foto ou take entra dentro do motion, em moldura.

## 2026.10.13-6 (13/10/2026)
- **Motion no tempo da fala:** cada elemento do motion (número, frase, selo, título) entra junto com a palavra falada, medido na transcrição palavra a palavra. Nada aparece antes de ser dito.

## 2026.10.13-3 (13/10/2026)
- **Novos nomes:** o preset "pontilhismo" agora é **point cloud** e o "metáforas" agora é **vector motion**.
- **O Gab escolhe o preset sozinho:** ao planejar o vídeo trecho a trecho, ele usa vitrine, point cloud ou vector motion onde cada um combina (curiosidade e história em point cloud, frase de efeito em vector motion, coisa de interface em vitrine) e diz o que escolheu. Dá para misturar no mesmo vídeo.

## 2026.10.13-2 (13/10/2026)
- **Preset pontilhismo:** vídeo minimalista em pontos: fotos reais (com crédito), textos com volume e formas se desenham com milhares de pontos que migram de uma cena para a outra, com câmera 3D. Peça "no preset pontilhismo".
- **Preset metáforas ("1 prompt, 1 vídeo"):** você manda um roteiro curto e cada frase vira uma metáfora visual em preto e branco (um entre muitos, multidão, caminho, porta, calendário, cartões de vidro, herói...), em 4 estilos: destaque, bolhas, grade e objetos. Peça "no preset metáforas, estilo grade".

## <versão> (<data>)` seguida dos itens.

## 2026.10.13-6 (13/10/2026)
- **Preset tela dividida:** Reels com o motion em cima e você embaixo, legenda em etiqueta branca na emenda e quebras em tela cheia a cada poucos segundos. O Gab enquadra seu rosto na metade de baixo sozinho. Peça "faz em tela dividida".

## 2026.10.13-5 (13/10/2026)
- **Takes vão brutos para o DaVinci:** o Gab não corta nem renderiza mais nenhum take antes. O vídeo original entra inteiro e o corte é feito na timeline, então você pode puxar a borda do clipe e reajustar. Vídeo horizontal numa timeline vertical é enquadrado pelo zoom do próprio DaVinci.
- **Edição mais rápida:** corte a cada 1,5 a 3 s, com a imagem acompanhando cada ideia da fala e o gancho sempre com o take mais forte.

## 2026.10.13-4 (13/10/2026)
- **Presets de edição:** estilos completos que você escolhe pelo nome. Primeiro: **VITRINE**, interface limpa de luxo. Cada frase vira um pedaço de interface (conversor que digita o valor, perfil com seguidores subindo, cartão do canal com sino, caixa de seleção, janela de arquivos, pílula de aviso), fundo branco e preto, uma cor de destaque e som de interface em cada movimento. Peça "no preset vitrine" ou coloque `preset: vitrine` no estilo do cliente.

## 2026.10.13-3 (13/10/2026)
- **Carrossel pronto em imagem:** peça "monta um carrossel sobre X" e o Gab entrega os slides em PNG (e PDF para o LinkedIn) nas cores e na fonte do cliente, sem você clicar em nada. 12 tipos de slide e formatos 4:5, quadrado, Stories e 16:9. Para ajustar o visual na mão, ele abre a prévia no navegador.
- **Claquete 3D:** nova cena pronta no Blender, com a marca em metal, para abertura de vídeo.
- **README novo:** motions mais caprichados, a claquete 3D animada e um exemplo de carrossel.

## 2026.10.13-2 (13/10/2026)
- **Instagram dentro do Gab:** peça a legenda do post, um carrossel, as hashtags, a semana de conteúdo, a revisão do perfil ou "por que esse Reel viralizou?". Escreve na voz do cliente, com gancho nos primeiros 125 caracteres, 3-5 hashtags e sem cara de IA. A legenda do post de cada vídeo já sai assim.
- **Publicar e agendar (opcional):** com a chave da Publora em `instagram/.env`, o Gab sobe o vídeo e agenda depois do seu ok. Sem chave, entrega o texto para você postar.

## 2026.10.13-1 (13/10/2026)
- **Render 3D com barra de progresso:** o Gab mostra quantos quadros já foram, a porcentagem e quanto tempo falta. Peça "como está o render?" a qualquer momento.
- **3D mais rápido:** o padrão volta a ser o motor rápido do Blender (EEVEE), agora com ray tracing e luz de estúdio. O Cycles (lento) só se você quiser abrir a cena na interface do Blender.

## 2026.10.12-18 (12/10/2026)
- **3D com cara de produto:** o Gab renderiza objetos 3D no Cycles com luz de estúdio real (HDRI) e texturas do Poly Haven, em tela cheia (nada de quadrado aparecendo), e usa o 3D só para complementar o motion 2D nos momentos de impacto. Objetos reais imitam o real (ex.: green card com a arte do cartão, marcado SPECIMEN).

## 2026.10.12-17 (12/10/2026)
- **O repositório agora se chama `ogab`:** github.com/gabrielxreis/ogab. Quem já tem instalado não precisa fazer nada (o endereço antigo redireciona e o Gab continua se atualizando sozinho). O instalador de um comando já usa o endereço novo.

## 2026.10.12-16 (12/10/2026)
- **Takes do Magnific baixam pelo MCP:** o Gab acha cada vídeo no seu histórico pelo prompt e baixa direto, sem abrir o navegador (muito mais rápido). Ele também confere se o vídeo saiu da imagem certa quando um plano foi refeito.

## 2026.10.12-15 (12/10/2026)
- **Som que combina com o chão e com a ação:** o Gab diz o que a cena mostra (queda não é freada; terra não é asfalto) e confere cada som com um classificador de áudio antes de mixar. Som do chão errado (pneu cantando numa estrada de terra) trava a mixagem até ser trocado.

## 2026.10.12-14 (12/10/2026)
- **Câmera lenta que se ouve:** o Gab percebe quando a imagem entra em slow-motion e o som acompanha: o mundo abafa, o objeto fica lento e grave, um som reverso cresce até o impacto e tudo volta seco na hora em que a ação retoma.

## 2026.10.12-13 (12/10/2026)
- **Sonorização de cenas e animações sem chave de IA:** o Gab lê o vídeo (quando algo entra, bate ou para, e de que lado da tela), monta o som em camadas (ambiente do lugar, foley dos personagens e batidas em 3 partes: golpe, peso e cauda), com pan pela posição na tela, música e ambiente que abaixam sozinhos embaixo da fala e volume final em -14 LUFS. Entrega os stems e uma prévia.

## 2026.10.12-12 (12/10/2026)
- **Efeitos sonoros que preenchem:** o Gab monta o som em camadas (base contínua, ambiente do lugar que aparece na imagem, transições do tamanho do movimento, impactos e detalhes), cada camada na sua trilha com nome.
- **Som conferido sem chute:** cada efeito é identificado por um classificador de áudio antes de entrar (não vale mais o título do banco), e o Gab confere se o vídeo tem som o tempo todo, se cada cena soa como o que mostra e se os sons batem com os movimentos. Na 1ª vez baixa o modelo (~600 MB).

## 2026.10.12-11 (12/10/2026)
- **B-roll real achado no trecho certo:** o Gab lê a legenda, os capítulos e a descrição do vídeo e acha onde a pessoa fala o que você pediu ("um corte do Powell falando de juros"), sem chutar o tempo.
- **Folha de quadros antes de baixar:** o Gab olha uma grade com os quadros do trecho (e o tempo de cada um) antes de pôr na timeline; pega marca d'água, legenda queimada e cena errada.
- **Novas fontes de b-roll:** acervo da NASA e Wikimedia Commons (domínio público, seguro para anúncio, com a licença anotada no links.txt), posts recentes de um perfil do TikTok sem login e print vertical de site ou notícia.
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
