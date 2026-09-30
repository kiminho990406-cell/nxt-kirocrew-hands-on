# -*- coding: utf-8 -*-
"""documents 폴더의 W04_*.md 8개 문서를 목차 + 본문으로 엮은 통합 HTML 하나를 만든다.
표준 라이브러리만 사용. 한글 UTF-8 안전 처리."""
import html
import re
from datetime import datetime
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent   # documents/
OUT = Path(__file__).resolve().parent            # documents/output/


def inline(t: str) -> str:
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t


def md_to_html_body(md: str) -> str:
    out, in_p, buf = [], [], []

    def flush_p():
        if in_p:
            text = " ".join(in_p).strip()
            if text:
                out.append(f"<p>{inline(text)}</p>")
            in_p.clear()

    for ln in md.splitlines():
        s = ln.rstrip()
        if not s.strip():
            flush_p()
            continue
        if s.startswith("> "):
            flush_p(); out.append(f'<blockquote>{inline(s[2:].strip())}</blockquote>')
        elif s.startswith("### "):
            flush_p(); out.append(f"<h3>{inline(s[4:].strip())}</h3>")
        elif s.startswith("## "):
            flush_p(); out.append(f"<h2>{inline(s[3:].strip())}</h2>")
        elif s.startswith("# "):
            flush_p()  # 문서 제목은 카드 헤더로 따로 뽑으므로 본문에선 h2로
            out.append(f"<h2 class='doc-title'>{inline(s[2:].strip())}</h2>")
        elif re.match(r"^[-*] ", s):
            flush_p(); out.append(f"<li>{inline(s[2:].strip())}</li>")
        else:
            in_p.append(s.strip())
    flush_p()

    result = []
    for el in out:
        if el.startswith("<li>"):
            buf.append(el)
        else:
            if buf:
                result.append("<ul>" + "".join(buf) + "</ul>"); buf = []
            result.append(el)
    if buf:
        result.append("<ul>" + "".join(buf) + "</ul>")
    return "\n".join(result)


docs = []
for md_path in sorted(DOCS.glob("W04_*.md")):
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"^# (.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else md_path.stem
    docs.append((md_path.name, title, md_to_html_body(text)))

toc = "\n".join(
    f'<li><a href="#doc{i}">{html.escape(title)}</a> '
    f'<span class="fn">{html.escape(name)}</span></li>'
    for i, (name, title, _) in enumerate(docs)
)

sections = "\n".join(
    f'<section id="doc{i}" class="doc">\n'
    f'<div class="src">출처: {html.escape(name)}</div>\n{body}\n</section>'
    for i, (name, title, body) in enumerate(docs)
)

now = datetime.now().strftime("%Y-%m-%d %H:%M")
page = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>빛담 가을사진전(E04) 통합 문서</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
          max-width: 820px; margin: 0 auto; padding: 40px 20px 80px; line-height: 1.7;
          color: #1f2328; background: #fafbfc; }}
  header.top {{ border-bottom: 3px solid #24475f; padding-bottom: 1em; margin-bottom: 1.5em; }}
  header.top h1 {{ font-size: 1.7rem; margin: 0 0 .2em; color: #24475f; }}
  header.top .meta {{ color: #656d76; font-size: .85rem; }}
  nav.toc {{ background: #fff; border: 1px solid #e1e4e8; border-radius: 10px;
             padding: 18px 22px; margin-bottom: 2.5em; }}
  nav.toc h2 {{ font-size: 1rem; margin: 0 0 .6em; color: #24475f; }}
  nav.toc ol {{ margin: 0; padding-left: 1.4em; }}
  nav.toc li {{ margin: .35em 0; }}
  nav.toc a {{ color: #0969da; text-decoration: none; }}
  nav.toc a:hover {{ text-decoration: underline; }}
  nav.toc .fn {{ color: #8b949e; font-size: .78rem; }}
  section.doc {{ background: #fff; border: 1px solid #e1e4e8; border-radius: 10px;
                 padding: 8px 28px 24px; margin-bottom: 1.6em; scroll-margin-top: 20px; }}
  section.doc .src {{ color: #8b949e; font-size: .78rem; text-align: right; margin-top: 8px; }}
  h2.doc-title {{ font-size: 1.3rem; color: #24475f; border-bottom: 2px solid #eaecef;
                  padding-bottom: .3em; margin-top: .4em; }}
  h2 {{ font-size: 1.1rem; margin-top: 1.4em; color: #24475f; }}
  h3 {{ font-size: 1rem; color: #444; }}
  blockquote {{ border-left: 4px solid #d0d7de; margin: 0 0 1em; padding: .4em 1em;
                color: #656d76; background: #f6f8fa; font-size: .85rem; }}
  ul {{ padding-left: 1.4em; }}
  p {{ margin: .55em 0; }}
  footer {{ margin-top: 2em; color: #8b949e; font-size: .8rem; text-align: center; }}
</style>
</head>
<body>
<header class="top">
  <h1>빛담 가을사진전(E04) 통합 문서</h1>
  <div class="meta">documents 폴더의 8개 문서 통합 · 생성 {now}</div>
</header>

<nav class="toc">
  <h2>목차</h2>
  <ol>
{toc}
  </ol>
</nav>

{sections}

<footer>자동 통합 (documents/output) · 원본 8개 문서 보존</footer>
</body>
</html>
"""

out_file = OUT / "통합문서.html"
out_file.write_text(page, encoding="utf-8")
print(f"DONE: {len(docs)} documents merged -> {out_file}")
