import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE MOBİL UYUM (PWA) - YÜKSEK OKUNURLUK
# =================================================================
st.set_page_config(page_title="Borsa Robotu Master V7", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #111418 !important; border-right: 2px solid #3b82f6; }
        
        /* Sidebar Yazıları Cam Gibi Net */
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { 
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1rem !important;
        }
        
        /* BİLANÇO KARTLARI - YÜKSEK OKUNURLUK AYARI */
        .bilanco-card {
            background: #1e293b; padding: 18px; border-radius: 12px; 
            border-left: 6px solid #3b82f6; margin-bottom: 12px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        }
        .bilanco-text {
            color: #E2E8F0 !important; font-size: 1rem !important; font-weight: 600 !important;
            line-height: 1.5;
        }

        /* KAYDET BUTONU - HER ZAMAN GÖRÜNÜR VE PARLAK */
        .stButton>button {
            background-color: #00D4FF !important; color: #000000 !important;
            font-weight: 900 !important; border-radius: 10px !important; 
            height: 60px !important; width: 100% !important;
            border: 3px solid #FFFFFF !important; font-size: 1.2rem !important;
            box-shadow: 0px 4px 15px rgba(0, 212, 255, 0.4);
        }
        
        /* GİRİŞ KUTULARI */
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
            color: #000000 !important; background-color: #FFFFFF !important; font-weight: bold !important;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. VERİ SAKLAMA MİMARİSİ
# =================================================================
class ProductionDB:
    def __init__(self, db_name="borsa_v7_final_pro.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def get_user_space(self, key):
        safe_key = "".join(filter(str.isalnum, key))
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS u_{safe_key} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return f"u_{safe_key}"

    def save(self, table, s, q, c, t, stp):
        with self.conn:
            self.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (s, q, c, t, stp))

    def get_all(self, table):
        try: return pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
        except: return pd.DataFrame()

    def delete(self, table, s):
        with self.conn: self.conn.execute(f"DELETE FROM {table} WHERE symbol = ?", (s,))

# =================================================================
# 3. ANALİZ VE TERCÜME MOTORU
# =================================================================
class MasterEngine:
    @staticmethod
    def get_data(symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None
            # Teknik Veriler
            df['SMA50'] = df['Close'].rolling(50).mean()
            delta = df['Close'].diff()
            g = delta.where(delta > 0, 0).rolling(14).mean()
            l = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g / (l + 1e-9))))
            df['MB'] = df['Close'].rolling(20).mean()
            df['UB'] = df['MB'] + (df['Close'].rolling(20).std() * 2)
            df['LB'] = df['MB'] - (df['Close'].rolling(20).std() * 2)
            
            info = t.info
            fin = {
                "ad": info.get("longName", "Bilinmiyor"),
                "fk": info.get("trailingPE", "N/A"),
                "pddd": info.get("priceToBook", "N/A"),
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100
            }
            return df, fin
        except: return None, None

    @staticmethod
    def ai_predict(df):
        y = df['Close'].values[-100:]
        x = np.arange(len(y)).reshape(-1, 1)
        m = LinearRegression().fit(x, y)
        f = np.array([len(y) + i for i in range(5)]).reshape(-1, 1)
        return m.predict(f)

# =================================================================
# 4. ANA PROGRAM
# =================================================================
def main():
    db = ProductionDB()
    eng = MasterEngine()

    st.sidebar.title("🔑 Güvenli Giriş")
    user_key = st.sidebar.text_input("Kişisel Şifreniz:", type="password", help="Bu şifre size özel kasanızı açar.")
    
    if not user_key:
        st.info("👋 Hoş geldin öğretmenim! Arkadaşınızla beraber kullanmaya başlamak için lütfen sol tarafa size özel bir şifre girin.")
        return

    table = db.get_user_space(user_key)

    st.sidebar.divider()
    st.sidebar.subheader("➕ Hisse Ekle")
    s_in = st.sidebar.text_input("Kod (Örn: ESEN)").upper().strip()
    q_in = st.sidebar.number_input("Adet", min_value=0.0)
    c_in = st.sidebar.number_input("Maliyet", min_value=0.0)
    t_in = st.sidebar.number_input("Hedef", min_value=0.0)
    st_in = st.sidebar.number_input("Stop", min_value=0.0)
    
    # DEV KAYDET BUTONU
    if st.sidebar.button("VERİLERİ SİSTEME KAYDET"):
        if s_in:
            sc = s_in + ".IS" if not s_in.endswith(".IS") else s_in
            db.save(table, sc, q_in, c_in, t_in, st_in)
            st.sidebar.success(f"{s_in} Kaydedildi!")
            st.rerun()

    p_df = db.get_all(table)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu Master V7")
        active = st.selectbox("Analiz Edilecek Varlık:", p_df['symbol'].tolist())
        df, fin = eng.get_data(active)
        
        if df is not None:
            pred = eng.ai_predict(df)
            
            # --- ÜST PANEL ---
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""<div style="background:#1e3a8a; padding:20px; border-radius:15px; border:2px solid #60a5fa;">
                    <h3 style="color:white; margin:0;">🧠 AI Fiyat Tahmini (5 Gün)</h3>
                    <h1 style="color:#00D4FF; margin:0;">{pred[0]:.2f} ➔ {pred[-1]:.2f} TL</h1>
                </div>""", unsafe_allow_html=True)
            
            with col2:
                st.subheader("📋 Bilanço Özet Karnesi")
                # Dinamik Yorumlar
                c_status = "🟢" if fin['cari'] > 1.5 else "🟡" if fin['cari'] > 1 else "🔴"
                k_status = "🟢" if fin['oz_kar'] > 20 else "🟡" if fin['oz_kar'] > 0 else "🔴"
                
                st.markdown(f"""<div class='bilanco-card'><p class='bilanco-text'>{c_status} <b>Borç Ödeme:</b> Şirketin cari oranı {fin['cari']:.2f}. Borçlarını ödeme kabiliyeti { 'güçlü.' if fin['cari']>1.5 else 'takip edilmeli.' }</p></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class='bilanco-card'><p class='bilanco-text'>{k_status} <b>Karlılık:</b> Özsermaye karlılığı %{fin['oz_kar']:.1f}. Şirket sermayesini { 'verimli kullanıyor.' if fin['oz_kar']>20 else 'normal düzeyde kullanıyor.' }</p></div>""", unsafe_allow_html=True)

            # --- GRAFİK ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=('Fiyat & Bollinger & Trend', 'RSI Güç Endeksi'), row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['UB'], line=dict(color='rgba(255,255,255,0.2)'), name="Üst Bant"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['LB'], line=dict(color='rgba(255,255,255,0.2)'), name="Alt Bant", fill='tonexty'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold', width=2), name="Trend"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
            fig.update_layout(height=750, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- SİLME VE METRİKLER ---
            c_last, c_del = st.columns([4, 1])
            c_last.metric("Güncel Fiyat", f"{df['Close'].iloc[-1]:.2f} TL")
            if c_del.button(f"🗑️ {active.split('.')[0]} SİL"):
                db.delete(table, active); st.rerun()

    else:
        st.info("👈 Başlamak için şifrenizi girin ve sol taraftan ilk hissenizi kaydedin.")

if __name__ == "__main__":
    main()
