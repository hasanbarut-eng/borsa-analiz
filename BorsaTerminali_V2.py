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
# 1. TASARIM VE GÜVENLİK YAPILANDIRMASI
# =================================================================
st.set_page_config(page_title="Master Robot Ultimate", layout="wide", page_icon="🛡️")

# Şifre Tanımlama (Burayı istediğiniz şifreyle değiştirebilirsiniz)
MASTER_PASS = "1923" 

if 'live_prices' not in st.session_state: st.session_state.live_prices = {}
if 'live_depth' not in st.session_state: st.session_state.live_depth = {}
if 'live_akd' not in st.session_state: st.session_state.live_akd = {}
if 'ws_connected' not in st.session_state: st.session_state.ws_connected = False

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        .master-card {
            background: #1e293b; padding: 18px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 12px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .ai-box { background: #1e1b4b; border: 1px solid #4338ca; padding: 15px; border-radius: 10px; margin-top: 10px; }
        .green { color: #00ff00; font-weight: bold; }
        .red { color: #ff4b4b; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. CANLI VERİ MOTORU (ARKA PLAN DİNLEYİCİ)
# =================================================================
def ws_engine(url):
    async def listen():
        while True:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    st.session_state.ws_connected = True
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong"}))
                            continue
                        symbol = data.get("s", data.get("symbol"))
                        if not symbol: continue
                        s_key = f"{symbol}.IS"
                        if "p" in data: st.session_state.live_prices[s_key] = float(data["p"])
                        elif data.get("type") == "depth": st.session_state.live_depth[s_key] = data.get("data", [])
                        elif data.get("type") == "akd": st.session_state.live_akd[s_key] = data.get("data", [])
            except:
                st.session_state.ws_connected = False
                await asyncio.sleep(5)

def start_threads(url):
    if "ws_thread_active" not in st.session_state:
        t = threading.Thread(target=lambda: asyncio.run(ws_engine(url)), daemon=True)
        t.start()
        st.session_state.ws_thread_active = True

# =================================================================
# 3. ANALİZ VE KARAR DESTEK SINIFI
# =================================================================
class MasterSystemUltimate:
    def __init__(self):
        self.conn = sqlite3.connect("master_ultimate_v12_final.db", check_same_thread=False)

    def get_space(self, key):
        safe = "".join(filter(str.isalnum, key))
        table = f"u_{safe}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def fetch_full_data(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, [], None, None
            
            # 10 TEKNİK İNDİKATÖR (V12 STANDARTLARI)
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            e1 = df['Close'].ewm(span=12, adjust=False).mean()
            e2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = e1 - e2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            info = t.info
            fin = {
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", 0),
                "pddd": info.get("priceToBook", 0),
                "fiyat": df['Close'].iloc[-1],
                "halka_acik": (info.get("floatShares", 0) / info.get("sharesOutstanding", 1) * 100) if info.get("sharesOutstanding") else 0
            }
            news = t.news if t.news else []
            return df, fin, news, t.quarterly_balance_sheet, t.quarterly_financials
        except: return None, None, [], None, None

# =================================================================
# 4. ANA PROGRAM (GÜVENLİ GİRİŞ VE KARAR MOTORLARI)
# =================================================================
def main():
    sys = MasterSystemUltimate()
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=user%3D%257B%2522id%2522%253A8479457745%252C%2522first_name%2522%253A%2522Hasan%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522language_code%2522%253A%2522tr%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FqFQnxlCiDCD3PBWXXq2LYBtQf6-xy3roI737vHv1ZzfLPtDDm6ILM1w-D0z51rMQ.svg%2522%257D%26chat_instance%3D6343175205638196527%26chat_type%3Dsender%26auth_date%3D1770599132%26signature%3DHBPngCoF21mUtuu4RR-a1AcI1IyYqBQjed1ADKfJXrM7zhXTfInvUuyNs3pPUysstbDdVpNUZXZC_zlWc5h3Aw%26hash%3D7c06577956860cbe621177d869355725b7a920ebc449cf12d7f263eefcc89bb0"
    
    st.sidebar.title("🔐 Hasan Hoca Terminali")
    pwd = st.sidebar.text_input("Şifreniz:", type="password")
    
    # 1. GÜVENLİK KONTROLÜ (Şifre yanlışsa hiçbir şey gösterme)
    if pwd != MASTER_PASS:
        st.warning("⚠️ Lütfen geçerli bir anahtar şifre giriniz.")
        return

    table = sys.get_space(pwd)

    with st.sidebar:
        st.divider()
        canli_mod = st.toggle("🛰️ Canlı Veriyi Aktif Et", value=False)
        if canli_mod: start_threads(WS_LINK)
        
        st.divider()
        h_kod = st.text_input("Hisse Ekle (SASA, ESEN):").upper().strip()
        q_in = st.number_input("Adet:", 0.0)
        c_in = st.number_input("Maliyet:", 0.0)
        t_in = st.number_input("Hedef:", 0.0)
        s_in = st.number_input("Stop:", 0.0)
        if st.button("PORTFÖYE EKLE") and h_kod:
            sym = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
            with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (sym, q_in, c_in, t_in, s_in))
            st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("İncelemek İstediğiniz Hisse:", p_df['symbol'].tolist())
        df, fin, news, balance, financials = sys.fetch_full_data(active)
        
        if df is not None:
            live_p = st.session_state.live_prices.get(active, fin['fiyat']) if canli_mod else fin['fiyat']
            row = p_df[p_df['symbol'] == active].iloc[0]
            
            # SEKMELİ MİMARİ
            tab1, tab2, tab3 = st.tabs(["📊 Karar Destek & Teknik", "📋 Temel Analiz & KAP", "🎲 Gelecek Simülasyonu"])

            # --- TAB 1: AI KARAR DESTEK VE TEKNİK ---
            with tab1:
                st.subheader("🚥 AI Karar Destek Motoru")
                
                # İndikatör Skorlaması
                skor = 0
                rsi_val = df['RSI'].iloc[-1]
                if 40 < rsi_val < 60: skor += 1
                if live_p > df['SMA50'].iloc[-1]: skor += 1
                if df['MACD'].iloc[-1] > df['Signal'].iloc[-1]: skor += 1
                
                # HOCA YORUMU (KARAR VERMENİZİ SAĞLAYACAK KISIM)
                st.markdown(f"""<div class="ai-box">
                    <h3>🤖 Robot Müfettiş Raporu ({active})</h3>
                    <p><b>Teknik Skor:</b> {skor}/3 Onay</p>
                    <p><b>RSI Analizi:</b> {rsi_val:.2f} - {'Aşırı Alımda, Dikkat!' if rsi_val > 70 else 'Toplama Bölgesinde' if rsi_val < 30 else 'Dengeli Seyir.'}</p>
                    <p><b>Trend Analizi:</b> Hisse fiyatı 50 günlük ortalamanın {'<span class="green">Üzerinde</span>' if live_p > df['SMA50'].iloc[-1] else '<span class="red">Altında</span>'}.</p>
                    <p><b>Karar Destek:</b> { 'Mevcut veriler pozisyonu korumak için matematiksel onay veriyor.' if skor >= 2 else 'Veriler zayıf, temkinli olunmalı veya stop seviyesi takip edilmeli.' }</p>
                </div>""", unsafe_allow_html=True)

                # Mum Grafiği
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            # --- TAB 2: TEMEL ANALİZ VE KAP (HATA KORUMALI) ---
            with tab2:
                if news:
                    secilen = st.selectbox("Analiz Edilecek Haberi Seçin:", [n['title'] for n in news])
                    st.info(f"Hocam, {active} için gelen bu haber piyasa beklentisini etkileyebilir. Haber başlığı: {secilen}")
                else:
                    st.warning("Bu hisse için güncel KAP haberi bulunamadı.")
                
                st.subheader("📊 Bilanço Özeti")
                if balance is not None: st.dataframe(balance.iloc[:10, :4], use_container_width=True)

            # --- TAB 3: SİMÜLASYON (TARİHLİ) ---
            with tab3:
                days_sim = st.slider("Simülasyon Gün Sayısı:", 7, 60, 30)
                returns = np.random.normal(0.001, 0.02, days_sim)
                sim_path = live_p * (1 + returns).cumprod()
                dates = [datetime.now() + timedelta(days=i) for i in range(days_sim)]
                fig_sim = go.Figure(go.Scatter(x=dates, y=sim_path, line=dict(color='#00D4FF')))
                fig_sim.update_layout(template="plotly_dark", height=400, xaxis_title="Tahmini Tarih")
                st.plotly_chart(fig_sim, use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Master Robot V12 Final)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
