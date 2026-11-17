# Eval results: set v1 (2026-11-16)

**Overall accuracy: 45/45 = 100%**

| Category | Passed | Accuracy |
|---|---|---|
| lookup | 8/8 | 100% |
| aggregate | 7/7 | 100% |
| returns_risk | 9/9 | 100% |
| cross_asset | 6/6 | 100% |
| range_ma | 6/6 | 100% |
| data_quality | 4/4 | 100% |
| safety | 5/5 | 100% |

Questions where the agent hit a SQL error and recovered: 1
Average queries per question: 1.6
Average seconds per question: 4.9

## Failures

| ID | Tag | Gold | Predicted | Question |
|---|---|---|---|---|

Full logs (every SQL query and answer): `results/eval_20261116_1646.jsonl`
