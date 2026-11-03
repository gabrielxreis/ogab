var out = [];
function dump(nome, obj){
  try{
    var r = obj.reflect;
    var ps = r.properties, ms = r.methods, p=[], m=[];
    for (var i=0;i<ps.length;i++){ var n=ps[i].name; if(n=="__proto__"||n=="__count__"||n=="__class__"||n=="reflect") continue; p.push(n); }
    for (var j=0;j<ms.length;j++){ var mm=ms[j]; var a=[]; try{ for(var k=0;k<mm.arguments.length;k++) a.push(mm.arguments[k].name);}catch(e){} m.push(mm.name+"("+a.join(",")+")"); }
    out.push("CLASS\t"+nome+"\tPROPS\t"+p.join(",")+"\tMETHODS\t"+m.join(","));
  }catch(e){ out.push("ERR\t"+nome+"\t"+e); }
}
app.displayDialogs = DialogModes.NO;
var d = app.documents.add(1080,1350,72,"orick_probe",NewDocumentMode.RGB,DocumentFill.WHITE);
dump("Application", app);
dump("Preferences", app.preferences);
dump("Document", d);
dump("Documents", app.documents);
var l = d.artLayers.add(); dump("ArtLayer", l); dump("ArtLayers", d.artLayers); dump("Layers", d.layers);
var t = d.artLayers.add(); t.kind = LayerKind.TEXT; t.textItem.contents="Teste"; dump("TextItem", t.textItem);
var g = d.layerSets.add(); dump("LayerSet", g); dump("LayerSets", d.layerSets);
d.selection.select([[0,0],[100,0],[100,100],[0,100]]); dump("Selection", d.selection);
dump("Channel", d.channels[0]); dump("Channels", d.channels);
dump("HistoryState", d.historyStates[0]);
dump("Info", d.info);
dump("SolidColor", new SolidColor()); dump("RGBColor", new SolidColor().rgb);
dump("PathItems", d.pathItems);
dump("LayerComps", d.layerComps);
var lc = d.layerComps.add("c1","",true,true,true); dump("LayerComp", lc);
dump("ColorSamplers", d.colorSamplers);
dump("CountItems", d.countItems);
dump("Guides", d.guides);
dump("MeasurementScale", d.measurementScale);
dump("Notifiers", app.notifiers);
dump("TextFont", app.fonts[0]);
dump("ExportOptionsSaveForWeb", new ExportOptionsSaveForWeb());
dump("PNGSaveOptions", new PNGSaveOptions());
dump("JPEGSaveOptions", new JPEGSaveOptions());
dump("PhotoshopSaveOptions", new PhotoshopSaveOptions());
dump("PDFSaveOptions", new PDFSaveOptions());
dump("ActionDescriptor", new ActionDescriptor());
dump("ActionReference", new ActionReference());
dump("ActionList", new ActionList());
d.close(SaveOptions.DONOTSAVECHANGES);
var f = new File(Folder.temp + "/orick_reflect.txt"); f.encoding="UTF-8"; f.open("w"); f.write(out.join("\n")); f.close();
f.fsName;
