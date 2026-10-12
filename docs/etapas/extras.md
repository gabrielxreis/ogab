# Extras de apresentador: legenda atrás da pessoa e pacote de entrevista

Ler só quando a opção estiver ligada e o vídeo pedir. As duas usam skills do HyperFrames DENTRO do fluxo da /ogab
e voltam para a timeline como clipes por cima da V1 (a V1 nunca é tocada; regra 1g: retrato antes e depois).

## `opcoes.legenda_atras_da_pessoa` (true | false | "perguntar")
**Quando usar (só onde rende, não no vídeo todo):** o GANCHO (primeiros 3-5 s) e 1-2 frases de efeito, num trecho com
UMA pessoa e sem corte de cena no meio (se tiver corte, dividir em trechos). Nunca em cima de b-roll/motion.
**Como:**
1. Legenda validada (4b) e trecho escolhido: tempos de início/fim tirados da legenda.
2. `resolve_lib.renderizar_trecho(p, <pasta>/extras, "atras_<n>", ini, fim)` exporta só a V1 daquele trecho (desliga
   por um instante as outras trilhas e a legenda, renderiza, religa tudo).
3. Skill `embedded-captions` com esse MP4 e as palavras da legenda validada (mesmo texto, mesmos tempos); fonte Poppins
   Bold caixa alta (ou a do `estilo.md` do cliente), estilo escolhido com o usuário na 1ª vez e salvo no cliente.
4. Render do HyperFrames > importar > trilha de cima no mesmo tempo; as legendas desse trecho saem da trilha 1 (guardar
   em `legendas/legenda_atras.json` para desfazer, igual ao `legenda_baixa.py`).
5. QC: conferir num quadro que a legenda passa atrás da cabeça e não some atrás do rosto.

## `opcoes.pacote_entrevista` ("perguntar" | true | false)
**Quando usar:** entrevista, podcast, depoimento de cliente, duas ou mais pessoas, ou quando a fala tem nome/cargo,
números e citações fortes. Perguntar na 1ª vez por cliente e salvar no `estilo.md`.
**O que entra (skill `talking-head-recut`, sempre com as cores/fontes do site do cliente):**
- nome e cargo embaixo na primeira vez que cada pessoa aparece (3-4 s);
- cartão de número quando a fala cita dado ("3 mil", "10 anos", "bilhões");
- cartão de citação nas frases de efeito (texto exato da legenda);
- títulos de capítulo se o vídeo tiver blocos.
**Como:** plano em tabela (trecho | tempo da legenda | elemento | texto) mostrado ao usuário; render de cada elemento
como clipe transparente (ProRes 4444, 1080x1920, fps da timeline) com a duração da fala (regra 1h); entrar na trilha
de cima com `mp.AppendToTimeline` (trackIndex), nunca sobre o rosto (regra 1e); whoosh/pop vêm do `sfx_auto.py`.
