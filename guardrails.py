"""Layer 1 of read-only safety: reject anything that is not a single SELECT."""
import re

BLOCKED = re.compile(
    r"\b(insert|update|delete|drop|create|alter|attach|detach|copy|export|import|install|"
    r"load|pragma|set|reset|call|checkpoint|vacuum|truncate|grant|use)\b", re.I)

class UnsafeSQL(ValueError):
    pass

def check_sql(sql: str) -> str:
    s = sql.strip().rstrip(";").strip()
    if "--" in s or "/*" in s:
        raise UnsafeSQL("comments are not allowed")
    if ";" in s:
        raise UnsafeSQL("only one statement allowed")
    if not re.match(r"^(select|with)\b", s, re.I):
        raise UnsafeSQL("query must start with SELECT or WITH")
    no_strings = re.sub(r"'[^']*'", "''", s)      # ignore words inside string literals
    if m := BLOCKED.search(no_strings):
        raise UnsafeSQL(f"blocked keyword: {m.group(0)}")
    return s
