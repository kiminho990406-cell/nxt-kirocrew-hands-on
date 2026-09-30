"""창고 재고 마크다운 표 파서 (표준 라이브러리만 사용).

각 창고 파일은 다음과 같은 파이프 표 형식을 가진다:

    # 창고 A 재고

    | 품목 | 수량 |
    |---|---:|
    | mug | 12 |
    | bottle | 3 |

parse_warehouse(md_path)를 호출하면 창고 이름, 품목별 수량, 총합,
저재고 목록(수량 < 5)을 담은 dict를 돌려준다.
"""

import os

# 저재고 판정 기준: 이 값 미만이면 저재고
THRESHOLD = 5


def _warehouse_name(md_path):
    """파일명에서 창고 이름을 뽑는다. 예: 'warehouse-a.md' -> 'A'."""
    base = os.path.basename(md_path)
    stem = os.path.splitext(base)[0]        # warehouse-a
    if "-" in stem:
        return stem.rsplit("-", 1)[-1].upper()   # A
    return stem.upper()


def _is_separator_row(cells):
    """|---|---:| 같은 구분선 행인지 판별."""
    for c in cells:
        stripped = c.replace(":", "").replace("-", "").strip()
        if stripped != "":
            return False
    return bool(cells)


def parse_warehouse(md_path):
    """마크다운 창고 파일을 파싱해 집계 dict를 반환한다.

    반환 키:
        'warehouse' : str  창고 이름 (예: 'A')
        'items'     : dict 품목명 -> 수량(int)
        'total'     : int  수량 합계
        'low_stock' : list {'item','quantity','warehouse'} (수량 < THRESHOLD)
    """
    warehouse = _warehouse_name(md_path)
    items = {}
    low_stock = []

    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue  # 표 행이 아님 (제목/빈 줄 등)

            # 파이프로 나눈 뒤 양끝의 빈 셀 제거
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2:
                continue

            # 구분선 행(|---|---:|) 건너뛰기
            if _is_separator_row(cells):
                continue

            item, qty_raw = cells[0], cells[1]

            # 헤더 행(수량 열이 정수가 아님) 건너뛰기
            try:
                quantity = int(qty_raw)
            except ValueError:
                continue

            items[item] = quantity
            if quantity < THRESHOLD:
                low_stock.append({
                    "item": item,
                    "quantity": quantity,
                    "warehouse": warehouse,
                })

    total = sum(items.values())

    return {
        "warehouse": warehouse,
        "items": items,
        "total": total,
        "low_stock": low_stock,
    }


if __name__ == "__main__":
    # 간단한 자체 확인: 인자로 준 파일을 파싱해 출력
    import json
    import sys

    if len(sys.argv) > 1:
        print(json.dumps(parse_warehouse(sys.argv[1]),
                         ensure_ascii=False, indent=2))
