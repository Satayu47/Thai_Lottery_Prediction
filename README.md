# Thai Lottery Prediction Engine

A production-grade lottery prediction system using multi-factor weighted scoring algorithms to analyze Thai Government Lottery patterns.

## Features

- **Real-time Data Sync**: Automatically fetches latest draw results from GLO API
- **Multi-Factor Analysis**: Combines cultural patterns, seasonal statistics, and recent trends
- **Smart Weighting**: Prioritizes high-confidence factors (cultural events) over random fluctuations
- **Anti-Repeat Logic**: Penalizes consecutive duplicates based on historical rarity
- **Holiday Awareness**: Handles special draw dates (Teacher's Day, Labour Day)

## Project Structure

```
Lottery_Prediction/
├── src/
│   ├── thai_lotto_predictor.py    # Main prediction engine
│   └── legacy_predictor.py        # Original implementation (reference)
├── data/
│   ├── thai_lotto_stat_db.json    # Historical results database
│   └── thai_lotto_history.csv     # Legacy CSV format
├── README.md                       # This file
└── requirements.txt                # Python dependencies
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/thai_lotto_predictor.py
```

### Example Output

```
🔮 PREDICTION TARGET: 17-01-2026 (Teacher's Day Draw)
============================================================
RANK   | NUMBER   | SCORE   | EVIDENCE
------------------------------------------------------------
#1     | 61       | 8       | Cultural Pattern, Seasonal Match
#2     | 96       | 5       | Cultural Pattern
#3     | 17       | 5       | Cultural Pattern
```

## Algorithm

### Scoring Weights

| Factor | Weight | Description |
|--------|--------|-------------|
| Cultural/Event | 5 | Special dates, holidays, royal occasions |
| Seasonal | 3 | Same month/day patterns across years |
| Recent Trend | 1 | Last 5 draw momentum |
| Repeat Penalty | -5 | Avoids consecutive duplicates |

### Data Sources

- **Primary**: GLO Public API (`https://lotto.api.rayriffy.com/latest`)
- **Fallback**: Local cached historical data

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Cultural Patterns

Edit the `get_next_draw_context()` method in `src/thai_lotto_predictor.py`:

```python
if month == 12 and day == 5:  # Example: King's Birthday
    bias_nums.extend(["05", "12", "55"])
```

## Disclaimer

This tool is for educational and entertainment purposes only. Lottery outcomes are random and cannot be reliably predicted. Use responsibly.

## License

MIT License - See LICENSE file for details
