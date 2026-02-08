import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE MOBİL UYUM (PWA)
# =================================================================
st.set_page_config(page_title="Borsa Robotu Master V7", layout="wide", page_icon="🛡️")

st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="Borsa Robotu">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #111418 !important; border-right: 2px solid #3b82f6; }
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p { 
            color: #FFFFFF !important; font-weight: 900 !important;
        }
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
            color: #000000 !important; background-color: #FFFFFF !important; font-weight: bold !important;
        }
        .bilanco-card {
            background: #1e293b; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 10px;
        }
        .stButton>button {
            background-color: #00D4FF !important; color: black !important;
            font-weight: 900 !important; border-radius: 12px !important; height: 50px; width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. GİZLİLİK VE VERİ SAKLAMA
# =================================================================
class SecureDB:
    def __init__(self, db_name="borsa_v7_master.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def init_user(self, key):
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
# 3. ANALİZ VE BİLANÇO TERCÜME MOTORU
# =================================================================
class AnalysisEngine:
    @staticmethod
    def get_full_package(symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None
            
            # Teknik
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
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
            # Bollinger
            df['MB'] = df['Close'].rolling(20).mean()
            df['UB'] = df['MB'] + (df['Close'].rolling(20).std() * 2)
            df['LB'] = df['MB'] - (df['Close'].rolling(20).std() * 2)

            # Bilanço & Temel Veriler
            info = t.info
            fin = {
                "ad": info.get("longName", "Bilinmiyor"),
                "fk": info.get("trailingPE", "N/A"),
                "pddd": info.get("priceToBook", "N/A"),
                "ozsermaye_kar": info.get("returnOnEquity", 0) * 100,
                "cari_oran": info.get("currentRatio", 0),
                "nakit": info.get("totalCash", 0) / 1e6,
                "borc": info.get("totalDebt", 0) / 1e6,
                "ozet": info.get("longBusinessSummary", "Bilgi yok.")
            }
            return df, fin, t
        except: return None, None, None

    @staticmethod
    def interpret_finance(fin):
        interpretations = []
        # Cari Oran (Borç ödeme)
        if fin['cari_oran'] > 1.5: interpretations.append("🟢 **Borç Ödeme Gücü:** Çok iyi. Şirketin kasası borçlarını ödemeye fazlasıyla yetiyor.")
        elif fin['cari_oran'] > 1: interpretations.append("🟡 **Borç Ödeme Gücü:** Dengeli. Borçlarını ödeyebilir ama nakit akışını izlemek lazım.")
        else: interpretations.append("🔴 **Borç Ödeme Gücü:** Zayıf. Şirket kısa vadeli borçlarını ödemekte zorlanabilir.")
        
        # Özsermaye Karlılığı
        if fin['ozsermaye_kar'] > 20: interpretations.append("🟢 **Karlılık:** Şirket kendi parasını çok verimli kullanıyor, kâr makinesi gibi çalışıyor.")
        elif fin['ozsermaye_kar'] > 0: interpretations.append("🟡 **Karlılık:** Standart. Şirket kâr ediyor ama daha verimli olabilir.")
        else: interpretations.append("🔴 **Karlılık:** Sıkıntılı. Şirket şu an öz sermayesini eritmiş veya kâr edemiyor.")
        
        # F/K Yorumu
        if isinstance(fin['fk'], (int, float)):
            if fin['fk'] < 10: interpretations.append("🟢 **Piyasa Değeri:** Hisse şu an kârına göre ucuz görünüyor.")
            elif fin['fk'] < 25: interpretations.append("🟡 **Piyasa Değeri:** Hisse gerçek değerine yakın, dengeli.")
            else: interpretations.append("🔴 **Piyasa Değeri:** Hisse kârına göre biraz pahalı fiyatlanıyor olabilir.")
        
        return interpretations

    @staticmethod
    def ai_model(df):
        y = df['Close'].values[-100:]
        x = np.arange(len(y)).reshape(-1, 1)
        m = LinearRegression().fit(x, y)
        f = np.array([len(y) + i for i in range(5)]).reshape(-1, 1)
        return m.predict(f)

# =================================================================
# 4. ANA PROGRAM
# =================================================================
def main():
    db = SecureDB()
    eng = AnalysisEngine()

    st.sidebar.title("🔑 Güvenli Erişim")
    user_key = st.sidebar.text_input("Kişisel Şifreniz:", type="password")
    
    if not user_key:
        st.info("👋 Devam etmek için lütfen sol taraftan şifrenizi girin. Bu şifre verilerinizi başkalarından gizler.")
        return

    u_table = db.init_user(user_key)

    st.sidebar.divider()
    with st.sidebar.form("ekle", clear_on_submit=True):
        st.subheader("➕ Hisse Ekle")
        s_in = st.text_input("Kod (ESEN)").upper().strip()
        q_in = st.number_input("Adet", min_value=0.0)
        c_in = st.number_input("Maliyet", min_value=0.0)
        t_in = st.number_input("Hedef", min_value=0.0)
        stop_in = st.number_input("Stop", min_value=0.0)
        if st.form_submit_button("KAYDET"):
            if s_in:
                sc = s_in + ".IS" if not s_in.endswith(".IS") else s_in
                db.save(u_table, sc, q_in, c_in, t_in, stop_in)
                st.rerun()

    p_df = db.get_all(u_table)
    if not p_df.empty:
        for s in p_df['symbol']:
            c1, c2 = st.sidebar.columns([4, 1])
            c1.info(f"**{s.replace('.IS', '')}**")
            if c2.button("🗑️", key=f"del_{s}"):
                db.delete(u_table, s); st.rerun()

        st.title("🛡️ Borsa Robotu Master V7")
        secim = st.selectbox("Analiz Edilecek Varlık:", p_df['symbol'].tolist())
        df, fin, t_obj = eng.get_full_package(secim)
        
        if df is not None:
            pred = eng.ai_model(df)
            yorumlar = eng.interpret_finance(fin)
            
            # --- TAHMİN VE BİLANÇO ÖZETİ ---
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""<div style="background:#1e3a8a; padding:20px; border-radius:15px; border:2px solid #60a5fa;">
                    <h3 style="color:white; margin:0;">🧠 AI Trend Tahmini</h3>
                    <h1 style="color:#00D4FF; margin:0;">{pred[0]:.2f} ➔ {pred[-1]:.2f} TL</h1>
                    <p style="color:white; font-size:0.8rem;">Matematiksel 5 günlük projeksiyon.</p>
                </div>""", unsafe_allow_html=True)
            
            with col2:
                st.subheader("📋 Bilanço Okuryazarı (Özet)")
                for y in yorumlar:
                    st.markdown(f"<div class='bilanco-card'>{y}</div>", unsafe_allow_html=True)

            # --- GRAFİKLER ---
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                               subplot_titles=('Fiyat & Bollinger & Trend', 'MACD', 'RSI'),
                               row_heights=[0.5, 0.25, 0.25])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['UB'], line=dict(color='rgba(255,255,255,0.2)'), name="Üst Bant"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['LB'], line=dict(color='rgba(255,255,255,0.2)'), name="Alt Bant", fill='tonexty'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold', width=2), name="Trend"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='cyan'), name="MACD"), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=3, col=1)
            fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- METRİKLER ---
            last = float(df['Close'].iloc[-1])
            m1, m2, m3 = st.columns(3)
            m1.metric("Anlık", f"{last:.2f} TL")
            row = p_df[p_df['symbol'] == secim].iloc[0]
            kz = (last - row['cost']) * row['qty']
            m3.metric("Kâr/Zarar", f"{kz:,.0f} TL", f"{((last/row['cost'])-1)*100:.2f}%")
            
            if row['target'] > 0 and last >= row['target']: st.balloons(); st.success("🎯 HEDEF GÖRÜLDÜ!")
            elif row['stop'] > 0 and last <= row['stop']: st.error("⚠️ STOP SEVİYESİ!")

    else:
        st.info("👈 Başlamak için giriş yapın ve hisse ekleyin.")

if __name__ == "__main__": main()
