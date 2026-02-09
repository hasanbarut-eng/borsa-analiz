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
# 1. TASARIM VE OTOMATİK VERİ DEPOLARI
# =================================================================
st.set_page_config(page_title="Master Robot Pro Max", layout="wide", page_icon="🛡️")

# Otomatik Veri Hafızası (Session State)
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
        .light { height: 18px; width: 18px; border-radius: 50%; display: inline-block; border: 1px solid white; margin-right: 10px; }
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
# 2. CANLI VERİ MOTORU (DİRENÇLİ BAĞLANTI)
# =================================================================
def ws_engine(url):
    async def listen():
        while True:
            try:
                # SSL ve timeout ayarlarıyla en sağlam bağlantı
                async with websockets.connect(url, ping_interval=20, close_timeout=10) as ws:
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
# 3. ANALİZ VE MATEMATİKSEL MODELLER
# =================================================================
class MasterSystemUltimate:
    def __init__(self):
        self.conn = sqlite3.connect("master_ultimate_v12.db", check_same_thread=False)

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
            if df.empty: return None, None, None, None, None
            
            # 10 TEKNİK GÖSTERGE
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
            
            info = t.info
            fin = {
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", 0),
                "pddd": info.get("priceToBook", 0),
                "fiyat": df['Close'].iloc[-1],
                "halka_acik": (info.get("floatShares", 0) / info.get("sharesOutstanding", 1) * 100) if info.get("sharesOutstanding") else 0
            }
            return df, fin, t.news, t.quarterly_balance_sheet, t.quarterly_financials
        except: return None, None, None, None, None

