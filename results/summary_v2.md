# Eval results: set v2 (2026-11-16)

**Overall accuracy: 19/20 = 95%**

| Category | Passed | Accuracy |
|---|---|---|
| relative_time | 9/9 | 100% |
| ambiguous_def | 6/7 | 86% |
| unanswerable | 4/4 | 100% |

Questions where the agent hit a SQL error and recovered: 1
Average queries per question: 1.9
Average seconds per question: 5.6

## Failures

| ID | Tag | Gold | Predicted | Question |
|---|---|---|---|---|
| h12 | wrong_value | weekdays | 2.34 | Is BTC more volatile on weekends or weekdays? Use 2025. |

Full logs (every SQL query and answer): `results/eval_20261116_1657.jsonl`
