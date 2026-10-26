import sys, time
sys.path.insert(0, __file__.rsplit("\\teste", 1)[0])
import premiere2019_lib as P

t = time.time(); print(P.versao()); print("1a chamada (carrega apoio)", round(time.time() - t, 3))
t = time.time()
for i in range(20):
    P.jsx("return 1")
print("media por chamada", round((time.time() - t) / 20 * 1000, 1), "ms")
for cod in ["return 1 +", "return naoExiste.x"]:
    try:
        P.jsx(cod)
    except RuntimeError as e:
        print("erro capturado:", e)
print(P.jsx("return {a: args.s, b: [1, 2]}", s="ção ✓"))
print(P.jsx("return app.project ? app.project.name : null"))
