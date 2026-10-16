// Motor comum dos presets de apresentador (DESTAQUE, PALCO, VITRINE, LENTE, BANCADA).
// Cada preset registra um módulo em CENA.mod[nome](P, C); o fim.js roda os módulos da camada e publica a timeline.
window.CENA = (function () {
  const P = window.PLANO, root = document.getElementById("root"), tl = gsap.timeline({ paused: true });
  root.style.setProperty("--dest", P.dest || "#F2D16B");
  const el = (tag, cls, pai, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; (pai || root).appendChild(e); return e; };
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  return { P, root, tl, el, esc, mod: {} };
})();
