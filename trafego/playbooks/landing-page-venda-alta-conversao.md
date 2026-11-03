---
name: landing-page-venda-alta-conversao
description: Cria (e pontua de 0 a 100) página de vendas longa de alta conversão para curso online ou infoproduto vendido no Brasil (ticket perto de R$ 997, tráfego do Meta Ads, maioria no celular). Estrutura seção por seção, regras de mobile e velocidade, copy, urgência só verdadeira (CDC e política do Meta), cuidados do nicho de finanças, Pixel + CAPI + UTM até o checkout e checklist de nota. Use para criar, reescrever ou revisar página de vendas, página de captura de alto ticket ou VSL page. Platform: Meta.
metadata:
  platform: Meta
---

# Página de vendas de alta conversão (infoproduto, Brasil, Meta Ads)

## O que faz
Monta do zero, ou reescreve, a página de vendas longa de um curso ou infoproduto (ticket na faixa de R$ 997) que recebe tráfego frio e morno do Meta Ads, quase todo no celular. Também roda uma nota de 0 a 100 em qualquer página pronta, com a lista do que corrigir primeiro.

## Quando usar este e quando usar os outros
- **Este playbook:** criar a página, definir a ordem das seções, escrever a copy, revisar oferta, urgência, compliance e rastreamento de uma página de VENDA (checkout no fim).
- **`landing-page-audit`:** conferir se cada anúncio bate com a página (message match), anúncio por anúncio.
- **`landing-page-audit-39`:** CRO genérico de qualquer landing (headline, CTA, confiança).
- **`ads-landing` (claude-ads):** auditoria técnica com fetch seguro (redirect, consentimento, segurança, formulário).
- Copy de anúncio que leva para a página: `ad-copy-variant-generator`. Teste A/B da página: `ab-test-setup-and-analysis`.

## O que pedir antes de começar
1. Produto: nome, promessa central, para quem é e para quem NÃO é, formato (aulas gravadas, ao vivo, comunidade, mentoria), tempo de acesso.
2. Preço: à vista, parcelado (quantas vezes e se tem juros), Pix, cupom. Plataforma de checkout (Hotmart, Kiwify, Eduzz, outra).
3. Bônus reais, com prazo real (data e hora em que saem, se saem).
4. Garantia: quantos dias e em que condição.
5. Provas: depoimentos com nome e autorização, prints, números de alunos, mídia, tempo de mercado. Só o que existe.
6. Mentor: história curta, credenciais verificáveis, foto boa.
7. Anúncios que vão rodar (ganchos e ângulos), para casar a primeira dobra com cada um.
8. Nicho regulado? (finanças, saúde, emagrecimento, renda). Se sim, ler a seção de compliance antes de escrever uma linha.
9. Dados atuais, se a página já existe: taxa de conversão da página (compras / visualizações da página), taxa de clique no botão, taxa de checkout iniciado para compra, % de tráfego mobile, Core Web Vitals.

Sem cliente salvo, perguntar só o que faltar. Com cliente, ler `clientes/<cliente>/trafego.md` primeiro.

## A estrutura: seção por seção (ordem padrão)

A página é um argumento contínuo: cada seção responde a dúvida que a anterior criou. Ordem padrão para tráfego frio do Meta; para remarketing ou lista quente, dá para encurtar (hero, oferta, garantia, FAQ, CTA).

### 1. Hero (primeira dobra no celular)
- Headline com o resultado desejado + o público + o prazo ou mecanismo, nas palavras do anúncio que trouxe a pessoa. Específica, não esperta.
- Subheadline com o "como" (o método em uma frase) e a quebra da objeção principal ("mesmo que você nunca tenha...", só se for verdade).
- VSL ou imagem do mentor/produto. VSL com capa clicável (fachada) em vez de carregar o player inteiro na abertura.
- Botão principal visível SEM rolar em tela de 360 x 640. Texto do botão diz o que a pessoa ganha ("Quero entrar na turma", "Garantir minha vaga com bônus"), nunca "Enviar" ou "Saiba mais".
- Uma prova curta perto do botão: número de alunos verificável, nota, logo de mídia ou um depoimento de uma linha.
- Sem menu de navegação, sem link para Instagram ou outra página. Uma página, uma ação.
- Se a oferta tem prazo real, a data aparece aqui em texto ("inscrições até domingo, 02/11, 23h59").

