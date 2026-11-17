# Eval results: set v2 (2026-11-16)

**Overall accuracy: 19/20 = 95%**

| Category | Passed | Accuracy |
|---|---|---|
| relative_time | 8/9 | 89% |
| ambiguous_def | 7/7 | 100% |
| unanswerable | 4/4 | 100% |

Questions where the agent hit a SQL error and recovered: 0
Average queries per question: 1.9
Average seconds per question: 5.6

## Failures

| ID | Tag | Gold | Predicted | Question |
|---|---|---|---|---|
| h03 | wrong_value | 40.75632987347212 | 2.13 | How volatile was BTC last summer? |

Full logs (every SQL query and answer): `results/eval_20261116_1655.jsonl`
