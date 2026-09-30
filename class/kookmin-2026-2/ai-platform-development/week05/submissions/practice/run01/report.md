# 창고 재고 점검 보고서 (1차)

입력 파일: warehouse-a.md, warehouse-b.md, warehouse-c.md

## 창고별 합계

| 창고 | 합계 |
| --- | ---: |
| A | 22 |
| B | 16 |
| C | 16 |
| 전체 | 54 |

## 품목별 합계 (전체 창고)

| 품목 | 합계 |
| --- | ---: |
| bottle | 12 |
| cable | 1 |
| hub | 13 |
| mug | 17 |
| sensor | 11 |

## 저재고 목록

적용 기준: warehouse_row (수량 < 5)

| 품목 | 수량 | 창고 |
| --- | ---: | --- |
| bottle | 3 | A |
| hub | 2 | B |
| sensor | 4 | C |
| cable | 1 | C |
