import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression

# =================================================================
# 1. TASARIM VE MOBİL (PWA) KONFİGÜRASYONU - KRİSTAL NETLİK
# =================================================================
st.set_page_config(page_title="Borsa Robotu", layout="wide", page_icon="📈")

st.markdown("""
    <head>
        <meta name="apple-mobile-web-app-title" content="Borsa Robotu">
        <meta name="application-name" content="Borsa Robotu">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        .stApp { background-color: #0E1117; }
        section[data-testid="stSidebar"] { background-color: #0a0c10 !important; border-right: 3px solid #00D4FF; }
        
        /* SIDEBAR ULTRA NET BEYAZ */
        section[data-testid="stSidebar"] .stMarkdown p, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stSubheader { 
            color: #FFFFFF !important; font-weight: 900 !important; font-size: 1.15rem !important;
            text-shadow: 2px 2px 4px #000000;
        }

        /* ANALİZ KARTLARI - BEYAZ METİN GARANTİSİ */
        .master-card {
            background: #1e293b; padding: 20px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        }
        .master-card h3, .master-card h2, .master-card h1, .master-card p, .master-card b, .master-card span, .master-card li {
            color: #FFFFFF !important; font-weight: 800 !important;
        }
        
        /* TRAFİK IŞIKLARI */
        .light { height: 18px; width: 18px; border-radius: 50%; display: inline-block; border: 1px solid white; }
        .green { background-color: #00ff00; box-shadow: 0 0 12px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 12px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 12px #ff0000; }

        .stButton>button {
            background-color: #00D4FF !important; color: #000000 !important;
            font-weight: 900 !important; border-radius: 10px !important; 
            height: 60px !important; width: 100% !important; border: 3px solid white;
        }
        
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 8px; font-size: 0.85rem; font-weight: bold; border-top: 2px solid #3b82f6; z-index: 999;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. VERİ VE GİZLİLİK MİMARİSİ
# =================================================================
class MasterSystemFinal:
    def __init__(self, db_name="master_robot_v11_pro.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)

    def get_space(self, key):
        safe = "".join(filter(str.isalnum, key))
        table = f"u_{safe}"
        with self.conn:
            self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (symbol TEXT PRIMARY KEY, qty REAL, cost REAL, target REAL, stop REAL)")
        return table

    @st.cache_data(ttl=300)
    def fetch_everything(_self, symbol):
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="1y")
            if df.empty: return None, None, None
            
            # 10 TEKNİK VERİ (Işıklar İçin)
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
            def v_check(val): return f"{val:.2f}" if isinstance(val, (int, float)) and not np.isnan(val) else "Veri Bekleniyor"
            
            fin = {
                "ad": info.get("longName", symbol),
                "cari": info.get("currentRatio", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100,
                "fk": v_check(info.get("trailingPE")),
                "pddd": v_check(info.get("priceToBook")),
                "eps": v_check(info.get("trailingEps")),
                "fiyat": df['Close'].iloc[-1]
            }
            return df, fin, t.news
        except: return None, None, None

# =================================================================
# 3. ANA DÖNGÜ
# =================================================================
def main():
    sys = MasterSystemFinal()
    
    st.sidebar.title("🔑 Borsa Robotu Giriş")
    key = st.sidebar.text_input("Özel Şifreniz:", type="password")
    if not key:
        st.info("👋 Merhaba öğretmenim! Lütfen kasanı açmak için şifreni gir. Sonra KAP haberleri dahil her şey yüklenecek.")
        return

    ut = sys.get_space(key)

    with st.sidebar:
        st.divider()
        st.subheader("➕ Hisse Kaydet")
        s_raw = st.text_input("Kod (Örn: esen):").upper().strip()
        q_in = st.number_input("Adet", 0.0)
        c_in = st.number_input("Maliyet", 0.0)
        t_in = st.number_input("Hedef Fiyat", 0.0)
        st_in = st.number_input("Stop Fiyat", 0.0)
        if st.button("PORTFÖYE EKLE"):
            if s_raw:
                symbol = s_raw if s_raw.endswith(".IS") else f"{s_raw}.IS"
                with sys.conn:
                    sys.conn.execute(f"INSERT OR REPLACE INTO {ut} VALUES (?,?,?,?,?)", (symbol, q_in, c_in, t_in, st_in))
                st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {ut}", sys.conn)
    if not p_df.empty:
        st.title("🛡️ Borsa Robotu Master V11 Pro")
        active = st.selectbox("İncelemek İstediğiniz Hisseni Seç:", ["Seçiniz..."] + p_df['symbol'].tolist())
        
        if active != "Seçiniz...":
            df, fin, news = sys.fetch_everything(active)
            if df is not None:
                # --- HABERLER VE KAP PANELİ ---
                st.subheader(f"📰 {active} Son Dakika KAP ve Haberler")
                if news:
                    n_cols = st.columns(3)
                    for i, n in enumerate(news[:3]):
                        with n_cols[i]:
                            st.markdown(f"""<div class="master-card">
                                <a href="{n['link']}" target="_blank" style="text-decoration:none; color:#00D4FF; font-weight:bold;">{n['title'][:55]}...</a>
                                <p style="font-size:0.8rem; margin-top:10px; opacity:0.8;"><b>🔍 Müfettiş:</b> {n['publisher']} üzerinden gelen bu haber takip edilmelidir.</p>
                            </div>""", unsafe_allow_html=True)

                # --- 10 İNDİKATÖRLÜ TRAFİK IŞIKLARI ---
                st.subheader("🚥 10 Teknik Onay Trafik Işıkları")
                last = fin['fiyat']
                L = {
                    "RSI Gücü": ("green" if 35 < df['RSI'].iloc[-1] < 65 else "yellow", df['RSI'].iloc[-1]),
                    "SMA 50": ("green" if last > df['SMA50'].iloc[-1] else "red", df['SMA50'].iloc[-1]),
                    "SMA 200": ("green" if last > df['SMA200'].iloc[-1] else "red", df['SMA200'].iloc[-1]),
                    "MACD": ("green" if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else "red", 0),
                    "Bollinger": ("green" if df['LB'].iloc[-1] < last < df['UB'].iloc[-1] else "yellow", 0),
                    "Momentum": ("green" if df['Momentum'].iloc[-1] > 0 else "red", df['Momentum'].iloc[-1]),
                    "Kısa Vade": ("green" if last > df['SMA20'].iloc[-1] else "red", df['SMA20'].iloc[-1]),
                    "Orta Vade": ("green" if last > df['SMA100'].iloc[-1] else "red", df['SMA100'].iloc[-1]),
                    "Cari Oran": ("green" if fin['cari'] > 1.2 else "red", fin['cari']),
                    "Verimlilik": ("green" if fin['oz_kar'] > 20 else "yellow", fin['oz_kar'])
                }
                cols = st.columns(5)
                for idx, (name, data) in enumerate(L.items()):
                    color, val = data
                    with cols[idx % 5]:
                        val_str = f": {val:.2f}" if val != 0 else ""
                        st.markdown(f'<div class="master-card"><span class="light {color}"></span> <b>{name}{val_str}</b></div>', unsafe_allow_html=True)

                # --- DERİN BİLANÇO VE AI ---
                st.divider()
                c_muf, c_ai = st.columns(2)
                with c_muf:
                    st.markdown(f"""<div class="master-card" style="border-color:#10b981;">
                        <h3 style="color:#10b981;">🔍 Doyurucu Bilanço Müfettişi</h3>
                        <p><b>F/K:</b> {fin['fk']} | <b>PD/DD:</b> {fin['pddd']} | <b>EPS:</b> {fin['eps']}</p>
                        <p><b>Analiz:</b> Cari Oran {fin['cari']:.2f} ile likidite { 'sağlamdır.' if fin['cari']>1.5 else 'dengelidir.' } 
                        Özsermaye karlılığı %{fin['oz_kar']:.1f} seviyesinde, bu da her 100 TL'lik özkaynakta {fin['oz_kar']:.1f} TL kâr üretildiğini gösterir.</p>
                    </div>""", unsafe_allow_html=True)
                with c_ai:
                    y = df['Close'].values[-60:]
                    model = LinearRegression().fit(np.arange(len(y)).reshape(-1,1), y)
                    f_val = model.predict([[len(y)+5]])[0]
                    st.markdown(f"""<div class="master-card" style="border-color:#00D4FF;">
                        <h3 style="color:#00D4FF;">🧠 AI 5 GÜNLÜK TAHMİN</h3>
                        <h2 style="margin:0;">{last:.2f} ➔ {f_val:.2f} TL</h2>
                        <p><b>Neden:</b> Regresyon eğimi %{((f_val/last)-1)*100:.2f} yönünde bir ivme gösteriyor.</p>
                    </div>""", unsafe_allow_html=True)

                # --- GRAFİK ---
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['UB'], line=dict(color='gray', width=1), name="Bollinger"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='gold'), name="Trend"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='magenta'), name="RSI"), row=2, col=1)
                fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # --- ROBOTUN GENEL DEĞERLENDİRMESİ ---
                green_count = sum(1 for color, val in L.values() if color == "green")
                st.markdown(f"""<div class="master-card" style="border-left:10px solid #ff00ff;">
                    <h3>🤖 Hoca Özeti (Genel Değerlendirme)</h3>
                    <p>{active} şu an 10 kritik testin {green_count}'inden başarıyla geçti. 
                    AI tahmini ve bilanço verileri birlikte değerlendirildiğinde {active} için 
                    { 'pozitif bir ivme beklentisi hakim.' if f_val > last and green_count > 6 else 'dikkatli olunması gereken bir yatay seyir' } öngörülüyor.</p>
                </div>""", unsafe_allow_html=True)

                # METRİKLER VE ALARMLAR
                m1, m2, m3 = st.columns([2, 2, 1])
                row = p_df[p_df['symbol'] == active].iloc[0]
                m1.metric("Anlık", f"{last:.2f} TL")
                m2.metric("Kâr/Zarar", f"{(last - row['cost']) * row['qty']:,.0f} TL")
                if m3.button("🗑️ SİL"):
                    with sys.conn: sys.conn.execute(f"DELETE FROM {ut} WHERE symbol = ?", (active,))
                    st.rerun()
                if row['target'] > 0 and last >= row['target']: st.balloons(); st.success("🎯 HEDEF GÖRÜLDÜ!")
                elif row['stop'] > 0 and last <= row['stop']: st.error("⚠️ STOP SEVİYESİ!")

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR (YTD).</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
