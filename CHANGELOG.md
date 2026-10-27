# Novidades do Gab (/ogab)
## 2026.10.27-8 (27/10/2026)
- **Tela sempre mudando (todo vídeo):** cada ideia da fala ganha um elemento novo na tela, a cada 2,5 a 4 segundos; nenhuma cena fica mais de ~4,5 s (o convite final pode ir a 7 s). No Lúdico, o Gab nem gera o motion se alguma cena passar disso.
- **Lúdico com muitas cenas:** vídeos com 20+ cenários não perdem mais objetos (a luz agora é compartilhada entre as cenas).
## 2026.10.27-4 (27/10/2026)
- **Motion nunca parado (Lúdico):** a câmera anda o tempo todo e, nas palavras fortes da fala, entra uma batida (empurrão de câmera, pulso, onda e faíscas) com um whoosh baixinho. Acabou o quadro parado esperando a próxima frase.
- **Progresso do motion no Terminal:** todo render de motion mostra uma linha com a porcentagem, a etapa e quanto falta, e o Gab manda o link da aba para você tocar e acompanhar. Vários vídeos aparecem em fila, com o total.
## 2026.10.27-7 (27/10/2026)
- **Atualiza também no meio do projeto.** Antes o Gab só procurava atualização quando começava. Agora, numa conversa em que ele já está trabalhando, cada pedido seu confere se saiu versão nova (no máximo 1 vez por minuto, sem atrasar). Se tiver, ele baixa, relê as regras novas e avisa em uma linha antes de seguir. Vale a partir da próxima conversa depois desta atualização.
## 2026.10.27-6 (27/10/2026)
- **Lúdico mais vivo.** A câmera não para mais: gira devagar e vai chegando perto durante a cena, e as palavras fortes da narração ganham uma batida (empurrão de câmera, pulso do cenário e faíscas na cor da sua marca, com um whoosh bem baixo). Se quiser o estilo mais calmo, peça "sem batidas".
## 2026.10.27-3 (27/10/2026)
- **Lúdico: CTA de seguir com o Instagram de verdade.** Quando a fala pede para seguir, entra um celular 3D com o perfil igual ao app (foto, bio, seguidores, seguindo, destaques e as capas dos últimos posts) e um toque em "Seguir". Vídeo sem essa fala ganha a cena no fim.
- **Lúdico: cartão mais limpo.** Série, seção e fontes aparecem só na abertura; depois fica só o que importa (etiqueta, número, tópicos). As fontes voltam discretas no final.
## 2026.10.27-4 (27/10/2026)
- **Estilo novo: Colagem.** Fotos antigas recortadas à tesoura em meio-tom, coladas em papel kraft ou jornal, etiquetas de papel rasgado e movimento em stop-motion. Ótimo para "você sabia", curiosidade histórica, invenção e personagem. Peça "no estilo colagem" ou marque **Colagem** no passo de estilo do `/ogab menu`.
- **Estilo novo: Linha.** O vídeo inteiro é uma linha dourada fina e contínua: escreve as palavras em cursiva, desenha formas (casa, árvore, coroa, chave), fecha o monograma da marca e termina num pôster. Para marca premium, luxo, arquitetura e manifesto curto. Peça "no estilo linha" ou marque **Linha** no menu.
- **Launch:** fundo na cor escura da sua marca (`"fundo"` no plano), camada animada própria por cima (`"extra"`) e tela vazia para mostrar uma interface viva no lugar do print.
- **Premiere:** o trecho de narração que começava antes do ponto de entrada não cai mais no 0 por cima do anterior (Premiere 26.2). Novo: pôr uma composição do After Effects direto na sequência, sem render (ainda em teste).
- **CapCut:** animação por keyframe em clipe aparado no começo agora acontece no trecho certo.
- **Windows:** comandos `npx` não falham mais com "WinError 2". Envato: uma aba por download (ele travava depois de 2). After Effects: 12 armadilhas novas documentadas.
## 2026.10.27-2 (27/10/2026)
- **Lúdico com 27 cenários novos:** bola que despenca e quica, bússola, cofre, escudo, placa de estrada, celular com o botão seguir, setas, moeda, martelo, ímã, dominó, escada, leilão, sismógrafo, cartão, foguete, chip de IA, planta, dado, urna, alvo, balão, ponte, pilha de moedas, casa, carnê e torneira. O Gab escolhe pelo sentido da frase e continua inventando cenas novas quando nenhum serve.
## 2026.10.27-3 (27/10/2026)
- **Motions mais firmes.** Morph de logo, traço se desenhando, texto entrando letra a letra e 3D no navegador ganharam as armadilhas conhecidas já resolvidas (forma que cruzava no meio do morph, texto que pulava ao dividir, modelo 3D saindo preto ou com cor lavada). O revisor agora também acusa sorteio sem semente escondido. A logo do morph entra sem o quique.
## 2026.10.27-2 (27/10/2026)
- **YouTube: título + capa, capítulos e retenção.** Antes de subir, o Gab escreve 10 títulos, confere cada um junto com o texto da capa (tamanho que aparece no celular e no computador, capa sem repetir o título, palavras vagas) e mostra os melhores para você escolher; escreve a descrição e os capítulos do vídeo longo já no formato que o YouTube aceita. Depois de publicado, mande o CSV de retenção do YouTube Studio (Análises > Engajamento > baixar) e ele diz onde as pessoas saíram, o que estava sendo dito naquele segundo e o que mudar. Peça "/ogab youtube" ou só "título do vídeo", "capítulos", "por que pararam de assistir".
- **YouTube: concorrência das buscas.** O Gab mostra os 10 primeiros vídeos das buscas que o seu vídeo quer ganhar, com views e as palavras que os vencedores usam, e diz se o seu título traz essas palavras.
- **Cores da marca medidas, não chutadas.** O Gab mede a paleta direto nos pixels da logo ou do print (já tirando as cores do Instagram) e, antes de mostrar um motion ou carrossel, confere se alguma cor saiu fora da marca.
- **Storyboard com leituras.** A tabela do storyboard ganhou a coluna do que você precisa entender em cada cena, uma coisa por vez, e avisa quando duas brigam pelo mesmo momento. O revisor também avisa quando vários elementos animam em sincronia perfeita (cara de template).
## 2026.10.27-1 (27/10/2026)
- **Estilo novo: Lúdico.** Explicador viral de notícia em estúdio 3D escuro: holofote em cone, objetos claros e um destaque de cor, com um cenário inventado para cada frase (balança, termômetro, elevador que despenca, placar, globo quando a frase é de lugar), cartão no canto, carimbo e chamada no fim, tudo nas cores da sua marca. Peça "no estilo lúdico" ou marque **Lúdico** no passo de estilo do `/ogab menu`.
- **Menu: um estilo por vídeo.** No passo "Estilo dos motions" agora você marca UM estilo (marcar outro troca o anterior); batidas visuais, b-roll animado e efeitos extras continuam somando. O Gab cria cenas e animações novas no padrão desse estilo, sem ficar preso às que o preset já tem.
## 2026.10.26-3 (26/10/2026)
- **Estilo novo: Explicador de notícia.** O estilo completo dos vídeos explicadores de mercado e notícia: globo 3D que gira até cada cidade da história, rotas pontilhadas ligando os lugares, cartão de dado no canto (seção, etiqueta, número contando e a fonte), tópicos, carimbo, chamada no fim e legenda karaokê. Bom para dólar, bolsa, economia, eleição, exportação e viagem. Peça "no estilo explicador de notícia" ou marque **Explicador de notícia** no passo de estilo do `/ogab menu`.
- **Menu:** um preset que já é oficial não aparece mais duas vezes (uma como "seu").
## 2026.10.26-2 (26/10/2026)
- **Preset novo: Whiteboard.** Uma ilustração se desenha na lousa com uma mão de verdade: primeiro as linhas, depois os personagens pintados cor por cor e por último o fundo. Ótimo para explicação, aula, mapa e infográfico. Peça "no preset whiteboard" ou marque **Whiteboard** no passo de estilo do `/ogab menu`. O motor (~1 GB) se instala sozinho em segundo plano na primeira vez que você abrir o Gab depois desta atualização; o Gab avisa quando ficar pronto. Funciona no Mac e no Windows, sem precisar de placa de vídeo (com NVIDIA fica mais rápido).
- **CapCut no Windows:** a checagem de "CapCut aberto" não quebra mais em Windows com nome de processo acentuado.
## 2026.10.26-1 (26/10/2026)
- **O Gab agora precisa de uma chave (grátis).** Na primeira vez, ele pede seu email e cria a chave na hora (1 chave por computador). É o que deixa o autor cuidar da comunidade e das atualizações.
- **Termos novos (v3):** a skill passa a ser licenciada e a inteligência do Gab fica protegida. Nada do que é seu (vídeos, projetos, config, clientes) é tocado. Ao abrir, o Gab pede o ACEITO de novo.
- **Atualização pelo autor:** o Gab passa a se atualizar pelo servidor do autor, baixando só o que muda.
## 2026.10.26-1 (26/10/2026)
- **Efeitos extras no `/ogab menu`:** física, IA pensando (orbe), ASCII, lupa e rabisco ganharam uma aba própria no passo de estilo dos motions, com prévia em loop. As animações Lottie para site e app agora aparecem em Extras.
## 2026.10.25-4 (25/10/2026)
- **6 estilos novos de efeito** (capa de revista, contorno rabiscado, fichas com objeto, palavra de vidro, recorte de papel, vertigem); o celular que saltava saiu. Eles aparecem no `/ogab menu` quando a prévia com take real ficar pronta.
- **Launch:** cena de editor (DaVinci simulado) e cenas na batida da música; o celular e o gráfico neon respeitam melhor o rosto; a trava de "motion começando do preto" parou de dar falso alarme com texto claro entrando.
## 2026.10.25-3 (25/10/2026)
- **Cortes de fala sem frase picotada:** o Gab só corta em fronteira de frase, tira o retake inteiro (nada de boas-vindas duas vezes) e confere cada emenda com o novo `emendas.py` antes de montar. A transcrição para cortar passa a ser sempre a do DaVinci (o Whisper escondia as repetições).
## 2026.10.25-2 (25/10/2026)
- **Tudo se atualiza sozinho:** uma vez por semana, sem você esperar, o Gab atualiza em segundo plano o ffmpeg, o yt-dlp, o node, o git, os pacotes de Python e as skills que ele usa (HyperFrames e as outras), e conta na conversa seguinte o que mudou. Se algo falhar, `/ogab doctor` resolve.
- **HyperFrames novo (0.8.200), pronto para o FFmpeg 9:** todos os motions usam a mesma versão, testada antes de chegar para você.
## 2026.10.25-1 (25/10/2026)
- **Pronto para o FFmpeg 9:** a prévia do CapCut/sem editor e a sonorização usavam uma opção que saiu do FFmpeg 9 e iam parar de funcionar quando ele atualizasse. Já está corrigido e continua funcionando no FFmpeg 7 e 8.
- **Componentes sempre atualizados:** uma vez por semana o Gab confere se o ffmpeg, o yt-dlp e o node estão na última versão e avisa; o `/ogab doctor` atualiza tudo sozinho. O yt-dlp velho é o que mais faz download do Instagram e do YouTube falhar.
## 2026.10.24-3 (24/10/2026)
- **Presets no CapCut:** fez um estilo de texto ou de clipe que gostou? Peça "salva esse estilo" e o Gab guarda o visual (fonte, cor, contorno, fundo, sombra, animação, filtro, efeitos) para aplicar em qualquer vídeo depois. Também faz cópia de segurança das suas predefinições do CapCut.
- **CapCut sem mexer na sua tela:** no Mac e no Windows o Gab faz tudo pelos arquivos do projeto; só pede para você clicar quando não tem outro jeito (abrir o projeto, exportar pelo app).
## 2026.10.24-2 (24/10/2026)
- **CapCut no Windows (beta):** quem usa Windows agora pode escolher o CapCut como editor (opção 3 no instalador ou `/ogab config editor capcut`). O Gab monta o vídeo direto no rascunho do CapCut, como já fazia no Mac: cortes, legenda, música, textos, filtros e animações da loja, e a prévia em MP4 sem abrir o app. Para abrir o projeto, é só clicar na primeira miniatura da tela inicial do CapCut.
## 2026.10.24-1 (24/10/2026)
- **Óculos Even Realities G2 (`/ogab eveng2`):** o roteiro aprovado vai para o teleprompter da lente (você rola no anel R1 ou deixa rolar sozinho), a lista de planos vira checklist que você marca no anel durante a gravação, e o Gab pode avisar na lente quando um render termina. Funciona por Bluetooth direto do Mac: desligue o Bluetooth do iPhone antes. Primeira vez: `/ogab eveng2` instala e procura o óculos. O teleprompter ainda é experimental.
## 2026.10.23-44 (23/10/2026)
- **Nada renderizado para a timeline sem você pedir:** fotos entram como arquivo original (duração e zoom ajustados no DaVinci) e a legenda não vira mais vídeo. O Gab só renderiza o motion e o export final.
## 2026.10.23-43 (23/10/2026)
- **Regra de emergência:** se você mexer na timeline enquanto o Gab trabalha, ele para tudo no editor na hora e espera você avisar que pode voltar. Ele continua só o que é fora do editor (motions, downloads).
## 2026.10.23-42 (23/10/2026)
- **Cor não pega mais nos motions:** se você arrastar um motion para uma trilha de takes, a LUT do Gab pula ele sozinha.
## 2026.10.23-41 (23/10/2026)
- **Fotos na timeline com movimento:** toda foto entra com um zoom bem leve por keyframe (aproxima ou afasta), para não ficar parada. Dá para ajustar no Fusion do clipe.
- **Fotos com a duração certa:** antes a foto entrava com 5 s fixos ou travava a montagem; agora ocupa exatamente o trecho planejado.
## 2026.10.23-40 (23/10/2026)
- **O menu do vídeo não fica mais de fora:** mesmo quando você começa pedindo só um roteiro ou só a voz e o pedido vira vídeo aos poucos, o Gab abre o menu antes de montar qualquer coisa. Agora é uma trava: sem o menu confirmado, nenhuma timeline, sequência ou rascunho novo é criado (DaVinci, Premiere, CapCut e Final Cut). Quer pular? É só dizer "pode fazer no automático".
## 2026.10.23-39 (23/10/2026)
- **README atualizado:** novidades do menu, da nova ordem da edição com validação por quadros, das prévias com pessoas reais e dos presets Letreiro, Órbita e Lente; print do menu e fluxo novo.
## 2026.10.23-38 (23/10/2026)
- **README novo no topo:** a claquete 3D saiu e entrou o vídeo de apresentação da /ogab (o mesmo publicado no LinkedIn).
## 2026.10.23-37 (23/10/2026)
- **Nova ordem da edição:** depois dos cortes vêm lettering e motions, depois música, SFX, takes e cor, e só então a legenda (que já desce para baixo dos motions numa passada só). Antes de renderizar, o Gab mostra uma folha com os quadros-chave para você validar a timeline no editor.
- **Conferência por quadros em PNG:** `conferir.py chave` exporta do DaVinci só os quadros que importam (cortes, entrada/meio/saída de lettering, motion e b-roll, marcadores) numa folha; se você apontar um problema, `conferir.py trecho --em <segundo>` mostra só aquele trecho. Nada de re-renderizar o vídeo inteiro para conferir.
## 2026.10.23-36 (23/10/2026)
- **Órbita:** o texto de cada cartão agora acompanha o tamanho dele (não estoura mais a borda em take fechado); prévia refeita com o cartão "Letreiro".
- **Prévias mais robustas:** se o cache de vídeos for apagado (limpeza de disco), os takes escolhidos são baixados de novo sozinhos.
## 2026.10.23-35 (23/10/2026)
- **Extras sem repetição:** saíram "Motion atrás da pessoa" e "Gancho com lettering" dos Extras (já existem nos passos de estilo e gancho).
## 2026.10.23-34 (23/10/2026)
- **Menu mais curto:** o passo "Efeitos" saiu do menu, junto com o preset Salta do celular.
## 2026.10.23-33 (23/10/2026)
- **Nomes mais claros:** o preset "Palco" agora se chama **Letreiro**, e Destaque, Órbita e Lente saíram sem o "(CENA)" no menu.
## 2026.10.23-32 (23/10/2026)
- **Estilo novo, Salta do celular (motion):** um celular entra em 3D e um cartão com o número ou a frase salta para fora da tela; motion puro, com fundo próprio, para usar como inserto.
## 2026.10.23-31 (23/10/2026)
- **Corte pelo escuro removido:** o estilo saiu do menu e da skill (não vai ser usado).
## 2026.10.23-30 (23/10/2026)
- **Título atrás da cabeça melhor:** a palavra fica no alto da cabeça e a pessoa cobre só a base das letras (leva em conta cabelo volumoso); sem espaço acima da cabeça o título diminui em vez de ir para trás do rosto.
## 2026.10.23-29 (23/10/2026)
- **Lente com pessoa real:** a prévia da Lente mostra só o zoom no rosto, sem legenda.
- **Órbita com cartões de tamanhos diferentes:** os cartões variam de tamanho sozinhos (ou use "tam" em cada cartão).
## 2026.10.23-28 (23/10/2026)
- **Órbita girando de verdade:** os cartões agora dão a volta inteira em volta da pessoa (por cima e por trás da cabeça, pela frente abaixo do queixo) sem sumir; o tamanho da volta se ajusta à cabeça e avisa se o take for fechado demais.
- **Correção:** a camada de trás da pessoa estava desenhando a parte da frente (a metade de trás da Órbita e dos estilos de duas camadas não aparecia).
## 2026.10.23-27 (23/10/2026)
- **Palco com pessoa real:** a prévia do Palco agora mostra a palavra gigante atrás da cabeça de uma pessoa de verdade.
## 2026.10.23-26 (23/10/2026)
- **Destaque com pessoa real:** a prévia do Destaque agora mostra uma pessoa de verdade, e a legenda ganhou contorno mais forte para ler bem até em cima de roupa estampada.
## 2026.10.23-25 (23/10/2026)
- **Zoom no rosto:** o zoom da Lente agora vai certo no rosto da pessoa (antes recortava do canto de cima).
- **Destaque, Palco e Lente sem erro:** esses motions voltaram a funcionar quando o vídeo não tem cartões da Órbita.
## 2026.10.23-24 (23/10/2026)
- **Cada estilo com uma pessoa diferente:** as prévias dos estilos no menu agora usam um vídeo real diferente para cada estilo (banco de vídeos gratuitos filtrado: rosto de frente, nítido e sem ficar claro demais).
## 2026.10.23-24 (23/10/2026)
- **Exemplos com gente de verdade:** os GIFs dos presets Destaque, Palco, Órbita, Lente e Podcast agora mostram pessoas reais (vídeos de banco gratuito), com a cabeça e o rosto sempre inteiros. O de Respostas ficou no centro da tela.
- **Podcast com legenda na linha do meio:** no preset de podcast a legenda agora fica sobre a linha que divide os dois vídeos, onde dá para ler sem tapar ninguém. Quem quiser o jeito antigo (abaixo do queixo) pede `"legenda": "rosto"`.
## 2026.10.23-23 (23/10/2026)
- **Estilo dos motions em pé:** nesse passo do menu as prévias agora são verticais (9:16), do jeito que o vídeo fica; os outros passos continuam como antes.
- **Prévia mais bonita:** o vídeo de exemplo dos estilos trocou por um take claro e nítido (o anterior era escuro e desfocado).
## 2026.10.23-22 (23/10/2026)
- **11 estilos novos de ritmo e cor:** punch no início da frase, zoom com desfoque e luz quente, dois enquadramentos num take só, zoom no rosto, círculo da marca para trocar de parte, e os acabamentos quente de cinema, claro e limpo, pastel azulado, sépia quente, editorial frio (LUTs próprias para o DaVinci) e amarelo chapado. Aparecem no menu assim que ganharem a prévia com vídeo real.
## 2026.10.23-18 (23/10/2026)
- **Prévias em vídeo:** no menu, a prévia de cada estilo agora é um vídeo curto em loop com pessoa real (mais nítido e bem mais leve que GIF). Estilos com prévia de apresentador desenhado saíram do menu e voltam conforme ganham a prévia com take real.
## 2026.10.23-17 (23/10/2026)
- **Prévias dos estilos com pessoa de verdade:** os GIFs do menu agora mostram cada estilo sobre um vídeo real de uma pessoa falando para a câmera (banco de vídeo com licença livre), em vez do apresentador desenhado.
## 2026.10.23-21 (23/10/2026)
- **16 estilos novos de prova e b-roll animado:** matéria com marca-texto, selo de trecho oficial, número atrás da cabeça, post de rede social, arquivo pessoal, cursor no número, pergunta no chat, robôs conversando, link que vira evento na agenda, link que abre a planilha, conversa no celular, clique na barra de apps, aviso do personagem, pílula de produto, fila de personagens e diagrama do conceito. Aparecem no menu assim que ganharem a prévia com vídeo real.
## 2026.10.23-20 (23/10/2026)
- **11 batidas visuais novas (estilos, parte 2):** logo com brilho, cronômetro em anel, calendário voltando no tempo, botões do celular desligando, comente a palavra, polaroids com flash, comentar e seguir, contador de série, notas com seta à mão, recado fixo no topo e grade de resultados. Aparecem no menu assim que ganharem a prévia com vídeo real.
## 2026.10.23-19 (23/10/2026)
- **8 layouts novos (estilos):** recorte com cartões flutuando e a sala desfocada, canvas colagem azul com vídeos e adesivos, gráficos no espaço acima da cabeça, faixa no topo para citação, foto de arquivo e número, lousa acima da cabeça, rodízio de três (prova em cima, palavra grande, prova em tela cheia), polaroid narrador (você numa polaroid no canto ao lado do print) e antes e depois. Aparecem no passo Layout do menu assim que ganharem a prévia com vídeo real.
## 2026.10.23-18 (23/10/2026)
- **11 batidas visuais novas (estilos):** logos com o papel de cada um, logos ligados por setas, palavra única na virada, roleta de logos, pilha de comparação de produtos, palavra clímax atrás da pessoa, frase cinética em tela cheia com ícones, citação no topo, rótulo de montagem, interface plana de patrocínio e cabeçalho de progresso da lista. Aparecem no menu assim que ganharem a prévia com vídeo real.
## 2026.10.23-17 (23/10/2026)
- **8 efeitos novos (estilos):** checklist ao lado da cabeça, celular com passo a passo, gráfico neon atrás, você dentro do app, parede de miniaturas, telas em órbita (passam atrás e na frente), sair da tela do celular e corte pelo escuro. Aparecem no passo Efeitos do menu assim que ganharem a prévia com vídeo real.
## 2026.10.23-16 (23/10/2026)
- **Menu sempre atualizado:** o menu abre sempre no mesmo endereço (127.0.0.1:47321); se já houver uma aba dele aberta, ela se recarrega sozinha com a versão nova em vez de abrir outra aba, e o menu antigo fecha sozinho.
- **Mais espaço para as opções:** o topo ficou compacto (progresso na linha da logo, título menor, abas de categoria numa linha só) e cabem mais cartões na tela.
## 2026.10.23-15 (23/10/2026)
- **Barra de rolagem do menu redesenhada:** fina, com a alça em degradê verde da /ogab.
## 2026.10.23-14 (23/10/2026)
- **Menu com rolagem:** quando um passo tem muitas opções, os cartões ficam num tamanho confortável e você rola para baixo para ver os outros (sem as setas de página).
## 2026.10.23-13 (23/10/2026)
- **Estilos novos no menu:** passos novos Gancho, Layout, Prova e Efeitos, e as abas Batidas visuais e B-roll animado nos estilos dos motions; legendas animadas e looks de cor novos entram nos passos que já existem. Cada estilo aparece assim que fica pronto, com a prévia em loop (os passos sem nenhum estilo ainda ficam escondidos).
## 2026.10.23-12 (23/10/2026)
- **Estilos novos (base):** nasceu a família de estilos curtos para o vídeo da pessoa (gancho, legenda, layout, prova, batidas, b-roll animado, efeitos, ritmo e cor), cada um com prévia em loop. Os primeiros: título atrás da cabeça, notificação do celular e notas na parede. Os próximos chegam nos próximos updates e aparecem sozinhos no menu.
## 2026.10.23-13 (23/10/2026)
- **Link para abrir o menu:** quando o Gab abre o `/ogab menu`, ele mostra na conversa um link "Abrir o menu do vídeo" e explica o que fazer, para o caso de o navegador não abrir sozinho.
## 2026.10.23-12 (23/10/2026)
- **Seus presets no menu:** o preset que o Gab cria para você aparece no `/ogab menu` (estilo dos motions, com o selo "seu" e a prévia em GIF) depois de enviado à comunidade. O Gab acha sozinho tudo que o preset precisa para funcionar (imagens de fora da pasta, fontes, bibliotecas) e manda completo; se for grande demais, avisa em vez de mandar pela metade. `meus_presets.py listar` mostra o estado de cada um.
## 2026.10.23-11 (23/10/2026)
- **O Gab abre o menu sozinho:** quando você pede para criar ou editar um vídeo (ou manda o arquivo), ele pergunta só o que faltar (marca, assunto, objetivo) e já abre o menu para você escolher os detalhes ou apertar Automático.
- **Tela final do menu mais clara:** um bloco grande "Cole no Claude" com as teclas ⌘ + V (Ctrl + V no Windows), os dois passos, a prévia da mensagem e um botão para copiar de novo.
## 2026.10.23-10 (23/10/2026)
- **Menu:** os estilos dos motions abrem na aba "Todos"; a música ficou só com o sentimento e os exemplos de uso (sem o botão de amostra), e os cartões cabem melhor numa página só.
## 2026.10.23-9 (23/10/2026)
- **Ícones das plataformas no menu:** as abas e os cartões do passo de formato mostram o ícone do Instagram, TikTok, YouTube, Facebook, LinkedIn e Anúncios.
## 2026.10.23-8 (23/10/2026)
- **Menu mais fácil:** a legenda nativa agora se chama "Padrão do DaVinci" (ou do seu editor); a música é escolhida pelo sentimento, com exemplos de uso e um botão ▶ para ouvir uma amostra do clima; os estilos dos motions vêm em abas por tipo de conteúdo, com uma aba "Sugeridos"; cartões maiores, e quando não cabe tudo o passo vira páginas (‹ 1/2 ›) em vez de letra miúda.
- **Nada passa em branco:** o "Avançar" só libera depois de marcar uma opção ou apertar "Automático neste passo".
- **Mensagem do Confirmar:** sai por extenso, uma linha por passo, sem caminho de pasta (funciona em qualquer computador).
## 2026.10.23-7 (23/10/2026)
- **Menu sem rolagem:** os cartões se ajustam ao tamanho da tela e cada passo mostra todas as opções de uma vez, inclusive em telas grandes; quando não cabe, a descrição curta vira dica ao passar o mouse.
## 2026.10.23-6 (23/10/2026)
- **Ajuste de enquadramento não quebra mais com vídeo do DaVinci 21:** o `enquadramento.py` lia o tamanho do vídeo errado em alguns MP4 exportados e parava. Não precisa fazer nada.
- **Trocar os títulos duas vezes na mesma timeline:** a segunda troca do lettering parava com erro; agora a timeline auxiliar ganha um nome livre ("(titulos via API 2)") e, se o DaVinci recusar, o Gab avisa com clareza.
## 2026.10.23-5 (23/10/2026)
- **Revisão do menu redesenhada:** anel com quantas escolhas são suas e quantas ficaram no automático, e um cartão por passo com a prévia em loop do que você marcou (clique para mudar).
- **Confirmar volta para o Claude:** ao confirmar, o Gab recebe as escolhas na hora, o Claude vem para a frente e a mensagem já fica copiada; se precisar, é só colar (Cmd+V) no Claude.
## 2026.10.23-4 (23/10/2026)
- **Menu mais organizado:** o formato agora é escolhido por plataforma (Instagram, TikTok, YouTube, Facebook, LinkedIn e Anúncios), com proporção e resolução de cada um; dá para marcar vários. A legenda tem a opção nativa do seu editor (como o preset GAB USA do DaVinci) separada das animadas. O lettering mostra os títulos do editor que você usa (DaVinci, Premiere, CapCut ou Final Cut). O passo de estilo virou "estilo dos motions" e some se você marcar "sem motion". O botão de cada passo agora se chama "Automático neste passo".
## 2026.10.23-3 (23/10/2026)
- **`/ogab menu`:** antes de criar um vídeo, o Gab pergunta se você quer escolher no menu ou deixar no automático. O menu abre no navegador com a cara da /ogab, em português ou inglês, um passo por tela (formato, estilo, legenda, lettering, motion, b-roll, música, efeitos, ritmo, cor e extras), com prévias em loop e um check em cada opção. O que você não marcar, o Gab escolhe; no automático, ele decide tudo pelo que já sabe de você e da marca.
## 2026.10.23-3 (23/10/2026)
- **Modo sem editor:** quem não tem editor de vídeo escolhe "Nenhum" na instalação (ou `/ogab config editor nenhum`) e o Gab faz o vídeo inteiro aqui no Claude, entregando o MP4 pronto (roteiro, voz, legenda, música, SFX e motions). Ele recomenda instalar pelo menos o CapCut (grátis) para você poder mudar o que quiser; se instalar depois, `capcut.py levar` leva os vídeos já feitos para o CapCut. Quem escolheu um editor continua tendo tudo montado nele.
## 2026.10.23-2 (23/10/2026)
- **Lettering volta a sair do seu pacote de títulos do DaVinci:** pedido de lettering, palavra-chave ou texto na tela usa os títulos animados que o instalador colocou no DaVinci (editáveis no Inspector). O HyperFrames só entra quando você pede motion. O Gab não pergunta mais do título OGraf; ele só é usado se você pedir.
## 2026.10.23-1 (23/10/2026)
- **Motion atrás da pessoa com o Magic Mask:** o Gab marca a pessoa sozinho no Magic Mask do Fusion (cabelo, mãos e objetos que ela segura, modo Faster), clica em rastrear e deixa a composição na timeline, numa trilha acima do motion, para você ajustar se precisar. A versão por profundidade virou plano B.
## 2026.10.22-8 (22/10/2026)
- **Motion atrás da pessoa, direto no DaVinci:** o Gab recorta a pessoa no Fusion com a IA de profundidade do próprio DaVinci (sem pintar e sem rastrear) e coloca o recorte numa trilha acima do motion; o motion, o lettering ou o objeto ficam atrás da pessoa e continuam editáveis na timeline. O corte é calibrado sozinho pelo rosto. Quando a pessoa está encostada no fundo, ele monta o Magic Mask para você só pintar e clicar em rastrear.
## 2026.10.22-7 (22/10/2026)
- **Menos tokens com imagens:** o Gab passa a olhar quadros, prints e fotos numa cópia de até 1024 px (o arquivo original não muda), o que gasta cerca de 60% menos por imagem. O `doctor` liga isso sozinho no Mac e no Windows; abra o Claude Code de novo depois de atualizar. Para ver um detalhe em tamanho cheio: `scripts/olhar.py recorte`.
## 2026.10.22-6 (22/10/2026)
- **Cortes de gravação com a transcrição do DaVinci:** o `cortes.py plano` agora lê a transcrição feita pelo próprio DaVinci (antes quebrava com erro de número). Não precisa fazer nada.

