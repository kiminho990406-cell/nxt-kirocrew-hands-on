# -*- coding: utf-8 -*-
"""data-to-html: documents의 8개 문서를 요약하고 data의 3개 CSV를 집계해
HTML 한 파일로 정리한다. 표준 라이브러리만 사용, 한글 UTF-8 안전.

집계 규칙(문서 근거):
- 물품 기준 인원 = 확정 인원 (동아리운영규칙 CLUB-01 제1조)
- 재원별 현재 잔액 = 기초 + 수입 + 환불입금 - 지출 - 환불지급 (회계기준 ACCOUNT-01 제3조)
- 기초 잔액: 학교지원금 0, 동아리회비 800,000 (제1조)
- E04 순지출 = 지출 + 환불지급 - 환불입금 (수입 제외, 제3조)
- 구매계획 수량 = 참가자기준: 확정인원*계수 / 고정: 계수. 예정비용 = 단가*수량 (제5조)
  구매계획은 이미 처리된 회계와 합산하지 않는다 (제4조)
- 승인 정원 160명 (장소승인서 APPROVAL-SPACE-04), 홍보 180명과 충돌
"""
import csv
import html
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve()
# 이 스크립트는 documents/output/ 안에 두고 실행. week04 루트 = 3단계 상위
WEEK = BASE.parent.parent.parent
DOCDIR = WEEK / "documents"
DATADIR = WEEK / "data"
SUBDIR = WEEK / "submissions"
SUBDIR.mkdir(exist_ok=True)

BASELINE = {"학교지원금": 0, "동아리회비": 800000}


def esc(x):
    return html.escape(str(x))


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ---------- 문서 핵심 요약 (문서에서 확인한 내용) ----------
doc_summary = [
    ("W04_01_학교지원금지침.md", "RULE-01",
     "승인 한도 내 집행. 식음료 1인 4,000원 이내·실참석 대조. 기념품·개인선물·주류 제외. 미입금 승인액은 현금에 더하지 않음."),
    ("W04_02_학교공간이용안내.md", "RULE-02",
     "참가 정원은 장소 승인서를 따른다(운영요원 제외). 변경 승인서 없이는 홍보·회의만으로 정원 변경 불가."),
    ("W04_03_동아리운영규칙.md", "CLUB-01",
     "신청상태 확정/대기/취소. 물품 기본 인원 = 확정 인원. 회비 기념품 1인 3,000원 이내. 미전환 대기자는 확정에 미리 더하지 않음."),
    ("W04_04_행사안내.md", "NOTICE-04",
     "E04 빛담 가을사진전, 2026-09-28 학생회관 전시실. 홍보 모집 정원 180명(홍보용, 승인서 아님). 검토 기준일 2026-09-22."),
    ("W04_05_지원금승인서.md", "APPROVAL-FUND-04",
     "총 승인 한도 1,500,000원. 1차 지급 1,000,000원(거래 T091로 확인). 잔여 500,000원은 정산 후 지급 예정, 현재 가용현금 아님."),
    ("W04_06_장소사용승인서.md", "APPROVAL-SPACE-04",
     "승인 참가 정원 160명(운영요원 별도). 홍보 180명과 다르므로 정정 검토 필요. 유효 변경 승인 전까지 정원 160명."),
    ("W04_07_운영회의메모.md", "MEMO-04",
     "홍보 180 vs 승인 160. 180명으로 변경 요청 예정이나 승인 기록 없음. 기념품 회비 처리 논의. 용도 불명 인화비 재확인."),
    ("W04_08_회계기준.md", "ACCOUNT-01",
     "거래 120건(2026-07-01~09-22). 기초: 학교지원금 0·동아리회비 800,000. 잔액=기초+수입+환불입금-지출-환불지급. E04 순지출은 수입 제외."),
]

# ---------- 참가신청 집계 ----------
apply = read_csv(DATADIR / "참가신청.csv")
status_count = {}
option_cols = [c for c in apply[0].keys() if c not in
               ("신청_ID", "행사_ID", "이름", "신청상태", "신청일")] if apply else []
option_count = {c: 0 for c in option_cols}
for r in apply:
    st = r.get("신청상태", "").strip()
    status_count[st] = status_count.get(st, 0) + 1
    for c in option_cols:
        if r.get(c, "").strip() == "신청":
            option_count[c] += 1
confirmed = status_count.get("확정", 0)

