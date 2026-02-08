import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE OKUNURLUK (HIGH-CONTRAST)
# =================================================================
st.set_page_config(page_title="Borsa Robotu Master V8", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 3px solid #00D4FF; }
        section[data-testid="stSidebar"] .stMarkdown p, 
        section[data-testid="stSidebar"] label { 
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important;
            text-shadow: 2px 2px 4px #000000;
        }
        .status-card { padding: 20px; border-radius: 15px; margin-bottom: 15px; border-left: 10px solid; }
        .olumlu { background-color: #064e3b; border-color: #10b981; color: white; }
        .olumsuz { background-color: #7f1d1d; border-color: #ef4444; color: white; }
        .notur { background-color: #1e293b; border-color: #94a3b8; color: white; }
        .stButton>button {
            background-color: #00D4FF !important; color: black !important;
            font-weight: 900 !important; border-radius: 12px !important; height: 55px; width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. VERİ VE ANALİZ MOTORLARI
# =================================================================
class MasterEngine:
    @staticmethod
    def get_user_db(key):
        safe_key = "".join(filter(str.isalnum, key))
        conn = sqlite3.connect("master_v8.db", check_same_thread=False)
        conn.execute(f"CREATE TABLE IF NOT EXISTS u_{safe_key} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return conn, f"u_{safe_key}"

    @staticmethod
    @st.cache_data(ttl=300)
    def fetch_full_data(symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None
            
            # --- 6 İNDİKATÖR HESAPLAMA ---
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            # Bollinger
            df['MB'] = df['Close'].rolling(20).mean()
            df['UB'] = df['MB'] + (df['Close'].rolling(20).std() * 2)
            df['LB'] = df['MB'] - (df['Close'].rolling(20).std() * 2)
            # RSI
            delta = df['Close'].diff()
            g = delta.where(delta > 0, 0).rolling(14).mean()
            l = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g / (l + 1e-9))))
            # MACD
            e1 = df['Close'].ewm(span=12, adjust=False).mean()
            e2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = e1 - e2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            info = t.info
            fin = {
                "net_kar": info.get("netIncomeToCommon", 0),
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", "N/A"),
                "pddd": info.get("priceToBook", "N/A")
            }
            return df, fin
        except: return None, None

# =================================================================
# 3. ANA ARAYÜZ
# =================================================================
def main():
    engine = MasterEngine()
    st.sidebar.title("🔑 Giriş Anahtarı")
    user_key = st.sidebar.text_input("Şifre:", type="password")
    
    if not user_key:
        st.info("👋 Hoş geldin öğretmenim! Önce şifreni girerek kasanı aç.")
        return

    conn, table = engine.get_user_db(user_key)

    # Hisse Ekleme
    st.sidebar.divider()
    with st.sidebar:
        raw_s = st.text_input("Hisse Kodu (esen, sasa):").strip().upper()
        q_in = st.number_input("Adet", 0.0)
        c_in = st.number_input("Maliyet", 0.0)
        t_in = st.number_input("Hedef", 0.0)
        s_in = st.number_input("Stop", 0.0)
        if st.button("KAYDET"):
            if raw_s:
                sc = raw_s if raw_s.endswith(".IS") else f"{raw_s}.IS"
                conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (sc, q_in, c_in, t_in, s_in))
                conn.commit(); st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu Master V8")
        selected = st.selectbox("Analiz Edilecek Varlık:", ["Seçiniz..."] + p_df['symbol'].tolist())
        
        if selected != "Seçiniz...":
            df, fin = engine.fetch_full_data(selected)
            if df is not None:
                # --- AI TAHMİN ---
                y = df['Close'].values[-60:]
                model = LinearRegression().fit(np.arange(len(y)).reshape(-1,1), y)
                f_val = model.predict([[len(y)+5]])[0]
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""<div class="status-card notur"><h3>🧠 AI TAHMİNİ (5 GÜN)</h3><h1>{df['Close'].iloc[-1]:.2f} ➔ {f_val:.2f} TL</h1></div>""", unsafe_allow_html=True)
                with c2:
                    st_cls = "olumlu" if fin['cari'] > 1.2 else "olumsuz"
                    st.markdown(f"""<div class="status-card {st_cls}"><h3>🔍 MÜFETTİŞ NOTU</h3><p>Borç Ödeme: {fin['cari']:.2f}<br>Özsermaye Kar: %{fin['oz_kar']:.1f}</p></div>""", unsafe_allow_html=True)

                # --- 6 İNDİKATÖRLÜ DEV GRAFİK ---
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, 
                                   subplot_titles=('Fiyat & Bollinger & SMA', 'MACD Sinyali', 'RSI Güç'),
                                   row_heights=[0.5, 0.25, 0.25])
                
                # Katman 1: Fiyat + Bollinger + SMA
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mum"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['UB'], line=dict(color='gray', width=1), name="Bollinger Üst"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['LB'], line=dict(color='gray', width=1), name="Bollinger Alt", fill='tonexty'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold', width=2), name="SMA50"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='red', width=2), name="SMA200"), row=1, col=1)
                
                # Katman 2: MACD
                fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='cyan'), name="MACD"), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], line=dict(color='orange'), name="Sinyal"), row=2, col=1)
                
                # Katman 3: RSI
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=3, col=1)
                fig.add_hline(y=70, line_dash="dot", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dot", line_color="green", row=3, col=1)

                fig.update_layout(height=900, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # Metrikler
                m1, m2, m3 = st.columns([2, 2, 1])
                curr = df['Close'].iloc[-1]
                row = p_df[p_df['symbol'] == selected].iloc[0]
                m1.metric("Anlık", f"{curr:.2f} TL")
                m2.metric("Kâr/Zarar", f"{(curr-row['cost'])*row['qty']:,.0f} TL")
                if m3.button("🗑️ SİL"):
                    conn.execute(f"DELETE FROM {table} WHERE symbol = ?", (selected,))
                    conn.commit(); st.rerun()
    else:
        st.warning("👈 Portföyünüz boş. Sol taraftan şifre girip hisse ekleyin.")

if __name__ == "__main__": main()