### 2. Dor e agitação
- Descrever a situação atual do público com as palavras que ele usa (tirar de comentários, DMs, pesquisas, call de vendas).
- Mostrar o custo de continuar assim (tempo, dinheiro perdido, frustração), sem humilhar e sem perguntar atributo pessoal ("você está endividado?" fica fora: política do Meta e bom senso).
- Nomear por que as tentativas anteriores falharam (não foi culpa da pessoa, foi o método). Isso prepara o mecanismo.

### 3. Mecanismo (o método)
- Dar nome ao método e explicar em 3 a 5 passos ou pilares, cada um com o que a pessoa ganha.
- Mostrar por que ele é diferente do que ela já tentou. Diferença concreta, não "revolucionário".
- Um diagrama ou imagem simples do método vale mais que um parágrafo.

### 4. História do mentor
- Curta (5 a 8 linhas ou 60 a 90 s no vídeo): de onde veio, o ponto de virada, o que construiu, por que ensina.
- Credenciais verificáveis: anos de mercado, alunos, onde já apareceu. Nada inventado ou arredondado para cima.
- Foto real, não banco de imagem.

### 5. Prova social
- Depoimentos com nome, foto ou vídeo e contexto (quem era antes, o que fez, o que mudou). Autorização por escrito de cada aluno.
- Variedade de perfis, para cada visitante se ver em pelo menos um.
- Depoimento em vídeo curto (até 40 s) com legenda, porque a maioria assiste sem som.
- Resultado financeiro de aluno só com aviso de que não é típico nem garantido (ver compliance). No nicho de finanças, preferir depoimento sobre aprendizado, disciplina e método, não sobre lucro.

### 6. O que está incluído (pilha da oferta)
- Lista em blocos: cada módulo ou entregável com nome + resultado que ele gera + formato (horas de aula, encontros ao vivo, comunidade, suporte, prazo de acesso).
- Mostrar a plataforma (print da área de membros no celular).
- Âncora de valor só se for verificável: preço que o próprio produtor já cobrou, ou preço de mercado de algo equivalente. Valor inventado ("R$ 12.000 em conteúdo") é propaganda enganosa e derruba confiança.

### 7. Bônus (com prazo real)
- 3 a 5 bônus, cada um fechando UMA objeção (sem tempo: plano de 30 dias; vou travar: plantão de dúvidas; não sei por onde começar: aula de configuração; e assim por diante).
- Valor declarado de cada bônus verificável; soma dos bônus menor que 2x o preço do produto.
- Se o bônus tem prazo, ele SAI na data dita. Escrever a data e a hora. Depois do prazo, tirar da página e do checkout.

### 8. Preço e CTA principal
- Preço claro: "12x de R$ XX,XX" e "ou R$ 997 à vista no Pix" (valor da parcela exatamente como o checkout cobra). Parcelado com juros: dizer que tem juros e o valor total (CDC art. 52 manda informar o preço total e os encargos no financiamento).
- Comparação honesta para dar escala ao preço (custo de uma consultoria, de continuar errando, de um curso presencial), sem prometer retorno.
- Botão grande, cor de contraste única na página (essa cor só para CTA), com microcopy embaixo: "Pagamento seguro pela Hotmart. Acesso imediato por e-mail."
- Selos de pagamento (Pix, cartão, boleto) e de segurança perto do botão.

