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
# 1. TASARIM VE GÜVENLİK SİSTEMİ (DEMİRLENMİŞ GİRİŞ)
# =================================================================
st.set_page_config(page_title="Finans Koçu V12 Pro", layout="wide", page_icon="🛡️")

# Otomatik Veri Hafızası
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
        .info-card {
            background: #1e293b; padding: 20px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 15px;
        }
        .light { height: 18px; width: 18px; border-radius: 50%; display: inline-block; border: 1px solid white; margin-right: 10px; }
        .green { background-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 15px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 15px #ff0000; }
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 8px; font-size: 0.85rem; font-weight: bold; border-top: 2px solid #3b82f6; z-index: 999;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. GÜVENLİK, KAYIT VE OTOMATİK WS MOTORU
# =================================================================
def check_password():
    if st.session_state.authenticated: return True
    st.title("🛡️ Master Robot Güvenlik Paneli")
    tab_login, tab_register = st.tabs(["Giriş Yap", "Yeni Şifre Belirle"])
    with tab_register:
        new_pwd = st.text_input("Kasa Şifrenizi Belirleyin:", type="password", key="reg_pwd")
        if st.button("Şifreyi Kaydet ve Sistemi Kilitle"):
            st.session_state.master_password = new_pwd
            st.session_state.authenticated = True
            st.rerun()
    with tab_login:
        login_pwd = st.text_input("Kasa Şifreniz:", type="password", key="log_pwd")
        if st.button("Giriş Yap"):
            if "master_password" in st.session_state and login_pwd == st.session_state.master_password:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("Hatalı Şifre!")
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

# =================================================================
# 3. ANALİZ VE KOÇLUK MOTORLARI (7 MOTOR BİLEŞİMİ)
# =================================================================
class MasterSystem:
    def __init__(self):
        self.conn = sqlite3.connect("master_ultimate_coach_v12.db", check_same_thread=False)

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
            
            # 10 TEKNİK MOTOR (V12 Standartları)
            df['SMA20'] = df['Close'].rolling(20).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            e1, e2 = df['Close'].ewm(span=12).mean(), df['Close'].ewm(span=26).mean()
            df['MACD'] = e1 - e2
            df['Signal'] = df['MACD'].ewm(span=9).mean()
            
            info = t.info
            fin = {
                "ad": info.get("longName", symbol),
                "ozet": info.get("longBusinessSummary", "Bilgi yok."),
                "fk": info.get("trailingPE", 0),
                "pddd": info.get("priceToBook", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "cari": info.get("currentRatio", 0),
                "sektor": info.get("sector", "N/A"),
                "fiyat": df['Close'].iloc[-1]
            }
            return df, fin, (t.news if t.news else []), t.quarterly_balance_sheet, t.quarterly_financials
        except: return None, None, [], None, None

# =================================================================
# 4. ANA TERMİNAL VE KOÇLUK KARAR MERKEZİ
# =================================================================
def main():
    if not check_password(): return
    sys = MasterSystem()
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=..." # URL Buraya

    table = sys.get_space(st.session_state.master_password)

    with st.sidebar:
        st.title("🛡️ Master Kontrol")
        canli_mod = st.toggle("🛰️ Canlı Veriyi Aktif Et", value=False)
        if canli_mod: start_threads(WS_LINK)
        st.divider()
        h_kod = st.text_input("Hisse Ekle (SASA, ESEN):").upper().strip()
        q_in = st.number_input("Adet:", 0.0); c_in = st.number_input("Maliyet:", 0.0)
        t_in = st.number_input("Hedef:", 0.0); s_in = st.number_input("Stop:", 0.0)
        if st.button("KAYDET") and h_kod:
            sym = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
            with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (sym, q_in, c_in, t_in, s_in))
            st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("İncele:", p_df['symbol'].tolist())
        df, fin, news, balance, financials = sys.fetch_full_data(active)
        
        if df is not None:
            live_p = st.session_state.live_prices.get(active, fin['fiyat'])
            row = p_df[p_df['symbol'] == active].iloc[0]

            # --- MOTOR 1: AI FİNANS KOÇU KARAR DESTEK ---
            st.header(f"🏢 {fin['ad']}")
            rsi_v = df['RSI'].iloc[-1]
            trend_ok = live_p > df['SMA50'].iloc[-1]
            
            # Karar Algoritması
            tavsiye = "Dengeli seyir, pozisyon KORUNABİLİR."
            if rsi_v < 40 and trend_ok: tavsiye = "Hisse matematiksel olarak ucuz ve trend üzerinde. **ALIM** için güçlü bir zemin var."
            elif rsi_v > 75: tavsiye = "Hisse aşırı alım bölgesinde yorulmuş. **KÂR SATIŞI** veya izleme önerilir."
            elif live_p < row['stop'] and row['stop'] > 0: tavsiye = "⚠️ **STOP:** Zarar kes seviyesinin altındasınız, dikkatli olunmalı."

            st.markdown(f"""<div class="coach-box">
                <h3>🤖 Robot Finans Koçu Karar Raporu</h3>
                <p><b>Şirket Analizi:</b> {fin['sektor']} sektöründe faaliyet gösteren şirket, %{fin['oz_kar']:.2f} özsermaye kârlılığına sahip. Cari oranı {fin['cari']:.2f} ile {'likidite açısından sağlam' if fin['cari']>1.2 else 'dikkat gerektiren'} bir yapıda.</p>
                <p><b>Yol Haritası:</b> {tavsiye} Hedef: {row['target']} TL seviyeleri teknik olarak beklenebilir.</p>
                <small>Hoca Notu: Bu robot temel ve teknik verileri tek bir potada eriterek size matematiksel ihtimali söyler.</small>
            </div>""", unsafe_allow_html=True)

            # --- MOTOR 2: AÇILIR LİSTELİ SON 10 KAP ANALİZİ ---
            st.subheader("📰 Son 10 KAP Haberi ve Müfettiş Yorumu")
            if news:
                news_titles = [n['title'] for n in news[:10]]
                selected_kap = st.selectbox("İncelemek istediğiniz haberi seçin:", news_titles)
                
                # Dinamik Haber Yorumlama
                h_low = selected_kap.lower()
                kap_notu = "Sıradan bir bilgilendirme haberi."
                if any(x in h_low for x in ["iş", "ihale", "anlaşma", "kâr"]): kap_notu = "✅ POZİTİF: Şirketin kasasına para gireceğini gösteren bir gelişme."
                elif any(x in h_low for x in ["dava", "zarar", "borç", "iptal"]): kap_notu = "⚠️ NEGATİF: Mali yapıyı veya marka algısını zorlayabilecek bir haber."
                
                st.markdown(f"""<div class="info-card" style="border-left-color: #00D4FF;">
                    <b>Seçilen Haber:</b> {selected_kap}<br>
                    <b>Müfettiş Yorumu:</b> {kap_notu}
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("Haber akışı şu an ulaşılamıyor.")

            # SEKMELİ ANALİZLER (7 Motorun Tamamı)
            tab1, tab2, tab3, tab4 = st.tabs(["📉 Teknik & Trend", "🛒 Derinlik & AKD", "📊 Bilanço & Detay", "🎲 Gelecek Tahmini"])
            
            with tab1:
                st.subheader("🚥 Teknik Onay Işıkları")
                cols = st.columns(4)
                cols[0].metric("RSI (Güç)", f"{rsi_v:.2f}")
                cols[1].metric("SMA50 Trend", "POZİTİF" if trend_ok else "NEGATİF")
                cols[2].metric("F/K Oranı", f"{fin['fk']:.2f}")
                cols[3].metric("Özsermaye Kârı", f"%{fin['oz_kar']:.1f}")
                
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                c_d, c_a = st.columns(2)
                with c_d:
                    st.subheader("🛒 Derinlik")
                    depth = st.session_state.live_depth.get(active, [])
                    if depth: st.table(pd.DataFrame(depth))
                    else: st.info("Derinlik için botta bu hisseyi bir kez açın.")
                with c_a:
                    st.subheader("🤝 AKD (Mal Toplama)")
                    akd = st.session_state.live_akd.get(active, [])
                    if akd: st.dataframe(pd.DataFrame(akd))
                    else: st.info("Takas verisi bekleniyor...")

            with tab3:
                st.subheader("📋 Bilanço & Şirket Profili")
                st.info(fin['ozet'])
                if balance is not None: st.dataframe(balance.iloc[:10, :4])

            with tab4:
                st.subheader("🎲 30 Günlük Tarihli Simülasyon")
                days = 30
                returns = np.random.normal(0.001, 0.02, days)
                sim_path = live_p * (1 + returns).cumprod()
                dates = [datetime.now() + timedelta(days=i) for i in range(days)]
                fig_sim = go.Figure(go.Scatter(x=dates, y=sim_path, line=dict(color='#00D4FF')))
                fig_sim.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig_sim, use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Master Robot V12 Pro)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
