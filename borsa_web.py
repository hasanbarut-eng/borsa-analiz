import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json
from streamlit_javascript import st_javascript

# --- ÜRETİM SEVİYESİ YAPILANDIRMASI ---
st.set_page_config(page_title="Hasan Bey Borsa Terminali", layout="wide")

@st.cache_data
def get_full_bist_list():
    """Tüm BİST hisse senetlerini alfabetik olarak döndürür."""
    # Listeyi güncel ve eksiksiz tutmak için tüm ana hisseler eklendi
    hisseler = [
        "A1CAP", "ACSEL", "ADEL", "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ", "AKBNK", "AKCNS", 
        "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKMGY", "AKSA", "AKSEN", "AKSGY", "AKSUE", "AKTVY", "ALARK", "ALBRK", 
        "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALKIM", "ALMAD", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", 
        "ARASE", "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ARTMS", "ARZUM", "ASCEG", "ASELS", "ASGYO", "ASTOR", "ASUZU", 
        "ATAKP", "ATATP", "ATEKS", "ATLAS", "ATSYH", "AVGYO", "AVHOL", "AVOD", "AVPGY", "AVTUR", "AYCES", "AYDEM", 
        "AYES", "AYGAZ", "AZTEK", "BAGFS", "BAKAB", "BALAT", "BANVT", "BARMA", "BAYRK", "BEBEK", "BERA", "BEYAZ", 
        "BFREN", "BIENY", "BIGCH", "BIMAS", "BINHO", "BIOEN", "BIZIM", "BJKAS", "BLCYT", "BMTKS", "BNASL", "BOBET", 
        "BORLS", "BORSK", "BOSSA", "BRISA", "BRKO", "BRKSN", "BRKVY", "BRLSM", "BRMEN", "BRSAN", "BRYAT", "BSOKE", 
        "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "BYDNR", "CANTE", "CARYE", "CATES", "CCOLA", "CELHA", "CEMAS", 
        "CEMTS", "CEOAS", "CIMSA", "CLEBI", "CONSE", "COSMO", "CRDFA", "CREVT", "CRFSA", "CUSAN", "CVKMD", "CWENE", 
        "DAGHL", "DAGI", "DAPGM", "DARDL", "DGATE", "DGGYO", "DGNMO", "DIRIT", "DITAS", "DMSAS", "DOAS", "DOCO", 
        "DOHOL", "DOKTA", "DRYHO", "DURDO", "DYOBY", "DZGYO", "EBEBK", "ECILC", "ECZYT", "EDATA", "EDIP", "EFORC", 
        "EGEEN", "EGEPO", "EGGUB", "EGLYO", "EGPAY", "EGPRO", "EGSER", "EKGYO", "EKIZ", "EKSUN", "ELITE", "EMKEL", 
        "ENERY", "ENJSA", "ENKAI", "ENTRA", "ERBOS", "ERCB", "EREGL", "ERSU", "ESCOM", "ESEN", "ETILR", "EUPWR", 
        "EUREN", "EYGYO", "FADE", "FENER", "FLAP", "FMIZP", "FONET", "FORMT", "FRIGO", "FROTO", "FZLGY", "GARAN", 
        "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLCVY", "GLRYH", "GLYHO", 
        "GMTAS", "GOKNR", "GOLTS", "GOODY", "GOZDE", "GRNYO", "GRSEL", "GSDDE", "GSDHO", "GSRAY", "GUBRF", "GWIND", 
        "GZNMI", "HALKB", "HATEK", "HEDEF", "HEKTS", "HKTM", "HLGYO", "HRKET", "HTTBT", "HUBVC", "HUNER", "HURGZ", 
        "ICBCT", "ICUGS", "IDGYO", "IEYHO", "IHAAS", "IHEVA", "IHLAS", "IHLGM", "IHMAD", "IKLGV", "IMASM", "INDES", 
        "INFO", "INGRM", "INTEM", "INVEO", "IPEKE", "ISATR", "ISBTR", "ISCTR", "ISDMR", "ISFIN", "ISGSY", "ISGYO", 
        "ISMEN", "ISKPL", "ISSEN", "ISYAT", "IZENR", "IZFAS", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARMA", "KARSAN", 
        "KARTN", "KARYE", "KATMR", "KAYSE", "KCAER", "KCHOL", "KFEIN", "KENT", "KERVN", "KERVT", "KGYO", "KIMMR", 
        "KLGYO", "KLRGY", "KLMSN", "KLNMA", "KLSYN", "KMPUR", "KNFRT", "KONTR", "KONYA", "KOPOL", "KORDS", "KOTON", 
        "KOZAL", "KOZAA", "KRONT", "KRSTL", "KRTEK", "KRVGD", "KSTUR", "KTSKR", "KUTPO", "KUZEY", "KZBGY", "KZGYO", 
        "LIDER", "LIDFA", "LIHTP", "LIMAK", "LMKDC", "LOGO", "LUKSK", "MAALT", "MACKO", "MAGEN", "MAKIM", "MAKTK", 
        "MANAS", "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEPET", "MERCN", "MERIT", "METRO", "METUR", "MHRGY", 
        "MIATK", "MIPAZ", "MNDRS", "MNDTR", "MOBTL", "MOGAN", "MPARK", "MRGYO", "MRSHL", "MSGYO", "MTRKS", "MUDO", 
        "MZHLD", "NATEN", "NETAS", "NIBAS", "NTGAZ", "NTHOL", "NUGYO", "NUHCM", "OBAMS", "ODAS", "ONCSH", "ORCA", 
        "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYYAT", "OZGYO", "OZKGY", "OZRDN", "OZSUB", 
        "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU", "PATEK", "PCILT", "PEGYO", "PEKGY", "PENTA", "PETKM", "PETUN", 
        "PGSUS", "PINSU", "PKART", "PKENT", "PLTUR", "PNLSN", "PNSUT", "POLHO", "POLTK", "PRKAB", "PRKME", "PRZMA", 
        "PSDTC", "PSGYO", "QNBFB", "QNBFL", "QUAGR", "RALYH", "RAYSG", "REEDR", "RNPOL", "RODRG", "RTALB", "RUBNS", 
        "RYGYO", "RYSAS", "SAHOL", "SAMAT", "SANEL", "SANFO", "SANKO", "SARKY", "SASA", "SAYAS", "SDTTR", "SEGYO", 
        "SEKFK", "SEKUR", "SELEC", "SELGD", "SELVA", "SEYKM", "SILVR", "SISE", "SKBNK", "SKTAS", "SMART", "SMRTG", 
        "SNGYO", "SNICA", "SNKRN", "SNPAM", "SOKM", "SONME", "SRVGY", "SUMAS", "SUNTK", "SURGY", "SUWEN", "TABGD", 
        "TARKM", "TATGD", "TAVHL", "TCELL", "TDGYO", "TEKTU", "TERA", "TETMT", "TGSAS", "THYAO", "TIRE", "TKFEN", 
        "TKNSA", "TLMAN", "TMPOL", "TMSN", "TOASO", "TRCAS", "TRGYO", "TRILC", "TSKB", "TSGYO", "TSPOR", "TTKOM", 
        "TTRAK", "TUCLK", "TUPRS", "TUREX", "TURSG", "UFUK", "ULAS", "ULKER", "ULUFA", "ULUSE", "UNLU", "USAK", 
        "VAKBN", "VAKFN", "VAKKO", "VANGD", "VBTYZ", "VERTU", "VERUS", "VESBE", "VESTL", "VKGYO", "VKING", "YAPRK", 
        "YATAS", "YAYLA", "YEOTK", "YESIL", "YGGYO", "YGYO", "YKBNK", "YLTEK", "YNSA", "YYLGD", "YYAPI", "ZEDUR", 
        "ZOREN", "ZRGYO"
    ]
    return sorted(list(set(hisseler)))

