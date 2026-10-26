import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import premiere2019_lib as P

pre = r"C:\Program Files\Adobe\Adobe Premiere Pro CC 2019\Settings\SequencePresets\Digital SLR\1080p\DSLR 1080p30.sqpreset"
print(P.jsx("""
  app.enableQE();
  var r = {};
  r.qeBins = qe.project.numBins; r.qeName = qe.project.name;
  r.ret = String(qe.project.newSequence(args.nome, args.pre));
  r.dom = app.project.sequences.numSequences;
  r.qeSeqs = qe.project.numSequences; r.qeItems = qe.project.numItems;
  return r;
""", nome="Reels 01", pre=pre))
