import requests
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import logging
import sys
import time
import html

# --- LOG AYARI ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])

class BorsaAnalizMasterV11:
    def __init__(self):
        self.TOKEN = "8255121421:AAG1biq7jrgLFAbWmzOFs6D4wsPzoDUjYeM"
        self.CHAT_ID = "8479457745" 
        self.hisseler = self.bist_aktif_liste_getir()

    def bist_aktif_liste_getir(self):
        logging.info("🔍 BIST Tam Liste Mühürleniyor...")
        return [
            "A1CAP", "ACSEL", "ADEL", "ADESE", "AEFES", "AFYON", "AGESA", "AGHOL", "AGROT", "AHGAZ",
            "AKBNK", "AKCNS", "AKENR", "AKFGY", "AKFYE", "AKGRT", "AKSA", "AKSEN", "ALARK", "ALBRK", 
            "ALCAR", "ALCTL", "ALFAS", "ALGYO", "ALKA", "ALVES", "ANELE", "ANGEN", "ANHYT", "ANSGR", 
            "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ASELS", "ASTOR", "ASUZU", "ATATP", "AVGYO", "AYDEM", 
            "AYEN", "AYGAZ", "AZTEK", "BAGFS", "BANVT", "BARMA", "BASGZ", "BERA", "BEYAZ", "BFREN", 
            "BIMAS", "BINHO", "BIOEN", "BIZIM", "BJKAS", "BLCYT", "BOBET", "BORLS", "BORSK", "BOSSA", 
            "BRISA", "BRYAT", "BTCIM", "BUCIM", "BURCE", "CANTE", "CATES", "CCOLA", "CELHA", "CEMTS", 
            "CIMSA", "CLEBI", "CONSE", "CVKMD", "CWENE", "DAGI", "DAPGM", "DARDL", "DGGYO", "DGNMO", 
            "DOAS", "DOHOL", "DOKTA", "DURDO", "DYOBY", "EBEBK", "ECILC", "ECZYT", "EDATA", "EGEEN", 
            "EGGUB", "EGPRO", "EGSER", "EKGYO", "EKOS", "EKSUN", "ENERY", "ENJSA", "ENKAI", "ENTRA", 
            "ERBOS", "EREGL", "ESCOM", "ESEN", "EUPWR", "EUREN", "EYGYO", "FADE", "FENER", "FLAP", 
            "FROTO", "FZLGY", "GARAN", "GENIL", "GENTS", "GEREL", "GESAN", "GIPTA", "GLYHO", "GOLTS", 
            "GOODY", "GOZDE", "GRSEL", "GSDHO", "GSRAY", "GUBRF", "GWIND", "HALKB", "HATEK", "HEKTS", 
            "HKTM", "HLGYO", "HTTBT", "HUNER", "HURGZ", "ICBCT", "IMASM", "INDES", "INFO", "INGRM", 
            "INVEO", "INVES", "IPEKE", "ISCTR", "ISDMR", "ISFIN", "ISGYO", "ISMEN", "IZENR", "IZMDC", 
            "JANTS", "KAREL", "KAYSE", "KCAER", "KCHOL", "KERVT", "KFEIN", "KLGYO", "KLMSN", "KLRHO", 
            "KLSYN", "KNFRT", "KONTR", "KONYA", "KORDS", "KOZAA", "KOZAL", "KRDMD", "KRONT", "KRPLS", 
            "KRVGD", "KUTPO", "KUYAS", "KZBGY", "LIDER", "LOGO", "MAALT", "MAGEN", "MAVI", "MEDTR", 
            "MEGAP", "MEGMT", "MERCN", "MIATK", "MIPAZ", "MNDRS", "MOBTL", "MPARK", "MRGYO", "MSGYO", 
            "MTRKS", "NATEN", "NETAS", "NIBAS", "NTGAZ", "NTHOL", "ODAS", "ONCSM", "ORGE", "OTKAR", 
            "OYAKC", "OZKGY", "PAGYO", "PAPIL", "PARSN", "PASEU", "PATEK", "PCILT", "PEKGY", "PENGD", 
            "PENTA", "PETKM", "PETUN", "PGSUS", "REEDR", "SAHOL", "SASA", "SISE", "TCELL", "THYAO", 
            "TOASO", "TUPRS", "YKBNK", "YEOTK", "ZOREN"
        ]

    def analiz_yap(self):
        logging.info(f"🚀 Master V11 - 253 Hisse İçin ŞAMPİYONLAR LİGİ Taraması Başladı...")
        for h in self.hisseler:
            try:
                ticker = yf.Ticker(f"{h}.IS")
                df = ticker.history(period="1y", interval="1d", auto_adjust=True)
                if df is None or df.empty or len(df) < 200: continue

                df['RSI'] = ta.rsi(df['Close'], length=14)
                df['SMA20'] = ta.sma(df['Close'], length=20)
                df['SMA200'] = ta.sma(df['Close'], length=200)

                fiyat = float(df['Close'].iloc[-1])
                rsi = float(df['RSI'].iloc[-1])
                sma20 = float(df['SMA20'].iloc[-1])
                sma200 = float(df['SMA200'].iloc[-1])
                
                h_ort = df['Volume'].rolling(10).mean().iloc[-1]
                h_son = df['Volume'].iloc[-1]
                hacim_patlamasi = h_son > (h_ort * 2.2)
                
                # --- PUANLAMA KRİTERLERİ ---
                skor = 0
                if fiyat > sma20: skor += 30
                if fiyat > sma200: skor += 20
                if 40 <= rsi <= 70: skor += 20
                if hacim_patlamasi: skor += 30

                # --- %90 SÜZGECİ (Sadece 5-10 Hisse Odaklı) ---
                if skor >= 90:
                    vade = "KISA VADE (TAVAN ADAYI 🚀)" if hacim_patlamasi else "ORTA VADE (GÜÇLÜ TREND 📈)"
                    self.telegram_v11_gonder(h, fiyat, skor, vade, rsi, hacim_patlamasi, sma200)
                
                time.sleep(0.3) 
            except Exception: continue

    def telegram_v11_gonder(self, kod, fiyat, skor, vade, rsi, hp, s200):
        v_notu = "Hacimdeki devasa artış agresif para girişini mühürlemektedir." if hp else "İstikrarlı hacim ve fiyat dengesi yükseliş trendini destekliyor."
        r_notu = f"RSI indikatörünün {round(rsi,1)} seviyesinde mühürlenmesi momentumun en üst seviyede olduğunu kanıtlıyor."
        k_notu = f"Fiyatın {round(s200,2)} (SMA200) kalesi üzerindeki kararlı seyri güvenli boğa bölgesinde olduğumuzu gösterir."
        
        analiz_metni = (
            f"#{kod} hissesi %{skor} skorla Şampiyonlar Ligi radarına girmiştir. "
            f"Matematiksel modelimiz bu hisseyi {vade} kategorisinde mühürlemiştir. "
            f"{v_notu} {r_notu} {k_notu} "
            f"Hacim onayı ve teknik disiplinimiz gereği bu hisse portföy odağında olmalıdır. "
            f"Eğitim notu: Ana desteklerin altında stop disiplinine sadık kalmak başarının anahtarıdır."
        )

        msg = f"🏆 <b>MASTER V11: ŞAMPİYONLAR LİGİ</b> 🏆\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"<b>#{kod} | SKOR: %{skor}</b>\n\n"
        msg += f"💡 <b>DERİN ANALİZ VE EĞİTİM:</b>\n{html.escape(analiz_metni)}\n\n"
        msg += f"────────────────────\n"
        msg += f"📊 <b>Fiyat:</b> {round(fiyat, 2)} TL | 📅 <b>Vade:</b> {vade}\n"
        msg += f"🔗 <a href='https://tr.tradingview.com/symbols/BIST-{kod}'>Grafiği Mühürle</a>\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━"

        requests.post(f"https://api.telegram.org/bot{self.TOKEN}/sendMessage", 
                      data={"chat_id": self.CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True})

if __name__ == "__main__":
    BorsaAnalizMasterV11().analiz_yap()