## 2026.10.22-5 (22/10/2026)
- **CapCut pela linha de comando:** `capcut/capcut.py` faz no CapCut o que o Gab já fazia no DaVinci, sem clicar: monta ou edita um rascunho a partir de um plano, lista e confere rascunhos (mídia offline, efeito sem arquivo, buraco na V1) e abre o projeto em 1o na tela inicial.
- **Prévia do CapCut sem o CapCut:** `capcut.py previa` renderiza o rascunho em MP4 direto (vídeo, fundo desfocado, textos, áudio), com o tamanho do texto medido no motor do CapCut. Exportar pelo próprio CapCut continua sendo um clique seu (o diálogo de exportação só aceita comando com o app na frente).
- **Cortes de vídeo longo no CapCut:** `capcut.py cortes` cria um rascunho vertical por corte (fundo desfocado, gancho no topo, legenda embaixo) a partir da fábrica de cortes.
- **Cortes de link do YouTube mais rápidos:** `scripts/vtt_transcricao.py` usa a legenda automática do YouTube como transcrição, para escolher os cortes antes do vídeo terminar de baixar.
- **Fábrica de cortes:** o fim do corte não pega mais o começo da palavra seguinte, e o `conferir` aceita o mesmo `--pausa` do `frases` (antes os S1, S2... apontavam para outras frases).
- **CapCut, um comando por ação:** `capcut.py faz "<rascunho ou CORTE*>" <ação> ...` roda qualquer ação (texto, transição, filtro, máscara, zoom, keyframes, adesivo, voz...) em um ou vários rascunhos de uma vez, encadeando com `+`. Seletores curtos no lugar dos ids (`@v0:2`, `@v0:todos`, `@em=12.5`, `@texto=Lula`); `capcut.py ids` mostra o seletor de cada clipe, `ops` lista as ações, `catalogo` e `loja` acham os nomes. Novas: `estilo_texto` (muda tamanho/cor/fonte/posição da legenda de todos os cortes num comando) e `trocar_texto`.
- **CapCut, recursos conferidos no app:** transição, filtro, efeito, adesivo, máscara, animação de entrada de vídeo, entrada e loop de texto e efeito de voz funcionam. Animação de legenda da loja ainda não (o Gab avisa em vez de gravar).
- **Prévia em lote:** `capcut.py previa "CORTE*" <pasta>` renderiza vários rascunhos em paralelo.
- **CapCut, legenda animada palavra por palavra:** descoberto o formato da legenda automática do CapCut (tempo de cada palavra). `animar(..., legenda=...)` volta a funcionar e a fábrica de cortes (`capcut.py cortes`) já grava o tempo real de cada palavra; `--anim-legenda <nome ou id>` liga a animação.
- **CapCut, palavra-chave colorida:** `texto(..., destaques={"LULA": "#FFE600"})` ou `destacar` pinta palavras dentro da legenda.
- **CapCut, modelos de legenda da loja** agora carregam com o seu texto (antes vinha o texto de exemplo do modelo).
- **CapCut, loja sem itens de teste:** itens internos que o app não baixa saíram da lista; `capcut.py validar` monta um lote para o app testar e guarda o que funciona.
- **CapCut, mais edição:** recortar clipe, espelhar (horizontal/vertical), caixa ou pílula atrás do texto (`fundo=`) e sombra do texto (`sombra=`), tudo conferido abrindo no CapCut. A prévia (`capcut.py previa`) agora desenha fundo e sombra, então bate com o app.

