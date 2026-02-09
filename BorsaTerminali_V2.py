import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression
import asyncio
import threading
import json
import websockets
from datetime import datetime, timedelta

# =================================================================
# 1. TASARIM VE GİRİŞ SİSTEMİ
# =================================================================
st.set_page_config(page_title="Finans Koçu Terminali", layout="wide", page_icon="🛡️")

if 'live_prices' not in st.session_state: st.session_state.live_prices = {}
if 'live_akd' not in st.session_state: st.session_state.live_akd = {}
if 'ws_connected' not in st.session_state: st.session_state.ws_connected = False
if 'authenticated' not in st.session_state: st.session_state.authenticated = False

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        .coach-box {
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
            border: 2px solid #6366f1; padding: 25px; border-radius: 15px;
            color: #e0e7ff; margin-bottom: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .master-card {
            background: #1e293b; padding: 15px; border-radius: 10px; 
            border-left: 5px solid #00D4FF; margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. GÜVENLİK VE VERİ MOTORU
# =================================================================
def check_password():
    if st.session_state.authenticated: return True
    st.title("🛡️ Master Robot Giriş")
    pwd = st.text_input("Şifrenizi Belirleyin veya Girin:", type="password")
    if st.button("Sistemi Aç"):
        st.session_state.master_password = pwd
        st.session_state.authenticated = True
        st.rerun()
    return False

def ws_engine(url):
    async def listen():
        while True:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    st.session_state.ws_connected = True
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping": await ws.send(json.dumps({"type": "pong"})); continue
                        symbol = data.get("s", data.get("symbol"))
                        if not symbol: continue
                        s_key = f"{symbol}.IS"
                        if "p" in data: st.session_state.live_prices[s_key] = float(data["p"])
                        elif data.get("type") == "akd": st.session_state.live_akd[s_key] = data.get("data", [])
            except:
                st.session_state.ws_connected = False
                await asyncio.sleep(5)

def start_threads(url):
    if "ws_thread_active" not in st.session_state:
        t = threading.Thread(target=lambda: asyncio.run(ws_engine(url)), daemon=True)
        t.start()
        st.session_state.ws_thread_active = True

class MasterSystem:
    def __init__(self):
        self.conn = sqlite3.connect("master_ultimate_coach.db", check_same_thread=False)

    def get_space(self, pwd):
        table = f"u_{"".join(filter(str.isalnum, pwd))}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def fetch_full_data(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, [], None
            
            # Teknik Veriler
            df['SMA50'] = df['Close'].rolling(50).mean()
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            
            info = t.info
            fin = {
                "fk": info.get("trailingPE", 0), "pddd": info.get("priceToBook", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100, "fiyat": df['Close'].iloc[-1]
            }
            return df, fin, (t.news if t.news else []), t.quarterly_balance_sheet
        except: return None, None, [], None

# =================================================================
# 3. ANA ARAYÜZ VE KOÇLUK MANTIĞI
# =================================================================
def main():
    if not check_password(): return
    sys = MasterSystem()
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=..." # Sizin anahtarınız

    table = sys.get_space(st.session_state.master_password)

    with st.sidebar:
        canli_mod = st.toggle("🛰️ Canlı Veriyi Aç", value=False)
        if canli_mod: start_threads(WS_LINK)
        st.divider()
        h_kod = st.text_input("Hisse (SASA, ESEN):").upper().strip()
        if st.button("LİSTEYE EKLE") and h_kod:
            sym = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
            with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,0,0,0,0)", (sym,))
            st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("Hisse Seçin:", p_df['symbol'].tolist())
        df, fin, news, balance = sys.fetch_full_data(active)
        
        if df is not None:
            live_p = st.session_state.live_prices.get(active, fin['fiyat'])
            
            # --- MOTOR 1: AI FİNANS KOÇU (Basitleştirilmiş Yorum) ---
            rsi_v = df['RSI'].iloc[-1]
            trend_ok = live_p > df['SMA50'].iloc[-1]
            
            st.markdown(f"""<div class="coach-box">
                <h3>🤖 Finans Koçunuzun Notu ({active})</h3>
                <p><b>Hisse Fiyatı:</b> {live_p:.2f} TL</p>
                <p><b>Ne Anlama Geliyor?</b> {active} hissesi {'teknik olarak güçlü' if trend_ok else 'biraz yorgun'} görünüyor. 
                RSI değeri {rsi_v:.1f}; bu da hissenin {'ucuz' if rsi_v < 40 else 'pahalı' if rsi_v > 70 else 'dengeli'} olduğunu söylüyor.</p>
                <p><b>Ne Yapmalı?</b> {'Kademeli alım düşünülebilir.' if rsi_v < 45 and trend_ok else 'Buralardan alım riskli, izlemede kalınmalı.'}</p>
            </div>""", unsafe_allow_html=True)

            # --- MOTOR 2: AÇILIR LİSTE İLE SON 10 KAP ---
            st.subheader("📰 Son 10 KAP Haberi ve Analizi")
            if news:
                news_list = news[:10]
                selected_news = st.selectbox("Analiz edilecek haberi seçin:", [n['title'] for n in news_list])
                
                # Seçilen habere göre AI yorumu
                kap_yorum = "Hocam bu haber şirketin büyümesi için pozitif bir adım olabilir." if any(x in selected_news.lower() for x in ["iş", "ihale", "anlaşma", "kâr"]) else "Genel bir bilgilendirme haberi, fiyata etkisi nötr kalabilir."
                
                st.markdown(f"""<div class="master-card" style="border-left-color:#00ff00;">
                    <b>Haber Başlığı:</b> {selected_news}<br>
                    <b>Koçun Yorumu:</b> {kap_yorum}
                </div>""", unsafe_allow_html=True)
            else:
                st.info("Bu hisse için güncel KAP haberi bulunamadı.")

            # SEKMELİ DİĞER VERİLER
            tab1, tab2 = st.tabs(["📉 Grafik & Teknik", "🎲 Olasılıklar"])
            with tab1:
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=450)
                st.plotly_chart(fig, use_container_width=True)
            with tab2:
                returns = np.random.normal(0.001, 0.02, 30)
                path = live_p * (1 + returns).cumprod()
                st.plotly_chart(go.Figure(go.Scatter(y=path, line=dict(color='#00D4FF'))), use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Hasan Hoca Finans Koçu)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
