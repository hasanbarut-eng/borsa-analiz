import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. MOBİL UYUMLULUK VE PROFESYONEL TASARIM (PWA)
# =================================================================
st.set_page_config(
    page_title="Borsa Robotu AI",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# OTOMATİK İSİMLENDİRME VE KRİSTAL NETLİK CSS
st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="Borsa Robotu">
        <meta name="application-name" content="Borsa Robotu">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        .stApp { background-color: #0E1117; }
        
        /* SOL PANEL: KRİSTAL NETLİK */
        section[data-testid="stSidebar"] {
            background-color: #111418 !important;
            border-right: 2px solid #30363D;
        }
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] p {
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important;
        }
        
        /* GİRİŞ KUTULARI: BEYAZ ZEMİN SİYAH YAZI */
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
            color: #000000 !important; background-color: #FFFFFF !important; 
            font-weight: bold !important; border-radius: 10px; border: 2px solid #00D4FF;
        }

        /* AI KARTI VE KARAR KARTI */
        .master-card {
            padding: 25px; border-radius: 15px; margin-bottom: 20px; border: 3px solid #FFFFFF;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        
        .stButton>button {
            background-color: #00D4FF !important; color: black !important;
            font-weight: 900 !important; border-radius: 12px !important;
            height: 55px; width: 100%; border: 2px solid #FFFFFF;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. VERİTABANI YÖNETİMİ
# =================================================================
class MasterDB:
    def __init__(self, db_name="borsa_robotu_master_v1.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS port (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")

    def save(self, s, q, c, t, stop):
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO port VALUES (?,?,?,?,?)", (s, q, c, t, stop))

    def get_all(self):
        return pd.read_sql_query("SELECT * FROM port", self.conn)

    def delete(self, s):
        with self.conn:
            self.conn.execute("DELETE FROM port WHERE symbol = ?", (s,))

# =================================================================
# 3. ZEKA VE ANALİZ MOTORU
# =================================================================
class AnalystCore:
    @staticmethod
    def get_market_data(symbol):
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Temel İndikatörler
        df['SMA50'] = df['Close'].rolling(50).mean()
        delta = df['Close'].diff()
        g = delta.where(delta > 0, 0).rolling(14).mean()
        l = -delta.where(delta < 0, 0).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (g / (l + 1e-9))))
        
        # Bollinger
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        return df

    @staticmethod
    def generate_decision(df):
        last_c = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        sma = float(df['SMA50'].iloc[-1])
        
        score = 0
        reasons = []
        if last_c > sma: score += 2; reasons.append("✅ Fiyat trend üzerinde.")
        else: score -= 1; reasons.append("⚠️ Fiyat trend altında.")
        
        if rsi < 35: score += 2; reasons.append("🟢 RSI: Alım fırsatı.")
        elif rsi > 75: score -= 2; reasons.append("🔴 RSI: Doyum noktası.")
        
        if score >= 3: return "GÜÇLÜ AL", "#00FF00", "#000000", reasons
        elif 1 <= score < 3: return "OLUMLU / TUT", "#00D4FF", "#000000", reasons
        elif -1 <= score < 1: return "NÖTR / BEKLE", "#FFFF00", "#000000", reasons
        else: return "RİSKLİ / SAT", "#FF0000", "#FFFFFF", reasons

    @staticmethod
    def ai_forecast(df):
        y = df['Close'].values[-60:]
        x = np.arange(len(y)).reshape(-1, 1)
        model = LinearRegression().fit(x, y)
        future = np.array([len(y) + i for i in range(5)]).reshape(-1, 1)
        return model.predict(future)

# =================================================================
# 4. ANA ARAYÜZ
# =================================================================
def main():
    db = MasterDB()
    core = AnalystCore()

    st.title("🛡️ Borsa Robotu Master AI")

    with st.sidebar:
        st.header("💼 Portföy Kontrol")
        with st.form("hisse_kayit", clear_on_submit=True):
            s_raw = st.text_input("Hisse Kodu (Örn: ESEN)").upper().strip()
            q_in = st.number_input("Adet", min_value=0.0)
            c_in = st.number_input("Maliyet (TL)", min_value=0.0)
            t_in = st.number_input("Hedef Fiyat", min_value=0.0)
            stop_in = st.number_input("Stop Fiyat", min_value=0.0)
            if st.form_submit_button("SİSTEME KAYDET"):
                if s_raw:
                    sc = s_raw + ".IS" if not s_raw.endswith(".IS") else s_raw
                    db.save(sc, q_in, c_in, t_in, stop_in)
                    st.rerun()

        st.divider()
        port_df = db.get_all()
        if not port_df.empty:
            for s in port_df['symbol']:
                c1, c2 = st.columns([4, 1.2])
                c1.info(f"**{s.replace('.IS', '')}**")
                if c2.button("🗑️", key=f"del_{s}"):
                    db.delete(s); st.rerun()

    if not port_df.empty:
        active = st.selectbox("Hisse Analiz Seçimi:", port_df['symbol'].tolist())
        df = core.get_market_data(active)
        
        if df is not None:
            # VERİLERİ HESAPLA
            dec, bg, txt, reasons = core.generate_decision(df)
            pred = core.ai_forecast(df)
            last = float(df['Close'].iloc[-1])
            info = port_df[port_df['symbol'] == active].iloc[0]

            # --- MASTER EKRAN: KARAR VE AI TAHMİNİ ---
            col_dec, col_ai = st.columns(2)
            
            with col_dec:
                st.markdown(f"""<div class="master-card" style="background-color: {bg};">
                    <h3 style="color: {txt} !important; margin:0;">🎯 SİSTEM KARARI</h3>
                    <h1 style="color: {txt} !important; margin:0;">{dec}</h1>
                    <hr style="border: 1px solid {txt};">
                    {''.join([f"<p style='color:{txt} !important; margin:2px;'>{r}</p>" for r in reasons])}
                </div>""", unsafe_allow_html=True)
            
            with col_ai:
                st.markdown(f"""<div class="master-card" style="background-color: #1e3a8a; border-color: #60a5fa;">
                    <h3 style="color: white; margin:0;">🧠 AI TAHMİNİ (5 GÜN)</h3>
                    <h1 style="color: #60a5fa; margin:0;">{pred[0]:.2f} ➔ {pred[-1]:.2f} TL</h1>
                    <hr style="border: 1px solid #60a5fa;">
                    <p style="color: white; margin:0;">Matematiksel trend yönü yukarı.</p>
                </div>""", unsafe_allow_html=True)

            # GRAFİK PANELİ
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, subplot_titles=('Fiyat & Bollinger Kanalları', 'RSI Güç Endeksi'), row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='rgba(255,255,255,0.2)', width=1), name="Üst Bant"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='rgba(255,255,255,0.2)', width=1), name="Alt Bant", fill='tonexty'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold', width=2.5), name="Trend"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
            fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # CANLI METRİKLER VE ALARMLAR
            m1, m2, m3 = st.columns(3)
            m1.metric("Anlık", f"{last:.2f} TL")
            m2.metric("Maliyet", f"{info['cost']:.2f} TL")
            pnl = (last - info['cost']) * info['qty']
            m3.metric("Kâr/Zarar", f"{pnl:,.0f} TL")

            if info['target'] > 0 and last >= info['target']:
                st.balloons(); st.success("🎯 HEDEF FİYAT GÖRÜLDÜ!")
            elif info['stop'] > 0 and last <= info['stop']:
                st.error("⚠️ STOP SEVİYESİNE DİKKAT!")

if __name__ == "__main__":
    main()