### 9. Garantia
- Lembrar: compra online já tem 7 dias de arrependimento por lei (CDC art. 49). Garantia de 7 dias não é diferencial, é obrigação. Diferencial é prazo maior (15, 30 dias) ou condição clara e simples.
- Escrever em linguagem humana, com a condição exata e como pedir ("mande um e-mail em até 30 dias e devolvemos 100%, sem perguntas").
- Selo visual + 2 a 3 linhas. Nada de "100% garantido" sem dizer o quê.

### 10. Para quem é / para quem não é
- Duas listas curtas. "Não é para quem quer ficar rico rápido" filtra o público errado, aumenta confiança e reduz reembolso.

### 11. FAQ (quebra de objeção)
- 6 a 10 perguntas tiradas de objeções reais (comentários dos anúncios, chat, reembolsos, call). Ordem: as que mais travam a compra primeiro.
- Obrigatórias: quanto tempo de acesso, como recebo, preciso de experiência, quanto tempo por dia, funciona no celular, tem suporte, e se eu não gostar (garantia), formas de pagamento, emite nota fiscal.
- Acordeão fechado no celular, com a pergunta inteira visível.

### 12. CTA final + recapitulação
- Resumo da oferta em lista (produto + bônus + garantia + preço) e o botão de novo.
- Prazo real repetido, se existir.
- Contato de suporte (WhatsApp ou e-mail) para dúvida antes da compra.

### 13. Rodapé legal
- Razão social e CNPJ do produtor, link para termos e política de privacidade, aviso de risco (nichos regulados), aviso de que resultados variam.

### CTA repetido e barra fixa
- Botão depois do hero, do mecanismo, da prova social, da oferta, da garantia e do FAQ (em média a cada 1,5 a 2 telas de rolagem no celular). Todos levam ao mesmo checkout.
- Barra fixa no rodapé do celular com o botão (e o preço curto), que aparece depois que a pessoa passa do hero e some quando o bloco de oferta está na tela, para não cobrir o botão principal. Altura até 64 px, não cobre texto, não pisca.

## Regras de mobile (a maioria do tráfego do Meta é celular)
- Projetar primeiro em 360 x 640 e 390 x 844; desktop é adaptação.
- **Zona do polegar:** ação principal na metade de baixo da tela ou na barra fixa. Nada importante nos cantos de cima.
- **Alvo de toque:** botões com pelo menos 48 x 48 px e 8 px de folga entre alvos (o mínimo do WCAG 2.2 é 24 x 24 px; 44 a 48 é o recomendado). Botão principal ocupa a largura toda menos as margens.
- **Texto:** corpo com 16 px ou mais, linha com 1,5 de altura, parágrafos de até 3 linhas no celular, contraste de pelo menos 4,5:1.
- **Sem pop-up** cobrindo a página na abertura (atrapalha a leitura, derruba a conversão e o Google penaliza intersticial intrusivo no celular).
- **Navegador do Instagram/Facebook:** testar a página DENTRO do app (navegador interno), não só no Chrome. Vídeo com autoplay mudo e legenda; checkout tem de abrir sem pedir login.
- **Formulário de captura** (quando houver antes do checkout): no máximo nome, e-mail e WhatsApp, com teclado certo (`type="email"`, `type="tel"`, `inputmode="numeric"`) e autocomplete ligado.

## Velocidade e Core Web Vitals
Metas do Google para o percentil 75 dos usuários (limites da biblioteca `web-vitals`):

| Métrica | Bom | Precisa melhorar | Ruim |
|---|---|---|---|
| LCP (maior elemento visível carregado) | até 2,5 s | até 4 s | acima de 4 s |
| INP (resposta ao toque) | até 200 ms | até 500 ms | acima de 500 ms |
| CLS (página pulando) | até 0,1 | até 0,25 | acima de 0,25 |
| FCP (primeiro conteúdo) | até 1,8 s | até 3 s | acima de 3 s |
| TTFB (resposta do servidor) | até 0,8 s | até 1,8 s | acima de 1,8 s |

