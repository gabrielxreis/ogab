"""Cliente mínimo do MCP do VoiceStudio (Streamable HTTP) para usar pelo terminal.

Uso: python3 vs_mcp.py <tool> '<json args>'     |   python3 vs_mcp.py list
"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:3900/mcp/"
HDR = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
       "X-OmniVoice-Client-Id": "claude-code"}


def rpc(method, params=None, sid=None, rid=1):
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if rid is not None:
        body["id"] = rid
    h = dict(HDR)
    if sid:
        h["Mcp-Session-Id"] = sid
    req = urllib.request.Request(URL, json.dumps(body).encode(), h)
    with urllib.request.urlopen(req, timeout=1800) as r:
        sid = r.headers.get("Mcp-Session-Id") or sid
        raw = r.read().decode()
    msg = None
    for line in raw.splitlines():
        if line.startswith("data:"):
            msg = json.loads(line[5:])
    if msg is None and raw.strip():
        msg = json.loads(raw)
    return msg, sid


def main():
    _, sid = rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                "clientInfo": {"name": "vs_mcp", "version": "1"}})
    rpc("notifications/initialized", sid=sid, rid=None)
    if sys.argv[1] == "list":
        msg, _ = rpc("tools/list", sid=sid, rid=2)
        for t in msg["result"]["tools"]:
            print(t["name"], json.dumps(t["inputSchema"].get("properties", {}), ensure_ascii=False))
        return
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    msg, _ = rpc("tools/call", {"name": sys.argv[1], "arguments": args}, sid=sid, rid=2)
    print(json.dumps(msg.get("result", msg), ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main()