## 2026.10.22-4 (22/10/2026)
- **Suas invenções ajudam todo mundo:** além dos motions novos, o Gab agora também encontra os scripts novos e as melhorias que você (ou o Claude) fizer nos arquivos da skill e manda ao Gabriel, anônimo, para virar novidade para todos. Por isso os termos foram para a versão 2, e o Gab pede o aceite de novo uma vez.

## 2026.10.22-4 (22/10/2026)
- **O Gab escolhe o preset sozinho e diz por quê:** lê o seu pedido (anima arte, cortes, abertura de logo, lançamento, animação para site...) e o roteiro frase por frase, escolhe o estilo do vídeo pelo assunto e coloca o preset certo em cada trecho (gráfico no dado, ranking, comentário, marco...).
- **Seletor de presets com GIF:** se preferir escolher você, peça "quero escolher o preset" (ou `/ogab seletor`). Abre uma página com a prévia animada de cada preset; clique no trecho, depois na miniatura, e confirme. O Gab segue com a sua escolha.

## 2026.10.22-3 (22/10/2026)
- **Termos de uso:** para instalar e usar o Gab agora é preciso aceitar os termos (digitando ACEITO). Quem já usa vai ver os termos na próxima vez que abrir o Gab. Eles explicam a licença de uso e que o Gab envia ao Gabriel, de forma anônima, os erros que corrigir e a estrutura dos motions novos (nunca vídeo, roteiro, cliente ou dado pessoal). Texto completo em `docs/TERMOS.md`.
- A apresentação ao Gabriel agora pede só o nome.

