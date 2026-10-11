---
name: video-redes
description: Produz vídeos para redes sociais (Instagram Reels, YouTube Shorts/longo, Meta Ads) do roteiro até a timeline pronta e renderizada no DaVinci Resolve - roteiro para aprovação, voz por IA, música, efeitos sonoros, takes de banco ou gerados, lettering animado, legenda com métrica e conferência automática. Use quando o usuário pedir para criar/fazer um vídeo, reels, anúncio, pauta ou roteiro para uma empresa/cliente, ou digitar /video-redes (subcomandos ajuda, config, update, pauta, cliente).
---

# video-redes

Pipeline de vídeo para redes sociais com IA + DaVinci Resolve. Duas paradas obrigatórias para o usuário decidir: **aprovar o roteiro** e **escolher a voz**. Nada que gaste crédito roda antes delas.

Pasta da skill: `~/.claude/skills/video-redes/` (chamada de `SKILL_DIR` abaixo). Scripts em `SKILL_DIR/scripts/`. Detalhes técnicos em `SKILL_DIR/docs/PROCESSO.md` (ler a seção da etapa só quando chegar nela, para economizar tokens).

## 0. Subcomandos (`/video-redes <sub>`)

- `ajuda` ou `help` (o `/help` puro é do Claude Code e não pode ser trocado): mostrar em tabela o que está **habilitado/desabilitado** em `SKILL_DIR/config.json` (se não existir, copiar de `config.example.json`), os provedores escolhidos por etapa e os comandos. Oferecer mudar qualquer item; ao mudar, editar `config.json` e confirmar.
- `config <chave> <valor>`: muda direto (ex.: `config opcoes.multi_formatos true`, `config provedores.musica ["envato"]`).
- `update`: `git -C SKILL_DIR pull --ff-only` e mostrar o que mudou (`git log -5 --oneline`). Nunca sobrescrever `config.json` nem `clientes/`.
- `cliente <nome>`: criar/atualizar o perfil do cliente (etapa 1).
- `pauta [cliente]`: rodar a pauta automática (etapa 2b) e sugerir roteiros.
- sem subcomando ou pedido livre ("faz um vídeo para X"): rodar o fluxo completo.

## Regras fixas (sempre)

0. **Contas são de quem usa a skill.** Usar SÓ os conectores e logins da pessoa que está rodando o Claude. Nunca pedir, guardar nem usar senha, token ou chave de outra pessoa; nunca colocar credenciais no `config.json` nem no repositório. Se um provedor não estiver conectado, pedir para a própria pessoa conectar a conta dela.

1. **Pasta do vídeo**: `<pasta_saida>/<Assunto> - <Empresa>/` (padrão `~/Desktop`), com `roteiro.txt`, `links.txt` (origem de tudo: notícia, voz, música, cada take, cada efeito), `narracoes/`, `musica/`, `sfx/`, `brolls/`, `videos/`, `legendas/`. **Projeto do DaVinci com o mesmo nome** `<Assunto> - <Empresa>`.
2. **Tudo via MCP/API, só download pelo navegador** (Claude in Chrome logado nas contas do usuário). Ver `navegador/downloads.md`.
3. **Economizar créditos e tokens**: 1 geração por vez, sem variações extras; estimar custo antes (ElevenLabs `estimate_only`); gerar takes **só em modo ilimitado** (Magnific pelo site); buscas com `perPage` pequeno; no navegador, JS enxuto e zoom pequeno em vez de screenshot grande; não reler arquivos grandes.
4. **Provedores**: usar os da lista de `config.json` na ordem, **pulando o que não estiver conectado** (conferir com a ferramenta de status de conectores / ToolSearch). Se nenhum provedor de uma etapa estiver disponível, avisar e oferecer alternativa (ex.: o usuário baixa à mão e coloca na pasta).
5. **Sem green screen** nem elemento isolado/canal alfa nos takes. Conferir a miniatura antes de baixar.
6. **Pessoas reais**: nunca gerar rosto realista de pessoa real em cena inventada; usar símbolo, pessoa de costas, foto real fornecida pelo usuário ou ilustração. Voz clonada só se for do próprio usuário/cliente ou autorizada.
7. **Movimentos nos takes e lettering no gancho: perguntar** antes (a não ser que `config` diga `sempre`/`nunca`).
8. Sem travessão (em dash) nos textos para o usuário e nas legendas.

## 1. Cliente (primeira vez por empresa)

Se não existir `SKILL_DIR/clientes/<empresa>/empresa.md`: pedir **site** + **logo** (PNG transparente, claro e escuro) + cores/fontes + redes. Ler o site inteiro e criar, copiando de `clientes/_exemplo/`:
- `empresa.md`: o que faz, público, dores, diferenciais, tom de voz, CTA, cores, o que **não** dizer (regras do setor).
- `pronuncia.json`: termos da marca/setor com `grafia` correta, `fala` (como escrever para a voz pronunciar certo) e `erros_transcricao` conhecidos.
- `logo/`: arquivos do logo.
Nos próximos vídeos, ler o perfil em vez de perguntar de novo (só confirmar se mudou algo).

## 2. Roteiro (PARAR para aprovação)

1. Perguntar a **plataforma** (Instagram, YouTube Shorts/longo, Meta Ads) e, se Meta Ads, a duração (15, 30 ou 60 s). Durações em `config.regras.duracao_segundos`; ~150 palavras/min.
2. Pesquisar o assunto (notícia recente com fonte e data) e escrever: gancho nos 3 primeiros segundos, frases curtas, sugestão visual por bloco, CTA do cliente. Respeitar o "não dizer" do cliente.
3. Mostrar e **esperar o "aprovado"**. Salvar como `roteiro.txt`.