def calculate_technical_indicators(hisse, df):
    """Her hisse için 10 adet teknik indikatörü hesaplar."""
    try:
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # 1. RSI
        delta = close.diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain/loss))
        
        # 2. MACD & 3. Signal
        exp12 = close.ewm(span=12, adjust=False).mean(); exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26; signal = macd.ewm(span=9, adjust=False).mean(); hist = macd - signal
        
        # 4. SMA20 & 5. SMA50
        sma20 = close.rolling(20).mean(); sma50 = close.rolling(50).mean()
        
        # 6. Bollinger Bands
        std20 = close.rolling(20).std(); bb_low = sma20 - (std20 * 2); bb_high = sma20 + (std20 * 2)
        
        # 7. CCI
        tp = (high + low + close) / 3; sma_tp = tp.rolling(20).mean(); mad_tp = tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (tp - sma_tp) / (0.015 * mad_tp)
        
        # 8. MFI
        mf = tp * df['Volume']; pos_mf = mf.where(tp > tp.shift(1), 0).rolling(14).sum(); neg_mf = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
        mfi = 100 - (100 / (1 + pos_mf / neg_mf))
        
        # 9. Stochastic %K
        stoch = 100 * (close - low.rolling(14).min()) / (high.rolling(14).max() - low.rolling(14).min())
        
        # 10. MOMENTUM
        mom = (close / close.shift(10)) * 100

        last_idx = -1
        puan = 0
        if rsi.iloc[last_idx] < 45: puan += 1
        if hist.iloc[last_idx] > 0: puan += 1
        if close.iloc[last_idx] > sma20.iloc[last_idx]: puan += 1
        if close.iloc[last_idx] < bb_low.iloc[last_idx] * 1.05: puan += 1

        return {
            "Hisse": hisse,
            "Fiyat": round(float(close.iloc[last_idx]), 2),
            "RSI": round(float(rsi.iloc[last_idx]), 1),
            "MACD": "POZİTİF" if hist.iloc[last_idx] > 0 else "NEGATİF",
            "SMA20": "ÜSTÜNDE" if close.iloc[last_idx] > sma20.iloc[last_idx] else "ALTINDA",
            "SMA50": "ÜSTÜNDE" if close.iloc[last_idx] > sma50.iloc[last_idx] else "ALTINDA",
            "BB_Bant": "ALT BANTTA" if close.iloc[last_idx] < bb_low.iloc[last_idx] * 1.05 else "NORMAL",
            "CCI": round(float(cci.iloc[last_idx]), 0),
            "MFI": round(float(mfi.iloc[last_idx]), 1),
            "Stoch": round(float(stoch.iloc[last_idx]), 1),
            "Momentum": round(float(mom.iloc[last_idx]), 1),
            "Puan": f"{puan}/4",
            "Sinyal": "🟢 GÜÇLÜ" if puan >= 3 else "🔴 ZAYIF" if puan <= 1 else "🟡 BEKLE"
        }
    except: return None

