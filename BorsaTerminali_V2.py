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
# 1. TASARIM VE OTOMATİK OTURUM SİSTEMİ
# =================================================================
st.set_page_config(page_title="Master Finans Koçu V12", layout="wide", page_icon="🛡️")

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
        .kap-card {
            background: #0f172a; border: 1px solid #334155; 
            padding: 15px; border-radius: 10px; margin-bottom: 10px;
        }
        .green-text { color: #00ff00; font-weight: bold; }
        .red-text { color: #ff4b4b; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. GÜVENLİK VE VERİ MOTORLARI
# =================================================================
def check_password():
    if st.session_state.authenticated: return True
    st.title("🛡️ Master Robot Güvenlik Paneli")
    tab_login, tab_register = st.tabs(["Giriş Yap", "Yeni Şifre Belirle"])
    with tab_register:
        new_pwd = st.text_input("Şifrenizi Belirleyin:", type="password", key="reg_pwd")
        if st.button("Şifreyi Kaydet"):
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

class MasterSystem:
    def __init__(self):
        self.conn = sqlite3.connect("master_ultimate_pro_final.db", check_same_thread=False)

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
            
            # 10 TEKNİK MOTOR
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
                "ozet": info.get("longBusinessSummary", "Bilgi bulunamadı."),
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
# 3. ANA ARAYÜZ VE KOÇLUK MANTIĞI
# =================================================================
def main():
    if not check_password(): return
    sys = MasterSystem()
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=..." # URL BURAYA

    table = sys.get_space(st.session_state.master_password)

    with st.sidebar:
        st.title("🛡️ Master Kontrol")
        canli_mod = st.toggle("🛰️ Canlı Veriyi Başlat", value=False)
        if canli_mod: start_threads(WS_LINK)
        st.divider()
        h_kod = st.text_input("Hisse Ekle (SASA, ESEN):").upper().strip()
        if st.button("LİSTEYE EKLE") and h_kod:
            sym = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
            with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,0,0,0,0)", (sym,))
            st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("İncele:", p_df['symbol'].tolist())
        df, fin, news, balance, financials = sys.fetch_full_data(active)
        
        if df is not None:
            live_p = st.session_state.live_prices.get(active, fin['fiyat'])
            
            # --- MOTOR 1: ŞİRKET HAKKINDA DOYURUCU BİLGİ ---
            st.header(f"🏢 {fin['ad']}")
            with st.expander("📖 Şirket Profili ve Faaliyet Özeti"):
                st.write(f"**Sektör:** {fin['sektor']}")
                st.write(fin['ozet'])

            # --- MOTOR 2: AI FİNANS KOÇU (DETAYLI STRATEJİ) ---
            rsi_v = df['RSI'].iloc[-1]
            trend_ok = live_p > df['SMA50'].iloc[-1]
            
            st.markdown(f"""<div class="coach-box">
                <h3>🤖 Finans Koçu Karar Raporu</h3>
                <p><b>Matematiksel Durum:</b> {active} hissesi şu an {live_p:.2f} TL. 
                Hisse {'50 günlük ortalamasının üzerinde (Trend Pozitif)' if trend_ok else 'ortalamanın altında (Trend Zayıf)'}.</p>
                <p><b>Temel Bakış:</b> Şirket %{fin['oz_kar']:.2f} özsermaye kârlılığı ile çalışıyor. 
                Cari oranı {fin['cari']:.2f}; yani {'borç ödeme gücü sağlam' if fin['cari'] > 1.2 else 'likiditeye dikkat edilmeli'}.</p>
                <p><b>Strateji:</b> {'RSI toplama bölgesinde, kademeli alım denenebilir.' if rsi_v < 45 else 'Hisse doygunluğa yakın, yeni alım için düzeltme beklenebilir.'}</p>
            </div>""", unsafe_allow_html=True)

            # --- MOTOR 3: SON 10 KAP HABERİ VE AI YORUMU ---
            st.subheader("📰 Son 10 KAP Haberi ve Müfettiş Analizi")
            if news:
                news_titles = [n['title'] for n in news[:10]]
                selected_kap = st.selectbox("Yorumlanacak Haberi Seçin:", news_titles)
                
                # Dinamik Haber Yorumu
                h_low = selected_kap.lower()
                impact = "NÖTR"
                if any(x in h_low for x in ["iş", "ihale", "anlaşma", "kâr", "yatırım"]): impact = "POZİTİF"
                elif any(x in h_low for x in ["dava", "zarar", "iptal", "borç"]): impact = "NEGATİF"
                
                st.markdown(f"""<div class="kap-card">
                    <b>Haber:</b> {selected_kap}<br>
                    <b>Muhtemel Etki:</b> <span class="{'green-text' if impact=='POZİTİF' else 'red-text' if impact=='NEGATİF' else ''}">{impact}</span><br>
                    <b>Yorum:</b> {'Bu gelişme şirketin gelecekteki nakit akışını olumlu etkileyebilir.' if impact=='POZİTİF' else 'Kısa vadeli baskı yaratabilir, takip edilmeli.' if impact=='NEGATİF' else 'Rutin bir bilgilendirme haberi.'}
                </div>""", unsafe_allow_html=True)
            else:
                st.info("KAP haberi bulunamadı.")

            # SEKMELİ DETAYLAR
            tab1, tab2, tab3 = st.tabs(["📉 Teknik Müfettiş", "📊 Bilanço & Rasyolar", "🎲 Gelecek Simülasyonu"])
            
            with tab1:
                st.subheader("🚥 Teknik Onay Işıkları")
                cols = st.columns(4)
                cols[0].metric("RSI (14)", f"{rsi_v:.2f}")
                cols[1].metric("F/K Oranı", f"{fin['fk']:.2f}")
                cols[2].metric("PD/DD", f"{fin['pddd']:.2f}")
                cols[3].metric("Özsermaye Kârı", f"%{fin['oz_kar']:.1f}")
                
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=500)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("📋 Bilanço ve Gelir Tablosu")
                if balance is not None: st.dataframe(balance.iloc[:10, :4], use_container_width=True)
                else: st.warning("Bilanço verisi yüklenemedi.")

            with tab3:
                st.subheader("🎲 30 Günlük Tarihli Simülasyon")
                days = 30
                returns = np.random.normal(0.001, 0.02, days)
                path = live_p * (1 + returns).cumprod()
                dates = [datetime.now() + timedelta(days=i) for i in range(days)]
                fig_sim = go.Figure(go.Scatter(x=dates, y=path, line=dict(color='#00D4FF')))
                fig_sim.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig_sim, use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Master Robot V12)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