Como chegar lá:
- **Imagem do hero (geralmente o LCP):** WebP ou AVIF, largura certa para celular (até ~800 px), alvo de até 100 a 150 KB, `fetchpriority="high"`, SEM `loading="lazy"`. Pré-carregar com `<link rel="preload" as="image">` se vier de CSS.
- **Todas as outras imagens:** `loading="lazy"`, `width` e `height` declarados (evita CLS), comprimidas. Depoimento em print: recortar e comprimir, não subir o print de 2 MB.
- **VSL:** fachada (capa + botão de play) e o player só carrega no toque. Iframe de vídeo carregado de cara costuma ser o maior vilão do LCP e do INP.
- **Fontes:** no máximo 2 famílias e 3 pesos, `font-display: swap`, pré-conectar ao servidor de fontes.
- **Scripts:** Pixel, GTM e chat carregam depois do conteúdo (`defer`/`async`). Tirar scripts de construtor que não são usados. Cada script de terceiro é um custo.
- **Peso:** a primeira tela deve abrir com poucas centenas de KB; a página inteira, idealmente abaixo de 2 MB sem contar o vídeo (referência prática, não regra do Google).
- **Construtor de página (Elementor, WordPress, Greatpages, etc.):** cache ligado, CDN, imagens convertidas, e desligar animação de entrada em tudo (atrasa o LCP e gera CLS).
- Medir no PageSpeed Insights (dados de campo do CrUX quando houver) e no celular real, no 4G, dentro do Instagram.

## Regras de copy
- Uma ideia por seção, uma promessa central na página toda.
- Benefício antes de característica: "você sai sabendo X" antes de "40 aulas".
- Específico vence superlativo: números, prazos, nomes, exemplos. Cortar "revolucionário", "segredo", "que ninguém te conta", "método infalível".
- Palavras do cliente, não do produtor (tirar das pesquisas e comentários).
- Frases curtas, voz ativa, segunda pessoa ("você").
- Subtítulos que, lidos sozinhos, contam a história da página (muita gente só rola e lê títulos).
- Headline do hero bate com o anúncio: mesmo gancho, mesma promessa, mesma palavra-chave. Um anúncio com ângulo muito diferente pede uma variação da primeira dobra.
- Cada afirmação forte vem com prova logo do lado (depoimento, número, print).
- Ler a página em voz alta: toda dúvida que aparecer vira resposta no texto ou no FAQ.

## Urgência e escassez: só as verdadeiras
Valem (porque são reais e verificáveis):
- Data de fechamento da turma ou do carrinho, escrita em data e hora, que acontece de fato.
- Bônus que sai em data e hora ditas, e sai mesmo.
- Aumento de preço em data marcada, que acontece.
- Vagas limitadas por capacidade real (mentoria ao vivo, encontros com número de lugares).
- Contador regressivo SÓ se apontar para essa data real, igual para todo mundo, e não reiniciar.

Proibido na página (e o Jhon tira se encontrar):
- Contador que reinicia ao recarregar ou que é diferente por visitante (evergreen falso).
- "Últimas 3 vagas" sem limite real, barra de "87% vendido" inventada.
- "X pessoas vendo esta página agora", pop-up de "Fulano acabou de comprar" com dado falso ou genérico.
- "Preço sobe amanhã" quando não sobe; "só hoje" que se repete toda semana.
- Preço "de R$ 4.997 por R$ 997" quando nunca foi vendido a R$ 4.997.

Por quê: o Código de Defesa do Consumidor proíbe publicidade enganosa, inclusive por omissão (art. 37) e quem anuncia tem de provar o que diz (art. 38); o CONAR também condena. A política de publicidade do Meta reprova práticas enganosas e afirmações irreais, e a página de destino conta na revisão do anúncio e na nota de qualidade. Além disso, escassez falsa vira print nos comentários e destrói a confiança do público que mais compra (o que volta).