## 2026.10.22-3 (22/10/2026)
- **Preset novo: painel** (apresentação de app e fintech). Fundo navy com uma cor de destaque, linha de gráfico que se desenha, cartões do app em 3D com os números rolando, câmera mergulhando no cartão, disco da cor cobrindo a tela e fecho com a marca. Peça "no preset painel".
- **Storyboard:** não quebra mais quando o texto de uma cena vem em lista (linhas, palavras, grupos).

## 2026.10.22-2 (22/10/2026)
- **Preset launch, cenas de texto mais vivas:** `flutuantes` (lista de imagens) espalha cartões nas bordas, atrás da frase, com profundidade e paralaxe. O fecho aceita `tamLogo`.
- **Preset launch na batida:** `batida` no plano dá um pulso às cenas a cada compasso da música; a lista aceita `cada`/`inicio` para cada item entrar na batida.
- **Preset launch com vídeo no painel:** a cena `tela` aceita `quadros` (uma sequência de JPGs que toca dentro do vidro, por exemplo um mosaico de motions rodando ou uma análise quadro a quadro). `<video>` dentro do painel 3D sai deslocado no render, por isso a sequência.
- **Preset launch, cena nova `editor`:** um DaVinci simulado montando a timeline (voz, takes, legenda, música, b-roll, motion e SFX entrando um por um, com aviso do que a IA está fazendo). Ideal para apresentar produto de edição.
- **Preset launch:** o fecho agora aceita `tam` como as outras cenas, para a letra ficar grande em vídeo 16:9; o logo aceita `tamFrase` para a frase embaixo dele; e o fundo já começa aceso no primeiro quadro.
- **Launch, gancho em batidas:** a palavra em destaque da primeira frase agora sai junto com ela (antes ficava por cima da frase seguinte).
- **Trava do "começa do preto":** não acusa mais quando o que acende é só um texto grande entrando; fade do preto de verdade continua travando.

