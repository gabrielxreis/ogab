import os, re, sys, json, collections
raiz = sys.argv[1]; saida = sys.argv[2]
pat = re.compile(r'_obj\s*:\s*["\']([A-Za-z0-9_]+)["\']')
ex = collections.defaultdict(list)
def objeto(txt, i):
    # volta até a { que abre este objeto
    prof = 0; j = i
    while j > 0:
        c = txt[j]
        if c == '}': prof += 1
        elif c == '{':
            if prof == 0: break
            prof -= 1
        j -= 1
    prof = 0; k = j
    while k < len(txt) and k - j < 1500:
        c = txt[k]
        if c == '{': prof += 1
        elif c == '}':
            prof -= 1
            if prof == 0: return txt[j:k+1]
        k += 1
    return txt[j:j+400]
for dp, dn, fn in os.walk(raiz):
    for f in fn:
        if not f.endswith('.js'): continue
        p = os.path.join(dp, f)
        try: txt = open(p, encoding='utf-8', errors='ignore').read()
        except: continue
        plugin = os.path.relpath(p, raiz).split(os.sep)[0]
        for m in pat.finditer(txt):
            nome = m.group(1)
            if len(ex[nome]) >= 3: continue
            o = objeto(txt, m.start())
            if any(o == e['obj'] for e in ex[nome]): continue
            ex[nome].append({'plugin': plugin, 'obj': o})
json.dump(ex, open(saida, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(ex), 'eventos/classes')
