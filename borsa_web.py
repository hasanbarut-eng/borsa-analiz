import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Hasan Bey Borsa Terminali", layout="wide")
st.title("🛡️ Hasan Bey BİST Karar Destek Terminali")
st.markdown(f"_Tarih: {datetime.now().strftime('%d/%m/%Y')} | Kriter: RSI, MACD, BB, SMA20_")

# --- TÜM BİST LİSTESİ ---
@st.cache_data
def get_bist_list():
    hisseler = [
        "ACSEL", "ADEL", "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AKBNK", "AKCNS",
        "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "ALARK", "ALBRK", "ALFAS",
        "ALGYO", "ALKA", "ALKIM", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARCLK",
        "ASELS", "ASTOR", "ASUZU", "AYDEM", "AYGAZ", "BIMAS", "BIOEN", "BOBET", "BRISA", "BRLSM",
        "CANTE", "CATES", "CCOLA", "CEMTS", "CIMSA", "CWENE", "DOAS", "DOHOL", "EBEBK", "ECILC",
        "EGEEN", "EKGYO", "ENJSA", "ENKAI", "EREGL", "ESEN", "EUPWR", "FROTO", "GARAN", "GESAN",
        "GUBRF", "HALKB", "HEKTS", "HUNER", "ISCTR", "ISDMR", "ISMEN", "IZENR", "KAYSE", "KCAER",
        "KCHOL", "KONTR", "KONYA", "KOZAL", "KOZAA", "KRDMD", "MIATK", "MPARK", "ODAS", "OTKAR",
        "OYAKC", "PETKM", "PGSUS", "QUAGR", "REEDR", "SAHOL", "SASA", "SAYAS", "SDTTR", "SISE",
        "SMRTG", "SOKM", "TABGD", "TAVHL", "TCELL", "THYAO", "TKFEN", "TOASO", "TSKB", "TTKOM",
        "TTRAK", "TUPRS", "ULKER", "VAKBN", "VESTL", "YEOTK", "YKBNK", "ZOREN"
    ]
    return sorted(list(set(hisseler)))

bist_havuz = get_bist_list()

# --- YAN PANEL ---
st.sidebar.header("📋 BİST Filtreleme")
secilenler = st.sidebar.multiselect(
    "Analiz edilecek hisseleri seçin (Örn: 10 adet):",
    options=bist_havuz,
    default=["ESEN", "CATES", "SASA", "KAYSE", "AGROT", "REEDR", "MIATK", "THYAO", "EREGL", "TUPRS"]
)

# --- TEKNİK HESAPLAMA MOTORU (MANUEL & HIZLI) ---
def profesyonel_analiz(hisse_kod):
    try:
        hisse_full = hisse_kod + ".IS"
        # Veriyi çekiyoruz
        df = yf.download(hisse_full, period="6mo", interval="1d", progress=False, auto_adjust=True)
        
        if df.empty or len(df) < 30: return None
        
        # MultiIndex sütun sorununu temizleme
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']

        # 1. RSI HESABI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 2. SMA20 HESABI
        df['SMA20'] = close.rolling(window=20).mean()

        # 3. BOLLINGER BANDS
        df['BB_Mid'] = close.rolling(window=20).mean()
        df['BB_Std'] = close.rolling(window=20).std()
        df['BB_Low'] = df['BB_Mid'] - (df['BB_Std'] * 2)

        # 4. MACD HESABI
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Hist'] = df['MACD'] - df['Signal']

        son = df.iloc[-1]
        
        # PUANLAMA (0-4)
        puan = 0
        if son["RSI"] < 45: puan += 1 # RSI ucuz mu?
        if son["Hist"] > 0: puan += 1 # MACD yukarı mı?
        if son["Close"] < son["BB_Low"] * 1.05: puan += 1 # Alt banda yakın mı?
        if son["Close"] > son["SMA20"]: puan += 1 # Trend üstünde mi?
        
        return {
            "Hisse": hisse_kod,
            "Fiyat": round(float(son["Close"]), 2),
            "RSI": round(float(son["RSI"]), 1),
            "SMA20": "ÜSTÜNDE" if son["Close"] > son["SMA20"] else "ALTINDA",
            "Puan": f"{puan}/4",
            "Sinyal": "🟢 GÜÇLÜ AL" if puan >= 3 else "🔴 RİSKLİ" if puan <= 1 else "🟡 BEKLE"
        }
    except Exception as e:
        return None

# --- ANA EKRAN ---
if st.button("🚀 Seçilen Hisseleri Analiz Et"):
    if not secilenler:
        st.error("⚠️ Lütfen sol taraftaki menüden hisse seçin.")
    else:
        sonuclar = []
        progress_bar = st.progress(0)
        
        for i, h in enumerate(secilenler):
            res = profesyonel_analiz(h)
            if res:
                sonuclar.append(res)
            progress_bar.progress((i + 1) / len(secilenler))
        
        if sonuclar:
            df_final = pd.DataFrame(sonuclar)
            st.subheader("📈 Stratejik Onay Tablosu")
            
            # Tabloyu puanı yüksekten düşüğe sırala
            df_final = df_final.sort_values(by="Puan", ascending=False)
            
            st.dataframe(df_final.style.apply(lambda x: [
                "background-color: #155724; color: white" if "GÜÇLÜ AL" in str(v) else 
                ("background-color: #721c24; color: white" if "RİSKLİ" in str(v) else "") 
                for v in x
            ], axis=1, subset=["Sinyal"]), use_container_width=True)
            
            # Kart Görünümü
            col1, col2, col3 = st.columns(3)
            with col1:
                en_iyi = df_final.iloc[0]
                st.metric("🌟 Favori", en_iyi["Hisse"], en_iyi["Puan"])
            with col2:
                st.metric("📊 Tarama", f"{len(secilenler)} Hisse")
            with col3:
                st.metric("🕒 Saat", datetime.now().strftime('%H:%M'))
        else:
            st.error("❌ Veri çekilemedi. Lütfen internet bağlantınızı veya hisse kodlarını kontrol edin.")
else:
    st.info("👈 Sol menüden hisseleri seçin ve 'Analiz Et' butonuna basın.")
