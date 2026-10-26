"""Reescreve o Source Text de um título nativo (Basic Title.mogrt) no 13.1.5: texto, fonte, tamanho, cor."""
import json, os, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import premiere2019_lib as P

r = P.jsx("""
  var c = GAB.seq("Reels 01").videoTracks[3].clips[0], txt = null;
  for (var i = 0; i < c.components.numItems; i++) if (c.components[i].matchName === "AE.ADBE Text") txt = c.components[i];
  return txt.properties[0].getValue().substr(4);
""")
j = json.loads(r)
ss = j["mTextParam"]["mStyleSheet"]
ss["mText"] = "SEM ATALHO. COM PROCESSO ÇÃ"
ss["mFontName"]["mParamValues"][0][1] = "Poppins-Bold"
ss["mFontSize"]["mParamValues"][0][1] = 90
ss["mFillColor"]["mParamValues"][0][1] = 0x00DCFF   # teste de ordem dos canais: amarelo se for BGR, azul-claro se RGB
novo = json.dumps(j, ensure_ascii=True, separators=(",", ":"))
for variante in ("prefixo", "sem_prefixo"):
    t = time.time()
    try:
        out = P.jsx("""
          var c = GAB.seq("Reels 01").videoTracks[3].clips[0], txt = null;
          for (var i = 0; i < c.components.numItems; i++) if (c.components[i].matchName === "AE.ADBE Text") txt = c.components[i];
          var js = args.json;
          var v = args.prefixo ? String.fromCharCode(js.length * 2) + String.fromCharCode(0, 0, 0) + js : js;
          txt.properties[0].setValue(v, true);
          var lido = txt.properties[0].getValue();
          return { ok: lido.indexOf("SEM ATALHO") >= 0, inicio: [lido.charCodeAt(0), lido.length] };
        """, json=novo, prefixo=(variante == "prefixo"))
    except Exception as e:
        out = str(e)
    print(variante, round(time.time() - t, 2), out)
    if isinstance(out, dict) and out.get("ok"):
        break
print(P.quadro("Reels 01", 16.0, os.path.join(AQUI, "render", "titulo_16s.png")))
