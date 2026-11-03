"""Ponte mínima do Rick com o Photoshop: ExtendScript via AppleScript `do javascript` (macOS) ou COM `DoJavaScript` (Windows, no fim do arquivo).

Testado no Photoshop 2026 (27.11.0), 16/10/2026. Não precisa de plugin, porta nem senha.
Uso:
    import ps_lib as PS
    PS.js('app.version')                      # roda um trecho e devolve o resultado (texto)
    PS.arquivo('/caminho/script.jsx')         # roda um .jsx inteiro ($.evalFile)
"""
import json
import os
import subprocess
import tempfile
import time

APP = 'application id "com.adobe.Photoshop"'


def _osascript(codigo_js, timeout=600):
    # O código vai num arquivo para não brigar com aspas do AppleScript.
    with tempfile.NamedTemporaryFile("w", suffix=".jsx", delete=False, encoding="utf-8") as f:
        f.write(codigo_js)
        caminho = f.name
    try:
        return arquivo(caminho, timeout=timeout)
    finally:
        os.unlink(caminho)


ALERTAS = []  # mensagens de alertas do Photoshop fechados pelo destravar() durante os comandos

_PROC = '(first process whose bundle identifier is "com.adobe.Photoshop")'


def destravar():
    """Fecha alerta modal do Photoshop (janela "Adobe Photoshop" com botão OK) e devolve o texto dele.
    Alguns comandos e ferramentas nativas abrem alerta mesmo com DialogModes.NO e travam tudo até alguém clicar OK."""
    script = f'''tell application "System Events" to tell {_PROC}
        set msgs to {{}}
        repeat with w in (every window whose name is "Adobe Photoshop")
            try
                set end of msgs to (value of every static text of w) as text
                click button "OK" of w
            end try
        end repeat
        return msgs as text
    end tell'''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=20)
    return r.stdout.strip()


def arquivo(caminho, timeout=600, alerta_apos=6):
    caminho = os.path.abspath(caminho).replace("\\", "/").replace("'", "\\'")
    # Saída vai para arquivo: resposta grande (>64 KB) num PIPE trava o osascript para sempre.
    with tempfile.TemporaryFile("w+", encoding="utf-8") as fo, tempfile.TemporaryFile("w+", encoding="utf-8") as fe:
        p = subprocess.Popen(
            ["osascript", "-e", f"with timeout of {timeout} seconds",
             "-e", f"tell {APP} to do javascript \"$.evalFile('{caminho}')\"", "-e", "end timeout"],
            stdout=fo, stderr=fe, text=True,
        )
        inicio = ultimo = time.time()
        while p.poll() is None:
            time.sleep(0.2)
            passou = time.time() - inicio
            if passou > timeout:
                p.kill()
                raise TimeoutError(f"Photoshop não respondeu em {timeout}s")
            if passou > alerta_apos and time.time() - ultimo > 3:  # a cada 3 s depois do limite
                ultimo = time.time()
                msg = destravar()
                if msg:
                    ALERTAS.append(msg)
        fo.seek(0); fe.seek(0)
        out, err = fo.read(), fe.read()
    if p.returncode != 0:
        raise RuntimeError(err.strip())
    return out.strip()


def js(codigo, timeout=600):
    return _osascript(codigo, timeout=timeout)


JSX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jsx")


def ferramenta(nome, params=None, timeout=600):
    """Chama uma ferramenta nativa do agente do Photoshop (docs/catalogo/agente_ferramentas.json).
    IDs de documento e camada são UUID: pegar com doc_frente() e document_get_structure.
    Devolve o dict {"status": "success"|"error", "data": ...}."""
    lib = os.path.join(JSX, "agente_lib.jsx").replace("\\", "/").replace("'", "\\'")
    codigo = f"$.evalFile('{lib}'); ferramenta({json.dumps(nome)}, {json.dumps(params or {}, ensure_ascii=False)});"
    return json.loads(js(codigo, timeout=timeout))


def doc_frente():
    """UUID do documento da frente (ferramenta escondida application_list_open_documents)."""
    return ferramenta("application_list_open_documents")["data"]["front_doc_id"]


def gravar(ligar=True):
    """Liga/desliga o gravador: cada ação que o USUÁRIO faz no Photoshop vira uma linha JSON
    (evento + descritor completo) em $TMPDIR/orick_gravacao.jsonl. Ações feitas por script não aparecem.
    Sempre desligar no fim."""
    if ligar:
        ev = os.path.join(JSX, "gravador_evento.jsx").replace("\\", "/").replace("'", "\\'")
        return js(f"app.notifiersEnabled=true; app.notifiers.removeAll(); app.notifiers.add('All ', new File('{ev}')); 'gravando'")
    return js("app.notifiers.removeAll(); app.notifiersEnabled=false; 'parado'")


