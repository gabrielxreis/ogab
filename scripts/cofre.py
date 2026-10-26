"""Cofre do Gab (/ogab): criptografia só com a biblioteca padrão do Python (roda igual em Mac, Windows e Linux,
sem instalar nada). A senha (chave do cofre) fica SÓ no servidor de licenças e só é entregue com key válida.

Esquema: encripta-e-autentica. Keystream = SHA-256(chave_enc || nonce || contador) em modo contador; autenticação
por HMAC-SHA-256. A segurança está na chave ser secreta (fica no servidor), nunca na obscuridade do código.

  python3 cofre.py testar          # teste rápido do ciclo encriptar/decriptar
"""
import hashlib, hmac, secrets, sys

MAGIA = b"OGC1"


def _subchaves(k: bytes):
    return hashlib.sha256(k + b"ogab-enc").digest(), hashlib.sha256(k + b"ogab-mac").digest()


def _keystream(k_enc: bytes, nonce: bytes, n: int) -> bytes:
    out = bytearray()
    i = 0
    while len(out) < n:
        out += hashlib.sha256(k_enc + nonce + i.to_bytes(8, "big")).digest()
        i += 1
    return bytes(out[:n])


def _xor(a: bytes, b: bytes) -> bytes:
    return (int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).to_bytes(len(a), "big") if a else b""


def chave(hexstr: str) -> bytes:
    k = bytes.fromhex(hexstr.strip())
    if len(k) < 16:
        raise ValueError("chave do cofre curta demais")
    return k


def encriptar(dados: bytes, k: bytes) -> bytes:
    nonce = secrets.token_bytes(16)
    k_enc, k_mac = _subchaves(k)
    ct = _xor(dados, _keystream(k_enc, nonce, len(dados)))
    tag = hmac.new(k_mac, nonce + ct, hashlib.sha256).digest()
    return MAGIA + nonce + tag + ct


def decriptar(blob: bytes, k: bytes) -> bytes:
    if blob[:4] != MAGIA:
        raise ValueError("cofre em formato desconhecido")
    nonce, tag, ct = blob[4:20], blob[20:52], blob[52:]
    k_enc, k_mac = _subchaves(k)
    if not hmac.compare_digest(tag, hmac.new(k_mac, nonce + ct, hashlib.sha256).digest()):
        raise ValueError("cofre adulterado (autenticação falhou)")
    return _xor(ct, _keystream(k_enc, nonce, len(ct)))


if __name__ == "__main__":
    if sys.argv[1:2] == ["testar"]:
        k = secrets.token_bytes(32)
        for msg in (b"", b"a", b"abravida" * 5000, secrets.token_bytes(123)):
            assert decriptar(encriptar(msg, k), k) == msg
        b = encriptar(b"teste", k)
        b2 = b[:52] + bytes([b[52] ^ 1]) + b[53:]   # mexe no 1o byte do texto cifrado
        try:
            decriptar(b2, k); print("FALHOU: adulteração não detectada"); sys.exit(1)
        except ValueError:
            pass
        try:
            decriptar(b, secrets.token_bytes(32)); print("FALHOU: chave errada passou"); sys.exit(1)
        except ValueError:
            pass
        print("cofre ok")
    else:
        raise SystemExit(__doc__)
