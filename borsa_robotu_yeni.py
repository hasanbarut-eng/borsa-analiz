import os
import sys

# --- OTOMATİK KÜTÜPHANE YÖNETİMİ ---
def install(package):
    os.system(f"{sys.executable} -m pip install {package}")

try:
    import yfinance as yf
    import pandas_ta as ta
    import requests
    import pandas as pd
except ImportError:
    install('yfinance')
    install('pandas-ta')
    install('requests')
    install('pandas')
    import yfinance as yf
    import pandas_ta as ta
    import requests
    import pandas as pd

from datetime import datetime
import time

# --- HASAN BEY ÖZEL AYARLAR ---
TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
CHAT_ID = "8479457745"

class YeniBorsaRobotu:
    def __init__(self):
        # 1. HASAN BEY FAVORİLER
        self.favoriler = ["ESEN", "CATES", "KAYSE", "AGROT", "ALVES", "REEDR", "MIATK", "EUPWR", "ASTOR", "SASA"]
        
        # 2. 100+ GENİŞ LİSTE
        self.ek_liste = [
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
            "SKBNK", "SNGYO", "TTKOM", "TTRAK", "ULKER", "VESBE", "ZOREN"
        ]
        
        # Temiz ve sıralı liste hazırlığı
        tum_hisseler = list(set(self.favoriler + self.ek_liste))
        self.hisseler = [h + ".IS" for h in sorted(tum_hisseler)]
        self.sonuclar = []

    def analiz_et(self, ticker):
        """Hisse verilerini çeken ve puanlayan ana motor."""
        try:
            # Veri indirme
            df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True, progress=False, timeout=15)
            if df.empty or len(df) < 20: return None
            
            # Sütun düzeltme (Multi-index hatasını engeller)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # İndikatörler
            rsi = ta.rsi(df["Close"], length=14)
            if rsi is None or len(rsi) == 0: return None
            
            son_rsi = rsi.iloc[-1]
            son_fiyat = df["Close"].iloc[-1]
            sma20 = ta.sma(df["Close"], length=20).iloc[-1]
            
            puan = 0
            if son_rsi < 50: puan += 1
            if son_fiyat > sma20: puan += 1

            sembol = ticker.replace(".IS", "")
            return {
                "Kod": sembol,
                "Fiyat": f"{son_fiyat:.2f}",
                "RSI": f"{son_rsi:.1f}",
                "Skor": f"{puan}/2",
                "Fav": sembol in self.favoriler
            }
        except:
            return None

    def html_uret(self):
        """Web sayfası oluşturur."""
        zaman = datetime.now().strftime('%d/%m/%Y %H:%M')
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Hasan Bey Borsa 100+</title>
            <style>
                body {{ background: #121212; color: white; font-family: sans-serif; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #333; padding: 12px; text-align: center; }}
                th {{ background: #222; }}
                .fav {{ background: #1e3a8a; font-weight: bold; }}
                .puan-iyi {{ color: #00ff88; }}
            </style>
        </head>
        <body>
            <h2 align="center">🎯 Stratejik Analiz Paneli (100+ Hisse)</h2>
            <p align="center">Son Güncelleme: {zaman}</p>
            <table>
                <tr><th>Hisse</th><th>Fiyat</th><th>RSI</th><th>Skor</th></tr>
        """
        # Favoriler üstte, sonra skora göre sırala
        sirali = sorted(self.sonuclar, key=lambda x: (not x['Fav'], -int(x['Skor'][0])))
        for s in sirali:
            cls = "class='fav'" if s['Fav'] else ""
            html += f"<tr {cls}><td>{s['Kod']}</td><td>{s['Fiyat']} TL</td><td>{s['RSI']}</td><td>{s['Skor']}</td></tr>"
        
        html += "</table></body></html>"
        with open("index_yeni.html", "w", encoding="utf-8") as f:
            f.write(html)

    def telegram_bildir(self):
        """Telegram'a özet rapor atar."""
        firsatlar = [h for h in self.sonuclar if int(h['Skor'][0]) >= 1]
        if not firsatlar: return
        
        msg = "📊 *HASAN BEY 100+ ANALİZ RAPORU*\n\n"
        for f in firsatlar[:15]:
            emoji = "💎" if f['Fav'] else "✅"
            msg += f"{emoji} *{f['Kod']}*: {f['Fiyat']} TL (RSI: {f['RSI']})\n"
        
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        except:
            pass

    def baslat(self):
        print(f"🚀 Analiz başlatıldı: {len(self.hisseler)} hisse taranıyor...")
        for h in self.hisseler:
            res = self.analiz_et(h)
            if res:
                self.sonuclar.append(res)
            time.sleep(0.1) # Engel yememek için bekleme
            
        self.html_uret()
        self.telegram_bildir()
        print("✅ Analiz tamamlandı ve raporlar üretildi.")

if __name__ == "__main__":
    YeniBorsaRobotu().baslat()
