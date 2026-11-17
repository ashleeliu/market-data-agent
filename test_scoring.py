from scoring import score, extract_answer, parse_number

num = {"type": "number"}
assert extract_answer("blah\nANSWER: 12.5\nSQL: ...") == "12.5"
assert parse_number("$124,720.09") == 124720.09
assert parse_number("about 1.5 billion USD") == 1.5e9
assert score(num, 124720.09, "ANSWER: $124,720.09")[0]
assert score(num, 124720.09, "ANSWER: 124,700")[0]                 # within 0.5%
assert score(num, 12.3, "ANSWER: 0.123")[1] == "wrong_units"
assert score(num, 30.0, "ANSWER: -30%")[1] == "wrong_sign"
assert score(num, 5.0, "no answer line")[1] == "no_answer"
assert score({"type": "count"}, 365, "ANSWER: 365 rows")[0]
assert not score({"type": "count"}, 365, "ANSWER: 364")[0]
assert score({"type": "date"}, "2025-10-06", "ANSWER: 2025-10-06")[0]
assert not score({"type": "date"}, "2025-10-06", "ANSWER: 2025-10-07")[0]
assert score({"type": "month"}, "2025-10", "ANSWER: 2025-10")[0]
assert score({"type": "text"}, "SOL-USD", "ANSWER: SOL-USD")[0]
assert score({"type": "text"}, "SOL-USD", "ANSWER: SOL")[0]
assert not score({"type": "text"}, "SOL-USD", "ANSWER: SOL or ETH")[0]
assert score({"type": "number", "abs_tol": 0.01}, 0.812, "ANSWER: 0.81")[0]
print("scoring ok")