if os.name == "nt":
    # Windows: mesma ponte por COM (DoJavaScript) via PowerShell, sem dependências. Testado no 2026 (27.11.0), 30/10/2026.
    # $.evalFile lê .jsx UTF-8 sem BOM normalmente; quem exige ASCII puro é o DoJavaScriptFile, que não é usado aqui.
    _PS1_RODAR = r'''param($js, $saida)
[Console]::OutputEncoding = [Text.Encoding]::UTF8
try { $app = [Runtime.InteropServices.Marshal]::GetActiveObject("Photoshop.Application") }
catch { [Console]::Error.WriteLine("Photoshop fechado ou carregando: abra o Photoshop 2026 e tente de novo."); exit 2 }
try { $r = $app.DoJavaScript([IO.File]::ReadAllText($js, [Text.Encoding]::UTF8)) }
catch { [Console]::Error.WriteLine($_.Exception.InnerException.Message + " " + $_.Exception.Message); exit 1 }
[IO.File]::WriteAllText($saida, [string]$r, (New-Object Text.UTF8Encoding $false))
'''
    # Alerta modal do Photoshop: janela de nível superior chamada só "Adobe Photoshop" (a principal é "Adobe Photoshop 2026").
    _PS1_DESTRAVAR = r'''Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$A = [Windows.Automation.AutomationElement]; $T = [Windows.Automation.TreeScope]
$msgs = @()
foreach ($p in Get-Process Photoshop -ErrorAction SilentlyContinue) {
  $c = New-Object Windows.Automation.PropertyCondition($A::ProcessIdProperty, $p.Id)
  foreach ($w in $A::RootElement.FindAll($T::Children, $c)) {
    if ($w.Current.Name -ne "Adobe Photoshop") { continue }
    foreach ($e in $w.FindAll($T::Descendants, [Windows.Automation.Condition]::TrueCondition)) {
      $t = $e.Current.ControlType.ProgrammaticName
      if ($t -eq "ControlType.Text") { $msgs += $e.Current.Name }
      elseif ($t -eq "ControlType.Button" -and $e.Current.Name -eq "OK") {
        try { $e.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke() } catch {} }
    }
  }
}
[Console]::OutputEncoding = [Text.Encoding]::UTF8; $msgs -join " "
'''

    def _powershell(script, *args, **kw):
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8-sig") as f:
            f.write(script)
        return f.name, ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", f.name, *args]

    def destravar():
        ps1, cmd = _powershell(_PS1_DESTRAVAR)
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=20)
            return r.stdout.decode("utf-8", "replace").strip()
        finally:
            os.unlink(ps1)

    def js(codigo, timeout=600, alerta_apos=6):
        with tempfile.NamedTemporaryFile("w", suffix=".jsx", delete=False, encoding="utf-8") as f:
            f.write(codigo)
        saida = f.name + ".out"
        ps1, cmd = _powershell(_PS1_RODAR, f.name, saida)
        try:
            with tempfile.TemporaryFile() as fe:
                p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=fe)
                inicio = ultimo = time.time()
                while p.poll() is None:
                    time.sleep(0.2)
                    passou = time.time() - inicio
                    if passou > timeout:
                        p.kill()
                        raise TimeoutError(f"Photoshop não respondeu em {timeout}s")
                    if passou > alerta_apos and time.time() - ultimo > 3:
                        ultimo = time.time()
                        msg = destravar()
                        if msg:
                            ALERTAS.append(msg)
                fe.seek(0)
                err = fe.read().decode("utf-8", "replace") if p.returncode else ""
            if p.returncode != 0:
                raise RuntimeError(err.strip())
            with open(saida, encoding="utf-8") as fo:
                return fo.read().strip()
        finally:
            for c in (f.name, saida, ps1):
                if os.path.exists(c):
                    os.unlink(c)

    def arquivo(caminho, timeout=600, alerta_apos=6):
        caminho = os.path.abspath(caminho).replace("\\", "/").replace("'", "\\'")
        return js(f"$.evalFile('{caminho}')", timeout=timeout, alerta_apos=alerta_apos)

    def _osascript(codigo_js, timeout=600):
        return js(codigo_js, timeout=timeout)


if __name__ == "__main__":
    print(js('app.version + " | ExtendScript " + $.version + " | fontes " + app.fonts.length'))
