# Voz local (clonador opcional do Gab)

Clona a voz do usuário e gera narração **no próprio Mac, de graça e sem limite**, com o motor do
[VoiceStudio](https://github.com/debpalash/VoiceStudio) (AGPL-3.0) rodando por trás do Claude.
Não instala o app visual: só baixa as pastas `backend/` e `omnivoice/` do repositório (versão fixa, revisada)
e monta o Python com `uv`. Opcional: só instala se o usuário disser sim.

Só Mac Apple Silicon (M1 ou mais novo) por enquanto. Windows: pendente.

## Quando oferecer

- Na instalação (`install.sh` pergunta uma vez) ou quando o usuário pedir "clona minha voz", "voz local", "voz grátis".
- Na etapa 3 (Voz), se `config.json > voz_local.ativo` for `true`: listar as vozes clonadas locais junto com as
  do ElevenLabs, dizendo qual é qual.
- **Avisar sempre a licença** antes de usar em vídeo de cliente: o modelo padrão (OmniVoice) é **CC-BY-NC, não
  comercial**. Para trabalho pago, usar ElevenLabs ou um motor de licença aberta da tabela abaixo.
- Ser honesto sobre a qualidade: copia bem o timbre, mas a entonação sai mais "lida" e com menos pausas que o
  ElevenLabs. Referência com emoção (trecho contando história, empolgado) melhora mais que qualquer ajuste.

## Instalar (pedir o "sim" antes de cada download, dizendo tamanho e licença)

```bash
VS=~/.claude/skills/ogab/voz_local
$VS/voicestudio.sh instalar     # código do motor + Python (~2 GB)
$VS/voicestudio.sh modelo       # OmniVoice ~3,3 GB, NÃO comercial; aria2c com 16 conexões, confere SHA-256
python3 $VS/voz.py motores      # motores com português: instalado ou não, onde roda, tamanho, licença
$VS/voicestudio.sh motor voxcpm2   # outro motor, no ambiente isolado dele
```

Rodar instalações e gerações **no terminal do app** (`mcp__terminal__run_in_terminal`), nunca escondido no Bash:
o usuário quer ver a barra de progresso em tempo real (regra do usuário, 15/10/2026).

## Motores que clonam e falam português (VoiceStudio 0.5.6)

| id | roda no Mac | tamanho | licença | destaque |
|---|---|---|---|---|
| `omnivoice` | GPU (MPS) | 3,3 GB | modelo **CC-BY-NC (não comercial)** | padrão, rápido |
| `voxcpm2` | GPU (MPS) | ~5 GB | Apache-2.0 | 48 kHz, voz por descrição |
| `confucius4-tts` | CPU | ~5 GB | Apache-2.0 | mantém a voz entre idiomas |
| `moss-tts-nano` | CPU | leve | Apache-2.0 | 48 kHz |
| `pockettts` | CPU | leve | pesos CC-BY-4.0 (aceitar termo no Hugging Face) | 6 idiomas |

IndexTTS (emoção) e CosyVoice (instrução) não falam português: não oferecer para pt-BR.

## Usar

```bash
python3 $VS/voz.py clonar "<audio da pessoa>" "Nome"     # corta ~18 s entre pausas, transcreve, clona
python3 $VS/voz.py vozes
python3 $VS/voz.py gerar "<texto>" --voz "Nome" --saida "<pasta>/narracoes/narracao.wav"
#   --motor voxcpm2   --passos 32 (8 rascunho, 16 equilibrado, 32 qualidade)   --efeito raw (padrão; o DaVinci mixa)
#   --seed N (repetir um take)   --instrucao "..."   --velocidade 1.0
```

- Referência boa: 10 a 20 s, só voz, sem música, começando e terminando em pausa (`--inicio/--fim` para escolher o
  trecho na mão). O modelo imita o jeito da amostra: trecho animado gera fala animada.
- Pausas: gerar frase por frase e juntar com silêncio na timeline funciona melhor que pontuação.
- Depois de gerar, transcrever de volta e conferir as palavras (mesma regra da narração do ElevenLabs).
- Arquivos: `~/Documents/Gab Voz Local/` (`referencias/`, `saida/`, `vozes.json`, `ritmo.json`, `backend.log`).
  Modelos no cache do Hugging Face (`~/.cache/huggingface/hub`), perfis em `~/Library/Application Support/OmniVoice`.

## Armadilhas conhecidas

- O download do próprio backend sai a ~0,6 MB/s e o contador dele trava em ~1%; o `modelo` usa aria2c.
- O campo "installed" do `/models` vira `true` antes do fim do download: só confiar quando
  `/models/install/status` estiver com `jobs` vazio.
- A transcrição embutida (sherpa-onnx) erra muito em português: o `clonar` usa o mlx-whisper turbo do ambiente.
- O backend grava os WAV com permissão 600, o que impede tocar pelo app: o `gerar` já corrige para 644.
- `steps` padrão do MCP é 16 (equilibrado); o `voz.py` usa 32.
