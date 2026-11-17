"""v2 test set: 20 realistic questions, phrased the way a real user would ask.

No definitions are given in the question. Each gold answer follows ONE stated convention
(see "rule"), so a failure shows where the agent's assumption differs from ours.

Time conventions (relative to the data, not the wall clock):
  - The last row in the data is today's UNFINISHED candle, so the "as-of" day is the latest
    COMPLETE day = max(date) - 1. "Yesterday" = that day. "This year" = 2026.
  - "Last month" = October 2026. "Last summer" = Jun 1 - Aug 31, 2026.
  - "Volume" means USD volume. Annualize with sqrt(365) (crypto trades every day).
"""
BTC, ETH, SOL = "product='BTC-USD'", "product='ETH-USD'", "product='SOL-USD'"
ASOF = "a AS (SELECT max(date) - 1 AS d FROM candles_1d)"            # latest complete day
LOGRET = "ln(close / LAG(close) OVER (PARTITION BY product ORDER BY date))"
RET = "close / LAG(close) OVER (PARTITION BY product ORDER BY date) - 1"

V2_QUESTIONS = [
    # --- relative time ---
    dict(id="h01", cat="relative_time", type="number", rel_tol=0.01,
         question="How much is ETH up this year?",
         rule="% return from the 2025-12-31 close to the latest complete day's close",
         gold_sql=f"WITH {ASOF} SELECT (MAX(close) FILTER (WHERE date = a.d) / MAX(close) FILTER (WHERE date = '2025-12-31') - 1) * 100 "
                  f"FROM candles_1d, a WHERE {ETH}"),
    dict(id="h02", cat="relative_time", type="number", rel_tol=0.001,
         question="What was BTC's most recent daily close?",
         rule="close of the latest COMPLETE day, not today's unfinished candle",
         gold_sql=f"WITH {ASOF} SELECT close FROM candles_1d, a WHERE {BTC} AND date = a.d"),
    dict(id="h03", cat="relative_time", type="number", rel_tol=0.03,
         question="How volatile was BTC last summer?",
         rule="Jun-Aug 2026; annualized: stddev_samp of daily log returns * sqrt(365), in %",
         gold_sql=f"WITH r AS (SELECT date, product, {LOGRET} AS lr FROM candles_1d) "
                  f"SELECT stddev_samp(lr) * sqrt(365) * 100 FROM r WHERE {BTC} AND date BETWEEN '2026-06-01' AND '2026-08-31'"),
    dict(id="h04", cat="relative_time", type="number", rel_tol=0.01,
         question="What was BTC's average daily volume last month?",
         rule="October 2026, USD volume",
         gold_sql=f"SELECT avg(volume_usd) FROM candles_1d WHERE {BTC} AND date BETWEEN '2026-10-01' AND '2026-10-31'"),
    dict(id="h05", cat="relative_time", type="text",
         question="Which coin performed best last month?",
         rule="October 2026 return, 2026-09-30 close to 2026-10-31 close",
         gold_sql="WITH g AS (SELECT product, MAX(close) FILTER (WHERE date = '2026-10-31') / MAX(close) FILTER (WHERE date = '2026-09-30') AS g "
                  "FROM candles_1d GROUP BY product) SELECT product FROM g ORDER BY g DESC LIMIT 1"),
    dict(id="h06", cat="relative_time", type="count",
         question="How many days was BTC down last month?",
         rule="October 2026, close lower than the previous day's close",
         gold_sql=f"WITH r AS (SELECT date, product, {RET} AS ret FROM candles_1d) "
                  f"SELECT count(*) FROM r WHERE {BTC} AND date BETWEEN '2026-10-01' AND '2026-10-31' AND ret < 0"),
    dict(id="h07", cat="relative_time", type="number", rel_tol=0.001,
         question="What's BTC's year-to-date high?",
         rule="highest intraday HIGH in 2026 (not highest close)",
         gold_sql=f"SELECT max(high) FROM candles_1d WHERE {BTC} AND year(date) = 2026"),
    dict(id="h08", cat="relative_time", type="count",
         question="How many days has BTC closed above $100k this year?",
         rule="2026, complete days only",
         gold_sql=f"WITH {ASOF} SELECT count(*) FROM candles_1d, a WHERE {BTC} AND year(date) = 2026 AND date <= a.d AND close > 100000"),
    dict(id="h09", cat="relative_time", type="date",
         question="What was the busiest trading day for ETH this year?",
         rule="2026, highest USD volume, complete days",
         gold_sql=f"WITH {ASOF} SELECT date FROM candles_1d, a WHERE {ETH} AND year(date) = 2026 AND date <= a.d "
                  "ORDER BY volume_usd DESC LIMIT 1"),
    # --- ambiguous definitions ---
    dict(id="h10", cat="ambiguous_def", type="number", rel_tol=0.03,
         question="How far is ETH below its all-time high?",
         rule="1 - latest complete close / highest intraday HIGH in the data, as a positive %",
         gold_sql=f"WITH {ASOF} SELECT (1 - MAX(close) FILTER (WHERE date = a.d) / max(high)) * 100 FROM candles_1d, a WHERE {ETH}"),
    dict(id="h11", cat="ambiguous_def", type="number", rel_tol=0.02,
         question="What was SOL's worst weekly return in 2026?",
         rule="ISO weeks (Mon-Sun) starting in 2026; last close of week vs last close of prior week; negative %",
         gold_sql=f"WITH {ASOF}, w AS (SELECT date_trunc('week', date) AS wk, arg_max(close, date) AS c FROM candles_1d, a "
                  f"WHERE {SOL} AND date <= a.d GROUP BY wk), r AS (SELECT wk, c / LAG(c) OVER (ORDER BY wk) - 1 AS ret FROM w) "
                  "SELECT min(ret) * 100 FROM r WHERE year(wk) = 2026"),
    dict(id="h12", cat="ambiguous_def", type="choice", options=["weekends", "weekdays"],
         question="Is BTC more volatile on weekends or weekdays? Use 2025.",
         rule="average absolute close-to-close daily return, Sat/Sun vs Mon-Fri, 2025",
         gold_sql=f"WITH r AS (SELECT date, product, abs({RET}) AS ar FROM candles_1d) "
                  "SELECT CASE WHEN avg(ar) FILTER (WHERE isodow(date) IN (6, 7)) > avg(ar) FILTER (WHERE isodow(date) < 6) "
                  f"THEN 'weekends' ELSE 'weekdays' END FROM r WHERE {BTC} AND year(date) = 2025"),
    dict(id="h13", cat="ambiguous_def", type="number", abs_tol=0.02,
         question="How correlated were BTC and SOL this year?",
         rule="Pearson correlation of daily close-to-close returns, 2026, complete days",
         gold_sql=f"WITH {ASOF}, r AS (SELECT date, product, {RET} AS ret FROM candles_1d) "
                  "SELECT corr(b.ret, s.ret) FROM r b JOIN r s ON b.date = s.date, a "
                  "WHERE b.product = 'BTC-USD' AND s.product = 'SOL-USD' AND year(b.date) = 2026 AND b.date <= a.d"),
    dict(id="h14", cat="ambiguous_def", type="number", rel_tol=0.05,
         question="What was BTC's Sharpe ratio in 2025?",
         rule="risk-free rate 0; mean / stddev_samp of daily simple returns * sqrt(365)",
         gold_sql=f"WITH r AS (SELECT date, product, {RET} AS ret FROM candles_1d) "
                  f"SELECT avg(ret) / stddev_samp(ret) * sqrt(365) FROM r WHERE {BTC} AND year(date) = 2025"),
    dict(id="h15", cat="ambiguous_def", type="number", rel_tol=0.02,
         question="How much did BTC drop in its biggest crash this year?",
         rule="maximum drawdown of daily closes within 2026 (complete days), positive %",
         gold_sql=f"WITH {ASOF}, p AS (SELECT close, max(close) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS peak "
                  f"FROM candles_1d, a WHERE {BTC} AND year(date) = 2026 AND date <= a.d) SELECT max(1 - close / peak) * 100 FROM p"),
    dict(id="h16", cat="ambiguous_def", type="number", rel_tol=0.05,
         question="What's BTC's 30-day volatility as of yesterday?",
         rule="last 30 complete days of daily log returns; stddev_samp * sqrt(365), in %",
         gold_sql=f"WITH {ASOF}, r AS (SELECT date, product, {LOGRET} AS lr FROM candles_1d) "
                  f"SELECT stddev_samp(lr) * sqrt(365) * 100 FROM r, a WHERE {BTC} AND r.date > a.d - 30 AND r.date <= a.d"),
    # --- unanswerable: the right answer is to say the data can't answer it ---
    dict(id="h17", cat="unanswerable", type="unanswerable",
         question="What was ETH's price at noon UTC on 2026-03-01?", rule="only daily candles exist"),
    dict(id="h18", cat="unanswerable", type="unanswerable",
         question="What was BTC's funding rate yesterday?", rule="no perps / funding data"),
    dict(id="h19", cat="unanswerable", type="unanswerable",
         question="What was the BTC price in euros on 2026-01-01?", rule="only USD pairs"),
    dict(id="h20", cat="unanswerable", type="unanswerable",
         question="How did DOGE do in 2025?", rule="DOGE is not in the data"),
]
for q in V2_QUESTIONS:
    q["set"] = "v2"
