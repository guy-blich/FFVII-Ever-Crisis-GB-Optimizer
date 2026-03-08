# Guild Battle Optimizer

Assigns guild members to boss stages in FF7 Ever Crisis Guild Battles to maximize total damage dealt. Given each player's damage percentage per stage and their available attempts, the optimizer uses **0/1 knapsack dynamic programming** to find the smallest subset of player attempts whose combined damage is closest to (or exceeds) 100% of a boss stage's HP — prioritizing higher stages first.

**Stage 6** is a bonus stage that unlocks after stage 5 has been beaten 5 times (cumulative across respawns). Once unlocked it becomes the highest-priority stage in every subsequent round.

---

## How it works

Each guild battle consists of five boss stages with increasing difficulty. Players have a fixed number of attempts per battle and deal a different percentage of a boss's HP depending on the stage.

The optimizer runs in rounds:

1. For each active stage (highest first), it finds the **minimum set of players** whose combined damage ≥ 100% (or the best achievable total if 100% is not reachable).
2. Used attempts are removed from the pool.
3. If all currently active stages are cleared, the bosses respawn and the process repeats with remaining attempts.
4. The round ends when players run out of attempts or a stage can no longer be cleared.
5. **Stage 6 unlock:** once stage 5 has been beaten 5 times, stage 6 is unlocked and becomes the top priority (processed before stage 5) in all future rounds.

### Algorithm

The core function (`closest_above_100_with_indices`) is a **0/1 knapsack** variant:

- Scores are scaled to integers to avoid floating-point precision issues.
- A DP table tracks which sums are reachable and which player indices achieve them.
- The result is the minimum reachable sum ≥ 100%, or the maximum achievable sum if 100% is not reachable.
- **Time complexity:** O(n × S) where n = number of player attempts and S = sum of all scaled scores.

---

## Project structure

```
guild-battle-optimizer/
├── config/
│   ├── boss_data.json       # Boss stage HP and death counts
│   └── player_data.json     # Player scores per stage and attempt counts
├── src/
│   ├── main.py              # Entry point + CLI
│   ├── models/
│   │   ├── BossData.py      # Pydantic model for boss stages
│   │   └── PlayerData.py    # Pydantic model for players
│   ├── optimizer/
│   │   └── boss_optimizer.py  # Core optimization loop
│   └── utils/
│       ├── data_utils.py    # Score list builder + DP algorithm
│       ├── file_utils.py    # JSON loader
│       └── logger.py        # Logging configuration
├── tests/                   # pytest test suite
├── logs/                    # Rotating log output
├── pyproject.toml
└── requirements.txt
```

---

## Setup

**Requirements:** Python 3.11+

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install dev dependencies (includes pytest, black, mypy)
pip install -r requirements-dev.txt
```

---

## Usage

### Run with default config files

```bash
python -m src.main
```

### Specify custom data files

```bash
python -m src.main --players path/to/player_data.json --bosses path/to/boss_data.json
```

### Change log verbosity

```bash
python -m src.main --log-level DEBUG
```

```
usage: guild-battle-optimizer [-h] [--players FILE] [--bosses FILE] [--log-level LEVEL]

options:
  --players FILE, -p FILE   Path to player data JSON (default: config/player_data.json)
  --bosses FILE,  -b FILE   Path to boss data JSON  (default: config/boss_data.json)
  --log-level LEVEL         DEBUG | INFO | WARNING | ERROR (default: INFO)
```

---

## Configuration

### `config/player_data.json`

Each player entry lists their damage percentage per stage and how many attempts they have:

```json
{
  "PlayerName": {
    "stage1": 100.0,
    "stage2": 80.0,
    "stage3": 55.5,
    "stage4": 30.0,
    "stage5": 15.0,
    "stage6": 8.3,
    "attempts": 3
  }
}
```

Percentages can be written as numbers (`55.5`) or strings (`"55.5%"`).

### `config/boss_data.json`

Current HP for each boss stage (updated after each battle if bosses are mid-fight):

```json
{
  "stage1": {"hp": "100%", "deaths": 0},
  "stage2": {"hp": "75%",  "deaths": 1},
  "stage3": {"hp": "100%", "deaths": 0},
  "stage4": {"hp": "100%", "deaths": 0},
  "stage5": {"hp": "100%", "deaths": 0},
  "stage6": {"hp": "100%", "deaths": 0}
}
```

---

## Running tests

```bash
python -m pytest tests/ -v
```

43 tests cover the DP algorithm, Pydantic model validation (including `%`-string parsing), score list expansion, the full optimizer loop, and all stage 6 unlock mechanics.

---

## Example output

```
2026-03-07 20:30:00 INFO: Starting boss optimization...
2026-03-07 20:30:00 INFO: Boss stage 5 efficiently killed by ['player5', 'player2'] with a sum of 100.00%
2026-03-07 20:30:00 INFO: Boss stage 4 efficiently killed by ['player5', 'player3'] with a sum of 104.66%
2026-03-07 20:30:00 INFO: Boss stage 3 efficiently killed by ['player2', 'player7'] with a sum of 138.46%
2026-03-07 20:30:00 INFO: Boss stage 2 efficiently killed by ['player1', 'player3'] with a sum of 200.00%
2026-03-07 20:30:00 INFO: Boss stage 1 efficiently killed by ['player6', 'player8'] with a sum of 194.00%
2026-03-07 20:30:00 INFO: All boss stages have been taken down!
```

---

## License

MIT
