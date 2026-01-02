# Data Directory

This directory contains historical lottery data and cached results.

## Files

- `thai_lotto_stat_db.json` - Main database (JSON format) used by the prediction engine
- `thai_lotto_history.csv` - Legacy CSV format for backward compatibility

## Data Format

### JSON Format (`thai_lotto_stat_db.json`)

```json
[
  {
    "date": "02-01-2026",
    "number": "16"
  }
]
```

### CSV Format (`thai_lotto_history.csv`)

```csv
date,day,month,weekday,number
17-01-2025,17,1,Friday,61
```

## Notes

- Data files are automatically created on first run if they don't exist
- The engine syncs with the GLO API to fetch latest results
- Historical data is preserved across runs
