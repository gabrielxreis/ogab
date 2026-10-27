"""Camada Windows do /ogab. NÃO altera nada no Mac: só entra no PYTHONPATH pelo windows/install.ps1.

O Python carrega este arquivo sozinho ao iniciar (sitecustomize). Ele deixa os scripts de SKILL_DIR/scripts, que
foram escritos para macOS, rodarem no Windows sem mudar uma linha deles:
  - garante RESOLVE_SCRIPT_API / RESOLVE_SCRIPT_LIB do Windows (os scripts usam os.environ.setdefault, então o
    valor daqui vence o caminho do Mac) e põe a pasta Modules do Resolve no sys.path;
  - traduz os dois comandos de Mac que os scripts chamam por subprocess:
      ["open", "-a", "DaVinci Resolve"]  -> abre o Resolve.exe
      ["defaults", "read", ...]          -> devolve vazio (a versão sai pela API do Resolve)
"""
import os
import sys

if os.name == "nt":
    _PF = os.environ.get("ProgramFiles", r"C:\Program Files")
    _PD = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    _API = os.path.join(_PD, "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting")
    _APP_DIR = os.path.join(_PF, "Blackmagic Design", "DaVinci Resolve")

    def _pasta_resolve():
        """DaVinci fora do Program Files (ex.: D:\\DaVinci, relato de 15/10/2026): procura no registro de desinstalação."""
        try:
            import winreg
        except ImportError:
            return None
        for raiz in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"):
            try:
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, raiz)
            except OSError:
                continue
            for i in range(winreg.QueryInfoKey(k)[0]):
                try:
                    sub = winreg.OpenKey(k, winreg.EnumKey(k, i))
                    nome = str(winreg.QueryValueEx(sub, "DisplayName")[0])
                    loc = str(winreg.QueryValueEx(sub, "InstallLocation")[0]).rstrip("\\")
                except OSError:
                    continue
                if nome.startswith("DaVinci Resolve") and os.path.exists(os.path.join(loc, "fusionscript.dll")):
                    return loc
        return None

    if os.environ.get("RESOLVE_SCRIPT_LIB") and os.path.exists(os.environ["RESOLVE_SCRIPT_LIB"]):
        _APP_DIR = os.path.dirname(os.environ["RESOLVE_SCRIPT_LIB"])
    elif not os.path.exists(os.path.join(_APP_DIR, "fusionscript.dll")):
        _APP_DIR = _pasta_resolve() or _APP_DIR
        os.environ["RESOLVE_SCRIPT_LIB"] = os.path.join(_APP_DIR, "fusionscript.dll")
    _EXE = os.path.join(_APP_DIR, "Resolve.exe")

    os.environ.setdefault("RESOLVE_SCRIPT_API", _API)
    os.environ.setdefault("RESOLVE_SCRIPT_LIB", os.path.join(_APP_DIR, "fusionscript.dll"))
    # Whisper na GPU: as DLLs CUDA dos pacotes nvidia-cublas-cu12/nvidia-cudnn-cu12 (pip) ficam em site-packages\nvidia\*\bin
    try:
        import glob as _glob, site as _site
        for _sp_dir in _site.getsitepackages() + [_site.getusersitepackages()]:
            for _bin in _glob.glob(os.path.join(_sp_dir, "nvidia", "*", "bin")):
                os.add_dll_directory(_bin)
                os.environ["PATH"] = _bin + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass
    _mods = os.path.join(os.environ["RESOLVE_SCRIPT_API"], "Modules")
    if _mods not in sys.path:
        sys.path.append(_mods)

    import subprocess as _sp

    def _traduz(args):
        """Devolve ('abrir', None), ('vazio', None) ou (None, None) para um comando de Mac conhecido."""
        if isinstance(args, (list, tuple)) and args:
            cmd = os.path.basename(str(args[0])).lower()
            if cmd == "open" and len(args) >= 3 and args[1] == "-a" and "davinci" in str(args[2]).lower():
                return "abrir"
            if cmd == "defaults":
                return "vazio"
        return None

    _run_original = _sp.run

    def _run(args, *a, **k):
        t = _traduz(args)
        if t == "abrir":
            if os.path.exists(_EXE):
                _sp.Popen([_EXE], cwd=_APP_DIR, close_fds=True)
            else:
                print(f"[ogab windows] Resolve.exe não encontrado em {_EXE}: abra o DaVinci Resolve manualmente.",
                      file=sys.stderr)
            return _sp.CompletedProcess(args, 0, "" if k.get("text") else b"", "" if k.get("text") else b"")
        if t == "vazio":
            vazio = "" if (k.get("text") or k.get("universal_newlines") or k.get("encoding")) else b""
            return _sp.CompletedProcess(args, 1, vazio, vazio)
        # npx/npm no Windows são .cmd: sem shell o subprocess não acha ("WinError 2"; centro.py preto, 23/10/2026)
        if isinstance(args, list) and args and str(args[0]).lower() in ("npx", "npm"):
            import shutil as _sh
            achado = _sh.which(str(args[0]))
            if achado:
                args = [achado] + list(args[1:])
        return _run_original(args, *a, **k)

    _sp.run = _run
