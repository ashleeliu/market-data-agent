# Eval results: set v2 (2026-11-16)

**Overall accuracy: 17/20 = 85%**

| Category | Passed | Accuracy |
|---|---|---|
| relative_time | 6/9 | 67% |
| ambiguous_def | 7/7 | 100% |
| unanswerable | 4/4 | 100% |

Questions where the agent hit a SQL error and recovered: 1
Average queries per question: 2.4
Average seconds per question: 8.1

## Failures

| ID | Tag | Gold | Predicted | Question |
|---|---|---|---|---|
| h01 | wrong_value | -38.165185854309634 | -38.87 | How much is ETH up this year? |
| h02 | wrong_value | 65315.35 | 64750.37 | What was BTC's most recent daily close? |
| h04 | wrong_value | 437298486.2660357 | 5345.44 | What was BTC's average daily volume last month? |

Full logs (every SQL query and answer): `results/eval_20261116_1637.jsonl`