## 2026.10.22-2 (22/10/2026)
- **Conheça quem fez o Gab:** uma vez, o Gab pergunta se você quer se apresentar ao Gabriel (só o nome que você confirmar). É opcional; dizendo não, ele não pergunta de novo.
- De vez em quando (no máximo uma vez por semana) o Gab lembra que dá para deixar uma estrela na skill no GitHub e seguir o Gabriel no Instagram, @gabrielxreis_.

## 2026.10.22-1 (22/10/2026)
- **Banco de presets da comunidade:** os motions que você cria (preset novo a partir de uma referência ou modelo salvo na biblioteca) são encontrados sozinhos e, se forem bem diferentes do que já existe e você tiver dito "sim" aos relatos, vão anônimos para o Gabriel avaliar. Os aprovados entram para todo mundo no próximo update. O banco inteiro fica em `biblioteca_motions/CATALOGO.md`.
- **5 presets novos:** **ranking** (tier list e top 3 que se montam com a fala), **respostas** (faixa de "?" que vira resposta, estilo entrevista de rua), **comentário** (card de comentário de seguidor), **cartões** (provas empilhando em profundidade) e **podcast** (tela dividida com legenda na cor de quem fala, acompanhando a cabeça). Peça pelo nome ou deixe o Gab escolher.
- **Grade com palavras para estudar referência:** `grade.py <video> --transcrever --cortes` mostra os quadros do vídeo com a palavra falada embaixo de cada um e os cortes marcados, para ver em que palavra cada texto ou motion entra e sai.
- **Duração do roteiro antes da voz:** `estimar.py --arquivo roteiro.txt` diz quantos segundos cada trecho vai durar (sílabas do português). Depois do primeiro vídeo, `estimar.py calibrar` aprende o ritmo da voz e acerta ainda mais.
- **Plano preso à palavra:** SFX e motions guardam em que palavra entram (`ancorar.py`). Regravou a narração ou trocou a voz? Tudo se reposiciona sozinho na fala nova.
- **Correções que vieram dos relatos:** Premiere coloca a música no tempo certo mesmo com ponto de entrada no meio da faixa, volta a ter a curva de volume (`envelope_volume`, para abaixar a música sob a fala) e a legenda entra em timeline ainda sem vídeo.
- **Variações de gancho para anúncio:** o mesmo vídeo com 3 a 5 ganchos diferentes, uma timeline por gancho e o corpo aninhado (mexeu no corpo, muda em todas). `variantes.py`.

## 2026.10.20-3 (20/10/2026)
- **Efeitos sonoros grátis do Pixabay:** quem não tem Artlist nem Envato (ou quando eles não acham o som) agora recebe SFX do Pixabay, sem conta e com uso comercial liberado. O Gab busca pelo navegador, baixa em WAV pronto para o DaVinci e anota a licença de cada som.

## 2026.10.20-2 (20/10/2026)
- **Mais acervo livre para b-roll:** além de Commons e NASA, a busca agora procura no Internet Archive (cinejornal e filmes antigos em domínio público), no Metropolitan Museum e no Art Institute of Chicago (pinturas, gravuras e mapas em domínio público). `--previa` mostra as miniaturas numeradas para escolher olhando.
- **Fábrica de cortes:** uma aula, live ou podcast vira vários cortes verticais, cada um numa timeline própria no DaVinci, em ordem de força. O Gab confere se cada corte prende no começo, se entende sozinho e se termina numa conclusão.

## 2026.10.20-1 (20/10/2026)
- **Novo preset GRAVURA:** cada frase vira uma prancha de gravura em cobre que se grava sozinha (contorno, hachura, título cortado letra a letra, nota em cursiva e aquarela só no que importa). Para história, fé, tradição e herança de marca. Peça "no preset gravura". Motor do lemo-opuscar (MIT).
- **Revisor mede o tempo de leitura:** lê o texto de cada quadro (OCR do Mac) e avisa quando uma frase sai da tela antes de dar tempo de ler.
- **Voz IA ouvida de volta:** a conferência final transcreve a narração e compara com o roteiro aprovado, apontando palavra, número ou nome falado errado com o tempo.

## 2026.10.19-6 (19/10/2026)
- **Motion HyperFrames da comunidade chega inteiro:** ao salvar um motion HyperFrames na biblioteca (`biblioteca_motions.py salvar modelo.json --pasta <pasta do motion>`), os arquivos do motion vão junto, e o relato anônimo leva esses arquivos (sem cor da marca, sem texto do cliente, sem nome nem pasta) para o Gabriel renderizar e publicar para todos. Só sai motion bem diferente dos presets que já existem.

## 2026.10.19-5 (19/10/2026)
- **Premiere: motion MOV sem áudio volta a entrar na timeline.** No Premiere 26.5 o motion (MOV com alfa, sem trilha de áudio) dava "startTime must be less than endTime"; agora o Gab confere se o arquivo tem áudio e, se não tem, coloca direto.
- **Premiere: volume certo.** Todo ganho de clipe entrava 15 dB alto (música pedida a -9,5 dB tocava a +5,5 dB e o export estourava). Vídeos montados no Premiere antes desta versão: refaça a mixagem (`P.volume`) ou abaixe os clipes 15 dB.

## 2026.10.19-4 (19/10/2026)
- **Organizar o Media Pool por vídeo:** `scripts/organizar_por_video.py` cria uma pasta por vídeo ("NN Nome") com Takes, Motions, Audio e Timelines, sem mexer em timeline nenhuma.
- **Export de vídeo já finalizado:** `renderizar(..., sem_cor=True)` para material de terceiro (dublagem) que não leva PowerGrade.
- **23,976 em timeline de 24:** a doc agora explica como saber se o DaVinci tocou quadro a quadro ou no tempo real antes de converter tempos.

