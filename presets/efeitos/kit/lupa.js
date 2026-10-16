// LUPA (bulge, como o filtro do PixiJS, em WebGL próprio): uma lente que estufa a imagem e passa por cima dela.
// EFX.lupa(canvas, fonte, { raio: .22, forca: .7, brilho: .12 }) -> draw(cx, cy, forca?)  (cx, cy de 0 a 1)
EFX.lupa = function (cv, fonte, o) {
  o = Object.assign({ raio: .22, forca: .7, brilho: .12 }, o);
  const gl = cv.getContext("webgl", { premultipliedAlpha: false, preserveDrawingBuffer: true, alpha: true });
  const sh = (tipo, src) => { const s = gl.createShader(tipo); gl.shaderSource(s, src); gl.compileShader(s); return s; };
  const pr = gl.createProgram();
  gl.attachShader(pr, sh(gl.VERTEX_SHADER, "attribute vec2 p; varying vec2 uv; void main(){ uv = vec2(p.x*.5+.5, .5-p.y*.5); gl_Position = vec4(p,0.,1.); }"));
  gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, `precision mediump float; varying vec2 uv; uniform sampler2D tx; uniform vec2 c; uniform float r, f, b, asp;
    void main(){ vec2 d = uv - c; d.x *= asp; float dist = length(d); vec2 q = uv;
      if (dist < r) { float k = dist / r; float s = mix(1., smoothstep(0., 1., k), f); q = c + (uv - c) * s; }
      vec4 col = texture2D(tx, q); float aro = smoothstep(r, r * .93, dist) * (1. - smoothstep(r * .93, r * .8, dist));
      col.rgb += b * (1. - smoothstep(0., r, dist)) * col.a + aro * .25 * f; gl_FragColor = col; }`));
  gl.linkProgram(pr); gl.useProgram(pr);
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const lp = gl.getAttribLocation(pr, "p"); gl.enableVertexAttribArray(lp); gl.vertexAttribPointer(lp, 2, gl.FLOAT, false, 0, 0);
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T].forEach(k => gl.texParameteri(gl.TEXTURE_2D, k, gl.CLAMP_TO_EDGE));
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  const U = n => gl.getUniformLocation(pr, n); let carregou = false;
  return function draw(cx, cy, forca) {
    if (!carregou || fonte.tagName === "VIDEO") { gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, fonte); carregou = true; }
    gl.viewport(0, 0, cv.width, cv.height); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.uniform2f(U("c"), cx, cy); gl.uniform1f(U("r"), o.raio); gl.uniform1f(U("f"), forca ?? o.forca); gl.uniform1f(U("b"), o.brilho);
    gl.uniform1f(U("asp"), cv.width / cv.height); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  };
};
