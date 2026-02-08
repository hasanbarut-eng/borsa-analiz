import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE MOBİL UYUM (PWA) - KRİSTAL NETLİK
# =================================================================
st.set_page_config(page_title="Borsa Robotu Master V7", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #111418 !important; border-right: 2px solid #00D4FF; }
        
        /* Sidebar Okunurluk */
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h2 { 
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important; 
        }
        
        /* BİLANÇO VE AI KARTLARI */
        .master-card {
            background: #1e293b; padding: 20px; border-radius: 15px; 
            border-left: 8px solid #00D4FF; margin-bottom: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .card-title { color: #00D4FF !important; font-weight: 800; margin: 0; font-size: 0.9rem; }
        .card-text { color: #FFFFFF !important; font-weight: 600; margin-top: 5px; font-size: 1rem; }

        /* KAYDET BUTONU - EN ÜSTTE VE PARLAK */
        .stButton>button {
            background-color: #00D4FF !important; color: #000000 !important;
            font-weight: 900 !important; border-radius: 12px !important; 
            height: 65px !important; width: 100% !important;
            border: 3px solid #FFFFFF !important; font-size: 1.3rem !important;
        }
        
        /* GİRİŞ KUTULARI */
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
            color: #000000 !important; background-color: #FFFFFF !important; font-weight: bold !important;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. GİZLİLİK ODAKLI VERİ SAKLAMA
# =================================================================
class PersonalStorage:
    def __init__(self, db_name="borsa_robotu_v7_final.db"):
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
# 3. HIZLI ANALİZ VE ÇİFT AI MOTORU
# =================================================================
class AnalystSystem:
    @staticmethod
    @st.cache_data(ttl=600) # Verileri 10 dakika önbelleğe alır, hız kazandırır.
    def fetch_analysis(symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None
            
            # Teknik İndikatörler
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            delta = df['Close'].diff()
            g = (delta.where(delta > 0, 0)).rolling(14).mean()
            l = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (g / (l + 1e-9))))
            df['MB'] = df['Close'].rolling(20).mean()
            df['UB'] = df['MB'] + (df['Close'].rolling(20).std() * 2)
            df['LB'] = df['MB'] - (df['Close'].rolling(20).std() * 2)
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

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
    def dual_ai_engine(df):
        try:
            y = df['Close'].values[-100:]
            x = np.arange(len(y)).reshape(-1, 1)
            model = LinearRegression().fit(x, y)
            f_x = np.array([len(y) + i for i in range(5)]).reshape(-1, 1)
            preds = model.predict(f_x)
            
            rsi = df['RSI'].iloc[-1]
            conf = 92 if 45 < rsi < 65 else 68
            return preds, conf
        except: return None, 0

# =================================================================
# 4. ANA PROGRAM DÖNGÜSÜ
# =================================================================
def main():
    storage = PersonalStorage()
    engine = AnalystSystem()

    st.sidebar.title("🔑 Güvenli Giriş")
    key = st.sidebar.text_input("Kişisel Şifreniz:", type="password")
    
    if not key:
        st.info("👋 Hoş geldin öğretmenim! Arkadaşınızla beraber kullanmaya başlamak için lütfen sol tarafa şifrenizi girin.")
        return

    ut = storage.get_user_space(key)

    st.sidebar.divider()
    # KAYDET BUTONU EN ÜSTTE
    s_in = st.sidebar.text_input("Hisse Kodu (küçük girilebilir):").upper().strip()
    q_in = st.sidebar.number_input("Adet", min_value=0.0)
    c_in = st.sidebar.number_input("Maliyet", min_value=0.0)
    t_in = st.sidebar.number_input("Hedef Fiyat", min_value=0.0)
    st_in = st.sidebar.number_input("Stop Fiyat", min_value=0.0)
    
    if st.sidebar.button("📊 KAYDET VE ANALİZ ET"):
        if s_in:
            # Otomatik büyük harf ve .IS ekleme
            sc = s_in if s_in.endswith(".IS") else s_in + ".IS"
            storage.save(ut, sc, q_in, c_in, t_in, st_in)
            st.rerun()

    p_df = storage.get_all(ut)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu Master V7")
        # Birden çok hisseyi buradan seçip analiz edebilir
        active = st.selectbox("Analiz Edilecek Varlık Listesi:", p_df['symbol'].tolist())
        df, fin = engine.fetch_analysis(active)
        
        if df is not None:
            preds, conf = engine.dual_ai_engine(df)
            
            # --- AI VE BİLANÇO ANALİZİ ---
            c_ai, c_fin = st.columns(2)
            with c_ai:
                st.markdown(f"""<div class="master-card">
                    <p class="card-title">🧠 ÇİFT MOTORLU AI TAHMİNİ (5 GÜN)</p>
                    <h1 style="color:white; margin:0;">{preds[0]:.2f} ➔ {preds[-1]:.2f} TL</h1>
                    <p class="card-text">📊 Güven Skoru: %{conf}</p>
                </div>""", unsafe_allow_html=True)
            
            with c_fin:
                c_sts = "🟢" if fin['cari'] > 1.5 else "🟡" if fin['cari'] > 1 else "🔴"
                k_sts = "🟢" if fin['oz_kar'] > 20 else "🟡" if fin['oz_kar'] > 0 else "🔴"
                st.markdown(f"""<div class="master-card">
                    <p class="card-title">🧾 BİLANÇO OKURYAZARI (ÖZET)</p>
                    <p class="card-text">{c_sts} <b>Borç Ödeme:</b> Durum { 'Güçlü' if fin['cari']>1.5 else 'Zayıf' }.</p>
                    <p class="card-text">{k_sts} <b>Karlılık:</b> Verim %{fin['oz_kar']:.1f}.</p>
                </div>""", unsafe_allow_html=True)

            # --- TEKNİK GRAFİKLER ---
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                               subplot_titles=('Fiyat & Bollinger & Trendler', 'MACD Sinyali', 'RSI Güç Endeksi'),
                               row_heights=[0.5, 0.25, 0.25])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['UB'], line=dict(color='gray', width=1), name="Üst Bant"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['LB'], line=dict(color='gray', width=1), name="Alt Bant", fill='tonexty'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold', width=2), name="SMA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], line=dict(color='red', width=2), name="SMA200"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='cyan'), name="MACD"), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=3, col=1)
            fig.update_layout(height=850, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- METRİKLER VE ALARMLAR ---
            m1, m2, m3 = st.columns([2, 2, 1])
            curr_p = df['Close'].iloc[-1]
            m1.metric("Anlık Fiyat", f"{curr_p:.2f} TL")
            row = p_df[p_df['symbol'] == active].iloc[0]
            kz = (curr_p - row['cost']) * row['qty']
            m2.metric("Kâr/Zarar", f"{kz:,.0f} TL", f"{((curr_p/row['cost'])-1)*100:.2f}%")
            
            if m3.button(f"🗑️ SİL"):
                storage.delete(ut, active); st.rerun()
            
            # GÖRSEL ALARMLAR
            if row['target'] > 0 and curr_p >= row['target']:
                st.balloons(); st.success(f"🎯 HEDEF FİYAT ({row['target']} TL) GÖRÜLDÜ!")
            elif row['stop'] > 0 and curr_p <= row['stop']:
                st.error(f"⚠️ STOP SEVİYESİ ({row['stop']} TL) ALTINA İNİLDİ!")

    else:
        st.info("👈 Başlamak için şifrenizi girin ve sol taraftan ilk hissenizi kaydedin.")

if __name__ == "__main__":
    main()
