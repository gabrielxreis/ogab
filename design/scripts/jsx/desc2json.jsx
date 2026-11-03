function s(x){return stringIDToTypeID(x);}
function nomeId(id){ try{ var n=typeIDToStringID(id); if(n) return n; }catch(e){} try{ return typeIDToCharID(id);}catch(e){} return String(id); }
function q(x){ return '"'+String(x).replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\r/g,'\\r').replace(/\n/g,'\\n').replace(/\t/g,'\\t')+'"'; }
function _d2jVal(c, k, t, prof){
  switch(t){
    case DescValueType.OBJECTTYPE: var cc=_d2jCorpo(c.getObjectValue(k),prof+1); return '{"_obj":'+q(nomeId(c.getObjectType(k)))+(cc=='{}'?'}':','+cc.slice(1));
    case DescValueType.LISTTYPE: return _d2jLista(c.getList(k),prof+1);
    case DescValueType.STRINGTYPE: return q(c.getString(k));
    case DescValueType.INTEGERTYPE: return String(c.getInteger(k));
    case DescValueType.LARGEINTEGERTYPE: return String(c.getLargeInteger(k));
    case DescValueType.DOUBLETYPE: return String(c.getDouble(k));
    case DescValueType.BOOLEANTYPE: return String(c.getBoolean(k));
    case DescValueType.UNITDOUBLE: return '{"_unit":'+q(nomeId(c.getUnitDoubleType(k)))+',"_value":'+c.getUnitDoubleValue(k)+'}';
    case DescValueType.ENUMERATEDTYPE: return '{"_enum":'+q(nomeId(c.getEnumerationType(k)))+',"_value":'+q(nomeId(c.getEnumerationValue(k)))+'}';
    case DescValueType.CLASSTYPE: return '{"_class":'+q(nomeId(c.getClass(k)))+'}';
    case DescValueType.ALIASTYPE: return q(c.getPath(k).fsName);
    case DescValueType.RAWTYPE: return '"<raw '+c.getData(k).length+' bytes>"';
    case DescValueType.REFERENCETYPE: return refj(c.getReference(k));
    default: return q(String(t));
  }
}
function _d2jCorpo(d,prof){ if(prof>12) return '{"_trunc":true}'; var a=[]; for(var i=0;i<d.count;i++){ var k=d.getKey(i); var v; try{ v=_d2jVal(d,k,d.getType(k),prof);}catch(e){ v=q("ERR "+e);} a.push(q(nomeId(k))+':'+v);} return '{'+a.join(',')+'}'; }
function _d2jLista(l,prof){ var a=[]; for(var i=0;i<l.count;i++){ try{ a.push(_d2jVal(l,i,l.getType(i),prof)); }catch(e){ a.push(q("ERR "+e)); } } return '['+a.join(',')+']'; }
function d2j(d){ return _d2jCorpo(d,0); }
function grava(nome, txt){ var f=new File(Folder.temp+"/"+nome); f.encoding="UTF-8"; f.lineFeed="Unix"; f.open("w"); f.write(txt); f.close(); return f.fsName; }

function refj(r){ var a=[]; try{ while(r){ var cls=nomeId(r.getDesiredClass()); var f=r.getForm(); var o='{"_ref":'+q(cls);
  if(f==ReferenceFormType.ENUMERATED) o+=',"_enum":'+q(nomeId(r.getEnumeratedType()))+',"_value":'+q(nomeId(r.getEnumeratedValue()));
  else if(f==ReferenceFormType.IDENTIFIER) o+=',"_id":'+r.getIdentifier();
  else if(f==ReferenceFormType.INDEX) o+=',"_index":'+r.getIndex();
  else if(f==ReferenceFormType.NAME) o+=',"_name":'+q(r.getName());
  else if(f==ReferenceFormType.PROPERTY) o+=',"_property":'+q(nomeId(r.getProperty()));
  else if(f==ReferenceFormType.OFFSET) o+=',"_offset":'+r.getOffset();
  a.push(o+'}'); r=r.getContainer(); } }catch(e){} return '['+a.join(',')+']'; }
