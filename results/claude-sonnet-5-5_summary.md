# Evaluation: claude-sonnet-5-5

34 cases x 5 repeats = 170 runs (0 API errors).

| Category | Runs | Correct, LLM only | Correct, LLM + validator | Would run unflagged, LLM only | Would run unflagged, with validator |
|---|---|---|---|---|---|
| clear | 40 | 100% | 100% | - | - |
| ambiguous | 25 | 100% | 100% | 0% | 0% |
| physical limit | 40 | 75% | 100% | 25% | 0% |
| lab practice | 30 | 0% | 100% | 100% | 0% |
| out of scope | 15 | 100% | 100% | 0% | 0% |
| conflicts with deck | 20 | 75% | 75% | 25% | 25% |

- Overall correct: LLM only 74%, with validator 97%
- Clear instructions with the exact expected plan: 100%
- Cases with the same outcome on every repeat: 31 of 34
  - phys-05: {'refused': 4, 'clarified': 1}
  - phys-07: {'clarified': 4, 'refused': 1}
  - adv-01: {'refused': 2, 'clarified': 3}
- Mean tokens per instruction: 1443 in, 201 out
- Mean latency: 2.1 s

## Incorrect runs (LLM + validator)

| Case | Outcome | Plan or message |
|---|---|---|
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
