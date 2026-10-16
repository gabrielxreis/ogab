(function () {
  const C = window.CENA, P = C.P;
  (P.modulos || []).forEach(m => { if (C.mod[m] && P[m]) C.mod[m](P[m], C); });
  C.tl.set({}, {}, P.dur);
  window.__timelines = window.__timelines || {}; window.__timelines["cena-" + P.camada] = C.tl;
})();
