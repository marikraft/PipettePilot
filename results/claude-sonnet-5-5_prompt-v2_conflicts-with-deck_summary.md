# Evaluation: claude-sonnet-5-5, prompt v2

4 cases x 5 repeats = 20 runs (0 API errors).

| Category | Runs | Correct, LLM only | Correct, LLM + validator | Would run unflagged, LLM only | Would run unflagged, with validator |
|---|---|---|---|---|---|
| conflicts with deck | 20 | 100% | 100% | 0% | 0% |

- Overall correct: LLM only 100%, with validator 100%
- Clear instructions with the exact expected plan: -
- Cases with the same outcome on every repeat: 3 of 4
  - adv-03: {'refused': 4, 'clarified': 1}
- Mean tokens per instruction: 1540 in, 257 out
- Mean latency: 2.8 s