## Compliance no nicho de finanças (trading, investimentos, renda)
- **Sem promessa de ganho:** nada de "ganhe R$ 10 mil por mês", "renda garantida", "lucro todo dia", "saia da CLT em 90 dias", "taxa de acerto de 90%". Nem na headline, nem no vídeo, nem no depoimento escolhido.
- **Resultado de aluno:** se aparecer, com aviso visível do lado: "Resultados individuais. Não são típicos nem garantidos. Resultados passados não garantem resultados futuros."
- **Aviso de risco** no rodapé e perto do preço, em texto legível (não cinza claro em 10 px): operar mercado futuro e derivativos envolve alto risco e alavancagem e pode gerar perdas maiores que o capital investido; o conteúdo é educacional e não é recomendação de investimento.
- **Curso não é recomendação:** a página vende educação. Não oferecer "sinais", "call de entrada" ou carteira recomendada sem o registro exigido pela CVM para analista ou consultor (Resolução CVM 20/2021 e 19/2021).
- **Prints de operação:** só reais, com data, sem cortar o prejuízo do lado; ou nenhum.
- **Meta:** anúncio e página com promessa de dinheiro rápido caem na regra de afirmações enganosas e podem bloquear a conta de anúncios. Produtos financeiros e de investimento podem exigir categoria especial ou verificação; conferir a política vigente antes de subir.
- **Personal attributes:** copy não afirma nem insinua a situação pessoal do leitor ("você está quebrado?", "suas dívidas"); falar do problema em terceira pessoa ou de forma geral.
- Mesmo cuidado vale para saúde, emagrecimento e "renda extra": sem promessa de resultado, aviso de que varia, prova real.

## Rastreamento: Meta Pixel + Conversions API + UTM até o checkout
- **Pixel na página** com eventos:
  - `PageView` na abertura.
  - `ViewContent` quando a pessoa chega na seção de oferta/preço (ou após 50% de rolagem). Sinal de interesse para otimizar e montar público.
  - `InitiateCheckout` no clique de QUALQUER botão de compra (ou na abertura do checkout, pela integração da plataforma; escolher um dos dois, não contar em dobro).
  - `Lead` se houver captura antes do checkout.
  - `Purchase` NUNCA na página de vendas. Vem do checkout (Hotmart, Kiwify, Eduzz) pela integração de Pixel + API de Conversões da plataforma, com valor e moeda (`BRL`).
- **CAPI:** ligar a API de Conversões (pela plataforma de checkout, GTM server-side ou integração nativa). Mesmo `event_id` no evento do navegador e do servidor para o Meta deduplicar. Mandar e-mail e telefone com hash quando houver, para subir a qualidade de correspondência (EMQ). Conferir no Gerenciador de Eventos: eventos recebidos, desduplicação e EMQ.
- **UTM:** anúncio com `utm_source=meta&utm_medium=paid&utm_campaign={{campaign.name}}&utm_content={{ad.name}}&utm_term={{adset.name}}` (parâmetros dinâmicos do Meta). A página REPASSA todos os parâmetros da URL para o link do checkout (script que copia `location.search` para cada botão). Sem isso a venda chega no checkout sem origem.
- Na Hotmart, usar também o parâmetro `src` (ou `sck`) para ver a origem no relatório de vendas; em outras plataformas, conferir na documentação qual parâmetro aparece no relatório.
- **Domínio:** domínio da página verificado no Business Manager, eventos priorizados.
- **Consentimento e privacidade:** política de privacidade linkada, banner de cookies quando aplicável (LGPD).
- Teste antes de subir verba: clicar no anúncio de teste, conferir os eventos no Meta Pixel Helper e no "Testar eventos", e ver se a UTM chegou no checkout.
- Gerar a convenção de UTM com `utm-tracking-generator`; problema de atribuição vai para `ads-attribution`.

