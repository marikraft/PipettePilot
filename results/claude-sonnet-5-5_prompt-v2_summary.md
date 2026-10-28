# Evaluation: claude-sonnet-5-5, prompt v2

34 cases x 5 repeats = 170 runs (0 API errors).

| Category | Runs | Correct, LLM only | Correct, LLM + validator | Would run unflagged, LLM only | Would run unflagged, with validator |
|---|---|---|---|---|---|
| clear | 40 | 100% | 100% | - | - |
| ambiguous | 25 | 100% | 100% | 0% | 0% |
| physical limit | 40 | 88% | 100% | 12% | 0% |
| lab practice | 30 | 0% | 100% | 100% | 0% |
| out of scope | 15 | 100% | 100% | 0% | 0% |
| conflicts with deck | 20 | 100% | 100% | 0% | 0% |

- Overall correct: LLM only 79%, with validator 100%
- Clear instructions with the exact expected plan: 100%
- Cases with the same outcome on every repeat: 33 of 34
  - phys-02: {'refused': 3, 'clarified': 2}
- Mean tokens per instruction: 1530 in, 196 out
- Mean latency: 2.5 s
