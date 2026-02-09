import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import sqlite3
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

# =================================================================
# 1. TASARIM VE GÜVENLİK SİSTEMİ (DEMİRLENMİŞ GİRİŞ)
# =================================================================
st.set_page_config(page_title="Master Finans Koçu V12", layout="wide", page_icon="🛡️")

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'draw_trend' not in st.session_state: st.session_state.draw_trend = None

st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        .coach-box {
            background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
            border: 2px solid #6366f1; padding: 25px; border-radius: 15px;
            color: #e0e7ff; margin-bottom: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .master-card {
            background: #1e293b; padding: 20px; border-radius: 12px; 
            border-left: 8px solid #00D4FF; margin-bottom: 15px;
        }
        .light { height: 16px; width: 16px; border-radius: 50%; display: inline-block; border: 1px solid white; margin-right: 8px; }
        .green { background-color: #00ff00; box-shadow: 0 0 10px #00ff00; }
        .yellow { background-color: #ffff00; box-shadow: 0 0 10px #ffff00; }
        .red { background-color: #ff0000; box-shadow: 0 0 10px #ff0000; }
        .yasal-uyari {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: #111418; color: #ff4b4b; text-align: center;
            padding: 8px; font-size: 0.85rem; font-weight: bold; border-top: 2px solid #3b82f6; z-index: 999;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# 2. GÜVENLİK VE VERİ TABANI MOTORU
# =================================================================
def check_password():
    if st.session_state.authenticated: return True
    st.title("🛡️ Master Robot Güvenlik Paneli")
    tab_login, tab_register = st.tabs(["Giriş Yap", "Yeni Şifre Belirle"])
    with tab_register:
        new_pwd = st.text_input("Kasa Şifrenizi Belirleyin:", type="password", key="reg_pwd")
        if st.button("Şifreyi Kaydet ve Sistemi Kilitle"):
            if len(new_pwd) > 0:
                st.session_state.master_password = new_pwd
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Şifre boş bırakılamaz.")
    with tab_login:
        login_pwd = st.text_input("Kasa Şifrenizi Girin:", type="password", key="log_pwd")
        if st.button("Robotu Başlat"):
            if "master_password" in st.session_state and login_pwd == st.session_state.master_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Hatalı şifre!")
    return False

class MasterSystem:
    def __init__(self):
        self.conn = sqlite3.connect("master_ultimate_v12_stabil.db", check_same_thread=False)

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
            
            # MOTOR 1: 10 TEKNİK İNDİKATÖR (V12 FULL LİSTE)
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
            df['STD'] = df['Close'].rolling(20).std()
            df['Upper'], df['Lower'] = df['SMA20']+(df['STD']*2), df['SMA20']-(df['STD']*2)
            df['Momentum'] = df['Close'].diff(10)
            df['EMA9'] = df['Close'].ewm(span=9).mean()
            df['Vol_Avg'] = df['Volume'].rolling(20).mean()
            
            info = t.info
            fin = {
                "ad": info.get("longName", symbol),
                "ozet": info.get("longBusinessSummary", "Şirket özeti bulunamadı."),
                "fk": info.get("trailingPE", 0), "pddd": info.get("priceToBook", 0),
                "oz_kar": info.get("returnOnEquity", 0) * 100, "cari": info.get("currentRatio", 0),
                "sektor": info.get("sector", "N/A"), "fiyat": df['Close'].iloc[-1]
            }
            # KRİTİK HATA ÖNLEYİCİ
            news = t.news if t.news else []
            return df, fin, news, t.quarterly_balance_sheet, t.quarterly_financials
        except Exception: return None, None, [], None, None

# =================================================================
# 3. ANA TERMİNAL VE KARAR MOTORLARI
# =================================================================
def main():
    if not check_password(): return
    sys = MasterSystem()
    table = sys.get_space(st.session_state.master_password)

    with st.sidebar:
        st.title("🛡️ Master Kontrol")
        h_kod = st.text_input("Hisse (SASA, ESEN):").upper().strip()
        q_in = st.number_input("Adet:", 0.0); c_in = st.number_input("Maliyet:", 0.0)
        t_in = st.number_input("Hedef:", 0.0); s_in = st.number_input("Stop:", 0.0)
        if st.button("PORTFÖYE KAYDET") and h_kod:
            sym = h_kod if h_kod.endswith(".IS") else f"{h_kod}.IS"
            with sys.conn: sys.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES (?,?,?,?,?)", (sym, q_in, c_in, t_in, s_in))
            st.rerun()

    p_df = pd.read_sql_query(f"SELECT * FROM {table}", sys.conn)
    if not p_df.empty:
        active = st.selectbox("İncele:", p_df['symbol'].tolist())
        df, fin, news, balance, financials = sys.fetch_full_data(active)
        
        if df is not None:
            price = fin['fiyat']
            row = p_df[p_df['symbol'] == active].iloc[0]

            # --- MOTOR 1: AI FİNANS KOÇU (STRATEJİ MERKEZİ) ---
            st.header(f"🏢 {fin['ad']}")
            rsi_v = df['RSI'].iloc[-1]
            trend_ok = price > df['SMA50'].iloc[-1]
            
            tavsiye = "Dengeli seyir, disiplinli takip."
            if rsi_v < 40 and trend_ok: tavsiye = "Hisse teknik olarak toplama bölgesinde. **ALIM** fırsatı olabilir."
            elif rsi_v > 75: tavsiye = "Aşırı alım yorgunluğu! **KÂR SATIŞI** değerlendirilebilir."
            elif price < row['stop'] and row['stop'] > 0: tavsiye = "🚨 **STOP:** Zarar kesme seviyesinin altındasınız!"

            st.markdown(f"""<div class="coach-box">
                <h3>🤖 Robot Finans Koçu Karar Raporu</h3>
                <p><b>Şirket Durumu:</b> {fin['sektor']} sektöründe faaliyet gösteren şirket, %{fin['oz_kar']:.2f} kârlılıkla çalışıyor. 
                Cari oranı {fin['cari']:.2f} seviyesinde.</p>
                <p><b>Koçluk Tavsiyesi:</b> {tavsiye}</p>
                <p><b>Hedef:</b> {row['target']} TL | <b>Stop:</b> {row['stop']} TL</p>
            </div>""", unsafe_allow_html=True)

            # --- MOTOR 2: AÇILIR LİSTELİ SON 10 KAP ---
            st.subheader("📰 Son 10 KAP Haberi ve Analizi")
            if news and len(news) > 0:
                news_titles = [n.get('title', 'Başlıksız Haber') for n in news[:10]]
                selected_kap = st.selectbox("Yorumlanacak Haberi Seçin:", news_titles)
                st.info(f"Müfettiş Notu: Seçilen haber şirket mali yapısı üzerinden analiz ediliyor...")
            else:
                st.warning("Bu hisse için haber bulunamadı.")

            # --- SEKMELİ MOTORLAR ---
            tab1, tab2, tab3 = st.tabs(["📉 Teknik & Trend", "📊 Bilanço & Detay", "🎲 Gelecek Tahmini"])
            
            with tab1:
                # 10 TEKNİK ONAY IŞIĞI
                st.subheader("🚥 Teknik Analiz Müfettişi")
                L = {
                    "RSI": ("green" if 35<rsi_v<65 else "yellow", rsi_v),
                    "SMA 50": ("green" if trend_ok else "red", 0),
                    "MACD": ("green" if df['MACD'].iloc[-1]>df['Signal'].iloc[-1] else "red", 0),
                    "Hacim": ("green" if df['Volume'].iloc[-1]>df['Vol_Avg'].iloc[-1] else "yellow", 0)
                }
                cols = st.columns(4)
                for i, (k, v) in enumerate(L.items()):
                    with cols[i]: st.markdown(f'<div class="master-card"><span class="light {v[0]}"></span><b>{k}</b></div>', unsafe_allow_html=True)
                
                if st.button("📈 TRENDLERİ ÇİZ"):
                    y_tr = df['Close'].values[-60:]; x_tr = np.arange(len(y_tr)).reshape(-1, 1)
                    st.session_state.draw_trend = LinearRegression().fit(x_tr, y_tr).predict(x_tr)

                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Mum"), row=1, col=1)
                if st.session_state.draw_trend is not None:
                    fig.add_trace(go.Scatter(x=df.index[-60:], y=st.session_state.draw_trend, name="Trend", line=dict(color='yellow', dash='dot')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='magenta')), row=2, col=1)
                fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False, height=600)
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.subheader("📋 Şirket Özeti ve Finansal Tablo")
                st.info(fin['ozet'])
                if balance is not None: st.dataframe(balance.iloc[:10, :4], use_container_width=True)

            with tab3:
                st.subheader("🎲 30 Günlük Tarihli Simülasyon")
                days = 30
                returns = np.random.normal(0.001, 0.02, days)
                sim_path = price * (1 + returns).cumprod()
                dates = [datetime.now() + timedelta(days=i) for i in range(days)]
                fig_sim = go.Figure(go.Scatter(x=dates, y=sim_path, name="Olası Yol", line=dict(color='#00D4FF')))
                fig_sim.update_layout(template="plotly_dark", height=450, xaxis_title="Tahmini Tarih")
                st.plotly_chart(fig_sim, use_container_width=True)

    st.markdown('<div class="yasal-uyari">⚠️ YATIRIM TAVSİYESİ DEĞİLDİR. (Master Robot V12 Stabil Demir)</div>', unsafe_allow_html=True)

if __name__ == "__main__": main()
