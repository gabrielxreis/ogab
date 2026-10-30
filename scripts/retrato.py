"""Retrato da timeline (regra 1g): fotografar ANTES de mexer e comparar DEPOIS.

  python3 retrato.py antes  "<timeline>" <pasta_do_video>
  python3 retrato.py depois "<timeline>" <pasta_do_video> [--alvo "subtitle1,audio3,x0*"]

`antes` grava <pasta>/retratos/<timeline>_<hora>.json (todas as trilhas: nome, início, fim, entrada, ligado, zoom/pan/tilt).
`depois` compara com o retrato mais recente e lista o que mudou FORA do alvo (trilhas "video2", "audio3", "subtitle1"
ou nomes de clipe com * no fim). Sai com código 1 se algo fora do alvo mudou: aí avisar e remontar a partir do retrato.
`depois` também grava <timeline>_gab.json: como o Gab DEIXOU a timeline.

REGRA DE EMERGÊNCIA (usuário, 23/10/2026): se o usuário mexeu na timeline, o Gab PARA TUDO e espera ele avisar.
`antes` (e `vigiar`) compara a timeline com o _gab.json: diferente = o usuário está ajustando: imprime USUARIO_MEXEU,
sai com código 3 e NÃO grava. Só volte com `antes ... --retomar` quando o usuário disser que pode voltar.
  python3 retrato.py vigiar "<timeline>" <pasta_do_video>      # só confere (código 3 = parar)
"""
import fnmatch, glob, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_lib as R


def tirar(t):
    F = float(t.GetSetting("timelineFrameRate")); S = t.GetStartFrame(); sec = lambda f: round((f - S) / F, 3)
    out = {"timeline": t.GetName(), "fim": sec(t.GetEndFrame()), "trilhas": {}}
    for tipo in ("video", "audio", "subtitle"):
        for k in range(1, t.GetTrackCount(tipo) + 1):
            itens = []
            for x in t.GetItemListInTrack(tipo, k) or []:
                d = {"nome": x.GetName(), "ini": sec(x.GetStart()), "fim": sec(x.GetEnd())}
                try: d["entrada"] = round((x.GetLeftOffset() or 0) / F, 3)
                except Exception: pass
                if tipo == "video":
                    d["on"] = x.GetClipEnabled()
                    for q in ("ZoomX", "Pan", "Tilt", "Opacity"): d[q] = x.GetProperty(q)
                itens.append(d)
            out["trilhas"][f"{tipo}{k}"] = {"nome": t.GetTrackName(tipo, k), "itens": itens}
    return out


def no_alvo(trilha, nome, alvos):
    return any(a == trilha or (a.endswith("*") and fnmatch.fnmatch(nome, a)) for a in alvos)


def comparar(a, b, alvos):
    difs = []
    for tr in sorted(set(a["trilhas"]) | set(b["trilhas"])):
        ia = a["trilhas"].get(tr, {"itens": []})["itens"]; ib = b["trilhas"].get(tr, {"itens": []})["itens"]
        chave = lambda d: (d["nome"], d["ini"])
        sa = {chave(d): d for d in ia}; sb = {chave(d): d for d in ib}
        for k in sa.keys() - sb.keys():
            if not no_alvo(tr, k[0], alvos): difs.append(f"{tr}: SUMIU {k[0]} em {k[1]}s")
        for k in sb.keys() - sa.keys():
            if not no_alvo(tr, k[0], alvos): difs.append(f"{tr}: NOVO {k[0]} em {k[1]}s")
        for k in sa.keys() & sb.keys():
            if sa[k] != sb[k] and not no_alvo(tr, k[0], alvos):
                mud = {q: (sa[k].get(q), sb[k].get(q)) for q in sa[k] if sa[k].get(q) != sb[k].get(q)}
                difs.append(f"{tr}: MUDOU {k[0]} em {k[1]}s {mud}")
    return difs


def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[0] not in ("antes", "depois", "vigiar"): print(__doc__); sys.exit(2)
    modo, nome, pasta = a[0], a[1], a[2]
    alvos = [x.strip() for x in a[a.index("--alvo") + 1].split(",")] if "--alvo" in a else []
    r = R.conectar(); p = r.GetProjectManager().GetCurrentProject()
    t = next((p.GetTimelineByIndex(i) for i in range(1, p.GetTimelineCount() + 1) if p.GetTimelineByIndex(i).GetName() == nome), None)
    if not t: sys.exit(f"timeline não encontrada: {nome}")
    d = os.path.join(pasta, "retratos"); os.makedirs(d, exist_ok=True)
    base = nome.replace("/", "-")
    agora = tirar(t)
    gab = os.path.join(d, f"{base}_gab.json")
    if modo in ("antes", "vigiar") and "--retomar" not in a and os.path.exists(gab):
        mexeu = comparar(json.load(open(gab, encoding="utf-8")), agora, [])
        if mexeu:
            print("USUARIO_MEXEU: a timeline mudou desde a última mexida do Gab. REGRA DE EMERGÊNCIA: PARAR TUDO no editor "
                  "e esperar o usuário avisar que pode voltar (depois: retrato.py antes ... --retomar).")
            [print("  " + x) for x in mexeu[:12]]; sys.exit(3)
    if modo == "vigiar": print("OK: ninguém mexeu desde a última mexida do Gab"); return
    if modo == "antes":
        arq = os.path.join(d, f"{base}_{time.strftime('%Y%m%d_%H%M%S')}.json"); json.dump(agora, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if "--retomar" in a: json.dump(agora, open(gab, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        n = sum(len(v["itens"]) for v in agora["trilhas"].values()); print(f"retrato salvo ({n} itens): {arq}"); return
    ant = sorted(glob.glob(os.path.join(d, f"{base}_*.json")))
    if not ant: sys.exit("sem retrato 'antes' desta timeline")
    difs = comparar(json.load(open(ant[-1], encoding="utf-8")), agora, alvos)
    json.dump(agora, open(gab, "w", encoding="utf-8"), ensure_ascii=False, indent=1)   # como o Gab deixou a timeline
    if not difs: print(f"OK: nada fora do alvo mudou (comparado com {os.path.basename(ant[-1])})"); return
    print("ATENÇÃO, mudou fora do alvo:"); [print("  " + x) for x in difs]; sys.exit(1)


if __name__ == "__main__":
    main()
