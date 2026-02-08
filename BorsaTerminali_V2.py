import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression
from datetime import datetime

# =================================================================
# 1. GÜVENLİK VE MOBİL UYUMLULUK AYARLARI (PWA DESTEĞİ)
# =================================================================
st.set_page_config(
    page_title="Borsa Robotu AI",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Telefonlar için otomatik "Ana Ekrana Ekle" isimlendirmesi ve tam ekran modu
st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="Borsa Robotu">
        <meta name="application-name" content="Borsa Robotu">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    </head>
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #111418 !important; border-right: 1px solid #2d333b; }
        section[data-testid="stSidebar"] h1, h2, h3, label, p { color: #FFFFFF !important; font-weight: 800 !important; }
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
            color: #000000 !important; background-color: #FFFFFF !important; font-weight: bold !important; border-radius: 10px;
        }
        .ai-card { 
            background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); 
            padding: 25px; border-radius: 15px; border: 2px solid #3b82f6; margin-bottom: 25px; 
        }
        .stButton>button { 
            background-color: #00D4FF !important; color: black !important; 
            font-weight: bold !important; border-radius: 12px !important; 
            width: 100%; height: 55px; transition: 0.3s;
        }
        .stButton>button:hover { transform: scale(1.02); background-color: #FFFFFF !important; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. VERİTABANI YÖNETİMİ (KİŞİYE ÖZEL YEREL DEPOLAMA)
# =================================================================
class ProductionDB:
    def __init__(self, db_name="borsa_robotu_v6_final.db"):
        try:
            self.conn = sqlite3.connect(db_name, check_same_thread=False)
            self._init_schema()
        except Exception as e:
            st.error(f"Veritabanı bağlantı hatası: {e}")

    def _init_schema(self):
        with self.conn:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS my_portfolio 
                (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)""")

    def save_stock(self, s, q, c, t, stop):
        try:
            with self.conn:
                self.conn.execute("INSERT OR REPLACE INTO my_portfolio VALUES (?,?,?,?,?)", (s, q, c, t, stop))
        except Exception as e:
            st.error(f"Kayıt hatası: {e}")

    def get_portfolio(self):
        return pd.read_sql_query("SELECT * FROM my_portfolio", self.conn)

    def delete_stock(self, s):
        with self.conn:
            self.conn.execute("DELETE FROM my_portfolio WHERE symbol = ?", (s,))

# =================================================================
# 3. ANALİZ VE YAPAY ZEKA MOTORU
# =================================================================
class AnalysisEngine:
    @staticmethod
    def get_indicators(df):
        """Bollinger Bantları, MACD, RSI ve SMA50 hesaplar."""
        try:
            # RSI 14
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))

            # MACD (12, 26, 9)
            df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = df['EMA12'] - df['EMA26']
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

            # Bollinger Bantları (20, 2)
            df['MA20'] = df['Close'].rolling(20).mean()
            df['STD20'] = df['Close'].rolling(20).std()
            df['Upper'] = df['MA20'] + (df['STD20'] * 2)
            df['Lower'] = df['MA20'] - (df['STD20'] * 2)
            
            # Trend SMA 50
            df['SMA_50'] = df['Close'].rolling(50).mean()
            return df
        except Exception as e:
            st.error(f"İndikatör hatası: {e}")
            return df

    @staticmethod
    def ai_forecast(df, days=5):
        """Lineer Regresyon ile fiyat trend tahmini yapar."""
        try:
            clean_df = df.dropna()
            y = clean_df['Close'].values
            X = np.arange(len(y)).reshape(-1, 1)
            
            model = LinearRegression().fit(X, y)
            future_X = np.array([len(y) + i for i in range(days)]).reshape(-1, 1)
            return model.predict(future_X)
        except Exception:
            return None

# =================================================================
# 4. ANA PROGRAM DÖNGÜSÜ
# =================================================================
def main():
    db = ProductionDB()
    engine = AnalysisEngine()

    st.title("🛡️ Borsa Robotu AI | Stratejik Karar Üssü")

    # SOL PANEL (SIDEBAR)
    with st.sidebar:
        st.header("💼 Portföy Yönetimi")
        with st.form("add_stock_form", clear_on_submit=True):
            s_raw = st.text_input("Hisse Kodu (Örn: ESEN)").upper().strip()
            q_val = st.number_input("Adet", min_value=0.0, step=1.0)
            c_val = st.number_input("Maliyet (TL)", min_value=0.0, step=0.01)
            t_val = st.number_input("Hedef Fiyat (Kâr)", min_value=0.0, step=0.1)
            stop_val = st.number_input("Stop Seviyesi (Zarar)", min_value=0.0, step=0.1)
            
            if st.form_submit_button("SİSTEME KAYDET"):
                if s_raw:
                    s_code = s_raw + ".IS" if not s_raw.endswith(".IS") else s_raw
                    db.save_stock(s_code, q_val, c_val, t_val, stop_val)
                    st.success(f"{s_raw} Başarıyla Eklendi!")
                    st.rerun()

        st.divider()
        st.subheader("📋 Takip Listem")
        p_df = db.get_portfolio()
        if not p_df.empty:
            for s in p_df['symbol']:
                col_n, col_d = st.columns([4, 1.2])
                col_n.info(f"**{s.replace('.IS', '')}**")
                if col_d.button("🗑️", key=f"btn_{s}"):
                    db.delete_stock(s); st.rerun()

    # ANA EKRAN ANALİZ ALANI
    if not p_df.empty:
        active_s = st.selectbox("Detaylı Analiz Edilecek Hisse:", p_df['symbol'].tolist())
        
        try:
            with st.spinner('Piyasa Verileri Analiz Ediliyor...'):
                data = yf.download(active_s, period="1y", interval="1d", progress=False)
                if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
                
                data = engine.get_indicators(data)
                forecast = engine.ai_forecast(data)
                last_p = float(data['Close'].iloc[-1])
                stock_info = p_df[p_df['symbol'] == active_s].iloc[0]

                # --- AI TAHMİN KARTI ---
                st.markdown(f"""<div class="ai-card">
                    <h2 style='margin:0;