## 2026.10.19-3 (19/10/2026)
- **DaVinci mais confiável em vídeo longo:** sincronia certa com vídeo 23,976 em timeline de 24, overlays sem vãos de quadro e troca de mídia sem desfazer seus cortes (detalhes em docs/etapas/davinci_api.md).

## 2026.10.19-3 (19/10/2026)
- **Armadilhas do Premiere e do HyperFrames registradas** (do job Baldi 08, Windows): instalador que não achava o Premiere fora do `Program Files`, `createSubClipAction` que não existe no Premiere 26.0, overwrite que recorta o clipe seguinte, Whisper local com PyAV incompatível, `npx` na pasta temporária e estado inicial escondido no lint. As correções já estavam no código; agora estão em `docs/PROCESSO.md` para não se repetirem.

## 2026.10.19-2 (19/10/2026)
- **Export sem imagem corrigido:** o render agora parte do preset H.264 Master e avisa se o arquivo sair sem vídeo.

## 2026.10.19-1 (19/10/2026)
- **Narração longa mais natural:** texto grande é gerado em trechos de ~1 minuto (a voz clonada fica estranha em gerações longas) e juntado de forma conferida num único `narracao.wav`.

## 2026.10.17-4 (17/10/2026)
- **Voz sempre no ElevenLabs v4:** toda narração sai no modelo eleven_v4. Texto longo (mais de 5.000 caracteres) é gerado em partes e juntado sozinho num único `narracao.wav`.

## 2026.10.17-3 (17/10/2026)
- **Preset LUME** (aprendido de um Reels de "antes e depois"): legenda com a palavra-chave brilhando em amarelo letra a letra, passando atrás da sua mão; cenas de mesa vista de cima com objetos que nascem desfocados, seta tracejada e anotação à mão que se desenham; mergulho de foco e luz vazada quente para o close. Peça com "no preset lume".

## 2026.10.17-3 (17/10/2026)
- **Corte de silêncio não come mais o fim da palavra:** o `silencios.py` confere no áudio e estica cada corte até a voz calar (a transcrição marcava o fim da palavra cedo).

## 2026.10.17-2 (17/10/2026)
- **Personagem nunca cortado:** `enquadramento.py` acha os rostos na prévia e reprova pessoa cortada, apertada ou no canto; material de arquivo 4:3 entra em moldura (inteiro, sobre o fundo do kit, acima da legenda).
- **Sketch com desenhos de iluminação** (luz de cima apagada, luz lateral 45-90° em planta baixa, afastar da parede, lado claro, rebatedor).

## 2026.10.17-1 (17/10/2026)
- **Preset SKETCH com bonequinhos:** bloco `desenho` (cenas de bonecos de palito que se desenham: câmera na igreja, editando de madrugada, bolso vazio, peso, oferta, apresentação...), `em` (quando o bloco entra, para casar com a fala), `tempos` (quando cada item da lista marca) e `base` (o desenho termina acima da legenda). Ícone novo: microfone.
- **Material real baixado entra direto na timeline:** o download inteiro deixou de ser recusado como "take re-renderizado"; vídeo que já vem em H.264 nem é re-encodado.
- **Windows:** storyboard acha o npm (npm.cmd); instalador do Premiere acha o Premiere instalado fora do C: (pelo programa aberto); Premiere 26.0 avisa com clareza que precisa do 26.5+ para subclipe.
- **Motion não começa mais do preto:** fundo já aparece no quadro 0 e o fade fica no DaVinci; `centro.py preto <motion>` trava quem começar escuro.
- **Filmagem de arquivo P&B exporta sem LUT** (a trava de cor não barra mais o export).
- **Legenda desce também debaixo de motion** (não só de lettering) no `legenda_ui.py`.
## 2026.10.16-4 (16/10/2026)
- **Instalar colando o link no Claude:** cole o link do GitHub do Gab no Claude e peça "instala". Ele pergunta no chat o editor, os motions, os relatos e a voz local, e instala mostrando o progresso: no painel Terminal do app você vê o painel ao vivo; no Claude Code ele cola o painel no chat a cada etapa (o que baixa, MB de quanto, velocidade, o que já tinha e o que falta). Se faltar o Homebrew, ele pede para você rodar um comando no Terminal (é o único passo que precisa da sua senha).

## 2026.10.16-3 (16/10/2026)
- **Instalador com painel ao vivo (Mac):** agora você vê o que está sendo instalado, quantos MB já baixou e de quanto, a velocidade, quanto tempo falta, o que já estava no seu Mac e o que ainda está na fila. No fim aparece o que não deu certo, com o comando para tentar de novo, e o log completo fica em `~/.claude/ogab-instalacao.log`. Para só ver o que tem e o que falta: `python3 ~/.claude/skills/ogab/scripts/instalador.py --lista`.

## 2026.10.16-5 (16/10/2026)
- **Motions, b-roll, SFX e música encaixam no quadro certo:** acabaram o quadro a menos e o vão de 1 quadro entre clipes colocados pelo Gab.
- **Sem clipe duplicado no Media Pool:** reimportar o mesmo arquivo reaproveita o clipe que já está lá.
- **Detecção de rosto não quebra mais** quando o OpenCV vem incompleto: o `/ogab doctor` conserta sozinho.
- **Motions sem neon por padrão:** a palavra-chave acende na cor da marca. Neon só se você pedir.
- **Transcrição e corte de silêncios mais firmes:** o Gab abre a página Edit e espera o DaVinci terminar de transcrever, e o corte de silêncios mantém o fps da sua timeline (antes podia virar 24 fps).
- **Letterings da V2 voltam a sair no vídeo:** timeline nova liga todas as trilhas, e o export avisa se alguma trilha com clipes estiver desligada.
- **DaVinci 21.0:** como os SFX e a música ficam no volume certo mesmo sem volume pela API.

## 2026.10.16-2 (16/10/2026)
- **Acabamento de cinema nos motions:** brilho estourado, grão de filme, separação de cor e luz entrando pelos cantos, em três níveis (sutil, suave, forte). Peça "com cinema" ou deixe `cinema: suave` no estilo do cliente. Funciona também nos motions com fundo transparente que vão por cima do vídeo.
- **Física nos motions:** peças (pílulas, moedas, velas, logos, ícones) que caem, quicam, empilham e depois explodem revelando o CTA. Ótimo para "tudo que você precisa", "acumular" e "bagunça vira solução".

## 2026.10.16-4 (16/10/2026)
- **Storyboard antes do render:** antes de renderizar um motion, o Gab te mostra o roteiro cena a cena e 3 quadros parados (gancho, cena principal e fecho). Você aprova ou pede ajuste pelo número da cena ("na 3, troca o texto"), e só aquela cena muda. Menos render jogado fora.
- **Revisor com nota antes de entregar:** o vídeo passa por uma conferência automática:
  - quadro preto ou imagem congelada;
  - gancho parado;
  - algo encostado na borda;
  - volume fora de -14 LUFS;
  - clichê proibido no código.

  Depois, um revisor de olhos novos dá nota de 0 a 10 em 7 critérios: gancho, leitura no celular, som na batida, acabamento, ritmo, marca e fatos, movimento. O Gab corrige os 3 piores e repete; só entrega com tudo acima de 8.
- **Clichês proibidos nos motions:** texto digitando letra a letra, brilho em texto, quique, degradê colorido em texto, fundo roxo e azul de "IA", movimento linear e efeitos empilhados ficam de fora. Só entram se você pedir ou se forem a assinatura do preset escolhido.
- **Presets novos:**
  - **GRÁFICO**: barras, linha, rosca ou comparação com o valor exato e a fonte do dado na tela;
  - **MARCO**: pontos que se juntam e formam o seu número;
  - **LOGO REVEAL**: abertura de marca com luz, linhas ou pontos.

  Todos têm GIF no README.
- **LOTTIE para site e app:** carregando, sucesso, curtir e botão "saiba mais" nas cores da marca, em arquivo leve que o site toca, com GIF de prévia.
- **Referência de estilo:** peça "um vídeo estilo X". O Gab busca na galeria Prompt Motion (230+ filmes feitos com Claude) e indica a AI x Leaders e a Promptcat. Ele assiste e recria a linguagem com o seu material, sem copiar.
- **Launch:** a perna do "g" e o acento no texto dourado não são mais cortados.

## 2026.10.16-4 (16/10/2026)
- **Efeitos novos para os motions:** palavras e cartões caindo e empilhando com física de verdade, esfera de pontos de "IA pensando" (6 jeitos: pensando, buscando, resolvendo, ouvindo, escrevendo, moldando), texto virando ASCII, lupa que estufa o texto e rabiscos à mão (círculo, sublinhado, seta, X e hachura) que se desenham e tremem como animação feita à mão.