# ---------- 회계 집계 ----------
acct = read_csv(DATADIR / "회계내역.csv")
funds = {}   # 재원 -> {수입, 환불입금, 지출, 환불지급}
e04_out = {}  # 재원 -> E04 순지출
for r in acct:
    fund = r.get("재원", "").strip()
    typ = r.get("유형", "").strip()
    amt = int(r.get("금액", "0") or 0)
    ev = r.get("행사_ID", "").strip()
    f = funds.setdefault(fund, {"수입": 0, "환불입금": 0, "지출": 0, "환불지급": 0})
    if typ in f:
        f[typ] += amt
    else:
        # 유형 표기 변형 대비
        if "수입" in typ:
            f["수입"] += amt
        elif typ == "지출":
            f["지출"] += amt
        elif "환불" in typ and "입금" in typ:
            f["환불입금"] += amt
        elif "환불" in typ and "지급" in typ:
            f["환불지급"] += amt
        else:
            f["지출"] += amt
    if ev == "E04":
        o = e04_out.setdefault(fund, {"지출": 0, "환불지급": 0, "환불입금": 0})
        if typ == "지출":
            o["지출"] += amt
        elif "환불" in typ and "지급" in typ:
            o["환불지급"] += amt
        elif "환불" in typ and "입금" in typ:
            o["환불입금"] += amt

# ---------- 구매계획 집계 ----------
plan = read_csv(DATADIR / "구매계획.csv")
plan_rows = []
plan_by_fund = {}
for r in plan:
    basis = r.get("수량기준", "").strip()
    coef = int(r.get("계수", "0") or 0)
    unit = int(r.get("단가", "0") or 0)
    fund = r.get("예정재원", "").strip()
    qty = confirmed * coef if basis == "참가자" else coef
    cost = unit * qty
    plan_rows.append((r.get("항목_ID", ""), r.get("물품", ""), basis, coef, unit, qty, cost, fund))
    plan_by_fund[fund] = plan_by_fund.get(fund, 0) + cost


# ---------- HTML 조립 ----------
def won(n):
    return f"{n:,}원"


rows_docs = "\n".join(
    f"<tr><td>{esc(t)}</td><td><code>{esc(did)}</code></td><td>{esc(s)}</td></tr>"
    for (name, did, s) in doc_summary
    for t in [name.replace('.md', '')]
)

rows_status = "\n".join(
    f"<tr><td>{esc(k)}</td><td class='num'>{v}명</td></tr>"
    for k, v in sorted(status_count.items(), key=lambda x: -x[1])
)
rows_option = "\n".join(
    f"<tr><td>{esc(c)} 신청</td><td class='num'>{v}명</td></tr>"
    for c, v in option_count.items()
)

rows_fund = ""
for fund, f in funds.items():
    base = BASELINE.get(fund, 0)
    bal = base + f["수입"] + f["환불입금"] - f["지출"] - f["환불지급"]
    rows_fund += (f"<tr><td>{esc(fund)}</td><td class='num'>{won(base)}</td>"
                  f"<td class='num'>{won(f['수입'])}</td><td class='num'>{won(f['환불입금'])}</td>"
                  f"<td class='num'>{won(f['지출'])}</td><td class='num'>{won(f['환불지급'])}</td>"
                  f"<td class='num'><strong>{won(bal)}</strong></td></tr>\n")

rows_e04 = ""
for fund, o in e04_out.items():
    net = o["지출"] + o["환불지급"] - o["환불입금"]
    rows_e04 += (f"<tr><td>{esc(fund)}</td><td class='num'>{won(o['지출'])}</td>"
                 f"<td class='num'>{won(o['환불지급'])}</td><td class='num'>{won(o['환불입금'])}</td>"
                 f"<td class='num'><strong>{won(net)}</strong></td></tr>\n")

rows_plan = "\n".join(
    f"<tr><td><code>{esc(pid)}</code></td><td>{esc(item)}</td><td>{esc(basis)}</td>"
    f"<td class='num'>{coef}</td><td class='num'>{won(unit)}</td><td class='num'>{qty}</td>"
    f"<td class='num'>{won(cost)}</td><td>{esc(fund)}</td></tr>"
    for (pid, item, basis, coef, unit, qty, cost, fund) in plan_rows
)
rows_plan_fund = "\n".join(
    f"<tr><td>{esc(fund)}</td><td class='num'><strong>{won(c)}</strong></td></tr>"
    for fund, c in plan_by_fund.items()
)

# 확인 필요 / 충돌
noproof = [r for r in acct if r.get("증빙", "").strip() in ("없음", "") or "인화비" in r.get("항목", "")]
issues = [
    "정원 충돌: 홍보 안내 <strong>180명</strong>(NOTICE-04) vs 장소 승인 <strong>160명</strong>(APPROVAL-SPACE-04). "
    "유효한 변경 승인서 없음(MEMO-04) → 현재 적용 정원은 <strong>160명</strong>.",
    "지원금 잔여 <strong>500,000원</strong>은 정산 후 지급 예정이라 현재 가용 현금이 아님(APPROVAL-FUND-04).",
    "구매계획(구매계획.csv)은 <strong>예정 비용</strong>이며 이미 처리된 회계와 합산하지 않음(ACCOUNT-01 제4조).",
]
if noproof:
    issues.append(f"증빙 없음/용도 불명(인화비 포함) 의심 거래 <strong>{len(noproof)}건</strong> → 영수증·사용 목적 재확인 필요.")
