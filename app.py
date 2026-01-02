import streamlit as st
import requests
import pandas as pd
import json
import os
from datetime import datetime
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

# --- CONFIGURATION ---
API_ENDPOINT = "https://lotto.api.rayriffy.com/latest"
DB_FILE = os.path.join("data", "thai_lotto_stat_db.json")
CACHE_TTL = 3600  # Cache API results for 1 hour to prevent spamming
THEME_COLOR = "#FF4B4B"

st.set_page_config(
    page_title="Satayu Intersection Engine",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inject custom CSS for a cleaner, "App-like" feel
st.markdown(f"""
    <style>
    .stApp {{ background-color: #FAFAFA; }}
    .main-title {{ font-size: 2.2rem; font-weight: 800; color: #333; margin-bottom: 0; }}
    .subtitle {{ font-size: 1rem; color: #666; margin-bottom: 2rem; }}
    .metric-box {{
        background: white; border: 1px solid #e0e0e0; 
        border-radius: 8px; padding: 15px; text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    .prediction-card {{
        background: linear-gradient(135deg, #FF4B4B 0%, #FF9068 100%);
        color: white; padding: 20px; border-radius: 12px;
        text-align: center; margin-top: 20px;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
    }}
    </style>
""", unsafe_allow_html=True)

class LottoAnalyzer:
    """
    Production-grade prediction engine integrating the advanced CLI algorithm
    with web interface capabilities. Uses persistent database and multi-factor scoring.
    """
    
    def __init__(self):
        # Weight configurations matching the advanced CLI engine
        self.weights = {
            'CULTURE': 5,      # Cultural/Event patterns
            'SEASONAL': 3,     # Historical same-month patterns
            'RECENT': 1,       # Last 20 draws trend
            'PENALTY': -5      # Anti-repeat logic
        }
        self.history = self._load_history()
        self.api_failures = 0

    def _load_history(self) -> List[Dict]:
        """Load historical data from persistent database."""
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Seed data if no database exists
        seed = [
            {"date": "02-01-2026", "number": "16"},
            {"date": "30-12-2025", "number": "59"},
            {"date": "16-12-2025", "number": "52"},
            {"date": "01-12-2025", "number": "22"},
            {"date": "16-11-2025", "number": "38"},
            {"date": "01-11-2025", "number": "87"},
            {"date": "17-01-2025", "number": "61"},
            {"date": "17-01-2024", "number": "47"},
            {"date": "17-01-2023", "number": "92"},
            {"date": "17-01-2022", "number": "15"},
            {"date": "17-01-2021", "number": "68"},
        ]
        
        try:
            os.makedirs("data", exist_ok=True)
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(seed, f, indent=2)
        except IOError:
            pass
            
        return seed

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def fetch_latest_draw(_self):
        """Fetches data from GLO API with caching to optimize performance."""
        try:
            response = requests.get(API_ENDPOINT, timeout=8)
            if response.status_code != 200:
                _self.api_failures += 1
                return {"date": "Unknown", "number": "N/A", "status": "Offline"}
                
            data = response.json()
            raw_date = data['response']['date']
            result_2d = data['response']['runningNumbers'][0]['number'][0]
            
            # Try parsing multiple date formats
            dt = None
            for fmt in ["%d %B %Y", "%d %b %Y"]:
                try:
                    dt = datetime.strptime(raw_date, fmt)
                    break
                except ValueError:
                    continue
            
            if not dt:
                return {"date": raw_date, "number": result_2d, "status": "Online"}
            
            fmt_date = dt.strftime("%d-%m-%Y")
            
            # Update history if new
            if not any(d['date'] == fmt_date for d in _self.history):
                _self.history.insert(0, {"date": fmt_date, "number": result_2d})
                try:
                    with open(DB_FILE, 'w', encoding='utf-8') as f:
                        json.dump(_self.history, f, indent=2)
                except IOError:
                    pass
            
            return {
                "date": raw_date,
                "number": result_2d,
                "status": "Online"
            }
        except Exception as e:
            _self.api_failures += 1
            return {"date": "Error", "number": "N/A", "status": "Offline"}

    def get_next_draw_context(self) -> Tuple[datetime, List[str]]:
        """
        Calculates the next draw date and cultural bias numbers.
        Handles Thai GLO special dates (Teacher's Day, Labour Day).
        """
        today = datetime.now()
        year, month = today.year, today.month
        
        # Determine next draw date
        if today.day > 16:
            month += 1
            if month > 12:
                month = 1
                year += 1
            day = 1
        else:
            day = 16
            
        # Apply holiday exceptions
        if month == 1 and day == 16:
            day = 17  # Teacher's Day shift
        elif month == 5 and day == 1:
            day = 2   # Labour Day shift
            
        next_date = datetime(year, month, day)
        
        # Build cultural bias set
        bias_nums = []
        
        if month == 1 and day == 17:
            bias_nums.extend(["16", "17", "61", "95", "97"])
        elif month == 5 and day == 2:
            bias_nums.extend(["01", "02", "05"])
            
        # Year-based numbers
        year_str = str(year)[-2:]
        bias_nums.extend([year_str, "96"])
        
        return next_date, list(set(bias_nums))

    def run_advanced_algorithm(self, target_date: datetime, cultural_bias: List[str]) -> List[Tuple[str, int, List[str]]]:
        """
        Advanced multi-factor scoring algorithm.
        Combines cultural patterns, seasonal statistics, and recent trends.
        """
        target_month = str(target_date.month).zfill(2)
        
        scores = Counter()
        evidence = defaultdict(list)
        
        # Factor 1: Cultural/Event-based scoring (Weight: 5)
        for num in cultural_bias:
            scores[num] += self.weights['CULTURE']
            evidence[num].append("Cultural Pattern")
        
        # Factor 2: Seasonal analysis - same month across years (Weight: 3)
        seasonal_nums = [d['number'] for d in self.history 
                        if d['date'].split('-')[1] == target_month]
        
        for num in seasonal_nums:
            scores[num] += self.weights['SEASONAL']
            evidence[num].append("Seasonal Match")
        
        # Factor 3: Recent trend - last 20 draws (Weight: 1)
        if len(self.history) >= 20:
            recent_nums = [d['number'] for d in self.history[:20]]
        else:
            recent_nums = [d['number'] for d in self.history]
            
        for num in recent_nums:
            scores[num] += self.weights['RECENT']
            evidence[num].append("Recent Trend")
        
        # Factor 4: Anti-repeat penalty
        if self.history:
            latest = self.history[0]['number']
            if latest in scores:
                scores[latest] += self.weights['PENALTY']
                evidence[latest].append("⚠️ Repeat Risk")
        
        # Sort and format results
        ranked = scores.most_common(5)
        results = []
        for num, score in ranked:
            results.append((num, score, evidence[num]))
        
        return results

# --- UI IMPLEMENTATION ---
def main():
    analyzer = LottoAnalyzer()
    
    # Header
    st.markdown('<div class="main-title">🔮 Satayu Intersection Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Statistical & Cultural Bias Integration Model</div>', unsafe_allow_html=True)

    # Status Bar
    latest_data = analyzer.fetch_latest_draw()
    
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        st.markdown(f'<div class="metric-box">📅 <b>Latest Draw</b><br>{latest_data["date"]}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-box">🏆 <b>Result (2-Tail)</b><br><span style="color:{THEME_COLOR}; font-weight:bold; font-size:1.2em">{latest_data["number"]}</span></div>', unsafe_allow_html=True)
    with c3:
        status_color = "green" if latest_data["status"] == "Online" else "red"
        st.markdown(f'<div class="metric-box" style="border-left: 5px solid {status_color}">📡<br>{latest_data["status"]}</div>', unsafe_allow_html=True)

    st.write("---")

    # Control Panel
    with st.container():
        col_btn, col_opts = st.columns([1, 2])
        
        with col_opts:
            dev_mode = st.toggle("Developer Mode (Show Logic)", value=False)
            
        with col_btn:
            run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Calculating Intersection Matrix..."):
            # 1. Get next draw context
            target_date, cultural_bias = analyzer.get_next_draw_context()
            
            # 2. Run advanced algorithm
            top_picks = analyzer.run_advanced_algorithm(target_date, cultural_bias)
            winner = top_picks[0]

            # 3. Display Winner
            st.markdown(f"""
                <div class="prediction-card">
                    <div style="font-size: 1.2rem; opacity: 0.9;">✨ Highest Probability Target</div>
                    <div style="font-size: 4.5rem; font-weight: 800; line-height: 1.2;">{winner[0]}</div>
                    <div style="font-size: 0.9rem; background: rgba(0,0,0,0.2); display: inline-block; padding: 5px 15px; border-radius: 20px;">
                        Confidence Score: {winner[1]} | {target_date.strftime('%d-%m-%Y')}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # 4. Display Table
            st.markdown("### 📊 Top 5 Candidates (Evidence-Based)")
            
            # Create detailed DataFrame
            df_display = pd.DataFrame([
                {
                    "Rank": f"#{i+1}",
                    "Number": num,
                    "Score": score,
                    "Evidence": ", ".join(reasons)
                }
                for i, (num, score, reasons) in enumerate(top_picks)
            ])
            
            st.dataframe(
                df_display,
                column_config={
                    "Score": st.column_config.ProgressColumn(
                        "Algorithmic Score",
                        format="%d",
                        min_value=min(x[1] for x in top_picks) if top_picks else 0,
                        max_value=max(x[1] for x in top_picks) if top_picks else 10,
                    ),
                },
                use_container_width=True,
                hide_index=True
            )

            # 5. Dev Mode (Human Touch)
            if dev_mode:
                st.info(f"""👨‍💻 **Debug Info:**
- Target Draw: {target_date.strftime('%d %B %Y')}
- Penalized Number: {latest_data['number']}
- Cultural Bias Set: {cultural_bias}
- Historical Records: {len(analyzer.history)} draws
- Algorithm: Multi-Factor v2.0 (CLI Engine)
- Weights: Culture={analyzer.weights['CULTURE']}, Seasonal={analyzer.weights['SEASONAL']}, Recent={analyzer.weights['RECENT']}
                """)

if __name__ == "__main__":
    main()
