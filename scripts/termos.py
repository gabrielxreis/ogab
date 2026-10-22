"""Aceite dos termos de uso (docs/TERMOS.md). Regra do Gabriel (22/10/2026): sem o aceite, a skill e os programas NÃO
instalam e o Gab não roda, porque a skill vai ser licenciada.

  python3 termos.py resumo          # texto curto para mostrar antes de perguntar (com o caminho do texto inteiro)
  python3 termos.py checar          # sai 0 se esta máquina aceitou a versão atual; 1 se precisa perguntar
  python3 termos.py aceitar         # grava o aceite (SÓ depois que a PESSOA digitou "aceito"; nunca por conta própria)
  python3 termos.py recusar         # grava a recusa: o Gab não roda até aceitar

O aceite inclui o envio ANÔNIMO de erros da skill e da estrutura dos motions novos (seção 2 dos termos), então
aceitar liga "relatos" no config. A apresentação com o nome continua opcional e separada (comunidade.py): dado
pessoal não pode ser condição para usar (LGPD). Na máquina do dono ("dono_biblioteca": true) não pede nada.
Termos mudaram de forma relevante: subir VERSAO e o Gab pede o aceite de novo.
"""
import json, os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(AQUI)
CONFIG = os.path.join(SKILL, "config.json")
TEXTO = os.path.join(SKILL, "docs", "TERMOS.md")
URL = "https://github.com/gabrielxreis/ogab/blob/main/docs/TERMOS.md"
VERSAO = 2
RESUMO = f"""TERMOS DE USO DO GAB (/ogab), versão {VERSAO}
- Licença pessoal de uso do Gab nos seus vídeos e nos dos seus clientes (os vídeos são seus).
  Revender ou distribuir a skill depende de autorização do autor (Gabriel Reis).
- Para melhorar a skill, o Gab envia ao autor, de forma ANÔNIMA, os erros da skill que ele corrigir, a
  estrutura dos motions novos que você criar e as invenções (scripts novos e melhorias) feitas nos arquivos
  da própria skill. Nunca sai vídeo, roteiro, cliente, senha, chave ou dado pessoal.
- Se apresentar com o nome é opcional e perguntado à parte.
- Programas de terceiros (DaVinci, Premiere, ElevenLabs...) têm licenças próprias. Sem garantia: confira antes de entregar.
Texto completo: {URL}
Sem o aceite, nada é instalado e o Gab não roda. Para aceitar, digite ACEITO."""


def _cfg():
    try:
        return json.load(open(CONFIG, encoding="utf-8"))
    except Exception:
        return {}


def aceito():
    c = _cfg()
    return bool(c.get("dono_biblioteca")) or int((c.get("termos") or {}).get("versao", 0)) >= VERSAO \
        and (c.get("termos") or {}).get("aceito") is True


def gravar(sim):
    c = _cfg()
    c["termos"] = {"versao": VERSAO, "aceito": bool(sim), "quando": time.strftime("%Y-%m-%d %H:%M")}
    if sim:   # relatos anônimos fazem parte da licença (seção 2)
        c["relatos"], c["relatos_v"], c["relatos_respondido"] = True, 2, time.strftime("%Y-%m-%d")
    json.dump(c, open(CONFIG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def main(a):
    cmd = a[0] if a else ""
    if cmd == "resumo":
        print(RESUMO)
    elif cmd == "checar":
        if aceito():
            sys.exit(0)
        print("TERMOS_PENDENTES: mostrar `termos.py resumo` e só seguir depois que a pessoa digitar ACEITO")
        sys.exit(1)
    elif cmd == "aceitar":
        gravar(True); print(f"termos versão {VERSAO} aceitos")
    elif cmd == "recusar":
        gravar(False); print("termos recusados: o Gab não roda até aceitar (python3 termos.py aceitar)")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
