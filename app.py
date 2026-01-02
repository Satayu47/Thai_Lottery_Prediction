import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from collections import Counter

# --- CONFIGURATION ---
API_BASE = "https://lotto.api.rayriffy.com/lotto"
API_LATEST = "https://lotto.api.rayriffy.com/latest"

st.set_page_config(
    page_title="Satayu Ultimate Engine",
    page_icon="🧬",
    layout="centered"
)

# --- ENGINE: REAL-TIME MINER ---
def get_target_date():
    """Auto-detects the next draw date based on today."""
    now = datetime.now()
    
    # Logic: ถ้าวันนี้ยังไม่ถึงวันที่ 16 ให้เล็งเป้าไปที่งวดกลางเดือน
    if now.day <= 16:
        day = 17 if now.month == 1 else 16  # ถ้าเดือน 1 เป็นวันที่ 17 (วันครู)
        return datetime(now.year, now.month, day)
    else:
        # ถ้าเลยวันที่ 16 แล้ว ให้เล็งเป้าไปที่งวดต้นเดือนหน้า
        m = now.month + 1 if now.month < 12 else 1
        y = now.year + 1 if now.month == 12 else now.year
        return datetime(y, m, 1)

def mine_historical_data(target_month, target_day):
    """
    MINING: เชื่อมต่อ API ดึงผลย้อนหลัง 10 ปี ของวันที่เป้าหมาย (เช่น 17 ม.ค.)
    """
    history = []
    current_year = datetime.now().year
    
    # Progress Bar UI
    progress_text = f"📡 Mining Data: เจาะเวลาหาผล {target_day}/{target_month} ย้อนหลัง 10 ปี..."
    my_bar = st.progress(0, text=progress_text)
    
    years_range = range(current_year - 10, current_year)
    total_steps = len(years_range)
    
    for i, year in enumerate(years_range):
        # Update UI
        my_bar.progress(int((i / total_steps) * 100))
        
        # ยิง Request ไปที่ API
        url = f"{API_BASE}/{year}-{target_month:02d}-{target_day:02d}"
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if 'response' in data and 'runningNumbers' in data['response']:
                    # ดึงเลขท้าย 2 ตัว
                    num = data['response']['runningNumbers'][0]['number'][0]
                    history.append({"Year": year, "Number": num})
        except:
            continue  # ถ้าปีไหนไม่มีข้อมูล (เช่น หวยงด) ให้ข้าม
            
    my_bar.empty()
    return history

def get_latest_draw_penalty():
    """ดึงเลขที่เพิ่งออกล่าสุด (เพื่อเอามาทำ Penalty)"""
    try:
        r = requests.get(API_LATEST, timeout=2)
        data = r.json()
        return data['response']['runningNumbers'][0]['number'][0]
    except:
        return None

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

st.title("🧬 Satayu Ultimate Engine")
st.caption("Real-Time Data Mining + Thai Cultural Logic Intersection")

# แสดงเป้าหมาย (Target)
target = get_target_date()
st.info(f"🎯 Target Draw Detected: **{target.strftime('%d %B %Y')}** (ระบบตรวจจับอัตโนมัติ)")

if st.button("🚀 Run Live Analysis", type="primary"):
    
    # --- STEP 1: MINING (ขุดข้อมูลจริง) ---
    with st.spinner("⏳ กำลังดึงข้อมูลจาก Server กองสลากฯ..."):
        raw_history = mine_historical_data(target.month, target.day)
        penalty_num = get_latest_draw_penalty()
    
    if not raw_history:
        st.error("❌ ไม่พบข้อมูล (Check Internet Connection)")
        st.stop()

    # แสดงหลักฐานข้อมูลดิบ (Evidence)
    st.subheader("1. Hard Evidence (สถิติของจริงที่ดึงมา)")
    df = pd.DataFrame(raw_history)
    st.dataframe(df.set_index("Year").T, use_container_width=True)

    # --- STEP 2: LOGIC PROCESSING ---
    
    # A. วิเคราะห์สถิติ (Statistical Analysis)
    numbers = [x['Number'] for x in raw_history]
    all_digits = "".join(numbers)
    # หา "เลขวิ่ง" ที่มาบ่อยที่สุดในประวัติศาสตร์วันนี้
    top_digit = Counter(all_digits).most_common(1)[0][0]
    
    # B. วิเคราะห์บริบท (Cultural Bias)
    bias_set = set()
    # 1. เลขวันที่
    bias_set.add(f"{target.day:02d}")       
    bias_set.add(f"{target.day-1:02d}")     
    # 2. เลขปี (พ.ศ./ค.ศ.)
    bias_set.add(str(target.year)[-2:])     # 26
    bias_set.add(str(target.year+543)[-2:]) # 69
    # 3. เลข Event (เฉพาะวันครู)
    if target.month == 1 and target.day == 17:
        bias_set.update(["61", "95", "19", "79"])

    # --- STEP 3: INTERSECTION SCORING ---
    scores = {}
    reasons = {}

    # Logic 1: ให้คะแนนเลขตามบริบท (+5)
    for n in bias_set:
        scores[n] = scores.get(n, 0) + 5
        reasons[n] = ["Cultural Bias"]

    # Logic 2: ให้คะแนนถ้าเลขมีส่วนประกอบของ "เลขวิ่ง" สถิติ (+3)
    # (เช่น ถ้าสถิติบอกว่าเลข 9 มาบ่อย เลข 97, 19 จะได้คะแนนเพิ่ม)
    for n in scores:
        if top_digit in n:
            scores[n] += 3
            reasons[n].append(f"Stat Match '{top_digit}'")

    # Logic 3: ให้คะแนนถ้าเลขเคยออกจริงในประวัติศาสตร์ (+5)
    for hist in raw_history:
        n = hist['Number']
        scores[n] = scores.get(n, 0) + 5
        if n not in reasons: reasons[n] = []
        reasons[n].append("History Repeat")

    # Logic 4: PENALTY (-20) **สำคัญมาก**
    # หักคะแนนเลขที่เพิ่งออกล่าสุด (เพราะโอกาสออกซ้ำยาก)
    if penalty_num and penalty_num in scores:
        scores[penalty_num] -= 20
        reasons[penalty_num].append("⛔ Penalty (Recent)")

    # --- STEP 4: RESULT DISPLAY ---
    st.subheader("2. Final Optimized Prediction")
    
    # จัดอันดับ
    top_picks = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Winner Card
    winner = top_picks[0]
    st.markdown(f"""
    <div style="background:linear-gradient(45deg, #FF4B4B, #FF9068); padding:20px; border-radius:15px; text-align:center; color:white; margin-bottom:20px; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4);">
        <div style="font-size:1rem; opacity:0.9;">✨ Best Intersection Match</div>
        <div style="font-size:4rem; font-weight:800; letter-spacing: 2px;">{winner[0]}</div>
        <div style="background:rgba(255,255,255,0.2); display:inline-block; padding:5px 15px; border-radius:20px; margin-top:5px;">
            Confidence Score: {winner[1]}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Detail Table
    table_data = []
    for num, score in top_picks:
        table_data.append({
            "Number": num,
            "Score": score,
            "Logic Sources": ", ".join(reasons.get(num, []))
        })
        
    st.table(pd.DataFrame(table_data))
    
    st.success(f"💡 **Insight:** สถิติบ่งชี้ว่าเลข **{top_digit}** ปรากฏบ่อยที่สุดในงวด {target.day}/{target.month} ย้อนหลัง 10 ปี ระบบจึงให้น้ำหนักกับเลขชุดที่มี {top_digit} ผสมอยู่")
