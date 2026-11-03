var out=[]; for (var i=1;i<40000;i++){ var n=""; try{ n=typeIDToStringID(i);}catch(e){} if(n) out.push(i+"\t"+n); }
var f=new File(Folder.temp+"/orick_ids.txt"); f.encoding="UTF-8"; f.lineFeed="Unix"; f.open("w"); f.write(out.join("\n")); f.close(); out.length;
