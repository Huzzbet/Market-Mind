# Integrated opportunity ranking v1

The integrated research-priority score starts with the existing technical score (maximum 100), then applies transparent context adjustments:
- Up to +12 for matched headline context (heuristic symbol matching; capped).
- +8 where a covered sector proxy has at least 60% positive 5-session breadth and two or more constituents.
- A -5 penalty each for price below MA20, below MA50, and negative 20-session return.
- Final score clipped to 0–100.

Scores are research priority—not probabilities, expected returns, or recommendations. Catalyst matching is heuristic and should be verified against the linked source. Sector proxy coverage is incomplete. This version is not backtested or runtime tested.