## 2026.10.16-3 (16/10/2026)
- **Carrossel de motion:** peça "faz um carrossel de motion sobre X" e cada slide vira um vídeo 4:5 que se monta sozinho: título subindo, celular com o app (números contando, lista recebendo check), cartões ligados por fios, hub mostrando como tudo se conecta e o CTA digitando a palavra que a pessoa deve comentar. Sai um MP4 e um PNG por slide, nas cores da sua marca.

## 2026.10.16-3 (16/10/2026)
- **Preset novo LAUNCH (filme de lançamento de produto):** mande o link do seu site, curso ou app e peça "um vídeo de 15 s apresentando o produto". O Gab captura a página inteira e a cor da sua marca e monta um filme curto com acabamento premium, no estilo dos lançamentos da Apple:
  - fundo preto e uma ideia por cena;
  - frases entrando com curvas longas;
  - o logo nascendo com contraluz e brilho;
  - o seu site num painel de vidro flutuando em 3D;
  - os recursos um por vez e o fecho limpo.

  Escolha a letra **apple**, **editorial** ou **cinema**. Cada vídeo sai também com um GIF de prévia. Peça "no preset launch".

## 2026.10.16-2 (16/10/2026)
- **Família nova de presets para quem fala para a câmera (CENA):** você no centro e tudo acontecendo em volta. São presets separados que se combinam: **DESTAQUE** (legenda palavra por palavra com a palavra-chave grande em amarelo, em serifa com brilhinhos, em pílula com marca-texto ou em frase empilhada), **PALCO** (palavra gigante atrás da sua cabeça; o recorte é feito no próprio Mac, grátis), **ÓRBITA** (checklist que marca na hora da fala, barra "pronto 100%", caixa de comentário digitando a palavra do CTA) e **LENTE** (zoom rápido no rosto). **ÓRBITA** também tem cartões girando em volta de você (passam atrás da cabeça e na frente abaixo do queixo). Em todos, nada fica na frente do rosto: o Gab detecta o rosto, desce a legenda e manda a animação para trás de você. A **BANCADA** (tela verde de comentário) vem a seguir. Peça "no preset palco" (ou destaque, órbita, lente) ou deixe o Gab escolher.

## 2026.10.16-1 (16/10/2026)
- **Arte estática vira animação (PSD, Canva ou imagem):** peça "anima essa arte" e mande o PSD, o PDF do Canva (Compartilhar > Baixar > PDF Impressão, sem achatar) ou só a imagem. O Gab separa cada camada (fundo, pessoas, título, textos, pílulas, linhas, ícones), anima cada uma do jeito dela e entrega o vídeo com o último quadro igual à arte. Com Photoshop no Mac, os estilos de camada saem perfeitos (ele trabalha numa cópia, seu arquivo não é tocado). Rode `/ogab doctor` para instalar os leitores de PSD e PDF.

## 2026.10.15-11 (15/10/2026)
- **Legenda automática mais segura:** o Gab vai para a página Edit e espera o DaVinci terminar de criar as legendas (antes, com o DaVinci recém-aberto, a legenda saía vazia e o script quebrava). O preset GAB USA maximiza a janela do DaVinci sozinho antes de aplicar.
- **Motions sem quadro preto entre cenas:** as cenas saem com uma folga no fim e o Gab confere que não ficou buraco; flash, queima de filme e caixa de texto não aparecem mais antes da hora.
- **Vídeo preto e branco:** filmagem de arquivo P&B fica cinza neutro (sem a LUT, que deixava sépia).
- **Correções:** motion renderizado não é mais recusado quando você libera; o conferidor de SFX diz o que falta instalar (ou qual Python da máquina já tem) e o `/ogab doctor` mostra isso; a voz local avisa que não roda bem em Mac de 16 GB com o DaVinci aberto.

## 2026.10.15-10 (15/10/2026)
- **CapCut e Final Cut Pro no instalador (Mac, beta):** agora dá para escolher o editor entre DaVinci, Premiere, CapCut e Final Cut na instalação ou depois, com `/ogab config editor capcut` ou `/ogab config editor finalcut`. O `/ogab doctor` confere o app escolhido (no Final Cut, se tem uma biblioteca criada). No Windows continuam DaVinci e Premiere.

## 2026.10.15-13 (15/10/2026)
- **Preset novo GLASS (YouTube 16:9, da comunidade):** motions premium em vidro escuro com aurora violeta, título metálico e destaque em serifa itálica; cenas que entram deslizando junto com um empurrão de câmera no seu vídeo, seus prints com o número destacado por um anel, vinhetas de capítulo e cartão de like + inscreva-se. A cor violeta troca pela da sua marca. Peça "no preset glass".

## 2026.10.15-12 (15/10/2026)
- **Sua fila de render fica intacta:** o Gab só apaga os renders que ele mesmo criou.
- **Windows:** o DaVinci é encontrado em qualquer pasta (ex.: D:\DaVinci); provas de render em ProRes (o H.264 do Windows derrubava o DaVinci); Whisper na placa NVIDIA quando houver (9 min de áudio em ~30 s). Rode o instalador de novo para receber.
- **DaVinci 21.0:** a skill não quebra mais por falta de fade e volume pela API; ela avisa o que fazer à mão (ou atualize para o 21.1).
- **Trilhas religadas** depois de uma prova de render.

## 2026.10.15-11 (15/10/2026)
- **Silêncios também na narração:** em vídeo com voz gerada ou locução, o Gab tira as pausas longas da narração logo que ela entra na timeline, antes da legenda e dos takes (a versão original fica guardada como "<nome> - com silencios").

## 2026.10.15-10 (15/10/2026)
- **Windows: instalador não trava mais** depois de instalar ffmpeg, Python e Node (ficava parado com o processador em 100%). Se a instalação travou, feche o PowerShell e rode o comando de instalação de novo.
- **Windows: o instalador voltou a abrir** (um erro de digitação fazia ele parar logo no começo, com "Referência de variável inválida"). Agora todo instalador do Windows é testado automaticamente no PowerShell do Windows antes de chegar a você.
- **Log da instalação no Windows:** acompanhe ao vivo com `Get-Content $env:TEMP\ogab-install.log -Wait`. Instalando pelo Claude Code, veja no README como responder as 3 perguntas antes.
- **Instalador não trava mais no plugin do Premiere** quando o Premiere não está instalado (Windows e Mac): ele pula o plugin e avisa como instalar depois.

## 2026.10.15-9 (15/10/2026)
- **Nada sai sem efeito sonoro:** o Gab não exporta mais uma timeline sem SFX (a não ser que você peça) e roda o checklist antes de exportar ou agendar.
- **Sem quadro preto ao trocar trecho de trailer:** cortes de vídeos com outro fps (25, 23,976) agora fecham sem buraco entre eles; fades do próprio trailer são conferidos antes de exportar.
- **Barra de progresso:** motions em qualquer trilha passam a contar.

## 2026.10.15-9 (15/10/2026)
- **Preset SERIF AZUL:** Reels editorial com a palavra-chave da legenda em serifada itálica azul, passos 1-2-3 que acendem, slider "iniciante → profissional" e cenas em papel claro subindo por cima de você (celular, ícone 3D, amostras de cor, nuvem de marcas). Peça "no preset serif azul".
- **Efeitos sonoros em 3 passadas:** o Gab primeiro lista cada movimento, evento e virada do vídeo e sonoriza nessa ordem (whooshes, depois texturas, depois risers). Agora entra um riser com impacto uns 5 s depois do gancho e em cada troca de bloco, para dar a sensação de subida.

## 2026.10.15-8 (15/10/2026)
- **Motion sem corte no Instagram:** textos, números e logos dos motions ficam dentro da área segura do feed (4:5), e o Instagram não corta mais as bordas quando o Reels aparece no feed ou no perfil. O fundo animado continua ocupando a tela toda.

## 2026.10.15-7 (15/10/2026)
- **Logos nos motions:** quando a narração cita uma empresa ou plataforma (Amazon, Netflix, Prime Video...), o motion mostra a logo oficial em vez do nome escrito.

## 2026.10.15-6 (15/10/2026)
- **Vídeo horizontal em Reels vertical:** depois do reenquadramento, o Gab tira a tarja preta dos filmes (cinemascope) com o zoom certo e confere um quadro de cada corte: pessoa ou objeto sempre dentro do vertical. Corte com legenda queimada ou título cortado é trocado por outro trecho.
- **Correções:** projeto em 29,97/30 fps não muda mais para 24 ao criar a timeline com a legenda GAB USA; o lettering editável não trava mais o export como "take sem cor".

## 2026.10.15-5 (15/10/2026)
- **Clonador de voz local (opcional, Mac M1 ou mais novo):** o Gab clona a sua voz e narra no próprio Mac, de graça e sem limite, tudo por aqui (sem app para abrir). O instalador pergunta se você quer; para instalar depois, peça `/ogab voz-local instalar`. Toda geração mostra a barra de progresso ao vivo no terminal. Dá para escolher outros motores de voz com português (VoxCPM2, Confucius4, MOSS-Nano, PocketTTS). Atenção: o motor padrão (OmniVoice) é de uso **não comercial**; para vídeo de cliente, continue no ElevenLabs ou use um motor de licença aberta.