### 2b. Pauta automática (se `opcoes.pauta_automatica.ativo` ou `/video-redes pauta`)
`python3 SKILL_DIR/scripts/pauta.py "<temas do cliente>" --fonte <gratis|newsapi|gnews>` e sugerir 2-3 pautas com roteiro curto. Pode ser agendada (tarefa recorrente) se o usuário pedir.

## 3. Voz (PARAR para o usuário escolher)

Listar 3-5 vozes no idioma (ElevenLabs `creative_list_voices`; incluir vozes do próprio usuário) com link de prévia. Depois da escolha: trocar no texto os termos de `pronuncia.json` pela forma `fala` (ex.: "EB-2" -> "ê-bê dois"), `estimate_only` -> informar custo -> gerar **1** take. Baixar para `narracoes/narracao.wav` (48 kHz). Transcrever (Resolve `TranscribeAudio` ou `creative_transcribe_audio`): se a transcrição mostrar erro de pronúncia de um termo, **atualizar `pronuncia.json` do cliente** (novo `erros_transcricao` e ajuste em `fala`) e regerar só o trecho, com aprovação.

## 4. DaVinci: projeto e narração

`scripts/resolve_lib.py`: `criar_projeto(nome, w, h, fps)` (grava fps de timeline **e playback** antes de qualquer timeline), `criar_timeline`, `colocar_narracao(db=+5)`. Formato pela plataforma (9:16 1080x1920; 4:5 1080x1350; 16:9 1920x1080).

## 5. Música

Clima padrão: **emotiva, que faz sonhar**, instrumental, priorizando as mais baixadas/em alta (Artlist `sortBy: TOP_DOWNLOADS`, Envato `sortBy: popular`). Mostrar 3-4 opções com prévia; o usuário escolhe. Baixar WAV pelo navegador. `preparar_musica` posiciona o trecho para o **clímax cair no CTA** (usar `hookStartSeconds` do Artlist), com **fade out** e 48 kHz; `colocar_musica(db=-10)` na A2.

## 6. Efeitos sonoros (se `opcoes.efeitos_sonoros`)

Buscar no Artlist (`search_sfx`) ou Envato (`search_sound_effects`): whoosh/swoosh suave nas trocas de take principais, um impacto/riser no gancho, um "ding"/pop no CTA. Poucos e baixos (`colocar_sfx`, -6 dB na A3). Registrar em `links.txt`.

## 7. Takes

1. Dividir a narração em blocos de 2-5 s pelos tempos da transcrição.
2. Primeiro **banco** (`provedores.takes_banco`, ex.: Envato `search_stock_video` com `orientation` certa). Baixar 1080P pelo navegador -> `brolls/take_XX`.
3. Se não achar, **gerar** (`provedores.geracao_takes`), **só ilimitado**: Magnific pelo site (Nano Banana 2 1K + Kling 2.5 720p 5 s). Se só sair pago, avisar e propor alternativa.
4. `midia.py preparar_take` para 4K/ProRes; `midia.py green` para garantir que não é chroma.
5. `montar_takes` (sem buracos: encadeia pelo fim real e usa ceil).
6. Se o usuário quis **movimentos**: `movimento()` (zoom leve) ou indicar onde animar.

## 7b. Cor (se `config.cor.aplicar_power_grade`)

Depois de montar os takes (e sempre que trocar um take), `aplicar_grade(r, t, config.cor.drx)` em todos os takes da V1. Conferir 2-3 quadros: se algum take de banco estourar (contraste/saturação exagerados), avisar o usuário. Lettering e legenda não recebem grade.

## 8. Lettering (se o usuário quis)

Pacote de títulos animados instalado (`config.lettering.pacote`, ex. `@gabrielxreis_ Text Presets.drfx` em `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/`; o Resolve precisa reiniciar após instalar). `lettering(t, "<Template>", "TEXTO", inicio, dur)` na V2: texto do gancho (2-4 palavras) e, se fizer sentido, um destaque no CTA. Ofereça 2-3 templates da lista `config.lettering.templates_disponiveis`.

## 9. Legenda

Regras: **uma linha só (nunca quebrar)**, pedaço natural da frase, até `config.regras.legenda.max_caracteres` (25 no 9:16), nunca terminar em palavra fraca, número junto da unidade, **sem misturar idiomas**, grafia do cliente corrigida.
1. `legendas.py rascunho transcricao.json legendas/frases.txt --cliente clientes/<empresa>` -> revisar o frases.txt (ajustar cortes estranhos à mão).
2. `legendas.py sincronizar transcricao.json legendas/frases.txt legendas/legendas_vN.srt` (nome único por versão).
3. `colocar_legendas` (troca só os itens: o **preset de estilo fica na trilha**; projeto novo: aplicar o preset do usuário na trilha pelo Inspector, ver `config.regras.legenda.preset_trilha`).

## 10. Render, formatos e conferência

1. `renderizar(p, <pasta>/videos, "<Assunto> - <Empresa>")` (H.264, legenda gravada).
2. Se `opcoes.multi_formatos`: criar timelines extras nos formatos de `formatos_extras` (e cortes 15/30/60 s para Ads) e renderizar cada uma com sufixo (`- 4x5`, `- 30s`).
3. **Conferência automática** (se habilitada): `python3 SKILL_DIR/scripts/qc.py <pasta> --cliente clientes/<empresa> --plataforma <p>`. Corrigir todo **ERRO** e reconferir. Olhar a `qc_folha.jpg`.
4. Salvar o projeto e entregar: link do vídeo, resumo (voz, música, takes banco x gerados, créditos gastos) e o que falta (ex.: logo).
