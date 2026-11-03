var out=[];
function s(x){return stringIDToTypeID(x);}
var r=new ActionReference(); r.putProperty(s("property"), s("menuBarInfo")); r.putEnumerated(s("application"), s("ordinal"), s("targetEnum"));
var d=executeActionGet(r).getObjectValue(s("menuBarInfo"));
function walk(desc, path){
  var name = desc.hasKey(s("name"))? desc.getString(s("name")).replace(/&/g,"") : "";
  var id = desc.hasKey(s("menuID"))? desc.getInteger(s("menuID")) : "";
  var cmd = desc.hasKey(s("command"))? desc.getString(s("command")) : "";
  var p = path? path+" > "+name : name;
  if (desc.hasKey(s("submenu"))) { var l=desc.getList(s("submenu")); for (var i=0;i<l.count;i++) walk(l.getObjectValue(i), p); }
  else if (name && name!="-") out.push(id+"\t"+p+"\t"+cmd);
}
walk(d,"");
var f=new File(Folder.temp+"/orick_menus.txt"); f.encoding="UTF-8"; f.lineFeed="Unix"; f.open("w"); f.write(out.join("\n")); f.close(); out.length;