## Como o Jhon roda (criar)
1. Ler o `trafego.md` do cliente e os anúncios que vão rodar. Fazer as perguntas que faltarem.
2. Montar o esqueleto com as 13 seções, cada uma com o objetivo em uma linha e a prova que vai usar.
3. Escrever a copy da primeira dobra em 3 variações (uma por ângulo de anúncio). O usuário escolhe.
4. Escrever o resto da página na ordem. Marcar com `[PROVA]` onde falta prova real e com `[CONFIRMAR]` todo número, data ou valor que precisa ser confirmado pelo cliente.
5. Rodar a checklist abaixo no próprio texto antes de entregar.
6. Entregar: copy completa por seção, especificação de mobile (barra fixa, botões, imagens), lista de eventos e UTMs, e 3 hipóteses de teste A/B priorizadas.

## Como o Jhon roda (pontuar uma página pronta)
1. Abrir a página no celular (360 x 640 ou 390 x 844) e no desktop. Se possível, dentro do navegador do Instagram.
2. Rodar PageSpeed Insights (mobile) e anotar LCP, INP, CLS e peso.
3. Conferir os eventos no Pixel Helper e se a UTM chega no checkout.
4. Preencher a checklist, item por item, com evidência (print, trecho ou número).
5. Aplicar os eliminatórios. Entregar nota, os 5 consertos de maior impacto primeiro e as hipóteses de teste.

## Checklist de nota (0 a 100)

Cada item vale os pontos indicados: inteiro se atende, metade se atende em parte, zero se não atende.

### A. Primeira dobra no celular (15)
- [ ] (4) Headline específica com resultado + público, igual ao gancho do anúncio
- [ ] (3) Subheadline com o método ou a quebra da objeção principal
- [ ] (4) Botão principal visível sem rolar em 360 x 640, com texto de benefício
- [ ] (2) Prova curta perto do botão
- [ ] (2) Sem menu, sem links de saída, sem pop-up na abertura

### B. Oferta e preço (15)
- [ ] (4) O que está incluído em blocos com resultado de cada parte
- [ ] (3) Preço à vista e parcelado claros, juros e total informados quando houver
- [ ] (3) 3 a 5 bônus, cada um fechando uma objeção, valores verificáveis, soma menor que 2x o preço
- [ ] (3) Âncora de valor honesta (sem "de/por" inventado)
- [ ] (2) Para quem é e para quem não é

### C. Prova e credibilidade (12)
- [ ] (5) Depoimentos com nome, rosto ou vídeo e contexto, perfis variados
- [ ] (4) História do mentor com credenciais verificáveis e foto real
- [ ] (3) Prova perto de cada afirmação forte (números, prints, mídia)

### D. Copy e estrutura (12)
- [ ] (3) Dor descrita com palavras do público, sem humilhar e sem atributo pessoal
- [ ] (3) Mecanismo com nome e passos, diferente do que o público já tentou
- [ ] (3) Subtítulos contam a história sozinhos; parágrafos curtos
- [ ] (3) Sem jargão vazio ("revolucionário", "segredo", "infalível")

### E. Garantia e risco (6)
- [ ] (4) Garantia com prazo, condição e como pedir, em linguagem humana
- [ ] (2) Selo e texto perto do botão de compra

### F. Objeções e FAQ (6)
- [ ] (4) 6 a 10 perguntas de objeções reais, incluindo acesso, pagamento e garantia
- [ ] (2) Contato de suporte antes da compra (WhatsApp ou e-mail)

### G. CTA e checkout (10)
- [ ] (3) CTA repetido nos pontos de decisão, todos para o mesmo checkout
- [ ] (3) Barra fixa no celular que não cobre conteúdo nem o botão principal
- [ ] (2) Cor do botão exclusiva e de alto contraste
- [ ] (2) Checkout abre rápido no navegador do Instagram, com Pix e parcelamento, sem pedir login

### H. Mobile e velocidade (12)
- [ ] (4) LCP até 2,5 s no celular (2 pontos se até 4 s)
- [ ] (2) INP até 200 ms e CLS até 0,1
- [ ] (2) Imagens em WebP/AVIF, com tamanho declarado, lazy fora da primeira dobra
- [ ] (2) VSL com fachada (player só no toque)
- [ ] (2) Corpo 16 px ou mais, alvos de toque de 48 px, contraste 4,5:1

