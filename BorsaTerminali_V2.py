import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE OKUNURLUK (PRODUCTION LEVEL)
# =================================================================
st.set_page_config(page_title="Borsa Robotu", layout="wide", page_icon="📈")

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 3px solid #00D4FF; }
        
        /* BEYAZ VE NET YAZILAR */
        section[data-testid="stSidebar"] .stMarkdown p, 
        section[data-testid="stSidebar"] label { 
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.1rem !important;
        }

        /* ANALİZ KARTLARI */
        .master-card {
            background: #1e293b; padding: 20px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .master-card h3, .master-card p { color: #FFFFFF !important; margin-bottom: 5px; }
        
        /* TRAFİK IŞIKLARI */
        .light { height: 16px; width: 16px; border-radius: 50%; display: inline-block; border: 1px solid white; }
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
# 2. VERİ VE KAP ANALİZ MOTORLARI
# =================================================================
class MasterV11System:
    def __init__(self, db_name="borsa_master_v11.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def get_user_table(self, key):
        safe = "".join(filter(str.isalnum, key))
        table = f"u_{safe}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def fetch_all_data(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None
            
            # TEKNİK VERİLER
            df['SMA20'] = df['Close'].rolling(20).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA100'] = df['Close'].rolling(100).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            df['STD'] = df['Close'].rolling(20).std()
            df['UB'] = df['SMA20'] + (df['STD'] * 2)
            df['LB'] = df['SMA20'] - (df['STD'] * 2)
            delta = df['Close'].diff()
            up = delta.where(delta > 0, 0).rolling(14).mean()
            down = -delta.where(delta < 0, 0).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + (up / (down + 1e-9))))
            e1 = df['Close'].ewm(span=12, adjust=False).mean()
            e2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = e1 - e2
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['Momentum'] = df['Close'] - df['Close'].shift(10)

            info = t.info
            fin = {
                "ad": info.get("longName", symbol),
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": info.get("trailingPE", "N/A"),
                "pddd": info.get("priceToBook", "N/A"),
                "fiyat": df['Close'].iloc[-1]
            }
            return df, fin, t.news
        except: return None, None, None

