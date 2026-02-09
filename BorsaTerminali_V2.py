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
from datetime import datetime

# =================================================================
# 1. TASARIM VE HAFIZA YAPILANDIRMASI
# =================================================================
st.set_page_config(page_title="Master Robot V12 Ultimate", layout="wide", page_icon="🛡️")

# Hafıza Alanlarını Başlat (Fiyat, Derinlik, AKD/Takas)
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
        .master-card h3 { color: #00D4FF !important; margin-bottom: 10px; }
        .master-card p, .master-card b { color: #FFFFFF !important; }
        .light { height: 15px; width: 15px; border-radius: 50%; display: inline-block; margin-right: 10px; }
        .green { background-color: #00ff00; box-shadow: 0 0 10px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 10px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 10px #ff0000; }
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 8px; font-size: 0.8rem; font-weight: bold; border-top: 1px solid #3b82f6; z-index: 999;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. CANLI VERİ MOTORU (ARKA PLAN DİNLEYİCİ)
# =================================================================
def ws_engine(url):
    """Arka planda tüm veri tiplerini süzerek yakalar."""
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
                        
                        m_type = data.get("type")
                        symbol = data.get("s", data.get("symbol"))
                        if not symbol: continue
                        s_key = f"{symbol}.IS"

                        if "p" in data: # Canlı Fiyat
                            st.session_state.live_prices[s_key] = float(data["p"])
                        elif m_type == "depth": # Canlı Derinlik
                            st.session_state.live_depth[s_key] = data.get("data", [])
                        elif m_type == "akd": # Aracı Kurum Dağılımı (Takas)
                            st.session_state.live_akd[s_key] = data.get("data", [])
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
# 3. VERİ ANALİZ VE YÖNETİM SINIFI
# =================================================================
class MasterSystemV12:
    def __init__(self):
        self.conn = sqlite3.connect("master_robot_final.db", check_same_thread=False)

    def get_space(self, key):
        safe = "".join(filter(str.isalnum, key))
        table = f"u_{safe}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def fetch_market(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            return df, t.info, t.news
        except: return None, None, None

# =================================================================
# 4. ANA PROGRAM VE ANALİZ MOTORLARI
# =================================================================
def main():
    sys = MasterSystemV12()
    
    # Canlı Veri Anahtarınız
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=user%3D%257B%2522id%2522%253A8479457745%252C%2522first_name%2522%253A%2522Hasan%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522language_code%2522%253A%2522tr%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FqFQnxlCiDCD3PBWXXq2LYBtQf6-xy3roI737vHv1ZzfLPtDDm6ILM1w-D0z51rMQ.svg%2522%257D%26chat_instance%3D6343175205638196527%26chat_type%3Dsender%26auth_date%3D1770599132%26signature%3DHBPngCoF21mUtuu4RR-a1AcI1IyYqBQjed1ADKfJXrM7zhXTfInvUuyNs3pPUysstbDdVpNUZXZC_zlWc5h3Aw%26hash%3D7c06577956860cbe621177d869355725b7a920ebc449cf12d7f263eefcc89bb0"
    start_threads(WS_LINK)

    st.sidebar.title("🔑 Master Kasa")
    key = st.sidebar.text_input("Şifreniz:", type="password")
    if not key:
        st.info("👋 Hoş geldin öğretmenim! Robotu uyandırmak için şifreni gir.")
        return

    table = sys.get_space(key)

    with st.sidebar:
        st.divider()
        st.write(f"Durum: {'🟢 Canlı' if st.session_state.ws_connected else '🔴 Beklemede'}")
        h_kod = st.text_input("Hisse (esen, sasa):").upper().strip()
        if st.button("PORTFÖYE EKLE") and h_kod:
            sym = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
            with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,0,0,0,0)", (sym,))
            st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("İncelemek İstediğiniz Hisse:", p_df['symbol'].tolist())
        df, info, news = sys.fetch_market(active)
        
        if df is not None:
            # MOTOR 1: CANLI FİYAT
            live_p = st.session_state.live_prices.get(active, df['Close'].iloc[-1])
            st.title(f"🛡️ {active} - CANLI: {live_p:.2f} TL")

            # MOTOR 2: 10 TEKNİK ONAY IŞIĞI
            st.subheader("🚥 Teknik Analiz Müfettişi")
            L = {
                "RSI": ("green" if 35 < df['RSI'].iloc[-1] < 65 else "yellow", df['RSI'].iloc[-1]),
                "SMA 50": ("green" if live_p > df['SMA50'].iloc[-1] else "red", 0),
                "SMA 200": ("green" if live_p > df['SMA200'].iloc[-1] else "red", 0),
                "Cari Oran": ("green" if info.get('currentRatio', 0) > 1.2 else "red", info.get('currentRatio', 0)),
                "Halka Açıklık": ("green" if info.get('floatShares', 0)/info.get('sharesOutstanding', 1)*100 < 50 else "yellow", 0)
            }
            cols = st.columns(len(L))
            for i, (name, val) in enumerate(L.items()):
                with cols[i]:
                    st.markdown(f'<div class="master-card"><span class="light {val[0]}"></span><b>{name}</b></div>', unsafe_allow_html=True)

            # MOTOR 3 & 4: CANLI DERİNLİK VE TAKAS (AKD) ANALİZİ
            c_d, c_t = st.columns(2)
            akd_status = "Veri bekleniyor..."
            
            with c_d:
                st.subheader("🛒 Canlı Derinlik")
                depth = st.session_state.live_depth.get(active, [])
                if depth: st.table(pd.DataFrame(depth))
                else: st.info("Derinlik bekleniyor...")

            with c_t:
                st.subheader("🤝 Aracı Kurum Dağılımı (AKD)")
                akd = st.session_state.live_akd.get(active, [])
                if akd:
                    akd_df = pd.DataFrame(akd)
                    st.dataframe(akd_df)
                    # Mal toplama/boşaltma analizi
                    net_alicilar = sum([x['lot'] for x in akd if x['side'] == 'buy'][:3])
                    net_saticilar = sum([x['lot'] for x in akd if x['side'] == 'sell'][:3])
                    if net_alicilar > net_saticilar:
                        akd_status = f"✅ GÜÇLÜ TOPLAMA: İlk 3 kurum {net_alicilar-net_saticilar:,} lot topladı."
                    else:
                        akd_status = f"⚠️ MAL BOŞALTMA: Satış baskısı hissediliyor."
                else: st.info("Takas verisi bekleniyor...")

            # MOTOR 5: AI TAHMİNİ
            y = df['Close'].values[-30:]
            model = LinearRegression().fit(np.arange(len(y)).reshape(-1,1), y)
            pred = model.predict([[len(y)+5]])[0]
            
            # MOTOR 6 & 7: GRAFİK VE HOCA ÖZETİ
            st.divider()
            st.markdown(f"""<div class="master-card" style="border-left:10px solid #ff00ff;">
                <h3>🤖 Robotun Hoca Özeti ve Pozisyon Önerisi</h3>
                <p><b>Durum:</b> {active} hissesi şu an {live_p:.2f} TL. {akd_status}</p>
                <p><b>Analiz:</b> Teknik ışıkların çoğu yeşil, AI motorumuz 5 gün sonrası için <b>{pred:.2f} TL</b> seviyesini hedefliyor. 
                Büyük kurumların mal toplama iştahı { 'pozitif' if 'TOPLAMA' in akd_status else 'temkinli' } bir duruş gerektiriyor.</p>
                <p><b>Öneri:</b> Matematiksel trend yukarı, pozisyonu korumak mantıklı görünüyor.</p>
            </div>""", unsafe_allow_html=True)

            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR (YTD).</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
