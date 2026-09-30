"""병합 단계 (DAG 수렴 노드).

task_a/task_b/task_c가 만든 세 중간 파일(warehouse-*.json)을 읽어
전체 결과를 consolidate한다:
  - source_files: 입력으로 쓴 세 .md 파일 이름
  - warehouse_totals: 창고별 정수 합계 {A, B, C}
  - item_totals: 전체 창고에 걸친 품목별 정수 합계
  - grand_total: 전체 수량
  - low_stock_basis: 'warehouse_row' (창고 행 기준)
  - threshold: 5 (수량이 이 값보다 작으면 저재고)
  - low_stock: 저재고 행 목록 {item, quantity, warehouse}

result.json(정수 저장)과 report.md(요약 보고서)를 만든다.
표준 라이브러리만 사용.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# 창고 라벨 -> 중간 파일 -> 원본 .md 파일 이름
WAREHOUSES = [
    ("A", "warehouse-a.json", "warehouse-a.md"),
    ("B", "warehouse-b.json", "warehouse-b.md"),
    ("C", "warehouse-c.json", "warehouse-c.md"),
]

THRESHOLD = 5
LOW_STOCK_BASIS = "warehouse_row"

RESULT_JSON = os.path.join(HERE, "result.json")
REPORT_MD = os.path.join(HERE, "report.md")


def load_intermediate():
    """세 중간 파일을 읽어 (라벨, 원본파일명, 데이터) 목록으로 반환."""
    loaded = []
    for label, json_name, md_name in WAREHOUSES:
        path = os.path.join(HERE, json_name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        loaded.append((label, md_name, data))
    return loaded


def merge(loaded):
    source_files = []
    warehouse_totals = {}
    item_totals = {}
    low_stock = []

    for label, md_name, data in loaded:
        source_files.append(md_name)
        warehouse_totals[label] = int(data["total"])

        # 품목별 전체 합계 누적
        for item, qty in data["items"].items():
            item_totals[item] = item_totals.get(item, 0) + int(qty)

        # 창고 행 기준 저재고는 각 태스크가 이미 계산한 목록을 그대로 결합
        for row in data["low_stock"]:
            low_stock.append({
                "item": row["item"],
                "quantity": int(row["quantity"]),
                "warehouse": row["warehouse"],
            })

    grand_total = sum(warehouse_totals.values())

    return {
        "source_files": source_files,
        "warehouse_totals": warehouse_totals,
        "item_totals": item_totals,
        "grand_total": grand_total,
        "low_stock_basis": LOW_STOCK_BASIS,
        "threshold": THRESHOLD,
        "low_stock": low_stock,
    }


def write_report(result):
    lines = []
    lines.append("# 창고 재고 점검 보고서 (1차)")
    lines.append("")
    lines.append("입력 파일: " + ", ".join(result["source_files"]))
    lines.append("")

    lines.append("## 창고별 합계")
    lines.append("")
    lines.append("| 창고 | 합계 |")
    lines.append("| --- | ---: |")
    for label in sorted(result["warehouse_totals"]):
        lines.append("| %s | %d |" % (label, result["warehouse_totals"][label]))
    lines.append("| 전체 | %d |" % result["grand_total"])
    lines.append("")

    lines.append("## 품목별 합계 (전체 창고)")
    lines.append("")
    lines.append("| 품목 | 합계 |")
    lines.append("| --- | ---: |")
    for item in sorted(result["item_totals"]):
        lines.append("| %s | %d |" % (item, result["item_totals"][item]))
    lines.append("")

    lines.append("## 저재고 목록")
    lines.append("")
    lines.append("적용 기준: %s (수량 < %d)" % (result["low_stock_basis"], result["threshold"]))
    lines.append("")
    if result["low_stock"]:
        lines.append("| 품목 | 수량 | 창고 |")
        lines.append("| --- | ---: | --- |")
        for row in result["low_stock"]:
            lines.append("| %s | %d | %s |" % (row["item"], row["quantity"], row["warehouse"]))
    else:
        lines.append("저재고 항목 없음.")
    lines.append("")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    loaded = load_intermediate()
    result = merge(loaded)

    with open(RESULT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    write_report(result)

    print("병합 완료: grand_total=%d, 품목 %d종, 저재고 %d건 -> %s, %s" % (
        result["grand_total"],
        len(result["item_totals"]),
        len(result["low_stock"]),
        os.path.basename(RESULT_JSON),
        os.path.basename(REPORT_MD),
    ))


if __name__ == "__main__":
    main()