rows_issue = "\n".join(f"<li>{s}</li>" for s in issues)

now = datetime.now().strftime("%Y-%m-%d %H:%M")
files_used = ("문서 8개(W04_01~08), CSV 3개(참가신청·회계내역·구매계획)")

page = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>빛담 E04 운영 요약·집계 보고서</title>
<style>
 body {{font-family:-apple-system,"Segoe UI","Malgun Gothic",sans-serif;max-width:900px;
  margin:0 auto;padding:40px 20px 80px;line-height:1.65;color:#1f2328;background:#fafbfc;}}
 h1 {{font-size:1.6rem;color:#24475f;margin:0 0 .2em;}}
 .meta {{color:#656d76;font-size:.85rem;margin-bottom:1.8em;}}
 h2 {{font-size:1.15rem;color:#24475f;border-bottom:2px solid #eaecef;padding-bottom:.3em;margin-top:2em;}}
 table {{border-collapse:collapse;width:100%;margin:.8em 0;background:#fff;font-size:.9rem;}}
 th,td {{border:1px solid #e1e4e8;padding:8px 10px;text-align:left;vertical-align:top;}}
 th {{background:#24475f;color:#fff;font-weight:600;}}
 tbody tr:nth-child(even) {{background:#f6f8fa;}}
 td.num {{text-align:right;white-space:nowrap;}}
 code {{background:#eef1f4;padding:1px 5px;border-radius:4px;font-size:.85em;}}
 .box {{background:#fff;border:1px solid #e1e4e8;border-radius:8px;padding:2px 18px;}}
 ul.issue li {{margin:.5em 0;}}
 footer {{margin-top:2.5em;color:#8b949e;font-size:.8rem;text-align:center;}}
 .note {{color:#8b949e;font-size:.8rem;margin:.3em 0 0;}}
</style></head><body>

<h1>빛담 가을사진전(E04) 운영 요약·집계 보고서</h1>
<div class="meta">생성 {now} · 사용 파일: {files_used}</div>

<h2>1. 문서 핵심 요약 <span class="note">(documents/ 8개)</span></h2>
<table><thead><tr><th>문서</th><th>문서ID</th><th>핵심 내용</th></tr></thead>
<tbody>{rows_docs}</tbody></table>

<h2>2. 참가신청 집계 <span class="note">(참가신청.csv, 전체 {len(apply)}건)</span></h2>
<table><thead><tr><th>신청 상태</th><th>인원</th></tr></thead><tbody>{rows_status}</tbody></table>
<p class="note">물품 준비 기준 인원 = 확정 인원 <strong>{confirmed}명</strong> (CLUB-01 제1조)</p>
<table><thead><tr><th>옵션</th><th>신청 수</th></tr></thead><tbody>{rows_option}</tbody></table>

<h2>3. 회계 집계 <span class="note">(회계내역.csv, 전체 {len(acct)}건)</span></h2>
<p class="note">재원별 현재 잔액 = 기초 + 수입 + 환불입금 − 지출 − 환불지급 (ACCOUNT-01 제3조)</p>
<table><thead><tr><th>재원</th><th>기초</th><th>수입</th><th>환불입금</th><th>지출</th><th>환불지급</th><th>현재 잔액</th></tr></thead>
<tbody>{rows_fund}</tbody></table>
<p class="note">E04 재원별 순지출 = 지출 + 환불지급 − 환불입금 (수입 제외)</p>
<table><thead><tr><th>재원</th><th>지출</th><th>환불지급</th><th>환불입금</th><th>E04 순지출</th></tr></thead>
<tbody>{rows_e04}</tbody></table>

<h2>4. 구매계획 집계 <span class="note">(구매계획.csv, 확정 {confirmed}명 기준)</span></h2>
<p class="note">수량 = 참가자기준이면 확정인원×계수, 고정이면 계수. 예정비용 = 단가×수량. (예정 비용이며 회계와 합산 안 함)</p>
<table><thead><tr><th>ID</th><th>물품</th><th>수량기준</th><th>계수</th><th>단가</th><th>수량</th><th>예정 비용</th><th>예정 재원</th></tr></thead>
<tbody>{rows_plan}</tbody></table>
<table><thead><tr><th>예정 재원</th><th>예정 비용 합계</th></tr></thead><tbody>{rows_plan_fund}</tbody></table>

<h2>5. 확인 필요 · 문서 충돌</h2>
<div class="box"><ul class="issue">{rows_issue}</ul></div>

<footer>data-to-html 스킬 산출 · 원본 파일 보존</footer>
</body></html>
"""

out = SUBDIR / "E04_운영요약_집계.html"
out.write_text(page, encoding="utf-8")
print(f"DONE -> {out}")
print(f"확정 인원={confirmed}, 재원={list(funds)}, 구매계획 항목={len(plan_rows)}")
