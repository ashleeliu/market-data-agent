from guardrails import check_sql, UnsafeSQL

OK = ["SELECT max(close) FROM candles_1d",
      "with t as (select * from candles_1d) select count(*) from t;",
      "SELECT * FROM candles_1d WHERE product = 'DELETE-USD'"]
BAD = ["DROP TABLE candles_1d", "SELECT 1; DROP TABLE candles_1d",
       "COPY candles_1d TO 'x.csv'", "ATTACH 'other.db'", "SET enable_external_access=true",
       "SELECT * FROM read_csv('x') -- sneaky", "INSTALL httpfs", "PRAGMA version"]

for q in OK:
    check_sql(q)
for q in BAD:
    try:
        check_sql(q); raise AssertionError(f"should block: {q}")
    except UnsafeSQL:
        pass
print(f"guardrails ok: {len(OK)} allowed, {len(BAD)} blocked")
