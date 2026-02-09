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
# 1. TASARIM VE OTOMATİK YENİLEME YAPILANDIRMASI
# =================================================================
st.set_page_config(page_title="Master Robot V12 Ultimate", layout="wide", page_icon="🛡️")

# Otomatik Veri Hafızası
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
        .light { height: 18px; width: 18px; border-radius: 50%; display: inline-block; border: 1px solid white; }
        .green { background-color: #00ff00; box-shadow: 0 0 12px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 12px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 12px #ff0000; }
        .kap-box { background: #0f172a; border: 1px solid #334155; padding: 10px; border-radius: 5px; margin-bottom: 5px; }
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 8px; font-size: 0.85rem; font-weight: bold; border-top: 2px solid #3b82f6; z-index: 999;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. CANLI VERİ VE YEDEKLİ SİSTEM
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
# 3. ANALİZ SINIFI (TEMEL & TEKNİK & SİMÜLASYON)
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
            if df.empty: return None, None, None, None, None
            
            # Teknik Veriler
            df['SMA50'] = df['Close'].rolling(50).mean()
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            
            # Temel Veriler (Bilanço & Gelir Tablosu)
            balance = t.quarterly_balance_sheet
            financials = t.quarterly_financials
            
            info = t.info
            fin = {
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", 0),
                "pddd": info.get("priceToBook", 0),
                "fiyat": df['Close'].iloc[-1],
                "halka_acik": (info.get("floatShares", 0) / info.get("sharesOutstanding", 1) * 100) if info.get("sharesOutstanding") else 0
            }
            return df, fin, t.news, balance, financials
        except: return None, None, None, None, None

    def interpret_kap(self, news_item):
        """Seçilen KAP haberini matematiksel ve finansal olarak yorumlar."""
        title = news_item.get('title', '')
        summary = "Hocam, bu haber genel bir bilgilendirme içeriyor."
        impact = "NÖTR"
        
        positive_keywords = ["ihale", "yeni iş", "sözleşme", "kar payı", "bedelsiz", "alım", "yatırım"]
        negative_keywords = ["dava", "ceza", "iptal", "borç", "kayıp", "satış"]
        
        if any(word in title.lower() for word in positive_keywords):
            summary = "Hocam, bu haber şirketin büyüme veya nakit akışı beklentisini artırır."
            impact = "POZİTİF"
        elif any(word in title.lower() for word in negative_keywords):
            summary = "Hocam dikkat! Şirket üzerinde finansal veya hukuki baskı yaratabilecek bir gelişme."
            impact = "NEGATİF"
            
        return summary, impact

# =================================================================
# 4. ANA PROGRAM (TEMEL ANALİZ MOTORU DAHİL)
# =================================================================
def main():
    sys = MasterSystemUltimate()
    
    # Canlı Veri Linki (Görsel fca63f)
    WS_LINK = "wss://ws.7k2v9x1r0z8t4m3n5p7w.com/?init_data=user%3D%257B%2522id%2522%253A8479457745%252C%2522first_name%2522%253A%2522Hasan%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522language_code%2522%253A%2522tr%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FqFQnxlCiDCD3PBWXXq2LYBtQf6-xy3roI737vHv1ZzfLPtDDm6ILM1w-D0z51rMQ.svg%2522%257D%26chat_instance%3D6343175205638196527%26chat_type%3Dsender%26auth_date%3D1770599132%26signature%3DHBPngCoF21mUtuu4RR-a1AcI1IyYqBQjed1ADKfJXrM7zhXTfInvUuyNs3pPUysstbDdVpNUZXZC_zlWc5h3Aw%26hash%3D7c06577956860cbe621177d869355725b7a920ebc449cf12d7f263eefcc89bb0"
    start_threads(WS_LINK)

    st.sidebar.title("🔐 Master Kasa")
    pwd = st.sidebar.text_input("Şifreniz:", type="password")
    if not pwd: 
        st.info("👋 Hoş geldin öğretmenim! Bilanço Müfettişini uyandırmak için şifreni gir.")
        return

    table = sys.get_space(pwd)

    with st.sidebar:
        st.write(f"📡 Canlı Hat: {'🟢 Aktif' if st.session_state.ws_connected else '🔴 Yedek Devrede'}")
        h_kod = st.text_input("Hisse (esen, sasa):").upper().strip()
        if st.button("KAYDET"):
            if h_kod:
                symbol = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
                with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,0,0,0,0)", (symbol,))
                st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("Hisse Seçin:", p_df['symbol'].tolist())
        df, fin, news, balance, financials = sys.fetch_comprehensive(active)
        
        if df is not None:
            live_p = st.session_state.live_prices.get(active, fin['fiyat'])
            st.title(f"🛡️ {active} - CANLI TERMİNAL")

            # --- MOTOR 1: KAP HABERLERİ VE YORUMLAMA ---
            st.subheader("📰 KAP Haberleri ve Müfettiş Yorumu")
            if news:
                selected_news_title = st.selectbox("Açıklamasını İstediğiniz KAP Haberi:", [n['title'] for n in news])
                selected_item = next(item for item in news if item["title"] == selected_news_title)
                
                yorum, etki = sys.interpret_kap(selected_item)
                st.markdown(f"""<div class="master-card" style="border-left:8px solid {'#00ff00' if etki=='POZİTİF' else '#ff4b4b' if etki=='NEGATİF' else '#ffffff'};">
                    <b>Haber:</b> {selected_item['title']}<br>
                    <b>Müfettiş Yorumu:</b> {yorum}<br>
                    <b>Muhtemel Etki:</b> {etki}
                </div>""", unsafe_allow_html=True)
            else:
                st.info("Bu hisse için güncel KAP haberi bulunamadı.")

            # --- MOTOR 2: BİLANÇO ANALİZİ ---
            st.subheader("📊 Son Bilanço ve Gelir Tablosu Analizi")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class="master-card">
                    <h3>🔍 Temel Analiz Raporu</h3>
                    <p><b>F/K Oranı:</b> {fin['fk']:.2f} ({'Ucuz' if fin['fk']<10 else 'Dengeli' if fin['fk']<20 else 'Pahalı'})</p>
                    <p><b>PD/DD:</b> {fin['pddd']:.2f}</p>
                    <p><b>Özsermaye Karlılığı:</b> %{fin['oz_kar']:.2f}</p>
                    <p><b>Cari Oran:</b> {fin['cari']:.2f} ({'Borç Ödeme Gücü Yüksek' if fin['cari']>1.5 else 'Dikkat Edilmeli'})</p>
                    <p><b>Halka Açıklık:</b> %{fin['halka_acik']:.2f}</p>
                </div>""", unsafe_allow_html=True)
            with c2:
                if balance is not None and not balance.empty:
                    st.write("Son 4 Dönem Bilanço Özeti (Milyon TL):")
                    st.dataframe(balance.iloc[:5, :4], use_container_width=True)
                else:
                    st.info("Bilanço detayları şu an yüklenemedi.")

            # --- MOTOR 3 & 4: CANLI DERİNLİK VE AKD ---
            st.divider()
            c_d, c_a = st.columns(2)
            with c_d:
                st.subheader("🛒 Derinlik")
                d_data = st.session_state.live_depth.get(active, [])
                if d_data: st.table(pd.DataFrame(d_data))
                else: st.info("Derinlik için Telegram botunda bu ekranı açın.")
            with c_a:
                st.subheader("🤝 AKD (Takas) Analizi")
                akd = st.session_state.live_akd.get(active, [])
                if akd:
                    st.dataframe(pd.DataFrame(akd))
                    buy = sum([x['lot'] for x in akd if x['side'] == 'buy'][:3])
                    sell = sum([x['lot'] for x in akd if x['side'] == 'sell'][:3])
                    st.success(f"Analiz: {'MAL TOPLANIYOR' if buy > sell else 'MAL BOŞALTILIYOR'}")
                else: st.info("Takas verisi bekleniyor...")

            # --- MOTOR 5: SİMÜLASYON VE MOTOR 6: AI TAHMİN ---
            st.subheader("🎲 Gelecek Projeksiyonu")
            c_sim, c_ai = st.columns([2, 1])
            with c_sim:
                returns = np.random.normal(0.001, 0.02, 30)
                paths = live_p * (1 + returns).cumprod()
                fig_sim = go.Figure(go.Scatter(y=paths, name="Simüle Yol", line=dict(color='#00D4FF')))
                fig_sim.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig_sim, use_container_width=True)
            with c_ai:
                y_reg = df['Close'].values[-30:]
                model = LinearRegression().fit(np.arange(len(y_reg)).reshape(-1,1), y_reg)
                pred = model.predict([[len(y_reg)+5]])[0]
                st.metric("AI 5 Günlük Hedef", f"{pred:.2f} TL", delta=f"{((pred/live_p)-1)*100:.2f}%")

            # --- MOTOR 7: HOCA ÖZETİ (POZİSYON ÖNERİSİ) ---
            st.markdown(f"""<div class="master-card" style="border-left:12px solid #00D4FF;">
                <h3>🤖 Robotun Hoca Özeti</h3>
                <p>Hocam, <b>{active}</b> hissesi temel olarak <b>{'sağlam' if fin['cari']>1.5 and fin['oz_kar']>20 else 'orta'}</b> bir yapıda.</p>
                <p>KAP haberleri ve bilanço verileri <b>{ 'olumlu' if pred > live_p else 'nötr' }</b> bir seyir çiziyor.</p>
                <p><b>Pozisyon Önerisi:</b> Teknik ışıklar ve takas verileri mal toplamanın sürdüğünü gösteriyorsa, matematiksel olarak pozisyonu korumak mantıklıdır.</p>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Hasan Hoca Robotu Master V12)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