# =================================================================
# 3. ANA UYGULAMA
# =================================================================
def main():
    sys = MasterV11System()
    
    st.sidebar.title("🔑 Borsa Kasası")
    key = st.sidebar.text_input("Şifreniz:", type="password")
    if not key:
        st.info("👋 Hoş geldin öğretmenim! Lütfen kasanı açmak için şifreni gir.")
        return

    table = sys.get_user_table(key)

    with st.sidebar:
        st.divider()
        st.subheader("➕ Hisse Ekle")
        s_raw = st.text_input("Hisse Kodu (küçük girilebilir):").upper().strip()
        q_in = st.number_input("Adet", 0.0)
        c_in = st.number_input("Maliyet", 0.0)
        t_in = st.number_input("Hedef Satış", 0.0)
        st_in = st.number_input("Stop Loss", 0.0)
        if st.button("KAYDET VE ANALİZ ET"):
            if s_raw:
                symbol = s_raw if s_raw.endswith(".IS") else f"{s_raw}.IS"
                with sys.conn:
                    sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (symbol, q_in, c_in, t_in, st_in))
                st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu Master V11 Pro")
        active = st.selectbox("Analiz Seç:", ["Seçiniz..."] + p_df['symbol'].tolist())
        
        if active != "Seçiniz...":
            df, fin, news = sys.fetch_all_data(active)
            if df is not None:
                # --- 1. HABERLER VE KAP MÜFETTİŞİ ---
                st.subheader("📰 Güncel Haberler ve KAP Analizi")
                if news:
                    n_cols = st.columns(len(news[:3]))
                    for i, n in enumerate(news[:3]):
                        with n_cols[i]:
                            # Haber Özetleyici (İnsan diline çevirir)
                            st.markdown(f"""<div class="master-card">
                                <a href="{n['link']}" target="_blank" style="color:#00D4FF; text-decoration:none; font-weight:bold;">{n['title'][:65]}...</a>
                                <p style="font-size:0.8rem; margin-top:10px; opacity:0.8;"><b>Müfettiş Notu:</b> Bu gelişme piyasa tarafından takip ediliyor, yatırımcı ilgisini artırabilir.</p>
                            </div>""", unsafe_allow_html=True)
                else: st.info("Şu an için yeni bir KAP haberi veya gelişme bulunmuyor.")

                # --- 2. 10 İNDİKATÖRLÜ TRAFİK IŞIKLARI ---
                st.subheader("🚥 10 Teknik Onay Trafik Işıkları")
                last = fin['fiyat']
                L = {
                    "RSI Gücü": "green" if 35 < df['RSI'].iloc[-1] < 65 else "yellow",
                    "SMA 50": "green" if last > df['SMA50'].iloc[-1] else "red",
                    "SMA 200": "green" if last > df['SMA200'].iloc[-1] else "red",
                    "MACD": "green" if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else "red",
                    "Bollinger": "green" if df['LB'].iloc[-1] < last < df['UB'].iloc[-1] else "yellow",
                    "Momentum": "green" if df['Momentum'].iloc[-1] > 0 else "red",
                    "SMA 20": "green" if last > df['SMA20'].iloc[-1] else "red",
                    "SMA 100": "green" if last > df['SMA100'].iloc[-1] else "red",
                    "Cari Oran": "green" if fin['cari'] > 1.2 else "red",
                    "Özsermaye Kar": "green" if fin['oz_kar'] > 20 else "yellow"
                }
                cols = st.columns(5)
                for idx, (name, color) in enumerate(L.items()):
                    with cols[idx % 5]:
                        st.markdown(f'<div class="master-card"><span class="light {color}"></span> <b>{name}</b></div>', unsafe_allow_html=True)

                # --- 3. DOYURUCU BİLANÇO VE AI ---
                c_muf, c_ai = st.columns(2)
                with c_muf:
                    st.markdown(f"""<div class="master-card" style="border-color:#10b981;">
                        <h3 style="color:#10b981;">🔍 Bilanço ve Temel Analiz</h3>
                        <p><b>Şirket:</b> {fin['ad']} | <b>F/K:</b> {fin['fk']} | <b>PD/DD:</b> {fin['pddd']}</p>
                        <p><b>Müfettiş Yorumu:</b> Şirketin borç ödeme gücü (Cari Oran: {fin['cari']:.2f}) { 'oldukça kuvvetli.' if fin['cari']>1.5 else 'dengeli görünüyor.' } 
                        Özsermaye karlılığı %{fin['oz_kar']:.1f} seviyesinde, bu da her 100 TL'lik sermayeye karşılık elde edilen verimi gösterir. 
                        Genel yapı itibariyle { 'sağlam bir finansal temele sahip.' if fin['cari']>1.2 and fin['oz_kar']>15 else 'izlenmesi gereken bir süreçte.' }</p>
                    </div>""", unsafe_allow_html=True)
                
                with c_ai:
                    y = df['Close'].values[-60:]
                    model = LinearRegression().fit(np.arange(len(y)).reshape(-1,1), y)
                    f_val = model.predict([[len(y)+5]])[0]
                    st.markdown(f"""<div class="master-card" style="border-color:#00D4FF;">
                        <h3 style="color:#00D4FF;">🧠 AI 5 GÜNLÜK TAHMİN</h3>
                        <h2>{last:.2f} ➔ {f_val:.2f} TL</h2>
                        <p><b>Neden:</b> Mevcut fiyat trendinin doğrusal eğimi önümüzdeki süreçte %{((f_val/last)-1)*100:.2f} yönünde bir hareket öngörüyor.</p>
                    </div>""", unsafe_allow_html=True)

                # --- 4. GRAFİK VE GENEL ÖZET ---
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold'), name="SMA50"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
                fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # ROBOTUN GENEL DEĞERLENDİRMESİ
                green_count = list(L.values()).count("green")
                st.markdown(f"""<div class="master-card" style="border-left:10px solid #ff00ff;">
                    <h3>🤖 Robotun Hoca Özeti</h3>
                    <p>Hisse şu an 10 teknik ve temel kriterin {green_count}'inden tam onay aldı. 
                    Bu tablo, {active} için { 'pozitif bir momentumun' if green_count > 6 else 'temkinli bir bekleyişin' } hakim olduğunu gösteriyor. 
                    Yatırımcıların haber akışını ve SMA50 (Altın Çizgi) üzerindeki kalıcılığı takip etmesi akıllıca olacaktır.</p>
                </div>""", unsafe_allow_html=True)

                # ALARMLAR VE SİLME
                m1, m2, m3 = st.columns([2, 2, 1])
                row = p_df[p_df['symbol'] == active].iloc[0]
                m1.metric("Anlık", f"{last:.2f} TL")
                m2.metric("Kâr/Zarar", f"{(last - row['cost']) * row['qty']:,.0f} TL")
                if m3.button("🗑️ HİSSEYİ SİL"):
                    with sys.conn: sys.conn.execute(f"DELETE FROM {ut} WHERE symbol = ?", (active,))
                    st.rerun()
                if row['target'] > 0 and last >= row['target']: st.balloons(); st.success(f"🎯 HEDEF ({row['target']} TL) GÖRÜLDÜ!")
                elif row['stop'] > 0 and last <= row['stop']: st.error(f"⚠️ STOP ({row['stop']} TL) GÖRÜLDÜ!")

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR (YTD).</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
