import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE KRİSTAL OKUNURLUK (PRODUCTION LEVEL)
# =================================================================
st.set_page_config(page_title="Borsa Robotu Master V7 Pro", layout="wide", page_icon="🏦")

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        
        /* SOL PANEL YAZILARI - ULTRA NET BEYAZ */
        section[data-testid="stSidebar"] { 
            background-color: #111418 !important; 
            border-right: 2px solid #00D4FF; 
        }
        section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h2 { 
            color: #FFFFFF !important; 
            font-weight: 900 !important; 
            font-size: 1.1rem !important;
            text-shadow: 1px 1px 2px #000000;
        }

        /* BİLANÇO KARAR KARTLARI */
        .status-card {
            padding: 20px; border-radius: 15px; margin-bottom: 15px; border-left: 10px solid;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
        }
        .olumlu { background-color: #064e3b; border-color: #10b981; color: #ecfdf5; }
        .olumsuz { background-color: #7f1d1d; border-color: #ef4444; color: #fef2f2; }
        .notur { background-color: #1e293b; border-color: #94a3b8; color: #f1f5f9; }

        /* BUTON TASARIMI */
        .stButton>button {
            background-color: #00D4FF !important; color: #000000 !important;
            font-weight: 900 !important; border-radius: 12px !important; 
            height: 60px !important; width: 100% !important;
            border: 2px solid #FFFFFF !important;
        }
        
        /* INPUT KUTULARI */
        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {
            color: #000000 !important; background-color: #FFFFFF !important; font-weight: bold !important;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. HIZLI VERİ VE PORTFÖY YÖNETİMİ
# =================================================================
class ProductionStorage:
    def __init__(self, db_name="master_portfoy_v7_final.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def get_user_table(self, key):
        safe_key = "".join(filter(str.isalnum, key))
        table_name = f"u_{safe_key}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table_name

    def save_stock(self, table, s, q, c, t, stp):
        with self.conn:
            self.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (s, q, c, t, stp))

    def get_portfolio(self, table):
        try: return pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
        except: return pd.DataFrame()

    def remove_stock(self, table, s):
        with self.conn: self.conn.execute(f"DELETE FROM {table} WHERE symbol = ?", (s,))

# =================================================================
# 3. MÜFETTİŞ ANALİZ MOTORU
# =================================================================
class StockInspector:
    @staticmethod
    @st.cache_data(ttl=300)
    def get_fast_data(symbol):
        # Hata veren t_obj'yi buradan çıkardık, sadece gerekli verileri dönüyoruz
        t = yf.Ticker(symbol)
        df = t.history(period="1y")
        if df.empty: return None, None
        
        info = t.info
        fin_report = {
            "ad": info.get("longName", "Bilinmiyor"),
            "net_kar": info.get("netIncomeToCommon", 0),
            "cari_oran": info.get("currentRatio", 0),
            "ozsermaye_kar": info.get("returnOnEquity", 0) * 100,
            "fk": info.get("trailingPE", "N/A"),
            "pddd": info.get("priceToBook", "N/A"),
            "borc_ozkaynak": info.get("debtToEquity", 0)
        }
        
        # Teknikler
        df['SMA50'] = df['Close'].rolling(50).mean()
        delta = df['Close'].diff()
        g = delta.where(delta > 0, 0).rolling(14).mean()
        l = -delta.where(delta < 0, 0).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (g / (l + 1e-9))))
        
        return df, fin_report

    @staticmethod
    def judge(fin):
        score = 0
        reasons = []
        # Kar/Zarar
        if fin['net_kar'] > 0:
            score += 1
            reasons.append(f"💰 Şirket {fin['net_kar']/1e6:.1f} Milyon TL kârda (Pozitif).")
        else:
            score -= 1
            reasons.append("💸 Şirket son dönemde zarar açıklamış (Negatif).")
        # Borç Gücü
        if fin['cari_oran'] > 1.5:
            score += 1
            reasons.append(f"🏦 Borç ödeme gücü ({fin['cari_oran']:.2f}) çok sağlam.")
        elif fin['cari_oran'] < 1:
            score -= 1
            reasons.append(f"⚠️ Nakit sıkıntısı olabilir (Cari Oran: {fin['cari_oran']:.2f}).")
        
        if score >= 1: return "olumlu", "OLUMLU", reasons
        elif score <= -1: return "olumsuz", "OLUMSUZ", reasons
        return "notur", "NÖTR / BEKLE", reasons

# =================================================================
# 4. ANA EKRAN
# =================================================================
def main():
    db = ProductionStorage()
    insp = StockInspector()

    st.sidebar.title("🔑 Portföy Anahtarı")
    key = st.sidebar.text_input("Şifrenizi Girin:", type="password")
    
    if not key:
        st.info("👋 Hoş geldin öğretmenim! Sol taraftaki 'Kişisel Şifrenizi' girerek portföyünüze ulaşabilirsiniz.")
        return

    table = db.get_user_table(key)

    st.sidebar.divider()
    st.sidebar.subheader("➕ Hisse Ekle")
    raw_s = st.sidebar.text_input("Kod (esen, sasa):").strip().upper()
    q_in = st.sidebar.number_input("Adet", min_value=0.0)
    c_in = st.sidebar.number_input("Maliyet", min_value=0.0)
    t_in = st.sidebar.number_input("Hedef", min_value=0.0)
    st_in = st.sidebar.number_input("Stop", min_value=0.0)
    
    if st.sidebar.button("PORTFÖYE KAYDET"):
        if raw_s:
            s_code = raw_s if raw_s.endswith(".IS") else f"{raw_s}.IS"
            db.save_stock(table, s_code, q_in, c_in, t_in, st_in)
            st.rerun()

    p_df = db.get_portfolio(table)
    
    if not p_df.empty:
        st.title("🛡️ Master Portföy ve Müfettiş Analizi")
        selected = st.selectbox("İncelemek istediğiniz hisseyi seçin:", p_df['symbol'].tolist())
        
        df, fin = insp.get_fast_data(selected)
        
        if df is not None:
            c_name, label, res = insp.judge(fin)
            
            # --- AI VE BİLANÇO ---
            c1, c2 = st.columns(2)
            with c1:
                # AI Projeksiyon
                y = df['Close'].values[-60:]
                x = np.arange(len(y)).reshape(-1, 1)
                model = LinearRegression().fit(x, y)
                f_val = model.predict([[len(y)+5]])[0]
                st.markdown(f"""<div class="status-card notur">
                    <p>🧠 AI FİYAT TAHMİNİ (5 GÜN)</p>
                    <h1 style="color:#00D4FF; margin:0;">{df['Close'].iloc[-1]:.2f} ➔ {f_val:.2f} TL</h1>
                </div>""", unsafe_allow_html=True)

            with c2:
                st.markdown(f"""<div class="status-card {c_name}">
                    <p>🔍 MÜFETTİŞ NOTU: {label}</p>
                    <div style="font-size:0.9rem;">{'<br>'.join(res)}</div>
                </div>""", unsafe_allow_html=True)

            # --- GRAFİK ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=('Fiyat & SMA50', 'RSI Güç Endeksi'), row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mum"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold'), name="Trend"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
            fig.update_layout(height=650, template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- PORTFÖY METRİKLERİ ---
            m1, m2, m3 = st.columns([2, 2, 1])
            curr = df['Close'].iloc[-1]
            row = p_df[p_df['symbol'] == selected].iloc[0]
            m1.metric("Anlık Fiyat", f"{curr:.2f} TL")
            kz = (curr - row['cost']) * row['qty']
            m2.metric("Kâr/Zarar", f"{kz:,.0f} TL", f"{((curr/row['cost'])-1)*100:.2f}%")
            if m3.button("🗑️ HİSSEYİ SİL"):
                db.remove_stock(table, selected); st.rerun()

    else:
        st.warning("👈 Portföyünüz boş. Sol taraftan şifrenizi girin ve hisse ekleyin.")

if __name__ == "__main__": main()
