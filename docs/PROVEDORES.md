# Provedores: o que conectar e o que cada um faz

A skill funciona com o que você tiver. Em `config.json`, cada etapa tem uma **lista em ordem de preferência**; a IA usa o primeiro que estiver conectado e pula os outros. Troque a ordem ou tire o que não usa.

| Etapa | Opções suportadas | Como conectar | Custo |
|---|---|---|---|
| Voz (narração) | `elevenlabs`, `artlist` | Claude: Configurações > Conectores > ElevenLabs (diretório) / Artlist: conector personalizado `https://mcp.artlist.io/mcp` | Créditos da plataforma. A skill estima antes e gera 1 take |
| Música | `artlist`, `envato` | Artlist (acima) / Envato: conector "Envato" no diretório | Assinatura. Só busca pelo MCP; download pelo navegador |
| Efeitos sonoros | `artlist`, `envato` | idem | Assinatura |
| Takes de banco | `envato`, `artlist`, `storyblocks`, `pexels` | Envato/Artlist (acima) / Storyblocks: conector oficial / Pexels: MCP comunitário com chave grátis | Assinatura (Pexels grátis) |
| Geração de takes | `magnific_site_ilimitado` (padrão), `artlist`, `magnific_mcp` | Magnific: conector `https://mcp.magnific.com` + login no site no Chrome | **Pelo site no modo ilimitado = sem crédito** (Nano Banana 2 1K + Kling 2.5 720p). Pelo MCP e Artlist **cobra crédito**: a skill só usa se `regras.geracao_so_ilimitada` for `false` |
| Download | `navegador` | Extensão **Claude in Chrome** logada na mesma conta do Claude, e você logado nos sites | - |
| Editor | `davinci_resolve` | DaVinci Resolve **Studio** com Preferences > System > General > External scripting using = **Local** | - |
| Pauta automática | `gratis` (Google News RSS), `newsapi`, `gnews` | Grátis não precisa de nada; pagas: variável `NEWSAPI_KEY` ou `GNEWS_KEY` | Grátis / plano da API |

## Trocar um provedor

- Pelo chat: `/video-redes config provedores.musica ["envato","artlist"]`
- Ou edite `config.json` à mão.
- Para usar um provedor novo (ex.: outra plataforma de geração), conecte o MCP dele no Claude, coloque o nome na lista da etapa e descreva em uma linha em `docs/PROVEDORES.md` como ele baixa/gera. A IA lê isso na hora.

## Conferir o que está conectado

No Claude Code: o app mostra os conectores em Configurações > Conectores; a skill também confere sozinha antes de cada etapa e avisa se faltar algum (ex.: "Magnific precisa de login: rode /mcp").