def main():
    st.title("🛡️ Hasan Bey BİST Karar Destek Terminali (500+ Unlimited)")
    
    # 1. KİŞİYE ÖZEL LİSTE YÜKLEME (LocalStorage)
    if 'user_list' not in st.session_state:
        saved_list = st_javascript('localStorage.getItem("hasan_bey_v3_list");')
        if saved_list and saved_list != "null":
            st.session_state.user_list = json.loads(saved_list)
        else:
            st.session_state.user_list = ["ESEN", "SASA", "THYAO"] # Varsayılan

    # 2. SIDEBAR
    all_stocks = get_full_bist_list()
    st.sidebar.header("📋 Sizin Takip Listeniz")
    
    secilenler = st.sidebar.multiselect(
        "Analiz edilecek hisseleri ekleyin/çıkarın:",
        options=all_stocks,
        default=st.session_state.user_list
    )

    if st.sidebar.button("💾 Listemi Bu Tarayıcıya Kaydet"):
        json_str = json.dumps(secilenler)
        st_javascript(f"localStorage.setItem('hasan_bey_v3_list', '{json_str}');")
        st.sidebar.success("Listeniz kaydedildi!")

    # 3. ANALİZ MOTORU
    if st.button(f"🚀 {len(secilenler)} Hisseyi Analiz Et"):
        if not secilenler:
            st.warning("Hisse seçilmedi.")
        else:
            sonuclar = []
            progress = st.progress(0)
            status = st.empty()
            
            for i, h in enumerate(secilenler):
                status.text(f"Analiz ediliyor: {h} ({i+1}/{len(secilenler)})")
                df = yf.download(h + ".IS", period="6mo", interval="1d", progress=False, auto_adjust=True)
                res = calculate_technical_indicators(h, df)
                if res: sonuclar.append(res)
                progress.progress((i + 1) / len(secilenler))
            
            if sonuclar:
                final_df = pd.DataFrame(sonuclar)
                st.subheader("📊 Stratejik Analiz Sonuçları")
                st.dataframe(final_df.sort_values(by="Puan", ascending=False), use_container_width=True)
            status.empty()
            progress.empty()

if __name__ == "__main__":
    main()
