// Chamado pelo Photoshop a cada ação do usuário (notifier "All "). Anexa o descritor em $TMPDIR/orick_gravacao.jsonl.
try{ $.evalFile(File($.fileName).path + "/desc2json.jsx");
 var desc=arguments[0], ev=arguments[1];
 var linha='{"t":'+new Date().getTime()+',"evento":"'+nomeId(ev)+'","desc":'+(desc?d2j(desc).replace(/,\}/g,"}"):'null')+'}';
 var f=new File(Folder.temp+"/orick_gravacao.jsonl"); f.encoding="UTF-8"; f.lineFeed="Unix"; f.open("a"); f.writeln(linha); f.close();
}catch(e){}
