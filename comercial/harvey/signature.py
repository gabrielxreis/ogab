"""Email signature: built once from harvey.yaml, used on every send.

Mariana never asks the model to write a signature (prompts forbid it), so a
signature is always the same, always correct, and never hallucinated. It is
appended at SEND time, after the pre-send gate has judged the body alone:
the site and Instagram links in a signature are expected, and must not count
against the one-link budget a cold body gets.

Two renderings:
  * text  — appended to the plain-text part every provider sends
  * html  — the multipart/alternative part (Gmail, SMTP) and the file
            `data/signature.html` you can paste into any mail client, or that
            `mariana signature --install-gmail` sets as your Gmail signature.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from harvey.paths import PROJECT_ROOT

SIGNATURE_DIR = PROJECT_ROOT / "data"
HTML_FILE = SIGNATURE_DIR / "signature.html"
TEXT_FILE = SIGNATURE_DIR / "signature.txt"
PREVIEW_FILE = SIGNATURE_DIR / "signature_preview.html"

# Plain-text signature delimiter: "-- " (with the trailing space) is the RFC
# 3676 marker mail clients use to fold or strip signatures in replies.
TEXT_DELIMITER = "-- "


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _bare(url: str) -> str:
    """'https://www.site.com/' → 'site.com' for display."""
    url = (url or "").strip()
    url = re.sub(r"^https?://", "", url, flags=re.I)
    url = re.sub(r"^www\.", "", url, flags=re.I)
    return url.rstrip("/")


def _href(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    return url if re.match(r"^https?://", url, re.I) else f"https://{url}"


def _instagram_url(handle_or_url: str) -> str:
    v = (handle_or_url or "").strip()
    if not v:
        return ""
    if "instagram.com" in v:
        return _href(v)
    return f"https://instagram.com/{v.lstrip('@')}"


def fields(config) -> dict:
    """The resolved signature fields, falling back to the persona."""
    persona = config.persona
    sig = persona.signature
    whatsapp = _digits(sig.whatsapp)
    return {
        "name": sig.name or persona.name,
        "title": sig.title or persona.role,
        "company": sig.company or persona.company,
        "email": persona.email,
        "phone": sig.phone,
        "whatsapp": whatsapp,
        "whatsapp_url": f"https://wa.me/{whatsapp}" if whatsapp else "",
        "website": _href(sig.website),
        "instagram": _instagram_url(sig.instagram),
        "portfolio": _href(sig.portfolio),
        "extra_lines": [line for line in sig.extra_lines if line.strip()],
        "accent": sig.accent_color or "#111111",
        "photo_url": sig.photo_url,
    }


def is_enabled(config) -> bool:
    sig = getattr(getattr(config, "persona", None), "signature", None)
    return bool(sig and sig.enabled)


def render_text(config) -> str:
    """Plain-text signature, without the delimiter line."""
    f = fields(config)
    lines = [f["name"]]
    role = " | ".join(x for x in (f["title"], f["company"]) if x and x != f["name"])
    if role:
        lines.append(role)
    if f["portfolio"]:
        lines.append(_bare(f["portfolio"]))
    if f["website"]:
        lines.append(_bare(f["website"]))
    if f["instagram"]:
        lines.append(_bare(f["instagram"]))
    if f["whatsapp"]:
        lines.append(f"WhatsApp: +{f['whatsapp']}")
    elif f["phone"]:
        lines.append(f["phone"])
    lines.extend(f["extra_lines"])
    return "\n".join(line for line in lines if line)


def render_html(config) -> str:
    """Email-client-safe HTML: one table, inline styles, no external CSS."""
    f = fields(config)
    esc = html.escape
    accent = esc(f["accent"])

    def link(url: str, label: str) -> str:
        return (f'<a href="{esc(url)}" style="color:{accent};text-decoration:none;">'
                f'{esc(label)}</a>')

    rows = [
        f'<div style="font-size:15px;font-weight:600;color:#111;">{esc(f["name"])}</div>'
    ]
    role = " | ".join(x for x in (f["title"], f["company"]) if x and x != f["name"])
    if role:
        rows.append(f'<div style="font-size:13px;color:#555;">{esc(role)}</div>')

    links = []
    if f["portfolio"]:
        links.append(link(f["portfolio"], "Portfólio"))
    if f["website"]:
        links.append(link(f["website"], _bare(f["website"])))
    if f["instagram"]:
        handle = "@" + _bare(f["instagram"]).split("/")[-1]
        links.append(link(f["instagram"], handle))
    if f["whatsapp_url"]:
        links.append(link(f["whatsapp_url"], "WhatsApp"))
    elif f["phone"]:
        links.append(esc(f["phone"]))
    if links:
        sep = '<span style="color:#bbb;"> &middot; </span>'
        rows.append(f'<div style="font-size:13px;margin-top:4px;">{sep.join(links)}</div>')
    for line in f["extra_lines"]:
        rows.append(f'<div style="font-size:12px;color:#777;">{esc(line)}</div>')

    photo = ""
    if f["photo_url"]:
        photo = (
            f'<td style="padding-right:12px;vertical-align:top;">'
            f'<img src="{esc(f["photo_url"])}" width="56" height="56" alt="" '
            f'style="border-radius:50%;display:block;"></td>'
        )
    return (
        '<table cellpadding="0" cellspacing="0" border="0" '
        'style="font-family:Arial,Helvetica,sans-serif;margin-top:16px;">'
        f'<tr>{photo}<td style="border-left:2px solid {accent};padding-left:12px;'
        f'vertical-align:top;">{"".join(rows)}</td></tr></table>'
    )


def body_to_html(body: str) -> str:
    """Plain body → minimal HTML paragraphs (keeps the text look)."""
    paragraphs = [p for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
    out = []
    for p in paragraphs:
        safe = html.escape(p).replace("\n", "<br>")
        out.append(f'<p style="margin:0 0 12px 0;">{safe}</p>')
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
        f'color:#222;line-height:1.5;">{"".join(out)}</div>'
    )


def compose(config, body: str) -> tuple[str, str | None]:
    """(plain text, html or None) for one outgoing email.

    Disabled signature → the body unchanged and no HTML part, which is
    exactly what the providers sent before signatures existed.
    """
    if not is_enabled(config):
        return body, None
    text = f"{body.rstrip()}\n\n{TEXT_DELIMITER}\n{render_text(config)}"
    html_body = body_to_html(body) + render_html(config)
    return text, html_body


def write_files(config) -> dict[str, Path]:
    """Write signature.html / .txt and a browser preview. Returns the paths."""
    SIGNATURE_DIR.mkdir(parents=True, exist_ok=True)
    sig_html = render_html(config)
    HTML_FILE.write_text(sig_html, encoding="utf-8")
    TEXT_FILE.write_text(render_text(config) + "\n", encoding="utf-8")
    sample = (
        "Oi Ana,\n\nVi que a igreja transmite o culto de domingo, mas os cortes "
        "do Instagram ainda saem sem legenda.\n\nFaz sentido conversar sobre isso?"
    )
    PREVIEW_FILE.write_text(
        "<!doctype html><meta charset='utf-8'><title>Assinatura</title>"
        "<body style='background:#f4f4f4;padding:32px;'>"
        "<div style='max-width:640px;margin:auto;background:#fff;padding:24px;"
        "border-radius:8px;'>"
        "<p style='font:12px Arial;color:#999;margin:0 0 16px;'>Prévia de um email "
        "com a assinatura</p>"
        f"{body_to_html(sample)}{sig_html}</div></body>",
        encoding="utf-8",
    )
    return {"html": HTML_FILE, "text": TEXT_FILE, "preview": PREVIEW_FILE}
