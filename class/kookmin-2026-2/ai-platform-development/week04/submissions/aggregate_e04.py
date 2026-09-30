# -*- coding: utf-8 -*-
"""
빛담 가을사진전(E04) 데이터 집계 스크립트
표준 라이브러리(csv, json)만 사용. 원본 CSV는 읽기만 하고 수정하지 않는다.

근거 문서/조항:
- ACCOUNT-01 제1조: 기간 2026-07-01~2026-09-22, 처리완료 120건.
  기초 잔액 = 학교지원금 0원, 동아리회비 800,000원. E01~E04 혼재.
- ACCOUNT-01 제2조: 수입·환불입금(+), 지출·환불지급(-). 금액은 양의 정수 원.
- ACCOUNT-01 제3조: 재원별 현재잔액 = 기초 + 수입 + 환불입금 - 지출 - 환불지급.
  E04 순지출 = 지출 + 환불지급 - 환불입금 (수입 제외).
- ACCOUNT-01 제5조: 구매계획 수량 - '참가자'=확정인원×계수, '고정'=계수. 예정비용=단가×수량.
- CLUB-01 제1조: 신청상태 확정·대기·취소. 물품 기본 인원은 확정 인원.
"""
import csv
import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")

OPENING = {"학교지원금": 0, "동아리회비": 800_000}  # ACCOUNT-01 제1조


