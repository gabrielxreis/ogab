# Preset PODCAST (duas pessoas em tela dividida, legenda na cor de quem fala)

Corte de podcast ou entrevista com DUAS pessoas: uma em cima, outra embaixo (1080x960 cada), com uma emenda fina na cor da marca. A legenda é karaokê por palavra: cada pessoa tem a sua cor (a da marca e uma secundária), a palavra falada acende e o bloco fica centrado na linha que divide os dois vídeos (metade em cada um): ali dá para ler e não atrapalha a imagem. A metade de quem está calado escurece um pouco. Ideia inspirada no repositório hypit; o código é todo nosso.

<img src="exemplo.gif" width="200" alt="Exemplo do preset podcast (vídeo de banco gratuito da Mixkit, fala fictícia)">

## Quando usar
- **Só podcast/entrevista com duas pessoas.** Nos outros vídeos, a legenda é a fixa da /ogab (Y 724, `docs/etapas/legenda.md`).
- Esta é a ÚNICA exceção à legenda fixa: aqui a legenda fica **sempre na linha que divide os dois vídeos** (`"legenda": "emenda"`, padrão; pedido do usuário, 23/10/2026), centrada, metade em cada vídeo. Ela **nunca cobre o rosto**: enquadrar com o queixo de quem está em cima e a cabeça de quem está embaixo longe da emenda (o gerar avisa se encostar; corrigir com `recorte` ou `tamLegenda`).
- **Nunca cortar a cabeça nem o rosto** (regra do usuário): take com folga acima da cabeça em todos os quadros; o gerar avisa quando o topo da cabeça sai da metade.
- Modo antigo, só se pedirem: `"legenda": "rosto"` (abaixo do queixo de quem fala, acompanhando a cabeça; sem trilha, `legendaY`).

## Regras
- **Duas pessoas, nesta ordem:** o 1º falante vai em cima, o 2º embaixo. Cores: `cor` (marca) para o 1º e para a emenda, `cor2` para o 2º (ou `cor` dentro de cada falante).
- **Legenda:** uma linha, até `maxPalavras` (3, ou 4 em fala lenta) e `maxCaracteres` (20). Quebra na pontuação, nas pausas e na troca de falante; nunca termina em palavra fraca (que, de, o, com...). A métrica do script não basta: reler as quebras e forçar com `"quebra": true` na palavra.
- **Contínua:** um bloco emenda no outro nas pausas curtas (até 1,2 s) e na troca de falante.
- **Texto idêntico à fala**, grafia do cliente corrigida (nomes, siglas e números um por um, como na legenda normal).
- **Movimento calmo:** aproximação contínua bem lenta (3,5 %) nas duas metades, entrada de bloco de 0,24 s que freia no fim, troca de realce de 0,45 s. Quadro 0 já com imagem, sem fade do preto.
- **Fonte:** Poppins (local, `assets/fontes/`), caixa alta. Outra fonte de `assets/fontes/` vai pelo nome; fora disso, Google Fonts.

## Entradas
- `midia` de cada falante: vídeo (mp4/mov) ou imagem. Recorte "cover" na metade: sem `recorte`, o rosto mediano da trilha fica centrado e a 36 % da altura da metade.
- `palavras`: `[{texto, ini, fim, falante}]` em segundos do corte.
- `trilha` (opcional, por falante): `python3 scripts/rastrear.py <video> --rosto --saida trilha.json`. Os pixels são do vídeo de origem e o gerar converte para a metade (escala cover, deslocamento, zoom lento). O rastrear não grava o tamanho do rosto: passe `rosto.alt` (altura do rosto em px da origem) ou deixe o gerar medir com a detecção de rosto da Apple (`presets/cena/rosto.py`).
- `audio` (opcional): o som do corte. Sem ele os vídeos ficam mudos; `"som": true` num falante usa o som daquele vídeo.

## Da transcrição do DaVinci para o plano
1. Cortar o trecho no DaVinci e pegar as palavras com tempo (`GetTranscription`, ver `docs/etapas/legenda.md`), descontando o início do corte.
2. Marcar o falante de cada palavra (0 = de cima, 1 = de baixo): pelo canal do microfone de cada um, pelos turnos da transcrição ou à mão nas trocas.
3. Um vídeo por pessoa (câmera de cada um, ou o mesmo plano aberto duas vezes com `recorte` diferente: `{"x": 0.2, "zoom": 1.4}` e `{"x": 0.8, "zoom": 1.4}`), com `inicio` = segundo do arquivo em que o corte começa.
4. Rastrear o rosto de cada vídeo no mesmo trecho (`rastrear.py --rosto --de <inicio> --ate <fim>`); o gerar desconta o `inicio` sozinho.

## Como fazer
```
python3 gerar.py plano.json <pasta> [--render podcast.mp4 --gif]
```
- O gerar lista os blocos de legenda (conferir quebras) e avisa quando algum bloco não cabe fora do rosto: aí reenquadrar (`recorte`) ou baixar `tamLegenda`.
- Depois: storyboard, aprovação, render e revisor (`docs/etapas/revisor.md`). Olhar 4 a 6 quadros: legenda nunca no rosto, nunca cortada.
- Exemplo: `exemplo/plano.json` com duas pessoas reais de banco gratuito (Mixkit, `exemplo/CREDITOS.md`); `exemplo/fazer.py` baixa os clipes e rastreia os rostos. Fala rápida gera blocos curtos: o revisor dá aviso de leitura (texto repete a fala, então pode) e ERRO abaixo de ~0,7 s; nesse caso, `maxPalavras` 4.

## Limitações
- Exatamente duas pessoas, sempre em cima e embaixo (sem tela cheia de uma só, sem três pessoas).
- Fala sobreposta: a palavra vai para o falante marcado; os blocos se revezam, nunca aparecem dois ao mesmo tempo.
- O rastreio do OpenCV pode perder o rosto de perfil; entre as detecções a posição é interpolada.
