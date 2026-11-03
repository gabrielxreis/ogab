function s(x){return stringIDToTypeID(x);} var out=[];
for (var i=1;;i++){ var r=new ActionReference(); r.putIndex(s("actionSet"),i); var d; try{ d=executeActionGet(r);}catch(e){break;}
 var nome=d.getString(s("name")), n=d.hasKey(s("numberOfChildren"))?d.getInteger(s("numberOfChildren")):0, a=[];
 for (var j=1;j<=n;j++){ var r2=new ActionReference(); r2.putIndex(s("action"),j); r2.putIndex(s("actionSet"),i); try{ a.push(executeActionGet(r2).getString(s("name"))); }catch(e){} }
 out.push(nome+" ("+n+"): "+a.join(" | ")); }
out.join("\n");
