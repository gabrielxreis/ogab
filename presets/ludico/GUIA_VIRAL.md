# Preset LÚDICO: explicador de notícia viral (engenharia reversa do @ludificando.br)

Estudado em 26/10/2026: perfil com 73 mil seguidores e 37 posts, com reels de **4,7 mi, 2,3 mi, 2,1 mi e 1,1 mi** de views
(o de 4,7 mi teve 428 mil curtidas e 5,1 mil comentários). Foram 6 reels baixados, transcritos e analisados quadro a quadro
(4 que estouraram e 2 que ficaram em 16-56 mil). Aqui está a **linguagem**, não uma cópia: o visual é sempre o do cliente.

## Por que viraliza (o que os 4 grandes têm e os fracos não)
1. **Assunto quente do dia, com o número mais chocante no 1º segundo.** O vídeo do mercado saiu na noite da eleição, com
   "o fundo das ações brasileiras em Nova York chegou a cair quase 20%". Os fracos falavam de tema morno.
2. **Gancho em 1 frase com o fato e a consequência** (3-4 s), sem nenhum "oi" antes. Logo depois vem a promessa:
   "Vem que eu te explico de forma lúdica" (por volta dos 8 s).
3. **Uma ideia, um lugar e um número por bloco** (5-10 s cada). O número vem exato, com hora e lugar:
   "Às 21h14, o EWZ caía 19,42%". Precisão passa credibilidade e faz o vídeo ser compartilhado.
4. **Uma metáfora visual só no vídeo inteiro**, num cenário 3D contínuo em que a câmera viaja e não há corte seco
   (o detector achou 0 ou 1 corte nos vídeos de 1-2 mi). O que muda é a câmera: globo girando até cada cidade,
   púlpitos com holofote no debate, um mar de urnas que acendem.
5. **Virada no meio:** "Mas atenção", com a ressalva honesta (mercado da noite, pouca liquidez, "o teste é amanhã às 10h").
6. **"Por que isso importa pra você"** com coisas concretas (combustível, eletrônico, viagem).
7. **"Resumindo:"** numa frase de efeito que dá para citar ("empate não se decide no voto, se decide na certidão").
8. **CTA de comentário com palavra-chave** ("Comenta LÚDICO"), que gera milhares de comentários e entrega um DM automático.
9. **Legenda do post como fonte:** um dado por linha com emoji de bandeira ou lugar, mais "Fontes no primeiro comentário".
10. **Neutralidade:** checam "veículos de direita, de esquerda e dados oficiais". Os dois lados compartilham o vídeo.

## Visual (gramática fixa)
- Fundo escuro com poeira/estrelas, um único objeto 3D no centro e **uma cor de destaque** (lá é amarelo-limão).
- Topo: linha da série em mono pequeno ("LUDIFICANDO · O MERCADO E O LULA") + pílula "• SEÇÃO" + linha de fontes.
- Etiqueta da cena (fundo de destaque, texto mono escuro), **número grande** com sinal (−19,42%), rótulo em mono.
- Tópicos em bullet que se acumulam (o novo entra destacado e o anterior volta para branco).
- Carimbo inclinado que bate e assenta (FALSO / EXAGERADO / VERDADEIRO / NEGADO / VOCÊ SENTE NO BOLSO).
- Legenda karaokê embaixo: a palavra falada em branco e o resto em cinza, numa caixa escura.
- Narração: voz única e calma, sem música alta. Duração entre 78 e 104 s.

## Como fazer no Gab
- **Assunto com lugar/mercado/viagem:** preset `globo` do /ogab (recriado desse mesmo reel, 26/10/2026), com `cor` = destaque
  do cliente. Um bloco do roteiro = uma cena (`foco` = cidade, `etiqueta`, `numero`, `topicos`, `carimbo`).
- **Comparação/checagem (A x B):** cena de púlpitos com holofote (ainda não existe no Gab, mas dá para criar no AE 3D nativo
  ou em Three.js).
- **Quantidade/escala (votos, pessoas, contratos):** mar de blocos que acendem por porcentagem (ainda não existe).
- **Com apresentador (X-Trader):** híbrido. O rosto aparece no gancho, na lição e no CTA. No miolo dos dados entra o globo em
  tela cheia com a voz dele em off. Rosto = confiança, e o miolo 3D = retenção.

## Fórmula de roteiro (preencher)
```
[GANCHO 3-4 s]  <fato mais chocante + consequência, número redondo>.
[REFORÇO 2 s]   <comparação histórica: "não acontecia desde...">.
[PROMESSA]      Vem que eu te explico em um minuto.
[BLOCO 1..4]    <hora/lugar> + <número exato> + <o que é, em 1 frase>.   (uma cena cada)
[POR QUÊ]       Por que o mercado reagiu assim? <causa em 2 frases curtas>.
[MAS ATENÇÃO]   <ressalva honesta / risco>.
[PRA VOCÊ]      E por que isso importa pra você? <3 coisas do dia a dia>.
[RESUMINDO]     <frase de efeito citável, ligada ao método do cliente>.
[CTA]           <pergunta de opinião com 2 lados> + Comenta <PALAVRA>.
```
Regras: frases de até 12 palavras; nada de "Já me segue..." antes do miolo (seguir vai para o fim); número igual em tudo
(fala, tela, legenda do post); fonte com data; sem travessão.
