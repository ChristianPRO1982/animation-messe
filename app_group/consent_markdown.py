import re
from urllib.parse import urlparse

from django.utils.html import escape
from django.utils.safestring import SafeString, mark_safe

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_STRONG_RE = re.compile(r"\*\*([^*]+)\*\*")
_EM_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$")
_HR_RE = re.compile(r"^([-*_])\1{2,}$")


def _sanitize_url(raw_url: str) -> str | None:
    value = str(raw_url or "").strip()
    if value.startswith("/"):
        return value

    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return value
    return None


def _render_inline(text: str) -> str:
    escaped = escape(text)
    link_tokens: list[str] = []

    def replace_link(match) -> str:
        label = escape(match.group(1))
        safe_url = _sanitize_url(match.group(2))
        if safe_url is None:
            return label
        token = f"@@AMCONSENTLINK{len(link_tokens)}@@"
        link_tokens.append(f'<a href="{escape(safe_url)}">{label}</a>')
        return token

    escaped = _LINK_RE.sub(replace_link, escaped)
    escaped = _STRONG_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _EM_RE.sub(r"<em>\1</em>", escaped)

    for index, html in enumerate(link_tokens):
        escaped = escaped.replace(f"@@AMCONSENTLINK{index}@@", html)
    return escaped


def _paragraph(lines: list[str]) -> str:
    return f"<p>{'<br>'.join(_render_inline(line) for line in lines)}</p>"


def render_consent_markdown(value: str | None) -> SafeString:
    normalized = str(value or "").replace("\r\n", "\n").strip()
    if not normalized:
        return mark_safe("")

    lines = normalized.split("\n")
    blocks: list[str] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        blocks.append(_paragraph(paragraph_lines))
        paragraph_lines.clear()

    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            flush_paragraph()
            continue

        heading_match = _HEADING_RE.match(trimmed)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            blocks.append(
                f"<h{level}>{_render_inline(heading_match.group(2))}</h{level}>"
            )
            continue

        if _HR_RE.match(trimmed):
            flush_paragraph()
            blocks.append("<hr>")
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    return mark_safe("".join(blocks))
