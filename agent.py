"""Plain-English question -> SQL -> run read-only -> check -> explain."""
import json, sys, threading
import anthropic, duckdb
from guardrails import check_sql, UnsafeSQL

MODEL = "claude-sonnet-5-5"
MAX_ROWS, TIMEOUT_S, MAX_STEPS = 200, 10, 6

def open_readonly(path="market.duckdb"):
    con = duckdb.connect(path, read_only=True)          # Layer 2: file opened read-only
    con.execute("SET enable_external_access = false")   # Layer 3: no files/URLs/S3
    con.execute("SET lock_configuration = true")        # ...and it can't be turned back on
    return con

def schema_text(con):
    rows = con.execute("SELECT table_name, column_name, data_type FROM information_schema.columns "
                       "ORDER BY table_name, ordinal_position").fetchall()
    return "\n".join(f"{t}.{c} ({d})" for t, c, d in rows)

def run_sql(con, sql):
    try:
        safe = check_sql(sql)
    except UnsafeSQL as e:
        return {"error": f"rejected: {e}"}
    timer = threading.Timer(TIMEOUT_S, con.interrupt); timer.start()   # Layer 4: timeout
    try:
        cur = con.execute(f"SELECT * FROM ({safe}) LIMIT {MAX_ROWS}")  # Layer 5: row cap
        cols = [d[0] for d in cur.description]
        rows = [[str(v) for v in r] for r in cur.fetchall()]
        return {"columns": cols, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        timer.cancel()

TOOLS = [{
    "name": "run_sql",
    "description": "Run one read-only DuckDB SELECT query. Returns columns and up to 200 rows.",
    "input_schema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]},
}]

SYSTEM = """You are a market data analyst. Answer questions using the DuckDB tables below.
Schema:
{schema}

Rules:
- Always get numbers by calling run_sql. Never guess.
- Dates are UTC days. volume_base is in coin units; volume_usd = volume_base * close.
- After each result, check it: empty? nulls? does the magnitude make sense (e.g. BTC price)?
  If something looks wrong, fix the query and run it again.
- Final answer: 1-3 sentences with the number, then a line 'SQL:' with the final query."""

def ask(question, con=None, verbose=True):
    con = con or open_readonly()
    client = anthropic.Anthropic()
    msgs = [{"role": "user", "content": question}]
    sql_log = []
    for _ in range(MAX_STEPS):
        resp = client.messages.create(model=MODEL, max_tokens=1500, tools=TOOLS,
                                      system=SYSTEM.format(schema=schema_text(con)), messages=msgs)
        msgs.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            answer = "".join(b.text for b in resp.content if b.type == "text")
            return {"answer": answer, "sql_log": sql_log}
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                out = run_sql(con, b.input["sql"])
                sql_log.append({"sql": b.input["sql"], "result": out})
                if verbose:
                    print("SQL>", b.input["sql"], "\n   ", json.dumps(out)[:300])
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": json.dumps(out)})
        msgs.append({"role": "user", "content": results})
    return {"answer": "Stopped: too many steps.", "sql_log": sql_log}

if __name__ == "__main__":
    print(ask(" ".join(sys.argv[1:]) or "What was BTC's highest close in the data?")["answer"])
