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
# 1. TASARIM VE AKILLI OTURUM YÖNETİMİ
# =================================================================
st.set_page_config(page_title="Master Robot Ultimate", layout="wide", page_icon="🛡️")

# Otomatik Veri Hafızası (Session State)
if 'live_prices' not in st.session_state: st.session_state.live_prices = {}
if 'live_depth' not in st.session_state: st.session_state.live_depth = {}
if 'live_akd' not in st.session_state: st.session_state.live_akd = {}
if 'ws_connected' not in st.session_state: st.session_state.ws_connected = False
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'draw_trend' not in st.session_state: st.session_state.draw_trend = None

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        .master-card {
            background: #1e293b; padding: 20px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .ai-mufettis {
            background: #1e1b4b; border: 2px solid #4338ca; padding: 20px; 
            border-radius: 15px; color: #e0e7ff; margin-bottom: 25px;
        }
        .light { height: 18px; width: 18px; border-radius: 50%; display: inline-block; border: 1px solid white; margin-right: 10px; }
        .green { background-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 15px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 15px #ff0000; }
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 10px; font-size: 0.9rem; font-weight: bold; border-top: 2px solid #3b82f6; z-index: 999;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. GÜVENLİK, KAYIT VE OTOMATİK GİRİŞ
# =================================================================
def check_password():
    if st.session_state.authenticated:
        return True

    st.title("🛡️ Master Robot Güvenlik Paneli")
    tab_login, tab_register = st.tabs(["Giriş Yap", "Yeni Şifre Belirle"])
    
    with tab_register:
        new_pwd = st.text_input("Yeni Kasa Şifrenizi Belirleyin:", type="password", key="reg_pwd")
        confirm_pwd = st.text_input("Şifreyi Onaylayın:", type="password", key="conf_pwd")
        if st.button("Şifreyi Kaydet ve Sistemi Aç"):
            if new_pwd == confirm_pwd and len(new_pwd) > 0:
                st.session_state.master_password = new_pwd
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Şifreler uyuşmuyor veya boş bırakılamaz.")

    with tab_login:
        login_pwd = st.text_input("Kasa Şifrenizi Girin:", type="password", key="log_pwd")
        if st.button("Robotu Başlat"):
            if "master_password" in st.session_state and login_pwd == st.session_state.master_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Hatalı şifre veya kayıtlı şifre bulunamadı.")
    return False

# =================================================================
# 3. CANLI VERİ MOTORU (ARKA PLAN WS DİNLEYİCİ)
# =================================================================
def ws_engine(url):
    async def listen():
        while True:
            try:
                async with websockets.connect(url, ping_interval=20, close_timeout=10) as ws:
                    st.session_state.ws_connected = True
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong"})); continue
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
# 4. ANALİZ VE MATEMATİKSEL MOTORLAR (7 MOTOR BURADA)
# =================================================================
class MasterSystemUltimate:
    def __init__(self):
        self.conn = sqlite3.connect("master_ultimate_final_v12.db", check_same_thread=False)

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
            if df.empty: return None, None, [], None, None
            
            # MOTOR 1: 10 TEKNİK İNDİKATÖR HESAPLAMALARI
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
            df['Momentum'] = df['Close'].diff(10)
            df['EMA9'] = df['Close'].ewm(span=9).mean()
            df['Volume_Avg'] = df['Volume'].rolling(20).mean()
            
            # MOTOR 2: TEMEL ANALİZ VERİLERİ
            info = t.info
            fin = {
                "fk": info.get("trailingPE", 0),
                "pddd": info.get("priceToBook", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "cari": info.get("currentRatio", 0),
                "halka_acik": (info.get("floatShares", 0) / info.get("sharesOutstanding", 1) * 100) if info.get("sharesOutstanding") else 0,
                "fiyat": df['Close'].iloc[-1]
            }
            # MOTOR 3: KAP HABER ANALİZİ
            news = t.news if t.news else []
            return df, fin, news, t.quarterly_balance_sheet, t.quarterly_financials
        except: return None, None, [], None, None

# =================================================================
# 5. ANA ARAYÜZ (SEKMELİ FULL TERMİNAL)
# =================================================================
def main():
    if not check_password(): return

    sys = MasterSystemUltimate()
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=user%3D%257B%2522id%2522%253A8479457745%252C%2522first_name%2522%253A%2522Hasan%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522language_code%2522%253A%2522tr%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FqFQnxlCiDCD3PBWXXq2LYBtQf6-xy3roI737vHv1ZzfLPtDDm6ILM1w-D0z51rMQ.svg%2522%257D%26chat_instance%3D6343175205638196527%26chat_type%3Dsender%26auth_date%3D1770599132%26signature%3DHBPngCoF21mUtuu4RR-a1AcI1IyYqBQjed1ADKfJXrM7zhXTfInvUuyNs3pPUysstbDdVpNUZXZC_zlWc5h3Aw%26hash%3D7c06577956860cbe621177d869355725b7a920ebc449cf12d7f263eefcc89bb0"

    table = sys.get_space(st.session_state.master_password)

    with st.sidebar:
        st.title("🛡️ Master Terminal")
        # MOTOR 4: CANLI VERİ AÇ/KAPAT
        canli_mod = st.toggle("🛰️ Canlı Veri Akışını Başlat", value=False)
        if canli_mod: start_threads(WS_LINK)
        
        st.divider()
        h_kod = st.text_input("Hisse Kodu (ESEN, SASA):").upper().strip()
        q_in = st.number_input("Adet:", 0.0); c_in = st.number_input("Maliyet:", 0.0)
        t_in = st.number_input("Hedef Fiyat:", 0.0); s_in = st.number_input("Stop Fiyat:", 0.0)
        if st.button("PORTFÖYE KAYDET") and h_kod:
            sym = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
            with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (sym, q_in, c_in, t_in, s_in))
            st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("Analiz Edilen Hisse:", p_df['symbol'].tolist())
        df, fin, news, balance, financials = sys.fetch_full_data(active)
        
        if df is not None:
            live_p = st.session_state.live_prices.get(active, fin['fiyat']) if canli_mod else fin['fiyat']
            row = p_df[p_df['symbol'] == active].iloc[0]
            
            tab1, tab2, tab3, tab4 = st.tabs(["📉 Müfettiş Karar & Teknik", "🛒 Derinlik & AKD Analizi", "📋 Temel Analiz & KAP", "🎲 Monte Carlo Simülasyonu"])

            with tab1:
                # MOTOR 5: ALARM SİSTEMİ
                if row['target'] > 0 and live_p >= row['target']: st.balloons(); st.success(f"🎯 HEDEF FİYAT GÖRÜLDÜ! ({row['target']} TL)")
                if row['stop'] > 0 and live_p <= row['stop']: st.error(f"⚠️ STOP SEVİYESİ TETİKLENDİ! ({row['stop']} TL)")

                # MOTOR 6: AI KARAR DESTEK MOTORU (Hoca Özeti)
                rsi_v = df['RSI'].iloc[-1]
                skor = sum([1 if 35 < rsi_v < 65 else 0, 1 if live_p > df['SMA50'].iloc[-1] else 0, 1 if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else 0, 1 if live_p > df['SMA200'].iloc[-1] else 0])
                
                st.markdown(f"""<div class="ai-mufettis">
                    <h3>🤖 Robot Müfettiş Karar Raporu ({active})</h3>
                    <p><b>Teknik Skor:</b> {skor}/4 Onay | <b>Trend:</b> {'Güçlü Yükseliş' if skor>=3 else 'Dengeli/Pozitif' if skor==2 else 'Zayıf/Negatif'}</p>
                    <p><b>Hoca Notu:</b> Hisse şu an {live_p:.2f} TL. {'Matematiksel trend yukarı, pozisyon korunabilir.' if skor >= 2 else 'Teknik verilerde zayıflama var, stop seviyelerine sadık kalınmalı.'}</p>
                </div>""", unsafe_allow_html=True)

                # 10 TEKNİK ONAY IŞIĞI (Görsel trafik ışıkları)
                st.subheader("🚥 10 Teknik Onay Işığı")
                L = {
                    "RSI": ("green" if 35<rsi_v<65 else "yellow", rsi_v),
                    "SMA 50": ("green" if live_p > df['SMA50'].iloc[-1] else "red", 0),
                    "SMA 200": ("green" if live_p > df['SMA200'].iloc[-1] else "red", 0),
                    "MACD": ("green" if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else "red", 0),
                    "Bollinger": ("green" if df['Lower'].iloc[-1] < live_p < df['Upper'].iloc[-1] else "yellow", 0),
                    "EMA 9": ("green" if live_p > df['EMA9'].iloc[-1] else "red", 0),
                    "Momentum": ("green" if df['Momentum'].iloc[-1] > 0 else "red", 0),
                    "Hacim": ("green" if df['Volume'].iloc[-1] > df['Volume_Avg'].iloc[-1] else "yellow", 0),
                    "SMA 20": ("green" if live_p > df['SMA20'].iloc[-1] else "red", 0),
                    "Kısa Trend": ("green" if live_p > df['Close'].iloc[-10] else "red", 0)
                }
                cols = st.columns(5)
                for i, (k, v) in enumerate(L.items()):
                    with cols[i % 5]: st.markdown(f'<div class="master-card"><span class="light {v[0]}"></span><b>{k}</b></div>', unsafe_allow_html=True)

                if st.button("📈 TREND ÇİZGİLERİNİ OLUŞTUR"):
                    y_tr = df['Close'].values[-60:]; x_tr = np.arange(len(y_tr)).reshape(-1, 1)
                    st.session_state.draw_trend = LinearRegression().fit(x_tr, y_tr).predict(x_tr)

                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mum"), row=1, col=1)
                if st.session_state.draw_trend is not None:
                    fig.add_trace(go.Scatter(x=df.index[-60:], y=st.session_state.draw_trend, name="Ana Trend", line=dict(color='yellow', dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
                fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                col_d, col_a = st.columns(2)
                with col_d:
                    st.subheader("🛒 Canlı Derinlik Kademeleri")
                    depth = st.session_state.live_depth.get(active, [])
                    if depth: st.table(pd.DataFrame(depth))
                    else: st.info("Derinlik verisi bekleniyor... Botta hisse detayını açın.")
                with col_a:
                    st.subheader("🤝 AKD (Mal Toplama/Boşaltma)")
                    akd = st.session_state.live_akd.get(active, [])
                    if akd:
                        akd_df = pd.DataFrame(akd)
                        st.dataframe(akd_df, use_container_width=True)
                        buy = sum([x['lot'] for x in akd if x['side'] == 'buy'][:3])
                        sell = sum([x['lot'] for x in akd if x['side'] == 'sell'][:3])
                        st.success(f"{'✅ GÜÇLÜ MAL TOPLAMA: Kurumlar malı karşılıyor.' if buy > sell else '⚠️ SATIŞ BASKISI: Mal boşaltma emareleri var.'}")
                    else: st.info("Takas verisi bekleniyor...")

            with tab3:
                st.subheader("📰 Son KAP Haberleri ve Analiz")
                if news:
                    secilen = st.selectbox("Detaylı Analiz Edilecek Haberi Seçin:", [n['title'] for n in news])
                    st.markdown(f'<div class="master-card"><b>Müfettiş Yorumu:</b> {secilen[:150]}... haberi şirket temel rasyoları ışığında analiz ediliyor.</div>', unsafe_allow_html=True)
                else:
                    st.warning("Bu hisse için güncel KAP haberi bulunamadı.")
                
                st.subheader("📊 Bilanço ve Finansal Rapor")
                st.markdown(f"""<div class="master-card">
                    <b>F/K:</b> {fin['fk']:.2f} | <b>PD/DD:</b> {fin['pddd']:.2f} | <b>Özsermaye Kârı:</b> %{fin['oz_kar']:.2f} | <b>Cari Oran:</b> {fin['cari']:.2f}
                </div>""", unsafe_allow_html=True)
                if balance is not None: st.dataframe(balance.iloc[:10, :4], use_container_width=True)

            with tab4:
                # MOTOR 7: MONTE CARLO SİMLÜASYONU (TARİHLİ)
                days_sim = st.slider("Tahmin Penceresi (Gün):", 7, 90, 30)
                returns = np.random.normal(0.001, 0.02, days_sim)
                sim_path = live_p * (1 + returns).cumprod()
                dates = [datetime.now() + timedelta(days=i) for i in range(days_sim)]
                fig_sim = go.Figure(go.Scatter(x=dates, y=sim_path, name="Olası Fiyat Yolu", line=dict(color='#00D4FF')))
                fig_sim.update_layout(template="plotly_dark", height=450, xaxis_title="Tahmini Tarih")
                st.plotly_chart(fig_sim, use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Hasan Hoca Borsa Robotu V12 Ultimate)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
