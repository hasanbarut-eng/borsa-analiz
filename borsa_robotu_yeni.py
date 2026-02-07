import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# --- AYARLAR ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

# HASAN BEY FAVORİLER VE 120+ GENİŞ LİSTE
favoriler = ["ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA"]
ek_liste = [
    "THYAO", "ASELS", "EREGL", "AKBNK", "GARAN", "SISE", "KCHOL", "BIMAS", "TUPRS", "ISCTR",
    "EKGYO", "KARDMD", "PETKM", "ARCLK", "PGSUS", "KOZAL", "TCELL", "FROTO", "TOASO", "ENJSA",
    "GUBRF", "KONTR", "YEOTK", "SMRTG", "ALARK", "ODAS", "DOAS", "KCAER", "VAKBN", "HALKB",
    "ISMEN", "SAHOL", "YKBNK", "MGROS", "VESTL", "DOCO", "EGEEN", "TAVHL", "TKFEN", "ADESE",
    "AEFES", "AFYON", "AGESA", "AGHOL", "AKCNS", "AKENR", "AKFGY", "AKFYE", "ALBRK", "ALFAS",
    "ALGYO", "ALKA", "ALKIM", "ANELE", "ANGEN", "ANHYT", "ANSGR", "ARASE", "ARZUM", "ASGYO",
    "ASUZU", "ATAKP", "ATEKS", "AVPGY", "AYDEM", "AYGAZ", "BAGFS", "BANVT", "BERA", "BIENY",
    "BRLSM", "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BVSAN", "CANTE", "CCOLA", "CEMTS", "CIMSA",
    "CWENE", "EBEBK", "ECILC", "ECZYT", "EGGUB", "ENKAI", "EUREN", "FENER", "GENIL", "GESAN",
    "GSDHO", "GWIND", "INVEO", "IPEKE", "ISDMR", "IZMDC", "KARSN", "KENT", "KERVT", "KLRGY",
    "KMPUR", "KONYA", "KORDS", "KOZAA", "LOGO", "MPARK", "NETAS", "OTKAR", "OYAKC", "QUAGR",
    "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN", "MAGEN", "FORMT", "HUNER"
]

hisseler = [h + ".IS" for h in sorted(list(set(favoriler + ek_liste)))]

def rsi_hesapla(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

sonuclar = []

for h in hisseler:
    try:
        # Daha güvenli veri çekme
        data = yf.download(h, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=20)
        if data.empty or len(data) < 20: continue
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)

        # 1. ANALİZ: RSI
        rsi_serisi = rsi_hesapla(data["Close"])
        son_rsi = rsi_serisi.iloc[-1]
        
        # 2. ANALİZ: 20 GÜNLÜK HAREKETLİ ORTALAMA (SMA)
        sma20 = data["Close"].rolling(20).mean().iloc[-1]
        son_fiyat = data["Close"].iloc[-1]
        
        # 3. ANALİZ: HACİM KONTROLÜ (Son hacim, 10 günlük ortalama hacmin üzerindeyse +1 puan)
        hacim_ort = data["Volume"].rolling(10).mean().iloc[-1]
        son_hacim = data["Volume"].iloc[-1]
        
        puan = 0
        if 30 < son_rsi < 60: puan += 1 # RSI uygun seviyede mi?
        if son_fiyat > sma20: puan += 1 # Fiyat ortalamanın üstünde mi?
        if son_hacim > hacim_ort: puan += 1 # Hacim artışı var mı?

        sonuclar.append({
            "Kod": h.replace(".IS", ""),
            "Fiyat": f"{son_fiyat:.2f}",
            "RSI": f"{son_rsi:.1f}",
            "Skor": f"{puan}/3", # Artık puanlama 3 üzerinden
            "Fav": h.replace(".IS", "") in favoriler
        })
        time.sleep(0.15)
    except: continue

# --- WEB PANELİ VE TELEGRAM GÖNDERİMİ AYNI KALIYOR ---
# (Buradaki HTML ve Telegram kısımları yukarıdaki kodla aynıdır)
