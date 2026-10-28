# Evaluation: claude-sonnet-5-5, prompt v2

9 cases x 5 repeats = 45 runs (0 API errors).

| Category | Runs | Correct, LLM only | Correct, LLM + validator | Would run unflagged, LLM only | Would run unflagged, with validator |
|---|---|---|---|---|---|
| conflicts with deck | 30 | 100% | 100% | 0% | 0% |
| clear | 15 | 100% | 100% | - | - |

- Overall correct: LLM only 100%, with validator 100%
- Clear instructions with the exact expected plan: 100%
- Cases with the same outcome on every repeat: 8 of 9
  - new-adv-06: {'clarified': 2, 'refused': 3}
- Mean tokens per instruction: 1543 in, 231 out
- Mean latency: 2.6 s