def read_csv(path):
    # BOM 안전 처리
    with io.open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    apply_rows = read_csv(os.path.join(DATA, "참가신청.csv"))
    acct_rows = read_csv(os.path.join(DATA, "회계내역.csv"))
    plan_rows = read_csv(os.path.join(DATA, "구매계획.csv"))

    result = {
        "읽은_행수": {
            "참가신청": len(apply_rows),
            "회계내역": len(acct_rows),
            "구매계획": len(plan_rows),
        },
        "근거": {
            "기초잔액": "ACCOUNT-01 제1조",
            "환불부호": "ACCOUNT-01 제2조",
            "현재잔액식": "ACCOUNT-01 제3조",
            "E04순지출식": "ACCOUNT-01 제3조",
            "구매수량식": "ACCOUNT-01 제5조",
            "확정인원기준": "CLUB-01 제1조",
        },
    }

    # ---- 1) 참가 상태별 인원 (E04만) ----
    e04_apps = [r for r in apply_rows if r["행사_ID"] == "E04"]
    status_count = {}
    for r in e04_apps:
        s = r["신청상태"]
        status_count[s] = status_count.get(s, 0) + 1
    result["참가상태별_인원_E04"] = status_count
    result["E04_신청_총건수"] = len(e04_apps)

    확정 = [r for r in e04_apps if r["신청상태"] == "확정"]
    confirmed_n = len(확정)
    result["확정인원"] = confirmed_n

    # ---- 2) 확정자의 선택 (인화체험/식음료 값별 분포) ----
    def dist(rows, field):
        d = {}
        for r in rows:
            v = (r.get(field) or "").strip()
            d[v] = d.get(v, 0) + 1
        return d

    result["확정자_선택"] = {
        "인화체험": dist(확정, "인화체험"),
        "식음료": dist(확정, "식음료"),
    }

    # ---- 3) 회계: 재원별 현재 잔액 (전체 행사) ----
    def to_int(x):
        return int(str(x).strip())

    balances = {k: v for k, v in OPENING.items()}
    fund_flow = {}  # 재원별 유형 합계 (검증용)
    for r in acct_rows:
        fund = r["재원"]
        typ = r["유형"]
        amt = to_int(r["금액"])
        fund_flow.setdefault(fund, {})
        fund_flow[fund][typ] = fund_flow[fund].get(typ, 0) + amt
        if fund not in balances:
            balances[fund] = 0  # 기초 미정 재원은 0으로 시작 (확인 필요 표시)
        if typ in ("수입", "환불입금"):
            balances[fund] += amt
        elif typ in ("지출", "환불지급"):
            balances[fund] -= amt
        else:
            # 알 수 없는 유형은 집계하지 않고 표시
            result.setdefault("확인필요", []).append(
                f"알 수 없는 거래 유형: {typ} (거래_ID={r.get('거래_ID')})"
            )
    result["재원별_현재잔액"] = balances
    result["재원별_유형합계"] = fund_flow
    result["학교지원금_현재잔액"] = balances.get("학교지원금")
    result["동아리회비_현재잔액"] = balances.get("동아리회비")

    # ---- 4) E04 재원별 순지출 = 지출 + 환불지급 - 환불입금 (수입 제외) ----
    e04_acct = [r for r in acct_rows if r["행사_ID"] == "E04"]
    net_out = {}
    for r in e04_acct:
        fund = r["재원"]
        typ = r["유형"]
        amt = to_int(r["금액"])
        net_out.setdefault(fund, 0)
        if typ == "지출":
            net_out[fund] += amt
        elif typ == "환불지급":
            net_out[fund] += amt
        elif typ == "환불입금":
            net_out[fund] -= amt
        # 수입은 순지출 계산에서 제외
    result["E04_거래건수"] = len(e04_acct)
    result["E04_재원별_순지출"] = net_out
    result["E04_순지출_합계"] = sum(net_out.values())

    # ---- 5) 구매계획: 140/160/180명 시나리오 ----
    # ACCOUNT-01 제5조: 참가자=인원×계수, 고정=계수. 예정비용=단가×수량.
    def plan_for(headcount):
        by_fund = {}
        items = []
        for p in plan_rows:
            기준 = p["수량기준"]
            계수 = to_int(p["계수"])
            단가 = to_int(p["단가"])
            재원 = p["예정재원"]
            if 기준 == "참가자":
                수량 = headcount * 계수
            elif 기준 == "고정":
                수량 = 계수
            else:
                수량 = None
                result.setdefault("확인필요", []).append(
                    f"알 수 없는 수량기준: {기준} (항목_ID={p.get('항목_ID')})"
                )
            비용 = 단가 * 수량 if 수량 is not None else None
            by_fund.setdefault(재원, 0)
            if 비용 is not None:
                by_fund[재원] += 비용
            items.append({
                "항목_ID": p["항목_ID"], "물품": p["물품"], "수량기준": 기준,
                "수량": 수량, "단가": 단가, "예정비용": 비용, "예정재원": 재원,
            })
        return {"재원별_예정비용": by_fund, "총_예정비용": sum(by_fund.values()), "항목": items}

    result["구매계획_시나리오"] = {}
    for hc in (140, 160, 180):
        result["구매계획_시나리오"][str(hc)] = plan_for(hc)

    # 확정 인원 기준(CLUB-01 제1조) 시나리오도 함께
    result["구매계획_확정인원기준"] = {
        "확정인원": confirmed_n,
        **plan_for(confirmed_n),
    }

    # 정원 근거 메모
    result["정원_주의"] = (
        "NOTICE-04 홍보 정원 180명, MEMO-04 승인 정원 160명(180명 변경 미승인). "
        "140명은 시나리오 계산용. 확정 인원 기준 물품은 CLUB-01 제1조."
    )

    out_json = os.path.join(BASE, "e04_aggregate.json")
    with io.open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 콘솔 출력 요약
    print("읽은 행수:", result["읽은_행수"])
    print("참가상태별 인원(E04):", status_count)
    print("확정 인원:", confirmed_n)
    print("확정자 인화체험:", result["확정자_선택"]["인화체험"])
    print("확정자 식음료:", result["확정자_선택"]["식음료"])
    print("재원별 현재잔액:", balances)
    print("E04 재원별 순지출:", net_out, "합계:", result["E04_순지출_합계"])
    for hc in (140, 160, 180):
        s = result["구매계획_시나리오"][str(hc)]
        print(f"구매계획 {hc}명: 재원별={s['재원별_예정비용']} 총={s['총_예정비용']}")
    sc = result["구매계획_확정인원기준"]
    print(f"구매계획 확정({confirmed_n})명: 재원별={sc['재원별_예정비용']} 총={sc['총_예정비용']}")
    print("JSON 저장:", out_json)


if __name__ == "__main__":
    main()
