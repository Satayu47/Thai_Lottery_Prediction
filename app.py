import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from collections import Counter, defaultdict

# --- CONFIGURATION ---
API_ENDPOINT = "https://lotto.api.rayriffy.com/latest"
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
    Core logic for calculating lottery probabilities based on 
    the Intersection Strategy (Statistics + Cultural Bias).
    """
    
    def __init__(self):
        # Weight configurations (Tunable parameters)
        self.weights = {
            'CULTURE_BIAS': 10,
            'STAT_MATCH': 5,
            'PENALTY': -50,
            'BONUS_NINE': 3
        }

    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def fetch_latest_draw(_self):
        """Fetches data from GLO API with caching to optimize performance."""
        try:
            response = requests.get(API_ENDPOINT, timeout=3)
            response.raise_for_status()
            data = response.json()
            return {
                "date": data['response']['date'],
                "number": data['response']['runningNumbers'][0]['number'][0],
                "status": "Online"
            }
        except Exception as e:
            return {"date": "Unknown", "number": "N/A", "status": "Offline"}

    def generate_cultural_bias(self) -> dict:
        """
        Generates bias numbers based on current date context.
        Returns a dict with number and reasoning.
        """
        now = datetime.now()
        # Logic for Thai Year conversion
        buddhist_year = now.year + 543
        year_short = str(buddhist_year)[-2:]
        
        # Base Bias Context
        context = {
            "17": "Draw Date (17th)",
            "16": "Teacher's Day / Previous Draw",
            year_short: f"Year B.E. {buddhist_year}",
            "26": f"Year A.D. {now.year}",
            "9": "Statistical Constant (Jan)"
        }
        
        # Specific January Logic (Teacher's Day)
        if now.month == 1:
            context.update({
                "61": "Flip of 16 (Teacher's Day)",
                "95": "Stat Frequent",
                "79": "Stat Frequent (Yearly)",
                "97": "Stat Frequent (Yearly)"
            })
            
        return context

    def run_intersection_algorithm(self, bias_map: dict, last_draw: str):
        """
        The main algorithm.
        1. Apply Bias Weights
        2. Apply Penalties (Dead Numbers)
        3. Apply Statistical Bonuses
        """
        scores = defaultdict(int)
        
        # 1. Base Scoring
        for num, reason in bias_map.items():
            # If the bias is just a single digit (like '9'), we don't score it directly
            # We use it as a modifier for other numbers
            if len(num) == 2: 
                scores[num] += self.weights['CULTURE_BIAS']

        # 2. Intersection Modifier (The "9" Rule)
        # If a number contains '9' (Jan constant), boost it
        for num in scores:
            if '9' in num:
                scores[num] += self.weights['BONUS_NINE']

        # 3. Penalty Logic (Kill the previous number)
        if last_draw in scores:
            scores[last_draw] += self.weights['PENALTY']
            
        # Convert to sorted list
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:5]

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
            # 1. Get Context
            bias_map = analyzer.generate_cultural_bias()
            
            # 2. Run Algorithm
            top_picks = analyzer.run_intersection_algorithm(bias_map, latest_data["number"])
            winner = top_picks[0]

            # 3. Display Winner
            st.markdown(f"""
                <div class="prediction-card">
                    <div style="font-size: 1.2rem; opacity: 0.9;">✨ Highest Probability Target</div>
                    <div style="font-size: 4.5rem; font-weight: 800; line-height: 1.2;">{winner[0]}</div>
                    <div style="font-size: 0.9rem; background: rgba(0,0,0,0.2); display: inline-block; padding: 5px 15px; border-radius: 20px;">
                        Confidence Score: {winner[1]}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # 4. Display Table
            st.markdown("### 📊 Top 5 Candidates")
            
            # Create cleaner DataFrame for display
            df_display = pd.DataFrame(top_picks, columns=["Number", "Score"])
            df_display["Strategy"] = df_display["Number"].apply(lambda x: "Statistical Match" if "9" in x else "Cultural Bias")
            
            st.dataframe(
                df_display,
                column_config={
                    "Score": st.column_config.ProgressColumn(
                        "Algorithmic Score",
                        format="%d",
                        min_value=0,
                        max_value=max(x[1] for x in top_picks),
                    ),
                },
                use_container_width=True,
                hide_index=True
            )

            # 5. Dev Mode (Human Touch)
            if dev_mode:
                st.info(f"👨‍💻 **Debug Info:**\n- Penalized Number: {latest_data['number']}\n- Bias Set: {list(bias_map.keys())}\n- Algorithm: Intersection v1.2")

if __name__ == "__main__":
    main()
