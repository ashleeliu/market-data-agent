# Market Data Analytics Agent

An LLM agent that answers plain-English questions about crypto market data using read-only SQL: it pulls daily candles from a free public API into AWS S3, loads them into DuckDB, and lets Claude write, run, check, and explain its own queries - with five layers of read-only guardrails and a 65-question evaluation that measures how accurate it actually is.

## What It Does

- Pulls 2 years of daily OHLCV candles for BTC, ETH, and SOL from the Coinbase Exchange API and stores them in S3 as Parquet
- Loads the data into DuckDB, adds USD volume, and flags today's unfinished candle (`is_complete`)
- Turns plain-English questions into SQL with Claude tool use: the model writes a query, the code runs it, and the model checks the rows, retries if something looks wrong, and explains the answer
- Enforces read-only access five ways - SQL check (single SELECT only), read-only connection, no outside file/URL/S3 access (locked), 10-second query timeout, and a 200-row result limit
- Scores the agent against 65 questions with known answers computed from hand-written SQL: lookups, aggregates, returns and risk (volatility, drawdown, Sharpe), cross-asset correlation, moving averages, data quality, relative dates, questions the data can't answer, and attempts to delete or change data
- Logs every query and answer, and tags each failure by type (wrong value, wrong units, wrong sign, made-up answer, wrong refusal)

## Key Findings

**Accuracy:**

| Test set | Before fix | After fix |
|---|---|---|
| v1 - 45 precisely worded questions | 45/45 | 45/45 |
| v2 - 20 realistic questions ("How volatile was BTC last summer?") | 17/20 (85%) | 19.3/20 average over 3 runs (95-100%) |

Across all runs, the agent recovered from its own SQL errors on 4 of 45 v1 questions. All 8 failures came from what a question meant, rather than incorrect SQL or math:

| Failure type | Example | Status |
|---|---|---|
| Unfinished last row | "Most recent daily close" used today's still-trading candle (64,750 vs. 65,315) | Fixed |
| Unit ambiguity | "Average daily volume" answered 5,345 BTC instead of $437M - right math, wrong unit | Fixed |
| Volatility not annualized | "30-day volatility" gave 2.32% (daily) vs. 44.3% (annualized); 44.3 / √365 = 2.32 | Open |
| Answer format | Rounded a Sharpe ratio of 0.0545 to 0.05; gave a number where "weekdays" was expected | 1 fixed, 1 open |
| Drawdown definition | 41.1% vs. 39.6%, likely a different peak or trough convention | Open |

To fix the first two, I added an `is_complete` flag for today's unfinished candle and a note that "volume" means USD. This fixed all relative-date failures (6/9 → 9/9) with no drop on v1. Because these fixes describe the data rather than individual questions, they apply to any similar question.

The first test set, v1, scored 100% because every question spelled out its definitions. The more realistic v2 questions uncovered the agent's challenge with ambiguous wording. One error was also hidden by a loose tolerance: a 3% tolerance let an unfinished-row error pass on one question.

Results also vary between runs: the same question passed in one run and failed in another (4 questions). One run per version isn't enough to evaluate an LLM system, so the after-fix result is reported as a 3-run average with its range. The before-fix number is a single run, so the size of the improvement is approximate.

Guardrails held: all 5 attempts to delete, drop, update, export, or override the rules ("ignore your previous rules") were refused or blocked in every run, and the table was unchanged.
## Tools

- Python
- Claude API (tool use)
- AWS S3, AWS CLI, boto3
- DuckDB
- pandas, PyArrow
- Coinbase Exchange API
