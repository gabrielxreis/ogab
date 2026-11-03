$.evalFile(File($.fileName).path + "/desc2json.jsx");
function _put(d, k, v){
  var id=s(k);
  if (v===null||v===undefined) return;
  if (typeof v=="boolean") d.putBoolean(id,v);
  else if (typeof v=="number") { if (v%1===0 && Math.abs(v)<2147483647) d.putInteger(id,v); else d.putDouble(id,v); }
  else if (typeof v=="string") d.putString(id,v);
  else if (v instanceof Array) d.putList(id,_lista(v));
  else d.putObject(id,s("null"),_desc(v));
}
function _desc(o){ var d=new ActionDescriptor(); for (var k in o) if (o.hasOwnProperty(k)) _put(d,k,o[k]); return d; }
function _lista(a){ var l=new ActionList(); for (var i=0;i<a.length;i++){ var v=a[i];
  if (typeof v=="boolean") l.putBoolean(v); else if (typeof v=="number"){ if(v%1===0) l.putInteger(v); else l.putDouble(v);} else if (typeof v=="string") l.putString(v); else if (v instanceof Array) l.putList(_lista(v)); else l.putObject(s("null"),_desc(v)); } return l; }
function _refAgente(){ var r=new ActionReference(); r.putClass(s("agent")); r.putClass(s("application")); return r; }
function ferramenta(nome, params){
  var a=new ActionDescriptor(); a.putReference(s("null"),_refAgente()); a.putString(s("name"),nome); a.putObject(s("params"),s("null"),_desc(params||{}));
  var res=executeAction(s("executeTool"),a,DialogModes.NO);
  return d2j(res).replace(/,\}/g,"}").replace(/"_obj":"null",?/g,"");
}
