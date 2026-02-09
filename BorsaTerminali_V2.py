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
# 1. TASARIM VE SESSION STATE YAPILANDIRMASI
# =================================================================
st.set_page_config(page_title="Master Robot V12 Ultimate", layout="wide", page_icon="🛡️")

# Hafıza Alanlarını Başlat
if 'live_prices' not in st.session_state: st.session_state.live_prices = {}
if 'live_depth' not in st.session_state: st.session_state.live_depth = {}
if 'live_akd' not in st.session_state: st.session_state.live_akd = {}
if 'ws_connected' not in st.session_state: st.session_state.ws_connected = False

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        .master-card {
            background: #1e293b; padding: 20px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .master-card h3 { color: #00D4FF !important; }
        .master-card p, .master-card b { color: #FFFFFF !important; }
        .light { height: 18px; width: 18px; border-radius: 50%; display: inline-block; border: 1px solid white; }
        .green { background-color: #00ff00; box-shadow: 0 0 12px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 12px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 12px #ff0000; }
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 8px; font-size: 0.85rem; font-weight: bold; border-top: 2px solid #3b82f6; z-index: 999;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. CANLI VERİ VE WEBSOCKET MOTORU
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
                        
                        m_type = data.get("type")
                        if "p" in data: st.session_state.live_prices[s_key] = float(data["p"])
                        elif m_type == "depth": st.session_state.live_depth[s_key] = data.get("data", [])
                        elif m_type == "akd": st.session_state.live_akd[s_key] = data.get("data", [])
            except:
                st.session_state.ws_connected = False
                await asyncio.sleep(5)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen())

def start_threads(url):
    if "ws_thread_active" not in st.session_state:
        t = threading.Thread(target=lambda: ws_engine(url), daemon=True)
        t.start()
        st.session_state.ws_thread_active = True

# =================================================================
# 3. VERİ ANALİZ VE SİMÜLASYON SINIFI
# =================================================================
class MasterSystemUltimate:
    def __init__(self, db_name="master_robot_final.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def get_space(self, key):
        safe = "".join(filter(str.isalnum, key))
        table = f"u_{safe}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def fetch_comprehensive(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None, None
            
            # 10 TEKNİK İNDİKATÖR
            df['SMA20'] = df['Close'].rolling(20).mean()
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
            df['STD'] = df['Close'].rolling(20).std()
            df['Upper'] = df['SMA20'] + (df['STD'] * 2)
            df['Lower'] = df['SMA20'] - (df['STD'] * 2)
            df['Momentum'] = df['Close'] - df['Close'].shift(10)
            
            info = t.info
            fin = {
                "ad": info.get("longName", symbol),
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", "N/A"),
                "pddd": info.get("priceToBook", "N/A"),
                "halka_acik": (info.get("floatShares", 0) / info.get("sharesOutstanding", 1) * 100)
            }
            return df, fin, t.news, info
        except: return None, None, None, None

    def create_simulation(self, current_price, days=30):
        """Monte Carlo Simülasyonu ile muhtemel gelecek grafiği"""
        returns = np.random.normal(0.001, 0.02, days)
        price_path = current_price * (1 + returns).cumprod()
        dates = [datetime.now() + timedelta(days=i) for i in range(days)]
        return pd.DataFrame({"Tarih": dates, "Simüle Fiyat": price_path})

# =================================================================
# 4. ANA PROGRAM VE ANALİZ MOTORLARI
# =================================================================
def main():
    sys = MasterSystemUltimate()
    
    # Canlı Veri URL'si (Görsel fca63f'den gelen)
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=user%3D%257B%2522id%2522%253A8479457745%252C%2522first_name%2522%253A%2522Hasan%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522language_code%2522%253A%2522tr%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FqFQnxlCiDCD3PBWXXq2LYBtQf6-xy3roI737vHv1ZzfLPtDDm6ILM1w-D0z51rMQ.svg%2522%257D%26chat_instance%3D6343175205638196527%26chat_type%3Dsender%26auth_date%3D1770599132%26signature%3DHBPngCoF21mUtuu4RR-a1AcI1IyYqBQjed1ADKfJXrM7zhXTfInvUuyNs3pPUysstbDdVpNUZXZC_zlWc5h3Aw%26hash%3D7c06577956860cbe621177d869355725b7a920ebc449cf12d7f263eefcc89bb0"
    start_threads(WS_LINK)

    st.sidebar.title("🔐 Hasan Hoca Kasası")
    pwd = st.sidebar.text_input("Giriş Şifresi:", type="password")
    if not pwd:
        st.info("👋 Merhaba Öğretmenim! Lütfen şifrenizi girerek 7 Motoru ateşleyin.")
        return

    table = sys.get_space(pwd)

    # PORTFÖY YÖNETİMİ
    with st.sidebar:
        st.divider()
        st.write(f"📡 Canlı Veri Hattı: {'🟢 Aktif' if st.session_state.ws_connected else '🔴 Kesildi'}")
        h_kod = st.text_input("Hisse Kodu (esen, sasa):").upper().strip()
        if st.button("KAYDET VE ANALİZE AL"):
            if h_kod:
                symbol = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
                with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,0,0,0,0)", (symbol,))
                st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu - MASTER V12 ULTIMATE")
        active = st.selectbox("İncelemek İstediğiniz Hisse:", p_df['symbol'].tolist())
        
        df, fin, news, info = sys.fetch_comprehensive(active)
        if df is not None:
            live_p = st.session_state.live_prices.get(active, df['Close'].iloc[-1])
            st.header(f"📊 {active} - Canlı Fiyat: {live_p:.2f} TL")

            # --- MOTOR 1: 10 TEKNİK ONAY IŞIĞI ---
            st.subheader("🚥 10 Teknik Onay ve Trafik Işıkları")
            L = {
                "RSI Gücü": ("green" if 35 < df['RSI'].iloc[-1] < 65 else "yellow", df['RSI'].iloc[-1]),
                "SMA 50": ("green" if live_p > df['SMA50'].iloc[-1] else "red", 0),
                "MACD Trend": ("green" if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else "red", 0),
                "Bollinger": ("green" if df['Lower'].iloc[-1] < live_p < df['Upper'].iloc[-1] else "yellow", 0),
                "Momentum": ("green" if df['Momentum'].iloc[-1] > 0 else "red", 0),
                "Cari Oran": ("green" if fin['cari'] > 1.2 else "red", fin['cari']),
                "Özsermaye Kâr": ("green" if fin['oz_kar'] > 20 else "yellow", fin['oz_kar']),
                "Halka Açıklık": ("green" if 0 < fin['halka_acik'] < 60 else "yellow", fin['halka_acik']),
                "F/K Değeri": ("green" if isinstance(fin['fk'], (int, float)) and fin['fk'] < 15 else "yellow", fin['fk']),
                "Kısa Vade (20)": ("green" if live_p > df['SMA20'].iloc[-1] else "red", 0)
            }
            cols = st.columns(5)
            for idx, (name, val) in enumerate(L.items()):
                with cols[idx % 5]:
                    st.markdown(f'<div class="master-card"><span class="light {val[0]}"></span><b>{name}</b><br><small>{val[1] if val[1] != 0 else ""}</small></div>', unsafe_allow_html=True)

            # --- MOTOR 2 & 3: CANLI DERİNLİK VE TAKAS (AKD) ---
            c_der, c_tak = st.columns(2)
            akd_notu = "Veri akışı bekleniyor..."
            
            with c_der:
                st.subheader("🛒 Canlı Derinlik (Kademeler)")
                depth = st.session_state.live_depth.get(active, [])
                if depth: st.table(pd.DataFrame(depth))
                else: st.info("Derinlik verisi için Telegram botunda bu ekranı bir kez açın.")

            with c_tak:
                st.subheader("🤝 Aracı Kurum Dağılımı (AKD)")
                akd = st.session_state.live_akd.get(active, [])
                if akd:
                    akd_df = pd.DataFrame(akd)
                    st.dataframe(akd_df, use_container_width=True)
                    # AKD Müfettiş Analizi
                    buy_power = sum([x['lot'] for x in akd if x['side'] == 'buy'][:3])
                    sell_power = sum([x['lot'] for x in akd if x['side'] == 'sell'][:3])
                    if buy_power > sell_power: akd_notu = "✅ GÜÇLÜ TOPLAMA: İlk 3 kurum malı topluyor."
                    else: akd_notu = "⚠️ MAL BOŞALTMA: Satış baskısı hakim."
                else: st.info("Takas verisi bekleniyor...")

            # --- MOTOR 4: AI TAHMİN VE MOTOR 5: SİMÜLASYON ---
            st.divider()
            c_ai, c_sim = st.columns(2)
            
            with c_ai:
                y_reg = df['Close'].values[-30:]
                model = LinearRegression().fit(np.arange(len(y_reg)).reshape(-1,1), y_reg)
                pred = model.predict([[len(y_reg)+5]])[0]
                st.markdown(f"""<div class="master-card" style="border-color:#ff00ff; text-align:center;">
                    <h3 style="color:#ff00ff;">🧠 AI 5 GÜNLÜK TAHMİN</h3>
                    <h2 style="color:white;">{live_p:.2f} ➔ {pred:.2f} TL</h2>
                    <p>Eğilim: %{((pred/live_p)-1)*100:.2f}</p>
                </div>""", unsafe_allow_html=True)

            with c_sim:
                st.subheader("🎲 Monte Carlo Simülasyonu (30 Gün)")
                sim_data = sys.create_simulation(live_p)
                fig_sim = go.Figure()
                fig_sim.add_trace(go.Scatter(x=sim_data['Tarih'], y=sim_data['Simüle Fiyat'], name="Muhtemel Yol"))
                fig_sim.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig_sim, use_container_width=True)

            # --- MOTOR 6: HABERLER VE MOTOR 7: HOCA ÖZETİ ---
            st.subheader("📰 Son Dakika Haberler ve KAP")
            if news:
                n_cols = st.columns(3)
                for i, n in enumerate(news[:3]):
                    with n_cols[i]:
                        st.markdown(f'<div class="master-card"><a href="{n["link"]}" style="color:#00D4FF;">{n["title"][:60]}...</a></div>', unsafe_allow_html=True)

            st.markdown(f"""<div class="master-card" style="border-left:12px solid #00D4FF;">
                <h3>🤖 Robotun Hoca Özeti ve Pozisyon Önerisi</h3>
                <p><b>Durum:</b> {active} hissesi şu an {live_p:.2f} TL. {akd_notu}</p>
                <p><b>Matematiksel Analiz:</b> 10 indikatörün {sum(1 for v in L.values() if v[0]=="green")}'u yeşil yanıyor. 
                AI motorumuz yükseliş beklerken, simülasyon grafiği volatiliteye dikkat çekiyor.</p>
                <p><b>Önerimiz:</b> Büyük kurumların mal toplama iştahı pozitif ise pozisyonu korumak mantıklıdır.</p>
            </div>""", unsafe_allow_html=True)

            # --- ANA FİYAT GRAFİĞİ ---
            fig_main = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
            fig_main.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mum"), row=1, col=1)
            fig_main.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold'), name="SMA50"), row=1, col=1)
            fig_main.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
            fig_main.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_main, use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Matematik Yanılmaz, Piyasa Yanıltır)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