### I. Rastreamento (6)
- [ ] (2) PageView, ViewContent e InitiateCheckout disparando (conferido no Pixel Helper)
- [ ] (2) CAPI ligada com deduplicação por `event_id`; Purchase vindo do checkout com valor
- [ ] (2) UTMs repassadas para o checkout e visíveis no relatório da plataforma

### J. Compliance (6)
- [ ] (2) Rodapé com CNPJ, termos e política de privacidade
- [ ] (2) Aviso de que resultados variam (e aviso de risco em nicho financeiro)
- [ ] (2) Urgência só com data real e verificável

### Eliminatórios (qualquer um limita a nota a 49 e vira o conserto número 1)
- Contador falso, "X pessoas vendo agora", notificação de compra falsa ou "últimas vagas" sem limite real.
- Promessa de ganho financeiro, renda garantida ou taxa de acerto (nicho de finanças) ou de resultado garantido (saúde, emagrecimento).
- Depoimento, número de alunos, mídia ou preço "de" inventado.
- Purchase disparando na página de vendas (infla resultado e treina o algoritmo errado).
- Botão de compra quebrado ou checkout que não abre no navegador do Instagram.

### Leitura da nota
| Nota | Leitura | O que fazer |
|---|---|---|
| 85 a 100 | Pronta para escalar | Testar variações de primeira dobra e oferta |
| 70 a 84 | Boa, com vazamentos | Corrigir os itens de maior peso que falharam antes de subir verba |
| 50 a 69 | Fraca | Reescrever as seções que zeraram; não escalar |
| 0 a 49 | Não rodar tráfego | Resolver eliminatórios e a primeira dobra primeiro |

## O que entregar
- Nota total e por bloco, com evidência de cada item que perdeu ponto.
- Os 5 consertos de maior impacto, em ordem (peso do item x facilidade).
- Copy pronta para as seções reescritas (primeira dobra em 3 variações).
- 3 hipóteses de teste A/B no formato "se mudarmos X, Y sobe, porque Z" (ver `ab-test-setup-and-analysis`).
- Lista de pendências que só o cliente resolve (provas reais, autorização de depoimento, data real de fechamento).

## Fontes e licença
Playbook escrito para o /ogab trafego em português, adaptado ao mercado brasileiro. Ideias e estruturas aproveitadas de:
- **coreyhaines31/marketingskills** (MIT), https://github.com/coreyhaines31/marketingskills : skills `cro` (ordem de análise: proposta de valor, headline, CTA, hierarquia, confiança, objeções, atrito), `offers` com as referências `bonus-stacking.md` (bônus como quebra de objeção, 3 a 5 bônus, soma menor que 2x o preço), `guarantee-design.md` (como escrever a garantia) e `scarcity-urgency.md` (escassez honesta x falsa) e `copywriting` (clareza, benefício, especificidade, palavras do cliente). A mesma base existe instalada como `anthropic-skills:page-cro`, `copywriting` e `marketing-psychology`.
- **GoogleChrome/web-vitals** (Apache-2.0), https://github.com/GoogleChrome/web-vitals : limites de LCP, INP, CLS, FCP e TTFB (arquivos `src/on*.ts`).
- **thedaviddias/Front-End-Performance-Checklist** (MIT), https://github.com/thedaviddias/Front-End-Performance-Checklist : práticas de imagem, pré-carregamento, fontes e scripts.
- Complementa, sem repetir, os playbooks `landing-page-audit` e `landing-page-audit-39` (irinabuht12-oss/marketing-skills) e o `ads-landing` do claude-ads.
- Base legal citada (texto de lei, domínio público): Código de Defesa do Consumidor, Lei 8.078/1990, arts. 37, 38, 49 e 52; Resoluções CVM 19/2021 e 20/2021; WCAG 2.2 (critérios 1.4.3 e 2.5.8). Políticas do Meta mudam: conferir a versão vigente antes de subir a campanha.
