from epd_1inch54 import *
from PIL import Image, ImageDraw, ImageFont
import requests
import time
from datetime import datetime
import socket
import csv
from io import StringIO

USD_EUR_RATE = 0.86  # USD → EUR Umrechnung
TEXTFILE = "silber_käufe.txt"

def pil_to_epd_buffer(image):
    """Wandelt PIL-Image in Bytearray für EPD_1Inch54 um"""
    image = image.convert('1')  # schwarz/weiß
    image = image.transpose(Image.FLIP_LEFT_RIGHT)  # horizontal spiegeln
    image = image.rotate(0, expand=True)  # 90° nach links drehen

    width, height = image.size
    buf = []

    for y in range(height):
        for x in range(0, width, 8):
            byte = 0
            for bit in range(8):
                if x + bit < width:
                    pixel = image.getpixel((x + bit, y))
                    if pixel == 0:  # schwarz
                        byte |= (0x80 >> bit)
            buf.append(byte)
    return buf

def get_gold_price_and_change():
    url = "https://stooq.com/q/d/l/?s=xagusd&i=d"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        # CSV einlesen
        csv_data = list(csv.DictReader(StringIO(r.text)))

        # Mindestens 7 Werte?
        if len(csv_data) < 7:
            print("Zu wenige Daten für 7-Tage-Analyse.")
            return None, None, None, None

        # Neuester Schlusskurs
        price_now = float(csv_data[-1]["Close"])

        # Schlusskurs vor 7 Tagen
        price_7days_ago = float(csv_data[-7]["Close"])

        # Veränderungen
        change_abs = price_now - price_7days_ago
        change_pct = (change_abs / price_7days_ago) * 100
        change_pct_display = f"{change_pct:+.2f}%"

        return price_now, change_abs, change_pct, change_pct_display

    except Exception as e:
        print("Fehler beim Abrufen des Silberpreises:", e)
        return None, None, None, None

def read_purchase_file(filename):
    """Liest die Textdatei mit Käufen und gibt eine Liste von dicts zurück"""
    """
    Liest die Textdatei mit Käufen.
    Format pro Zeile:
    DATUM, UNZEN, USD-PREIS-PRO-UNZE
    """
    purchases = []
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                date_str, ounces_str, usd_per_oz_str = line.split(",")

                purchases.append({
                    "date": date_str.strip(),
                    "ounces": float(ounces_str.strip()),     # Kaufmenge in Unzen
                    "usd_per_oz": float(usd_per_oz_str.strip())  # Preis pro Unze
                })

    except Exception as e:
        print("Fehler beim Lesen der Textdatei:", e)

    return purchases
def update_usd_eur_rate():
    """Ruft aktuellen USD→EUR Wechselkurs über Yahoo Finance ab"""
    url = "https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval=1d"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]

        if not closes:
            print("Konnte den Wechselkurs nicht abrufen (keine Daten).")
            return None

        eur_usd = closes[-1]          # EUR pro 1 USD
        usd_eur = 1 / eur_usd         # USD → EUR umrechnen

        #print(f"USD→EUR aktualisiert: {usd_eur:.4f}")
        return usd_eur

    except Exception as e:
        print("Fehler beim Abrufen des Wechselkurses:", e)
        return None


def calculate_profit(purchases, current_price_usd):
    """Berechnet Gewinn/Verlust in Euro basierend auf Unzen statt Gramm"""
    total_profit = 0

    for p in purchases:
        bought_oz = p["ounces"]

        profit_usd = (current_price_usd - p["usd_per_oz"]) * bought_oz

        total_profit += profit_usd

    # USD → EUR Umrechnung
    total_profit_eur = total_profit * USD_EUR_RATE

    return total_profit_eur

if __name__ == '__main__':
    #print("Starte Goldpreis E-Paper Monitor...")
    epd = EPD_1Inch54()
    epd.hw_init()
    epd.whitescreen_white()  # Hintergrund weiß

    WIDTH, HEIGHT = 200, 200
    font_20 = ImageFont.truetype("MiSans-Light.ttf", 18)
    font_16 = ImageFont.truetype("MiSans-Light.ttf", 12)

    try:
        while True:
            image = Image.new('1', (WIDTH, HEIGHT), 0)  # weißer Hintergrund
            draw = ImageDraw.Draw(image)

            # Goldpreis abrufen
            gold_price, change_abs, change_pct, change_pct_display = get_gold_price_and_change()
            if gold_price is None:
                text_lines = ["Fehler beim Abrufen", "des Goldpreises"]
            else:
                text_lines = [
                    f"{gold_price:.2f} USD/oz",
                    f"{change_abs:+.2f} USD ({change_pct_display})"
                ]

                # Käufe einlesen + IP adresse und website anzeigen
                purchases = read_purchase_file(TEXTFILE)
                total_ounces = sum(purchase["ounces"] for purchase in purchases)
                profit_eur = calculate_profit(purchases, gold_price)

                try:
                    ip = socket.gethostbyname(socket.gethostname())
                except:
                    ip = "IP unbekannt"
                text_lines.append(f" Portfolio | {profit_eur:+.2f} EUR\n       Unzen: {total_ounces}\n\n         "+ip+"\n  http://pi/index.html")

            # Text horizontal zentriert, oben beginnen
            y_offset = 5
            for line in text_lines:
                bbox = draw.textbbox((0,0), line, font=font_20)
                text_w = bbox[2] - bbox[0]
                x = (WIDTH - text_w) // 2
                draw.text((x, y_offset), line, font=font_20, fill=1)  # schwarz
                y_offset += bbox[3] - bbox[1] + 15  # Zeilenabstand

            # Konvertieren und anzeigen
            buf = pil_to_epd_buffer(image)
            epd.hw_init()
            epd.display(buf)

            #print(f"Goldpreis und Portfolio angezeigt um {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(60)  # alle 1 Minuten aktualisieren
            USD_EUR_RATE = update_usd_eur_rate() or USD_EUR_RATE

    except KeyboardInterrupt:
        #print("\nProgramm beendet.")
        epd.whitescreen_white()
        epd.sleep()
        exit(1)
