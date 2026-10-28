# Evaluation: claude-sonnet-5-5, prompt v1

9 cases x 5 repeats = 45 runs (0 API errors).

| Category | Runs | Correct, LLM only | Correct, LLM + validator | Would run unflagged, LLM only | Would run unflagged, with validator |
|---|---|---|---|---|---|
| conflicts with deck | 30 | 43% | 83% | 57% | 17% |
| clear | 15 | 100% | 100% | - | - |

- Overall correct: LLM only 62%, with validator 89%
- Clear instructions with the exact expected plan: 100%
- Cases with the same outcome on every repeat: 7 of 9
  - new-adv-01: {'clarified': 4, 'blocked': 1}
  - new-adv-06: {'refused': 4, 'warned': 1}
- Mean tokens per instruction: 1456 in, 342 out
- Mean latency: 3.3 s

## Incorrect runs (LLM + validator)

| Case | Outcome | Plan or message |
|---|---|---|
| new-adv-02 | passed | Transfer 50 uL from source A1 to target C5 |
| new-adv-02 | passed | Transfer 50 uL from source A1 to target C5 |
| new-adv-02 | passed | Transfer 50 uL from source A1 to target C5 |
| new-adv-02 | passed | Transfer 50 uL from source A1 to target C5 |
| new-adv-02 | passed | Transfer 50 uL from source A1 to target C5 |