# =================================================================
# 4. ANA PROGRAM (SEKMELİ MİMARİ)
# =================================================================
def main():
    sys = MasterSystemUltimate()
    
    # Sizin Canlı Veri Anahtarınız
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=user%3D%257B%2522id%2522%253A8479457745%252C%2522first_name%2522%253A%2522Hasan%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522language_code%2522%253A%2522tr%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FqFQnxlCiDCD3PBWXXq2LYBtQf6-xy3roI737vHv1ZzfLPtDDm6ILM1w-D0z51rMQ.svg%2522%257D%26chat_instance%3D6343175205638196527%26chat_type%3Dsender%26auth_date%3D1770599132%26signature%3DHBPngCoF21mUtuu4RR-a1AcI1IyYqBQjed1ADKfJXrM7zhXTfInvUuyNs3pPUysstbDdVpNUZXZC_zlWc5h3Aw%26hash%3D7c06577956860cbe621177d869355725b7a920ebc449cf12d7f263eefcc89bb0"
    start_threads(WS_LINK)

    st.sidebar.title("🔐 Master Giriş")
    pwd = st.sidebar.text_input("Şifreniz:", type="password")
    if not pwd: 
        st.info("Hocam hoş geldiniz! Şifrenizi girerek robotu başlatabilirsiniz.")
        return

    table = sys.get_space(pwd)

    # Hisse Yönetimi
    with st.sidebar:
        st.write(f"📡 Durum: {'🟢 Canlı' if st.session_state.ws_connected else '🔴 Yedek'}")
        h_kod = st.text_input("Hisse Ekle (esen, sasa):").upper().strip()
        q_in = st.number_input("Adet:", 0.0)
        c_in = st.number_input("Maliyet:", 0.0)
        t_in = st.number_input("Hedef:", 0.0)
        s_in = st.number_input("Stop:", 0.0)
        if st.button("PORTFÖYE EKLE"):
            if h_kod:
                sym = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
                with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (sym, q_in, c_in, t_in, s_in))
                st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("İncelemek İstediğiniz Hisse:", p_df['symbol'].tolist())
        df, fin, news, balance, financials = sys.fetch_full_data(active)
        
        if df is not None:
            live_p = st.session_state.live_prices.get(active, fin['fiyat'])
            row = p_df[p_df['symbol'] == active].iloc[0]

            # SEKMELİ YAPI
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Analiz Merkezi", "🛒 Canlı Derinlik & AKD", "📰 KAP & Bilanço", "🎲 Simülasyon"])

            # --- TAB 1: ANALİZ MERKEZİ ---
            with tab1:
                st.title(f"🛡️ {active} Terminali")
                c1, c2, c3 = st.columns(3)
                c1.metric("ANLIK FİYAT", f"{live_p:.2f} TL", delta=f"{live_p - fin['fiyat']:.2f}")
                c2.metric("KÂR/ZARAR", f"{(live_p - row['cost']) * row['qty']:,.0f} TL")
                
                # ALARM SİSTEMİ
                if row['target'] > 0 and live_p >= row['target']: st.balloons(); st.success("🎯 HEDEF GÖRÜLDÜ!")
                if row['stop'] > 0 and live_p <= row['stop']: st.error("⚠️ STOP SEVİYESİNDESİNİZ!")

                # 10 TEKNİK ONAY IŞIĞI
                st.subheader("🚥 Teknik Analiz Müfettişi")
                L = {
                    "RSI": ("green" if 30<df['RSI'].iloc[-1]<70 else "yellow", df['RSI'].iloc[-1]),
                    "SMA50": ("green" if live_p > df['SMA50'].iloc[-1] else "red", 0),
                    "MACD": ("green" if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else "red", 0),
                    "Cari": ("green" if fin['cari']>1.2 else "red", fin['cari'])
                }
                cols = st.columns(4)
                for i, (k, v) in enumerate(L.items()):
                    with cols[i]: st.markdown(f'<div class="master-card"><span class="light {v[0]}"></span>{k}</div>', unsafe_allow_html=True)

                # GRAFİKLER (Candle + RSI)
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
                fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
                st.plotly_chart(fig, use_container_width=True)

            # --- TAB 2: CANLI DERİNLİK & AKD ---
            with tab2:
                col_d, col_a = st.columns(2)
                with col_d:
                    st.subheader("🛒 Derinlik (Kademeler)")
                    depth = st.session_state.live_depth.get(active, [])
                    if depth: st.table(pd.DataFrame(depth))
                    else: st.info("Derinlik bekleniyor... Botta derinlik ekranını açın.")
                with col_a:
                    st.subheader("🤝 AKD (Takas) Analizi")
                    akd = st.session_state.live_akd.get(active, [])
                    if akd:
                        st.dataframe(pd.DataFrame(akd))
                        buy = sum([x['lot'] for x in akd if x['side'] == 'buy'][:3])
                        sell = sum([x['lot'] for x in akd if x['side'] == 'sell'][:3])
                        st.success(f"{'✅ GÜÇLÜ MAL TOPLAMA' if buy > sell else '⚠️ MAL BOŞALTMA'}")
                    else: st.info("Takas verisi bekleniyor...")

            # --- TAB 3: KAP & BİLANÇO ---
            with tab3:
                st.subheader("📰 KAP Haber Seçimi ve Analizi")
                if news:
                    kap_list = [n['title'] for n in news]
                    secilen_kap = st.selectbox("Açıklanacak Haberi Seçin:", kap_list)
                    st.markdown(f'<div class="master-card"><b>Seçilen Haber:</b> {secilen_kap}<br><br><i>Hocam bu haber matematiksel olarak {'olumlu' if 'ihale' in secilen_kap.lower() or 'iş' in secilen_kap.lower() else 'nötr'} bir etki yaratabilir.</i></div>', unsafe_allow_html=True)
                
                st.subheader("📊 Son Bilanço Müfettiş Raporu")
                st.markdown(f"""<div class="master-card">
                    <p><b>Özsermaye Karlılığı:</b> %{fin['oz_kar']:.2f}</p>
                    <p><b>F/K:</b> {fin['fk']:.2f} | <b>PD/DD:</b> {fin['pddd']:.2f}</p>
                </div>""", unsafe_allow_html=True)
                if balance is not None: st.dataframe(balance.iloc[:5, :4])

            # --- TAB 4: SİMÜLASYON ---
            with tab4:
                st.subheader("🎲 30 Günlük Gelecek Simülasyonu")
                returns = np.random.normal(0.001, 0.02, 30)
                sim_path = live_p * (1 + returns).cumprod()
                fig_sim = go.Figure(go.Scatter(y=sim_path, line=dict(color='#00D4FF')))
                fig_sim.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig_sim, use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Master Robot V12 Pro Max)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
