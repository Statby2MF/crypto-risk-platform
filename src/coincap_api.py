"""
API CoinCap - Données crypto fiables et gratuites
https://docs.coincap.io/
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

# Mapping des symboles vers les IDs CoinCap
COINCAP_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "MATIC": "polygon",
    "AVAX": "avalanche"
}

# Intervalle de temps pour l'historique
INTERVAL_MAP = {
    "1mo": "d1",   # 1 mois -> quotidien
    "3mo": "d1",
    "6mo": "d1",
    "1y": "d1",
    "2y": "d1",
    "5y": "d1"
}

# Nombre de jours pour chaque période
PERIOD_DAYS = {
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825
}

def get_price_coincap(crypto_symbol):
    """
    Récupère le prix actuel depuis CoinCap
    """
    try:
        crypto_id = COINCAP_IDS.get(crypto_symbol.upper())
        if not crypto_id:
            logger.warning(f"⚠️ Symbole {crypto_symbol} non reconnu par CoinCap")
            return None
        
        # Essayer avec l'IP directe si le DNS échoue
        urls = [
            f"https://api.coincap.io/v2/assets/{crypto_id}",
            f"https://104.26.11.101/v2/assets/{crypto_id}"  # IP de CoinCap
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=10, headers={"Host": "api.coincap.io"})
                if response.status_code == 200:
                    data = response.json()
                    price = float(data['data']['priceUsd'])
                    logger.info(f"✅ CoinCap: {crypto_symbol} = ${price:,.2f}")
                    return price
            except:
                continue
        
        logger.warning(f"⚠️ CoinCap échec pour {crypto_symbol}")
        return None
            
    except Exception as e:
        logger.error(f"❌ CoinCap error: {e}")
        return None


def get_historical_coincap(crypto_symbol, period="3mo"):
    """
    Récupère l'historique des prix depuis CoinCap
    
    Args:
        crypto_symbol: Symbole de la crypto (ex: "BTC")
        period: Période ("1mo", "3mo", "6mo", "1y", "2y", "5y")
    
    Returns:
        list: Liste des prix de clôture, ou None si erreur
    """
    try:
        crypto_id = COINCAP_IDS.get(crypto_symbol.upper())
        if not crypto_id:
            logger.warning(f"⚠️ Symbole {crypto_symbol} non reconnu par CoinCap")
            return None
        
        # Intervalle en fonction de la période
        interval = INTERVAL_MAP.get(period, "d1")
        
        # Nombre de jours à récupérer
        days = PERIOD_DAYS.get(period, 90)
        
        # CoinCap retourne max 2000 bougies, on va chercher les dernières
        limit = min(days, 100)  # 100 jours suffisent pour nos indicateurs
        
        url = f"https://api.coincap.io/v2/assets/{crypto_id}/history?interval={interval}&limit={limit}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            prices = []
            
            for item in data['data']:
                price = float(item['priceUsd'])
                prices.append(price)
            
            if prices:
                # Inverser pour avoir du plus ancien au plus récent
                prices = prices[::-1]
                logger.info(f"✅ CoinCap historique: {len(prices)} points pour {crypto_symbol}")
                return prices
            else:
                logger.warning(f"⚠️ Aucune donnée historique pour {crypto_symbol}")
                return None
        else:
            logger.warning(f"⚠️ CoinCap historique erreur {response.status_code} pour {crypto_symbol}")
            return None
            
    except Exception as e:
        logger.error(f"❌ CoinCap historique error: {e}")
        return None


def get_prices_coincap_batch(crypto_symbols):
    """
    Récupère les prix de plusieurs cryptos en une seule requête
    
    Args:
        crypto_symbols: Liste des symboles (ex: ["BTC", "ETH", "SOL"])
    
    Returns:
        dict: {symbole: prix}
    """
    try:
        # Construire la liste des IDs
        ids = []
        symbol_map = {}
        for sym in crypto_symbols:
            crypto_id = COINCAP_IDS.get(sym.upper())
            if crypto_id:
                ids.append(crypto_id)
                symbol_map[crypto_id] = sym.upper()
        
        if not ids:
            return {}
        
        url = f"https://api.coincap.io/v2/assets?ids={','.join(ids)}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = {}
            for item in data['data']:
                sym = symbol_map.get(item['id'])
                if sym:
                    result[sym] = float(item['priceUsd'])
            return result
        else:
            return {}
            
    except Exception as e:
        logger.error(f"❌ CoinCap batch error: {e}")
        return {}


# Test rapide
if __name__ == "__main__":
    print("🧪 Test de l'API CoinCap")
    print("-" * 40)
    
    # Tester le prix
    btc_price = get_price_coincap("BTC")
    eth_price = get_price_coincap("ETH")
    sol_price = get_price_coincap("SOL")
    
    print(f"💰 BTC: ${btc_price:,.2f}" if btc_price else "❌ BTC échec")
    print(f"💰 ETH: ${eth_price:,.2f}" if eth_price else "❌ ETH échec")
    print(f"💰 SOL: ${sol_price:,.2f}" if sol_price else "❌ SOL échec")
    
    print("\n" + "-" * 40)
    
    # Tester l'historique
    hist = get_historical_coincap("BTC", "1mo")
    if hist:
        print(f"📊 BTC historique: {len(hist)} points")
        print(f"   Premier: ${hist[0]:,.2f}")
        print(f"   Dernier: ${hist[-1]:,.2f}")
    else:
        print("❌ Historique échec")
