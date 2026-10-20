# Storyboard antes do render e revisor com nota antes de entregar

Regra do usuário (16/10/2026). Vale para todo motion feito em HyperFrames: presets, motions de Reels, letterings e só motion.

## 1. Storyboard (PARAR para aprovação)
Depois de montar o plano e o projeto, e ANTES de renderizar:
```
python3 SKILL_DIR/scripts/storyboard.py <pasta_do_motion>
```
- **O que gera:**
  - `storyboard.md`: tabela de batidas com cena, tempo, tipo, mensagem e som;
  - `storyboard.jpg`: 3 quadros parados (gancho, cena principal e fecho), fotografados direto da timeline, sem render.
- **Mandar ao usuário:** a tabela e a imagem (SendUserFile). Depois PARAR e esperar a resposta.
- **Ajuste vem por número de cena** ("na 3, troca o texto"):
  - mudar só aquela cena no plano;
  - fotografar de novo só ela, com `--cena 3`;
  - mandar só a cena alterada.
- **Render só depois do "pode renderizar".**
- **Quando pular:** só se o usuário disser para pular, ou num ajuste pequeno de um vídeo já aprovado.

## 2. Revisor com nota (antes de entregar)
Depois do render (e da mixagem de som, se for entrega final):
```
python3 SKILL_DIR/scripts/revisor.py <video.mp4> --pasta <pasta_do_motion> [--rodada N]
```
O script faz a parte objetiva. Ele sai com código 1 se achar ERRO. Na pasta `revisao_<nome>/` ficam:
- `folha.jpg` e `folha_celular.jpg`: 12 quadros, no tamanho de revisão e no de tela de celular;
- `corte_NN.jpg`: 6 quadros em volta de cada corte;
- `revisao.md`, com os defeitos e o tempo de cada um:
  - gancho parado nos 2 primeiros segundos;
  - quadro preto;
  - imagem congelada;
  - algo encostado na borda;
  - volume fora de -14 LUFS, pico acima de -1 dBTP, trecho mudo;
  - clichê proibido no código (lista em `motion_proibidos.md`);
  - seção **Tempo de leitura**: o OCR do macOS lê cada quadro e mede quanto tempo cada frase fica inteira na tela
    (`scripts/leitura.py texto`, mínimo 0,3 s por palavra + 0,5 s, nunca menos de 1 s). Texto que repete a fala pode
    passar mais rápido; texto que só aparece escrito e dá ERRO limita a nota de "Leitura no celular" a 7. Para
    acelerar, tirar palavra da tela, nunca cortar antes de dar tempo de ler.

**Voz IA ouvida de volta.** O `qc.py` transcreve o vídeo final (ou a narração) com o Whisper local e compara com o
`roteiro.txt` (`scripts/leitura.py voz <audio> <roteiro.txt>`; número escrito e falado contam igual). Cada diferença
vem com o tempo: ouvir o trecho. Nome próprio, número e sigla trocados são erro e a narração é refeita naquele trecho.

**Nota de olhos novos.** Chamar um subagente SEM o contexto da edição (modelo barato, ver "Economia de tokens"). Passar a ele:
- o `revisao.md`, as imagens e o plano;
- a lista de fatos aprovados (números, nomes, afirmações).

Pedir que preencha a tabela dos 7 critérios: nota de 0 a 10, evidência com arquivo e tempo, e a correção sugerida. Ele não edita nada. Quando não houver subagente disponível, o próprio Gab preenche, olhando SÓ as provas.

| # | Critério | O que olhar |
|---|---|---|
| 1 | Gancho | nos 2 primeiros segundos algo forte acontece e a mensagem principal aparece |
| 2 | Leitura no celular | na `folha_celular` todo texto se lê; cada frase fica na tela ~0,3 s por palavra + 0,5 s |
| 3 | Som na batida | cada efeito cai no quadro do movimento dele; nada embolado; volume certo |
| 4 | Acabamento | nada cortado (acento, perna do g, borda), sobreposto ou encostado na margem |
| 5 | Ritmo e respiro | uma ideia por cena, cortes sem pulo, nada arrastado nem atropelado |
| 6 | Marca e fatos | cores, fonte e logo do cliente; todo número vem da lista aprovada |
| 7 | Movimento | curvas que freiam no fim, nada linear no que se vê, nenhum clichê proibido |

**Rodadas:**
- Corrigir os 3 piores problemas (ERROs primeiro, depois as notas mais baixas).
- Renderizar de novo e rodar `--rodada 2`.
- **Entrega:** nenhum ERRO, todos os critérios >= 8 e pelo menos 2 rodadas.
- **Na rodada 3:** se ainda faltar, entregar mesmo assim e dizer ao usuário o que ficou em aberto e por quê.
- **Ao entregar:** contar ao usuário as notas finais numa linha, por exemplo "Revisor: gancho 9, leitura 8, som 8...".

## 3. Fatos aprovados
Todo número, data, nome e afirmação que aparece no vídeo vem de uma lista aprovada:
- o roteiro aprovado;
- o `empresa.md` do cliente;
- ou o que o usuário mandou.

Se precisar de um dado novo, perguntar antes. Nunca inventar um número para "ficar bonito" no gráfico ou no contador.
