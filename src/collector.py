"""
Collecte des données de prix depuis Binance et Yahoo Finance
"""
import requests
import yfinance as yf
from datetime import datetime
import time

def get_price_binance(symbol="BTCUSDT"):
    """
    Récupère le prix actuel depuis Binance
    """
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"❌ Erreur Binance: {e}")
        return None

def get_price_yahoo(symbol="BTC-USD"):
    """
    Récupère le prix actuel depuis Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
        return None
    except Exception as e:
        print(f"❌ Erreur Yahoo: {e}")
        return None

def get_historical_data(symbol="BTC-USD", period="1mo"):
    """
    Récupère les données historiques depuis Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        return data
    except Exception as e:
        print(f"❌ Erreur historique: {e}")
        return None

def collect_all():
    """
    Collecte les prix de toutes les cryptomonnaies configurées
    """
    cryptos = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD"
    }
    
    results = {}
    for name, symbol in cryptos.items():
        print(f"📊 Collecte de {name}...")
        price = get_price_yahoo(symbol)
        if price:
            results[name] = {
                "price": price,
                "timestamp": datetime.now().isoformat()
            }
            print(f"   ✅ {name}: ${price:,.2f}")
        else:
            print(f"   ❌ {name}: échec")
        time.sleep(0.5)
    
    return results

if __name__ == "__main__":
    print("🔍 Test de collecte...")
    print("-" * 40)
    data = collect_all()
    print("-" * 40)
    print("\n📈 Résultat:")
    for crypto, info in data.items():
        print(f"   {crypto}: ${info['price']:,.2f}")