## 2026.10.15-4 (15/10/2026)
- **"Arruma esses aqui":** selecione os clipes no DaVinci e peça; o Gab mexe só neles.
- **Podcast e entrevista com 2 câmeras:** o Gab monta o multicâmera sincronizado pelo áudio e troca de câmera sozinho conforme quem fala. Você ainda pode trocar o ângulo de qualquer trecho.
- **Vídeo horizontal em vertical:** o Gab pode usar o Smart Reframe do DaVinci, que segue a ação em vez de cortar só o centro. Ele pergunta antes.
- **Take tremido:** estabilização automática.
- **Música:** volume e fades conferidos no próprio clipe; o Gab avisa em vez de perder a música quando a trilha A2 já está ocupada.

## 2026.10.15-3 (15/10/2026)
- **Lettering editável dentro do DaVinci (beta):** o Gab pode pôr a frase de efeito como título em HTML que você edita no Inspector (texto, cores, tamanho, posição), sem vídeo renderizado. Ele pergunta antes de usar. Rode o instalador de novo e reinicie o DaVinci para receber o título "GabLettering".
- **Mais seguro no DaVinci:** o Gab agora se protege de falhas conhecidas da automação (render que não começou, projeto não salvo, clipes que somem no salvar).

## 2026.10.15-2 (15/10/2026)
- **Mapa do que o DaVinci faz por automação:** o Gab agora sabe tudo que dá pra fazer no DaVinci sem clicar, o que só dá pela tela e as armadilhas conhecidas. Também ficou mais seguro tirar silêncio de clipe com velocidade alterada.

## 2026.10.15-1 (15/10/2026)
- **Memória da marca:** antes de editar, o Gab cria a pasta e um .md com o nome da marca. Ali ele anota o que você pediu de diferente, o que funcionou e o que fazer da próxima vez, e lê tudo antes do próximo vídeo da marca.
- **Silêncios pela transcrição do DaVinci:** depois dos cortes e antes da legenda, o Gab corta as pausas entre as palavras que o DaVinci reconheceu, sem depender do volume, e guarda a timeline original como backup.

## 2026.10.15-1 (15/10/2026)
- **Preset de legenda GAB USA incluído:** o arquivo vem com a skill (instalação e update). Na primeira legenda, se o preset não existir no seu DaVinci, o Gab importa sozinho. Não precisa criar nem baixar nada.

## 2026.10.15-3 (15/10/2026)
- **CapCut: zoom e buracos certos.** Vídeo gravado em pé não entra mais com zoom gigante, e a trilha principal do CapCut não gruda mais os clipes: os espaços vazios da timeline do DaVinci ficam onde estavam.
## 2026.10.15-2 (15/10/2026)
- **CapCut: filtros, adesivos, vozes e modelos de texto.** O Gab agora usa a loja do seu próprio CapCut (o que você já abriu nos painéis): filtros de cor, adesivos, efeitos de voz, modelos de texto e animações de legenda palavra a palavra.
- **Do DaVinci para o CapCut:** peça "recria essa timeline no CapCut" e o Gab monta no CapCut a timeline aberta no DaVinci (cortes, zoom, posição, áudio, transições e legendas), sem mexer no DaVinci.
## 2026.10.15-1 (15/10/2026)
- **CapCut (Mac, beta):** o Gab agora edita no CapCut. Ele monta a timeline direto no projeto: vídeo, b-roll, música com fade, texto, legenda do SRT, keyframes, corte de silêncio, transições, animações de entrada e saída, efeitos e máscaras (mais de 900 da loja do CapCut). Use `/ogab config editor capcut`. Na hora de salvar, o projeto precisa estar fechado no CapCut (o app pode ficar na tela inicial).
## 2026.10.14-5 (14/10/2026)
- **Música mais limpa sob a voz:** quando alguém fala, o Gab abaixa só a parte da música que disputa com a voz e mantém o grave, então a música não some nem fica magra.
- **Música medida de verdade:** o Gab mede o BPM, as batidas, o tom e o segundo em que a batida entra, em vez de confiar no número do catálogo. Cortes e motions caem na batida, e riser, drone e impacto com nota saem no tom da música.
## 2026.10.14-4 (14/10/2026)
- **Export trava se faltar cor:** se algum take ligado (em qualquer trilha) estiver sem o PowerGrade/LUT, o Gab não exporta e avisa quais são.

## 2026.10.14-3 (14/10/2026)
- **SFX conferidos e no tempo:** cada som passa pelo classificador antes de entrar, nada começa antes da própria ação, e cenas grandes (prédio caindo) ganham som em camadas. O Gab procura primeiro nas suas pastas de SFX.

## 2026.10.14-2 (14/10/2026)
- **Efeitos sonoros no tempo da imagem:** antes de pôr som, o Gab olha os quadros de cada corte; passo cai na pisada, carimbo no contato, e só entra som do que a imagem mostra.

## 2026.10.14-1 (14/10/2026)
- **Montagem no seu estilo:** o Gab agora monta em escada de trilhas, guarda o take antigo desligado por baixo do novo, entra no take já na ação, corta 1 quadro antes da palavra e casa o take com o verbo da frase.

## 2026.10.13-18 (13/10/2026)
- **Preset novo KINETIC (tipografia cinética):** cada batida da fala vira palavras enormes trocando no ritmo da voz, fundo preto/vermelho/branco e entradas variadas. Peça `/ogab faz um motion no preset kinetic com <frase>`.

## 2026.10.13-17 (13/10/2026)
- **Takes de IA sem câmera lenta:** o Gab agora pede velocidade real em todo vídeo do Kling e confere a velocidade antes de pôr na timeline; cena com uma ação só sai em 5 s.

## 2026.10.13-16 (13/10/2026)
- **LUT DO GAB no DaVinci:** o instalador agora coloca a LUT na pasta de LUTs do DaVinci (no Mac pode pedir a senha uma vez) e o Gab aplica a LUT em todos os takes sozinho. Se você tem um PowerGrade próprio, ele continua valendo no lugar. Rode o instalador de novo para receber a LUT e o lettering.

## 2026.10.13-15 (13/10/2026)
- **Instalador corrigido (Mac e Windows):** quem instalou hoje e viu o instalador parar no meio ("unbound variable" no Mac, janela fechando ou nada acontecendo no Windows): rode o instalador de novo, agora ele vai até o fim. Ele também garante um Python atual no Mac, instala o que faltava para o preset sketch e não para mais por falta de internet num item opcional.

## 2026.10.13-14 (13/10/2026)
- **Preset novo: SKETCH.** Motion com cara de desenho de marcador sobre fundo preto: os contornos coloridos se desenham na hora, um cursor pisca, os ícones surgem, o texto manuscrito aparece digitado e as setas se traçam, com o traço tremendo como animação feita à mão. Ótimo para tutorial, lista de ferramentas e passo a passo. Peça "no preset sketch".

## 2026.10.13-13 (13/10/2026)
- **Seus motions podem virar motions de todo mundo:** quando você salva um motion novo na biblioteca, o Gab pode mandar a estrutura dele (sem textos, cores da marca, nomes ou pastas) para o Gabriel, que publica os melhores para todos. O Gab vai perguntar uma vez se pode, junto com os relatos de erro.

## 2026.10.13-12 (13/10/2026)
- **Relatos de erro anônimos (opcional):** o Gab pergunta uma única vez se pode mandar ao Gabriel, sem nada pessoal, os erros da skill que ele corrigiu no seu computador. Com "sim", ele envia sozinho em segundo plano e a correção chega para todo mundo nas próximas atualizações. Nada de vídeo, roteiro, cliente, nome ou pasta sai da máquina. Mudar quando quiser: `/ogab config relatos sim` ou `nao`.

## 2026.10.13-11
- Trava: o Gab não consegue mais colocar na timeline um take que ele mesmo re-renderizou (acelerado, cortado, foto virada vídeo). Só o arquivo original baixado entra.

## 2026.10.13-10
- Vídeo baixado entra ORIGINAL na timeline: o Gab não re-renderiza nem muda a velocidade, só se você pedir.

## 2026.10.13-9
- Takes de IA: toda imagem vira vídeo (nada de foto parada) e os cortes seguem a legenda, um por frase, contando a história.
- Legenda em timeline 24 fps: `legendas.py ... --fps 24` (antes lia sempre a 30 e a legenda podia sair até 0,2 s fora).

## 2026.10.13-8
- Efeitos sonoros caem no tempo do movimento: o plano agora é escrito pelo instante do evento e o Gab corta o silêncio do começo de cada som (`plano_sfx_eventos.py`). Nada para você fazer.


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
