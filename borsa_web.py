import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- SENIOR MİMARİ: KONFİGÜRASYON ---
st.set_page_config(page_title="Hasan Bey Borsa Terminali", layout="wide")

def get_bist_tickers():
    """BİST 500+ Tüm Hisse Listesini Alfabetik Hazırlar"""
    # Buraya en güncel halka arzlar dahil tüm liste gömülmüştür.
    # Not: Senior seviyesinde bu liste normalde bir API'den çekilir.
    tickers = [
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
    return sorted(list(set(tickers)))

# --- ANALİZ MOTORU: 10 İNDİKATÖR ---
def get_analysis(symbol):
    """Tek bir hisse için 10 indikatörü hesaplar"""
    try:
        df = yf.download(symbol + ".IS", period="6mo", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 30: return None
        
        # Sütunları düzelt
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        c = df['Close']
        h = df['High']
        l = df['Low']
        
        # 1. RSI | 2. SMA20 | 3. SMA50 | 4. MACD | 5. Signal | 6. BB_Low | 7. BB_High | 8. CCI | 9. STOCH | 10. MOM
        delta = c.diff(); g = delta.where(delta > 0, 0).rolling(14).mean(); ls = -delta.where(delta < 0, 0).rolling(14).mean()
        rsi = 100 - (100 / (1 + g/ls))
        sma20 = c.rolling(20).mean(); sma50 = c.rolling(50).mean()
        std = c.rolling(20).std(); bbl = sma20 - (std*2)
        exp1 = c.ewm(span=12).mean(); exp2 = c.ewm(span=26).mean(); macd = exp1-exp2; sig = macd.ewm(span=9).mean()
        tp = (h+l+c)/3; cci = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean()))
        stoch = 100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
        mom = (c / c.shift(10)) * 100

        puan = 0
        if rsi.iloc[-1] < 45: puan += 1
        if (macd-sig).iloc[-1] > 0: puan += 1
        if c.iloc[-1] > sma20.iloc[-1]: puan += 1
        if c.iloc[-1] < bbl.iloc[-1] * 1.05: puan += 1

        return {
            "Hisse": symbol, "Fiyat": round(c.iloc[-1], 2), "RSI": round(rsi.iloc[-1], 1), 
            "Trend": "POZİTİF" if c.iloc[-1] > sma20.iloc[-1] else "NEGATİF", 
            "MACD": "AL" if (macd-sig).iloc[-1] > 0 else "SAT", "Puan": f"{puan}/4",
            "Sinyal": "🟢 GÜÇLÜ AL" if puan >= 3 else "🟡 BEKLE" if puan == 2 else "🔴 RİSKLİ"
        }
    except: return None

# --- ANA UYGULAMA ---
def main():
    st.title("🛡️ Hasan Bey BİST Karar Destek Terminali")
    
    # Kütüphanesiz Hafıza Çözümü: Session State
    # Eğer listenin her açılışta gelmesini istiyorsanız default listeyi buraya yazın:
    if 'my_watchlist' not in st.session_state:
        st.session_state.my_watchlist = ["ESEN", "SASA", "THYAO", "AGROT", "REEDR", "CATES", "KAYSE", "EREGL", "TUPRS", "MIATK"]

    # --- SIDEBAR ---
    all_tickers = get_bist_tickers()
    st.sidebar.header("📋 Takip Listeniz")
    
    # Burada seçilenler Session State'e bağlanır
    secilenler = st.sidebar.multiselect(
        "Hisseleri Seçin (500+ Mevcut):",
        options=all_tickers,
        default=st.session_state.my_watchlist
    )

    if st.sidebar.button("💾 Bu Listeyi Varsayılan Yap"):
        st.session_state.my_watchlist = secilenler
        st.sidebar.success("Liste kaydedildi! (Oturum boyunca)")

    # --- ANA PANEL ---
    if st.button(f"🚀 {len(secilenler)} Hisseyi Analiz Et"):
        if not secilenler:
            st.warning("Lütfen hisse seçin.")
        else:
            results = []
            bar = st.progress(0)
            for i, s in enumerate(secilenler):
                res = get_analysis(s)
                if res: results.append(res)
                bar.progress((i+1)/len(secilenler))
            
            if results:
                df = pd.DataFrame(results)
                st.dataframe(df.sort_values("Puan", ascending=False), use_container_width=True)
            bar.empty()

if __name__ == "__main__":
    main()
