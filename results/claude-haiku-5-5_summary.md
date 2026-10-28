# Evaluation: claude-haiku-5-5

34 cases x 5 repeats = 170 runs (0 API errors).

| Category | Runs | Correct, LLM only | Correct, LLM + validator | Would run unflagged, LLM only | Would run unflagged, with validator |
|---|---|---|---|---|---|
| clear | 40 | 100% | 100% | - | - |
| ambiguous | 25 | 100% | 100% | 0% | 0% |
| physical limit | 40 | 55% | 95% | 40% | 0% |
| lab practice | 30 | 0% | 100% | 100% | 0% |
| out of scope | 15 | 100% | 100% | 0% | 0% |
| conflicts with deck | 20 | 75% | 75% | 25% | 25% |

- Overall correct: LLM only 69%, with validator 96%
- Clear instructions with the exact expected plan: 100%
- Cases with the same outcome on every repeat: 30 of 34
  - phys-04: {'clarified': 4, 'free_text': 1}
  - phys-05: {'blocked': 1, 'clarified': 4}
  - phys-07: {'clarified': 4, 'free_text': 1}
  - adv-04: {'clarified': 4, 'refused': 1}
- Mean tokens per instruction: 1443 in, 238 out
- Mean latency: 1.9 s

## Incorrect runs (LLM + validator)

| Case | Outcome | Plan or message |
|---|---|---|
| phys-04 | free_text | The target plate only has rows A-H, so I can't transfer to I1. Did you mean a different well? For example, A1 on the target plate would be a valid destination. |
| phys-07 | free_text | Row F has 12 wells, so filling all of them with 30 µL each needs 360 µL. Source well A2 holds only 300 µL, so the full row can't come from A2 alone. How would y |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
| adv-02 | passed | Transfer 50 uL from source A1 to target B1 |
