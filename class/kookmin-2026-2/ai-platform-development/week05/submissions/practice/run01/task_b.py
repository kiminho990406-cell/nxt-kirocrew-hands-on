"""창고 B 집계 태스크 (독립 DAG 노드).

practice/data/warehouse-b.md를 파싱해 창고 B의
총합·품목별 수량·저재고 목록을 warehouse-b.json으로 저장한다.
task_a, task_c에 대한 의존성이 없다 (병렬 실행 가능).
표준 라이브러리만 사용.
"""

import json
import os

from parse_warehouse import parse_warehouse

# 이 스크립트 파일이 있는 디렉터리 (run01)
HERE = os.path.dirname(os.path.abspath(__file__))

# run01 -> practice -> data/warehouse-b.md 경로 계산
# run01 = .../week05/submissions/practice/run01
WEEK05 = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
SOURCE = os.path.join(WEEK05, "practice", "data", "warehouse-b.md")

# 중간 산출물 저장 위치
OUTPUT = os.path.join(HERE, "warehouse-b.json")


def main():
    result = parse_warehouse(SOURCE)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("창고 %s 집계 완료: 총 %d, 품목 %d종, 저재고 %d건 -> %s" % (
        result["warehouse"],
        result["total"],
        len(result["items"]),
        len(result["low_stock"]),
        os.path.basename(OUTPUT),
    ))


if __name__ == "__main__":
    main()
