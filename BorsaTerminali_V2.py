import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE MOBİL (PWA) KONFİGÜRASYONU - ULTRA NETLİK
# =================================================================
st.set_page_config(page_title="Borsa Robotu", layout="wide", page_icon="📈")

# PWA ve Yüksek Zıtlıklı CSS (Hasan Hoca Özel)
st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="Borsa Robotu">
        <meta name="application-name" content="Borsa Robotu">
        <link rel="manifest" href="manifest.json">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 3px solid #00D4FF; }
        
        /* SOL PANEL YAZILARI */
        section[data-testid="stSidebar"] .stMarkdown p, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stSubheader { 
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important;
            text-shadow: 2px 2px 4px #000000;
        }

        /* ANALİZ KARTLARI */
        .master-card {
            background: #1e293b; padding: 20px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 12px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .master-card h3, .master-card p, .master-card b { color: #FFFFFF !important; }
        
        /* 10 TRAFİK IŞIĞI TABLOSU */
        .light { height: 16px; width: 16px; border-radius: 50%; display: inline-block; border: 1px solid white; }
        .green { background-color: #00ff00; box-shadow: 0 0 10px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 10px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 10px #ff0000; }

        .stButton>button {
            background-color: #00D4FF !important; color: #000000 !important;
            font-weight: 900 !important; border-radius: 10px !important; 
            height: 60px !important; border: 3px solid white;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. MASTER ANALİZ VE GİZLİLİK MOTORLARI
# =================================================================
class UltimateSystemV10:
    def __init__(self, db_name="ultimate_pro_v10.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def get_user_space(self, key):
        safe = "".join(filter(str.isalnum, key))
        table = f"u_{safe}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def fetch_full_report(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None
            
            # 10 İNDİKATÖR MATEMATİĞİ
            df['SMA20'] = df['Close'].rolling(20).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA100'] = df['Close'].rolling(100).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            # Bollinger
            df['STD'] = df['Close'].rolling(20).std()
            df['UB'] = df['SMA20'] + (df['STD'] * 2)
            df['LB'] = df['SMA20'] - (df['STD'] * 2)
            # RSI
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            # MACD
            e1 = df['Close'].ewm(span=12, adjust=False).mean()
            e2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = e1 - e2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            # Momentum
            df['Momentum'] = df['Close'] - df['Close'].shift(10)
            
            info = t.info
            fin = {
                "ad": info.get("longName", symbol),
                "ozet": info.get("longBusinessSummary", "Bilgi yok."),
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", "N/A"),
                "pddd": info.get("priceToBook", "N/A"),
                "fiyat": df['Close'].iloc[-1]
            }
            return df, fin, t.news
        except: return None, None, None

# =================================================================
# 3. ANA DÖNGÜ VE TRAFİK IŞIKLARI
# =================================================================
def main():
    sys = UltimateSystemV10()
    
    st.sidebar.title("🔑 Borsa Kasası")
    key = st.sidebar.text_input("Giriş Şifresi:", type="password")
    
    if not key:
        st.info("👋 Merhaba Öğretmenim! Lütfen kasanıza erişmek için şifrenizi girin.")
        return

    ut = sys.get_user_space(key)

    with st.sidebar:
        st.divider()
        st.subheader("➕ Portföy Ekle")
        s_raw = st.text_input("Kod (esen, sasa):").upper().strip()
        q_in = st.number_input("Adet", 0.0)
        c_in = st.number_input("Maliyet", 0.0)
        t_in = st.number_input("Hedef Fiyat", 0.0)
        st_in = st.number_input("Stop Fiyat", 0.0)
        if st.button("KAYDET VE ANALİZ ET"):
            if s_raw:
                symbol = s_raw if s_raw.endswith(".IS") else f"{s_raw}.IS"
                with sys.conn:
                    sys.conn.execute(f"INSERT OR REPLACE INTO {ut} VALUES (?,?,?,?,?)", (symbol, q_in, c_in, t_in, st_in))
                st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {ut}", sys.conn)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu Master V10 Ultimate")
        active = st.selectbox("İncelemek İstediğiniz Varlık:", ["Hisse Seçiniz..."] + p_df['symbol'].tolist())
        
        if active != "Hisse Seçiniz...":
            df, fin, news = sys.fetch_full_report(active)
            if df is not None:
                # --- 10 İNDİKATÖRLÜ TRAFİK IŞIKLARI ---
                st.subheader("🚥 10 Teknik Onay Trafik Işıkları")
                
                # Matematiksel Mantık
                last = df['Close'].iloc[-1]
                L = {
                    "RSI (Göreceli Güç)": "green" if 35 < df['RSI'].iloc[-1] < 65 else "yellow",
                    "Trend (SMA 50)": "green" if last > df['SMA50'].iloc[-1] else "red",
                    "Ana Yön (SMA 200)": "green" if last > df['SMA200'].iloc[-1] else "red",
                    "MACD (Kesişim)": "green" if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else "red",
                    "Bollinger (Konum)": "green" if df['LB'].iloc[-1] < last < df['UB'].iloc[-1] else "yellow",
                    "Hacim (Momentum)": "green" if df['Momentum'].iloc[-1] > 0 else "red",
                    "Kısa Vade (SMA 20)": "green" if last > df['SMA20'].iloc[-1] else "red",
                    "Bilanço (Borç Gücü)": "green" if fin['cari'] > 1.2 else "red",
                    "Karlılık (Özsermaye)": "green" if fin['oz_kar'] > 20 else "yellow",
                    "Fiyat İstikrarı": "green" if last > df['SMA100'].iloc[-1] else "yellow"
                }

                cols = st.columns(5)
                for idx, (name, color) in enumerate(L.items()):
                    with cols[idx % 5]:
                        st.markdown(f'<div class="master-card"><span class="light {color}"></span> <b>{name}</b></div>', unsafe_allow_html=True)

                # --- AI VE DERİN ANALİZ ---
                st.divider()
                c_ai, c_muf = st.columns(2)
                with c_ai:
                    y = df['Close'].values[-60:]
                    model = LinearRegression().fit(np.arange(len(y)).reshape(-1,1), y)
                    f_val = model.predict([[len(y)+5]])[0]
                    st.markdown(f"""<div class="master-card">
                        <h3 style="color:#00D4FF;">🧠 AI 5 GÜNLÜK TAHMİN</h3>
                        <h2>{last:.2f} ➔ {f_val:.2f} TL</h2>
                    </div>""", unsafe_allow_html=True)
                
                with c_muf:
                    st.markdown(f"""<div class="master-card">
                        <h3 style="color:#10b981;">🔍 BİLANÇO MÜFETTİŞİ</h3>
                        <p><b>Borç Ödeme Kapasitesi:</b> Cari Oran {fin['cari']:.2f}</p>
                        <p><b>Verimlilik:</b> Özsermaye Karlılığı %{fin['oz_kar']:.1f}</p>
                    </div>""", unsafe_allow_html=True)

                # --- GRAFİK ---
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold'), name="Trend"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='red'), name="SMA200"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
                fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # --- HABERLER ---
                st.subheader(f"📰 {active} Haber Akışı")
                if news:
                    n_cols = st.columns(3)
                    for i, n in enumerate(news[:3]):
                        with n_cols[i]:
                            st.markdown(f"""<div class="master-card"><a href="{n['link']}" target="_blank" style="text-decoration:none; color:#00D4FF; font-weight:bold;">{n['title'][:60]}...</a></div>""", unsafe_allow_html=True)

                # ALARMLAR VE SİLME
                row = p_df[p_df['symbol'] == active].iloc[0]
                if row['target'] > 0 and last >= row['target']: st.balloons(); st.success(f"🎯 HEDEF ({row['target']} TL) GÖRÜLDÜ!")
                elif row['stop'] > 0 and last <= row['stop']: st.error(f"⚠️ STOP ({row['stop']} TL) GÖRÜLDÜ!")
                
                if st.button("🗑️ BU HİSSEYİ SİL"):
                    with sys.conn: sys.conn.execute(f"DELETE FROM {ut} WHERE symbol = ?", (active,))
                    st.rerun()

    st.markdown('<div style="position:fixed; bottom:0; width:100%; background:#111; color:#ff4b4b; text-align:center; padding:5px; font-weight:bold; border-top:1px solid #3b82f6; z-index:999;">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR (YTD).</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
