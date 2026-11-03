"""Everything the user's AIs already know about them, in one file.

People have years of context sitting in ChatGPT and Claude memory. Instead of
answering the onboarding from scratch, `mariana dossie` hands them a prompt
(prompts/dossie.md) that makes those assistants dump it all, with the source
of each fact and NÃO SEI where they don't know.

Sources, all merged into data/sobre.md (the onboarding's material file):
  - the answer pasted from ChatGPT / claude.ai (`--add arquivo.md`); Claude
    in Chrome can run the prompt in the user's own logged-in tab and save it
  - Claude Code's local memory (`--claude-memory`), read straight from disk

Each source is a dated section, so running it again updates instead of
duplicating. Then `--onboard` rebuilds the dossier every agent reads.
"""

from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path

from harvey.paths import PROJECT_ROOT

PROMPT_FILE = PROJECT_ROOT / "prompts" / "dossie.md"
SOBRE_FILE = PROJECT_ROOT / "data" / "sobre.md"
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"


def prompt_text() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")


def copy_to_clipboard(text: str) -> bool:
    for cmd in (["pbcopy"], ["clip"], ["xclip", "-selection", "clipboard"]):
        try:
            subprocess.run(cmd, input=text.encode(), check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (OSError, subprocess.CalledProcessError):
            continue
    return False


def claude_memory_dirs() -> list[Path]:
    """Claude Code memory folders on this machine (one per project)."""
    if not CLAUDE_PROJECTS.exists():
        return []
    return sorted(p for p in CLAUDE_PROJECTS.glob("*/memory") if (p / "MEMORY.md").exists())


# "feedback" memories are rules for the assistant, not facts about the person.
MEMORY_TYPES = ("user", "project", "reference")


def read_claude_memory(folder: Path, types=MEMORY_TYPES) -> str:
    """Memory files about the person, without frontmatter, one block each."""
    blocks = []
    for f in sorted(folder.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        meta = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        body = text[meta.end():] if meta else text
        kind = re.search(r"^\s*type:\s*(\w+)", meta.group(1), re.M) if meta else None
        if kind and kind.group(1) not in types:
            continue
        desc = re.search(r"^description:\s*(.+)$", meta.group(1), re.M) if meta else None
        title = desc.group(1).strip() if desc else f.stem
        blocks.append(f"### {title}\n{body.strip()}")
    return "\n\n".join(blocks)


def _sections(text: str) -> dict[str, str]:
    parts = re.split(r"^(## Fonte: .+)$", text, flags=re.M)
    head, out = parts[0], {}
    for i in range(1, len(parts), 2):
        out[parts[i].strip()] = parts[i + 1].strip()
    return {"": head.strip(), **out}


def merge(source: str, content: str, path: Path = SOBRE_FILE) -> Path:
    """Put one source in data/sobre.md, replacing that source's last version."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    sections = _sections(existing)
    key = f"## Fonte: {source}"
    sections.pop(key, None)
    sections[key] = f"_Atualizado em {date.today().strftime('%d/%m/%Y')}_\n\n{content.strip()}"
    head = sections.pop("") or "# Sobre mim (material do onboarding)"
    out = [head, ""]
    for k, v in sections.items():
        out += [k, "", v, ""]
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    return path


def gaps(text: str) -> int:
    """How many fields the assistant marked as unknown."""
    return len(re.findall(r"N[ÃA]O SEI", text, flags=re.I))


async def answer_from(brain, material: str, source: str) -> str:
    """Answer the dossier prompt from raw material (e.g. Claude Code memory),
    the way ChatGPT would from its own memory. Empty when the brain fails."""
    prompt = (prompt_text().split("## Depois de preencher")[0]
              + f"\n\nSua memória sobre mim é o material abaixo ({source}). Use só ele. "
              "Não faça perguntas agora: preencha tudo o que der, marque NÃO SEI no resto "
              "e no fim liste as 10 perguntas que mais fariam diferença.\n\n"
              + material[:150000])
    text = await brain.think(prompt, agent="dossie", task="from_memory", timeout=600)
    return (text or "").replace("—", ",").replace("–", ",").strip()

