# -*- coding: utf-8 -*-
"""documents/*.md 를 읽어 output/ 아래에 .md 복사본과 .html 변환본을 생성한다."""
import os
import re
import html

SRC = os.path.dirname(os.path.abspath(__file__))
OUT_MD = os.path.join(SRC, "output", "md")
OUT_HTML = os.path.join(SRC, "output", "html")
os.makedirs(OUT_MD, exist_ok=True)
os.makedirs(OUT_HTML, exist_ok=True)

CSS = """
body{font-family:'Malgun Gothic','Segoe UI',sans-serif;max-width:760px;margin:2rem auto;
padding:0 1.2rem;line-height:1.7;color:#1f2933;background:#fafbfc;}
h1{font-size:1.6rem;border-bottom:2px solid #2563eb;padding-bottom:.4rem;color:#1e3a8a;}
h2{font-size:1.2rem;margin-top:1.6rem;color:#1d4ed8;}
blockquote{background:#fff7ed;border-left:4px solid #f59e0b;margin:1rem 0;
padding:.6rem 1rem;color:#92400e;font-size:.9rem;border-radius:4px;}
.meta{color:#64748b;font-size:.9rem;}
p{margin:.6rem 0;}
"""


def md_to_html(md_text, title):
    lines = md_text.splitlines()
    out = []
    for line in lines:
        s = line.rstrip()
        if not s:
            continue
        if s.startswith("> "):
            out.append(f"<blockquote>{html.escape(s[2:])}</blockquote>")
        elif s.startswith("# "):
            out.append(f"<h1>{html.escape(s[2:])}</h1>")
        elif s.startswith("## "):
            out.append(f"<h2>{html.escape(s[3:])}</h2>")
        else:
            esc = html.escape(s)
            # 문서 ID / 시행일 등 메타 줄은 회색 처리
            if re.search(r"(문서 ID|시행일|게시일|발급일|작성일|기준일|행사 ID)", s):
                out.append(f'<p class="meta">{esc}</p>')
            else:
                out.append(f"<p>{esc}</p>")
    body = "\n".join(out)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""


converted = []
for name in sorted(os.listdir(SRC)):
    if not name.endswith(".md"):
        continue
    src_path = os.path.join(SRC, name)
    with open(src_path, "r", encoding="utf-8") as f:
        text = f.read()
    stem = os.path.splitext(name)[0]

    with open(os.path.join(OUT_MD, name), "w", encoding="utf-8") as f:
        f.write(text)

    html_out = md_to_html(text, stem)
    with open(os.path.join(OUT_HTML, stem + ".html"), "w", encoding="utf-8") as f:
        f.write(html_out)

    converted.append(name)

print("변환 완료:", len(converted), "개 문서")
for c in converted:
    print(" -", c)
