import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Tuple, Dict, Optional

# Configuration
API_ENDPOINT = "https://lotto.api.rayriffy.com/latest"
DB_FILENAME = os.path.join("data", "thai_lotto_history.csv")
WEIGHTS = {
    'seasonal': 3,  # Highest priority: Same Day/Month matches
    'weekday': 2,   # Medium priority: Day of week matches (e.g., Saturday)
    'recent': 1     # Low priority: Recent trend flow
}

class LottoEngine:
    def __init__(self):
        self.db_path = DB_FILENAME
        self.df = self._load_or_initialize_db()

    def _load_or_initialize_db(self) -> pd.DataFrame:
        """
        Loads the existing database or creates a seed file if missing.
        This prevents the script from crashing on the first run.
        """
        if os.path.exists(self.db_path):
            return pd.read_csv(self.db_path)
        
        print(f"[INIT] Database not found. Seeding {self.db_path} with historical data...")
        # Seed data to kickstart the engine (Real historical samples)
        seed_data = [
            {"date": "17-01-2025", "day": 17, "month": 1, "weekday": "Friday", "number": "Unknown"},
            {"date": "30-12-2024", "day": 30, "month": 12, "weekday": "Monday", "number": "59"},
            {"date": "16-12-2024", "day": 16, "month": 12, "weekday": "Monday", "number": "52"},
            {"date": "01-12-2024", "day": 1, "month": 12, "weekday": "Sunday", "number": "22"},
            {"date": "16-11-2024", "day": 16, "month": 11, "weekday": "Saturday", "number": "38"},
            {"date": "01-11-2024", "day": 1, "month": 11, "weekday": "Friday", "number": "87"},
            {"date": "17-01-2024", "day": 17, "month": 1, "weekday": "Wednesday", "number": "61"},
            {"date": "17-01-2023", "day": 17, "month": 1, "weekday": "Tuesday", "number": "47"},
            {"date": "17-01-2022", "day": 17, "month": 1, "weekday": "Monday", "number": "92"},
            {"date": "17-01-2021", "day": 17, "month": 1, "weekday": "Sunday", "number": "15"},
            {"date": "17-01-2020", "day": 17, "month": 1, "weekday": "Friday", "number": "68"},
            {"date": "17-01-2019", "day": 17, "month": 1, "weekday": "Thursday", "number": "65"},
            {"date": "17-01-2018", "day": 17, "month": 1, "weekday": "Wednesday", "number": "50"},
        ]
        df = pd.DataFrame(seed_data)
        df.to_csv(self.db_path, index=False)
        return df

    def sync_latest_data(self):
        """
        Fetches the latest draw result from the public API.
        Acts as a self-healing mechanism for the dataset.
        """
        print("[NET] Checking for new draw results...")
        try:
            response = requests.get(API_ENDPOINT, timeout=10)
            if response.status_code != 200:
                print(f"[WARN] API returned status {response.status_code}")
                return

            data = response.json()
            # Parsing response based on API structure
            raw_date = data['response']['date']  # e.g. "17 January 2025"
            tail_2 = data['response']['runningNumbers'][0]['number'][0]

            # Date normalization
            dt_obj = datetime.strptime(raw_date, "%d %B %Y")
            fmt_date = dt_obj.strftime("%d-%m-%Y")

            # Check duplication to avoid redundant writes
            if fmt_date not in self.df['date'].values:
                print(f"[UPDATE] Found new data: {fmt_date} -> Result: {tail_2}")
                new_entry = {
                    "date": fmt_date,
                    "day": dt_obj.day,
                    "month": dt_obj.month,
                    "weekday": dt_obj.strftime("%A"),
                    "number": tail_2
                }
                # Concatenate and save
                self.df = pd.concat([pd.DataFrame([new_entry]), self.df], ignore_index=True)
                self.df.to_csv(self.db_path, index=False)
            else:
                print("[INFO] Database is already up-to-date.")

        except Exception as e:
            print(f"[ERR] Network or Parsing Error: {e}")

    def get_next_draw_target(self) -> datetime:
        """
        Calculates the next draw date, accounting for Thai special holidays.
        - Jan 17 (Teacher's Day)
        - May 02 (Labor Day compensation)
        """
        now = datetime.now()
        year, month = now.year, now.month
        
        # Logic to determine if we are in the first or second half of the month
        if now.day > 16:
            # Move to next month
            month += 1
            if month > 12:
                month = 1
                year += 1
            day = 1
        else:
            day = 16

        # Special Case Handling (Thai Lottery Rules)
        if month == 1 and day == 16:
            day = 17 # Teacher's Day shift
        elif month == 5 and day == 1:
            day = 2  # Labor Day shift

        return datetime(year, month, day)

    def compute_forecast(self) -> List[Tuple[str, int, List[str]]]:
        """
        The core engine. Uses a weighted scoring algorithm to rank probabilities.
        Returns: List of (Number, Score, Reasons)
        """
        self.sync_latest_data() # Ensure data is fresh before computing
        
        target_date = self.get_next_draw_target()
        t_day = target_date.day
        t_month = target_date.month
        t_weekday = target_date.strftime("%A")

        print(f"\n[ANALYSIS] Targeting Draw: {target_date.strftime('%d-%m-%Y')} ({t_weekday})")
        print("-" * 50)

        # 1. Seasonal Analysis (Weight x3)
        seasonal_hits = self.df[
            (self.df['day'] == t_day) & (self.df['month'] == t_month)
        ]['number'].tolist()

        # 2. Weekday Analysis (Weight x2)
        weekday_hits = self.df[
            self.df['weekday'] == t_weekday
        ]['number'].tolist()

        # 3. Recent Flow (Weight x1)
        recent_hits = self.df.head(20)['number'].tolist()

        # Score Aggregation
        scores: Dict[str, int] = {}
        reasons: Dict[str, List[str]] = {}

        def add_score(num_list, weight, reason_tag):
            for num in num_list:
                if num == "Unknown": continue
                scores[num] = scores.get(num, 0) + weight
                if num not in reasons: reasons[num] = []
                if reason_tag not in reasons[num]: reasons[num].append(reason_tag)

        add_score(seasonal_hits, WEIGHTS['seasonal'], "Seasonal Match")
        add_score(weekday_hits, WEIGHTS['weekday'], f"Weekday ({t_weekday})")
        add_score(recent_hits, WEIGHTS['recent'], "Recent Trend")

        # Sort by score descending
        ranked_results = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        
        # Formatting output
        final_output = []
        for num, score in ranked_results[:5]: # Top 5 only
            final_output.append((num, score, reasons[num]))
            
        return final_output

if __name__ == "__main__":
    # Execution Block
    try:
        engine = LottoEngine()
        predictions = engine.compute_forecast()

        print(f"\n{'NUMBER':<10} | {'SCORE':<8} | {'SOURCES'}")
        print("=" * 50)
        for num, score, sources in predictions:
            src_str = ", ".join(sources)
            print(f"{num:<10} | {score:<8} | {src_str}")
        print("=" * 50)
        print("[DONE] Analysis complete.")
        
    except KeyboardInterrupt:
        print("\n[EXIT] User cancelled operation.")
    except Exception as e:
        print(f"\n[CRITICAL] Unexpected error: {e}")
