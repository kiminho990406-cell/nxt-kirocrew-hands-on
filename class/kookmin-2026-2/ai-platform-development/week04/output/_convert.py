# -*- coding: utf-8 -*-
"""documents 폴더의 W04_*.md 문서를 각각 output/ 아래 .md 복사본과 .html로 변환한다.
표준 라이브러리만 사용. 한글 UTF-8 안전 처리."""
import html
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent   # documents/
OUT = Path(__file__).resolve().parent            # documents/output/


def md_to_html_body(md: str) -> str:
    lines = md.splitlines()
    out = []
    in_p = []

    def flush_p():
        if in_p:
            text = " ".join(in_p).strip()
            if text:
                out.append(f"<p>{inline(text)}</p>")
            in_p.clear()

    def inline(t: str) -> str:
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        return t

    for ln in lines:
        s = ln.rstrip()
        if not s.strip():
            flush_p()
            continue
        if s.startswith("> "):
            flush_p()
            out.append(f'<blockquote>{inline(s[2:].strip())}</blockquote>')
        elif s.startswith("### "):
            flush_p()
            out.append(f"<h3>{inline(s[4:].strip())}</h3>")
        elif s.startswith("## "):
            flush_p()
            out.append(f"<h2>{inline(s[3:].strip())}</h2>")
        elif s.startswith("# "):
            flush_p()
            out.append(f"<h1>{inline(s[2:].strip())}</h1>")
        elif re.match(r"^[-*] ", s):
            flush_p()
            out.append(f"<li>{inline(s[2:].strip())}</li>")
        else:
            in_p.append(s.strip())
    flush_p()

    # wrap consecutive <li> into <ul>
    result = []
    buf = []
    for el in out:
        if el.startswith("<li>"):
            buf.append(el)
        else:
            if buf:
                result.append("<ul>" + "".join(buf) + "</ul>")
                buf = []
            result.append(el)
    if buf:
        result.append("<ul>" + "".join(buf) + "</ul>")
    return "\n".join(result)


HTML_TMPL = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
          max-width: 760px; margin: 40px auto; padding: 0 20px; line-height: 1.7;
          color: #1f2328; background: #fff; }}
  h1 {{ font-size: 1.6rem; border-bottom: 2px solid #eaecef; padding-bottom: .3em; }}
  h2 {{ font-size: 1.2rem; margin-top: 1.6em; color: #24475f; }}
  h3 {{ font-size: 1.05rem; color: #444; }}
  blockquote {{ border-left: 4px solid #d0d7de; margin: 0 0 1em; padding: .4em 1em;
                color: #656d76; background: #f6f8fa; font-size: .9rem; }}
  ul {{ padding-left: 1.4em; }}
  p {{ margin: .6em 0; }}
  footer {{ margin-top: 3em; padding-top: 1em; border-top: 1px solid #eaecef;
            color: #8b949e; font-size: .8rem; }}
</style>
</head>
<body>
{body}
<footer>원본: {src} · 자동 변환 (documents/output)</footer>
</body>
</html>
"""

count = 0
for md_path in sorted(DOCS.glob("W04_*.md")):
    text = md_path.read_text(encoding="utf-8")
    # title = first '# ' heading or filename
    m = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else md_path.stem

    # .md copy
    (OUT / md_path.name).write_text(text, encoding="utf-8")
    # .html
    body = md_to_html_body(text)
    html_doc = HTML_TMPL.format(title=html.escape(title), body=body, src=md_path.name)
    (OUT / (md_path.stem + ".html")).write_text(html_doc, encoding="utf-8")
    count += 1
    print(f"OK  {md_path.name} -> {md_path.stem}.html + {md_path.name}")

print(f"\nDONE: {count} documents -> {count*2} files in {OUT}")
