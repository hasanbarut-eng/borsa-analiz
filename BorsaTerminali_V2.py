import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. MOBİL UYUMLULUK VE TASARIM AYARLARI
# =================================================================
st.set_page_config(
    page_title="Borsa Robotu AI",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Telefonlar için otomatik isim (Borsa Robotu) ve tam ekran desteği
st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="Borsa Robotu">
        <meta name="application-name" content="Borsa Robotu">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #111418 !important; border-right: 1px solid #2d333b; }
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 {
            color: #FFFFFF !important; font-weight: 800 !important;
        }
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
            color: #000000 !important; background-color: #FFFFFF !important; font-weight: bold !important;
        }
        .ai-card { 
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); 
            padding: 20px; border-radius: 15px; border: 2px solid #3b82f6; margin-bottom: 20px; 
        }
        .stButton>button { 
            background-color: #00D4FF !important; color: black !important; 
            font-weight: bold !important; border-radius: 10px !important; 
            width: 100%; height: 50px;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. VERİTABANI (KİŞİYE ÖZEL GİZLİ SAKLAMA)
# =================================================================
class SecureDB:
    def __init__(self, db_name="borsa_ai_final.db"):
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
# 3. ANALİZ VE TAHMİN MOTORU
# =================================================================
class Analyst:
    @staticmethod
    def get_data(symbol):
        df = yf.download(symbol, period="1y", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Göstergeler
        df['SMA50'] = df['Close'].rolling(50).mean()
        # RSI
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
    def forecast(df):
        y = df['Close'].values[-60:] # Son 60 gün
        x = np.arange(len(y)).reshape(-1, 1)
        model = LinearRegression().fit(x, y)
        future_x = np.array([len(y) + i for i in range(5)]).reshape(-1, 1)
        return model.predict(future_x)

# =================================================================
# 4. ANA EKRAN
# =================================================================
def main():
    db = SecureDB()
    engine = Analyst()

    st.title("🛡️ Borsa Robotu AI | Stratejik Karar Üssü")

    with st.sidebar:
        st.header("💼 Portföyüm")
        with st.form("hisse_ekle", clear_on_submit=True):
            s_raw = st.text_input("Hisse Kodu (Örn: ESEN)").upper().strip()
            q_in = st.number_input("Adet", min_value=0.0)
            c_in = st.number_input("Maliyet", min_value=0.0)
            t_in = st.number_input("Hedef Fiyat", min_value=0.0)
            stop_in = st.number_input("Stop Fiyat", min_value=0.0)
            if st.form_submit_button("KAYDET"):
                if s_raw:
                    sc = s_raw + ".IS" if not s_raw.endswith(".IS") else s_raw
                    db.save(sc, q_in, c_in, t_in, stop_in)
                    st.rerun()

        st.divider()
        port_df = db.get_all()
        if not port_df.empty:
            for s in port_df['symbol']:
                col_a, col_b = st.columns([4, 1])
                col_a.write(f"🔹 {s.replace('.IS', '')}")
                if col_b.button("🗑️", key=f"del_{s}"):
                    db.delete(s); st.rerun()

    if not port_df.empty:
        active = st.selectbox("Hisse Seçin:", port_df['symbol'].tolist())
        df = engine.get_data(active)
        
        if df is not None:
            pred = engine.forecast(df)
            st.markdown(f"""<div class="ai-card">
                <h2 style='color:white; margin:0;'>🧠 AI Fiyat Öngörüsü (5 Gün)</h2>
                <h1 style='color:#60a5fa;'>{pred[0]:.2f} TL ➔ {pred[-1]:.2f} TL</h1>
            </div>""", unsafe_allow_html=True)

            # Grafik
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=('Fiyat & Bollinger', 'RSI'), row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='gray', width=1), name="Üst Bant"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='gray', width=1), name="Alt Bant", fill='tonexty'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold', width=2), name="Trend"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
            fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # Metrikler
            last = float(df['Close'].iloc[-1])
            info = port_df[port_df['symbol'] == active].iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Anlık", f"{last:.2f} TL")
            c2.metric("Maliyet", f"{info['cost']:.2f} TL")
            pnl = (last - info['cost']) * info['qty']
            c3.metric("Kâr/Zarar", f"{pnl:,.0f} TL")

if __name__ == "__main__":
    main()
