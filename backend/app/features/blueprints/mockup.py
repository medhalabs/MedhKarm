"""Anaya's screen mockups are HTML written by a model, shown to the founder in a sandboxed frame
(no scripts, no network) and put in the project's docs/. Before either, they are made inert:
scripts, frames, forms, event handlers, links and anything that loads from outside are removed.
The sandboxed frame is the real wall; this is the second one."""

import html
import re

# Removed with everything inside them
ACTIVE = "script|iframe|object|embed|audio|video"
# Only the tag goes (a form's fields and buttons stay: they draw a screen and do nothing here)
INERT = ACTIVE + "|form|base|link|meta"
TAG_PAIR = re.compile(rf"<\s*({ACTIVE})\b[^>]*>.*?<\s*/\s*\1\s*>", re.I | re.S)
TAG_SINGLE = re.compile(rf"<\s*/?\s*({INERT})\b[^>]*>", re.I)
HANDLER = re.compile(r"\s+on[a-z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
URL_ATTR = re.compile(
    r"\s+(src|href|action|formaction|xlink:href|srcset|poster)\s*="
    r"\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)",
    re.I,
)
CSS_URL = re.compile(r"url\s*\([^)]*\)", re.I)
CSS_IMPORT = re.compile(r"@import[^;]*;?", re.I)
JS_SCHEME = re.compile(r"(java|vb)script\s*:", re.I)
FENCE = re.compile(r"^```(?:html)?\s*|\s*```\s*$", re.I)
HAS_MARKUP = re.compile(r"<\s*(div|section|main|body|article|h1|h2|p|ul|button)\b", re.I)
SKELETON = (
    '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "<title>Screen mockups</title></head><body>\n{body}\n</body></html>"
)


def sanitize_mockup(text: str) -> str:
    """The model's HTML, made inert, as a complete page. Text with no markup becomes a page
    that says so, never an empty frame."""
    text = FENCE.sub("", text.strip())
    if not HAS_MARKUP.search(text):
        shown = html.escape(text[:400])
        return SKELETON.format(
            body=f"<p>The mockups couldn't be drawn this time.</p><pre>{shown}</pre>"
        )
    text = TAG_PAIR.sub("", text)
    text = TAG_SINGLE.sub("", text)
    text = HANDLER.sub("", text)
    text = URL_ATTR.sub("", text)
    text = JS_SCHEME.sub("", text)
    text = CSS_IMPORT.sub("", text)
    text = CSS_URL.sub("none", text)
    if not re.search(r"<\s*html\b", text, re.I):
        text = SKELETON.format(body=text)
    if not re.match(r"\s*<!doctype", text, re.I):
        text = "<!doctype html>\n" + text
    return text
