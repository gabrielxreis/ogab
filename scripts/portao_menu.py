"""Portão do menu (regra do usuário, 23/10/2026: "em nenhum momento antes da edição entrou o menu").

Nenhuma timeline, sequência ou rascunho de vídeo NOVO é criado sem o `menu_escolha.json` do vídeo: é o menu que deixa a
pessoa apontar o que quer (formato, motions, legenda, lettering, takes, música, SFX, ritmo, cor). Vale também quando o
pedido começou pequeno ("só um roteiro", "só a voz") e foi virando vídeo aos poucos.

    checar(pasta)                      # procura <pasta>/menu_escolha.json (ou nas 2 pastas acima)
    checar(pasta, sem_menu="motivo")   # pula, com motivo: a pessoa disse "pode fazer no automático"/"sem menu",
                                       # ajuste numa timeline já montada, ou variação de um vídeo já aprovado
Sem `pasta` e sem `sem_menu`: erro (é assim que o portão não deixa esquecer).
Pulou sem menu: anotar o motivo no PROJETO.md (decisões).
"""
import os

ARQ = "menu_escolha.json"


def achar(pasta):
    d = os.path.abspath(os.path.expanduser(pasta))
    for _ in range(3):
        f = os.path.join(d, ARQ)
        if os.path.isfile(f):
            return f
        d = os.path.dirname(d)
    return None


def checar(pasta=None, sem_menu=None):
    if sem_menu:
        print(f"portão do menu: pulado ({sem_menu}); anotar no PROJETO.md")
        return None
    f = achar(pasta) if pasta else None
    if f:
        return f
    onde = f" em {pasta}" if pasta else " (passe pasta=<pasta do vídeo>)"
    raise RuntimeError(
        "MENU_PENDENTE: nenhum menu_escolha.json" + onde + ". Antes de montar, abrir o menu do vídeo em segundo plano: "
        "python3 SKILL_DIR/scripts/menu.py --pasta <pasta do vídeo> --cliente <empresa> --pedido \"<pedido>\" "
        "[--roteiro roteiro.txt], mandar o link clicável e esperar o Confirmar. Só pular com sem_menu=\"<motivo>\" "
        "quando a pessoa disse que não quer menu ou é ajuste numa timeline já montada.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    print(checar(sys.argv[1]) or "pulado")
