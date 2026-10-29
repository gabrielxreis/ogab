"""Ponte do Premiere para o Gab: escolhe sozinho entre a UXP (Premiere 26+, 127.0.0.1:8765, premiere_lib.py) e a
CEP (Premiere 2018 a 25.x, 127.0.0.1:8767, cep/premiere2019_lib.py). O Gab importa `ponte` e usa a MESMA interface
(abrir_projeto, criar_sequencia, colocar, volume, colocar_musica, montar_takes, legenda, marcador, cortar, efeito,
transicao, velocidade, aplicar_lut, quadro, exportar, retrato, salvar); não precisa saber a versão.

    import sys, os; sys.path.insert(0, os.path.expanduser("~/.claude/skills/ogab/premiere")); import ponte as P
    P.qual()                       # "cep (Premiere 13.1.5)" ou "uxp (Premiere 26.x)"
    P.colocar(seq, arquivo, tempo, video=1)

Regra: se a ponte CEP responde no 8767 (Premiere antigo aberto), usa ela; senão, usa a UXP (26+).

SALVAR A CADA MODIFICAÇÃO (29/10/2026, pedido do Gabriel): o Premiere fecha sozinho (crash) no meio da edição. Por isso
toda função da ponte que mexe no projeto (colocar, volume, legenda, cortar, efeito, lettering, animar...) é seguida de
um salvar() automático; só leitura (qual, versao, sequencias, retrato, luts_instalados, mogrts, efeitos, exportar,
quadro...) não salva. Falha no salvamento não derruba a edição: avisa no stderr. Desligar só para lote muito grande:
OGAB_PREMIERE_SALVAR=0 (e aí chamar P.salvar() no fim de cada bloco).
Recursos que SÓ existem no 26 (transcrever, isolar_voz, envelope_volume, colocar_narracao, lettering/MOGRT do Gab,
lettering_ae, animar_rastreado, mogrts, sequencias): no Premiere antigo o Gab trata fora (whisper/ffmpeg) ou usa o
nativo. Chamá-los pela ponte CEP dá erro claro apontando o caminho (ver cep/ENGENHARIA_REVERSA_PREMIERE_2019.md).
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
_BACK = None


def _backend():
    """Carrega e memoriza a ponte certa. CEP primeiro (ping rápido no 8767); senão UXP (26+)."""
    global _BACK
    if _BACK is not None:
        return _BACK
    if AQUI not in sys.path:
        sys.path.insert(0, AQUI)
    cep_dir = os.path.join(AQUI, "cep")
    if cep_dir not in sys.path:
        sys.path.insert(0, cep_dir)
    try:
        import premiere2019_lib as cep
        if cep.conectado():          # Premiere 2018-25 aberto com a ponte CEP
            _BACK = cep
            return _BACK
    except Exception:
        pass
    import premiere_lib as uxp       # Premiere 26+ (UXP) é o padrão
    _BACK = uxp
    return _BACK


def _eh_cep(b):
    return b.__name__.endswith("premiere2019_lib")


def qual():
    """Qual ponte está ativa, com a versão do Premiere."""
    b = _backend()
    nome = "cep" if _eh_cep(b) else "uxp"
    try:
        return f"{nome} (Premiere {b.versao()})"
    except Exception:
        return nome


def reset():
    """Esquece a ponte escolhida (para re-detectar, ex.: trocou de versão do Premiere)."""
    global _BACK
    _BACK = None


# Funções que só leem, exportam ou conectam: não precisam salvar depois.
SO_LEITURA = {"versao", "conectado", "conectar", "projeto", "retrato", "descrever", "sequencias", "luts_instalados",
              "mogrts", "efeitos", "efeitos_audio", "preset_padrao", "exportar", "quadro", "xmeml", "salvar", "qual", "reset"}


def _salvando(b, nome, f):
    """Embrulha uma função que modifica o projeto: roda e salva em seguida (o Premiere pode fechar sozinho)."""
    def chamada(*a, **k):
        r = f(*a, **k)
        if os.environ.get("OGAB_PREMIERE_SALVAR", "1") != "0":
            try:
                b.salvar()
            except Exception as e:
                print(f"[ponte] aviso: não consegui salvar depois de {nome}: {e}", file=sys.stderr)
        return r
    chamada.__name__, chamada.__doc__ = nome, f.__doc__
    return chamada


def __getattr__(nome):   # PEP 562: ponte.colocar, ponte.volume... caem aqui e vão para a ponte ativa
    b = _backend()
    if hasattr(b, nome):
        f = getattr(b, nome)
        if callable(f) and not nome.startswith("_") and nome not in SO_LEITURA:
            return _salvando(b, nome, f)
        return f
    onde = "Premiere 2018-25 (ponte CEP)" if _eh_cep(b) else "Premiere 26 (ponte UXP)"
    raise AttributeError(
        f"'{nome}' não existe na {onde}. No Premiere antigo, transcrição (Speech to Text) e Enhance Speech não "
        f"existem na API: transcreva com o whisper do transcrever.py e trate o áudio com ffmpeg ANTES de importar. "
        f"Para legenda no estilo GAB, título e lettering no 2019 há `legenda_gab`, `titulo` e `lettering_ae`. Ver "
        f"premiere/cep/ENGENHARIA_REVERSA_PREMIERE_2019.md.")
