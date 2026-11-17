"""Pure-Python answer scoring (no API or database needed, so it is easy to unit test)."""
import math, re

COINS = ["BTC", "ETH", "SOL"]
NA = re.compile(r"\b(n/?a|not available|unavailable|unknown|none|cannot|can't|no data)\b", re.I)

def extract_answer(text):
    """Return the value after the last 'ANSWER:' line, or None."""
    hits = re.findall(r"ANSWER:\s*(.+)", text or "")
    return hits[-1].strip().strip("*`").strip() if hits else None

def parse_number(s):
    s = s.replace(",", "").replace("$", "")
    m = re.search(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s)
    if not m:
        return None
    x = float(m.group(0))
    unit = re.search(r"\d\s*(billion|bn|b|million|mm|m|thousand|k)\b", s, re.I)   # "1.2 billion"
    if unit:
        x *= {"b": 1e9, "bn": 1e9, "billion": 1e9, "m": 1e6, "mm": 1e6, "million": 1e6,
              "k": 1e3, "thousand": 1e3}[unit.group(1).lower()]
    return x

def score(q, gold, answer_text):
    """Return (passed: bool, tag: str, predicted: str|None)."""
    ans = extract_answer(answer_text)
    if ans is None:
        return False, "no_answer", None
    t = q["type"]
    if t == "unanswerable":
        ok = bool(NA.search(ans)) and not re.search(r"\d", ans)
        return ok, "ok" if ok else "hallucinated", ans
    if NA.search(ans) and not re.search(r"\d", ans):
        return False, "false_refusal", ans                  # said N/A to an answerable question
    if t in ("number", "count"):
        pred = parse_number(ans)
        if pred is None:
            return False, "unparseable", ans
        g = float(gold)
        if t == "count":
            return (round(pred) == round(g), "ok" if round(pred) == round(g) else "wrong_value", ans)
        close = lambda a: math.isclose(a, g, rel_tol=q.get("rel_tol", 0.005), abs_tol=q.get("abs_tol", 1e-6))
        if close(pred):
            return True, "ok", ans
        if close(pred * 100) or close(pred / 100):
            return False, "wrong_units", ans          # e.g. 0.12 instead of 12%
        if close(-pred):
            return False, "wrong_sign", ans
        return False, "wrong_value", ans
    if t in ("date", "month"):
        pat = r"\d{4}-\d{2}-\d{2}" if t == "date" else r"\d{4}-\d{2}"
        m = re.search(pat, ans)
        ok = bool(m) and m.group(0) == str(gold)[: len(m.group(0))] and len(m.group(0)) == (10 if t == "date" else 7)
        return ok, "ok" if ok else "wrong_value", ans
    if t == "text":
        want = str(gold).split("-")[0].upper()
        found = {c for c in COINS if re.search(rf"\b{c}\b", ans.upper())}
        ok = found == {want}
        return ok, "ok" if ok else "wrong_value", ans
    if t == "choice":
        found = {o for o in q["options"] if o.lower() in ans.lower()}
        ok = found == {str(gold)}
        return ok, "ok" if ok else "wrong_value", ans
    raise ValueError(f"unknown type {t}")
