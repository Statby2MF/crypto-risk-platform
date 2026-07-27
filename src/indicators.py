"""
Indicateurs techniques pour l'analyse des cryptomonnaies
"""
import numpy as np
import pandas as pd

def calculate_rsi(prices, period=14):
    """
    Calcule le RSI (Relative Strength Index)
    
    Args:
        prices: Liste ou array des prix
        period: Période de calcul (défaut: 14)
    
    Returns:
        float: Valeur du RSI (0-100)
    """
    if len(prices) < period + 1:
        return 50  # Valeur neutre si pas assez de données
    
    # Convertir en array numpy
    prices = np.array(prices)
    
    # Calculer les variations
    deltas = np.diff(prices)
    
    # Séparer les gains et les pertes
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Moyenne des gains et des pertes
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Calcule le MACD
    
    Args:
        prices: Liste des prix
        fast: Période rapide (défaut: 12)
        slow: Période lente (défaut: 26)
        signal: Période du signal (défaut: 9)
    
    Returns:
        dict: MACD, Signal, Histogramme
    """
    if len(prices) < slow + signal:
        return {"macd": 0, "signal": 0, "histogram": 0}
    
    # Convertir en DataFrame pour les calculs
    df = pd.DataFrame(prices, columns=['close'])
    
    # Calculer les EMA
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    
    # Ligne MACD
    macd_line = ema_fast - ema_slow
    
    # Ligne de signal
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    
    # Histogramme
    histogram = macd_line - signal_line
    
    return {
        "macd": round(macd_line.iloc[-1], 4),
        "signal": round(signal_line.iloc[-1], 4),
        "histogram": round(histogram.iloc[-1], 4)
    }

def calculate_bollinger(prices, period=20, std_dev=2):
    """
    Calcule les Bandes de Bollinger
    
    Args:
        prices: Liste des prix
        period: Période (défaut: 20)
        std_dev: Nombre d'écarts-types (défaut: 2)
    
    Returns:
        dict: Moyenne, Bande haute, Bande basse
    """
    if len(prices) < period:
        recent_prices = prices
    else:
        recent_prices = prices[-period:]
    
    mean_price = np.mean(recent_prices)
    std_price = np.std(recent_prices)
    
    return {
        "middle": round(mean_price, 2),
        "upper": round(mean_price + std_dev * std_price, 2),
        "lower": round(mean_price - std_dev * std_price, 2)
    }

def calculate_moving_averages(prices):
    """
    Calcule les moyennes mobiles (MA20 et MA50)
    
    Args:
        prices: Liste des prix
    
    Returns:
        dict: MA20, MA50, Tendance
    """
    if len(prices) < 50:
        ma20 = np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)
        ma50 = ma20
    else:
        ma20 = np.mean(prices[-20:])
        ma50 = np.mean(prices[-50:])
    
    return {
        "ma20": round(ma20, 2),
        "ma50": round(ma50, 2),
        "trend": "HAUSSIÈRE" if ma20 > ma50 else "BAISSIÈRE"
    }

def calculate_all_indicators(prices):
    """
    Calcule tous les indicateurs en une seule fonction
    
    Args:
        prices: Liste des prix
    
    Returns:
        dict: Tous les indicateurs
    """
    return {
        "rsi": calculate_rsi(prices),
        "macd": calculate_macd(prices),
        "bollinger": calculate_bollinger(prices),
        "moving_averages": calculate_moving_averages(prices)
    }

# Test de la fonction
if __name__ == "__main__":
    # Simuler des prix pour le test
    import random
    test_prices = [50000 + random.randint(-500, 500) for _ in range(100)]
    
    print("📊 Test des indicateurs techniques")
    print("-" * 40)
    
    indicators = calculate_all_indicators(test_prices)
    
    print(f"RSI: {indicators['rsi']}")
    print(f"MACD: {indicators['macd']['macd']}")
    print(f"Signal MACD: {indicators['macd']['signal']}")
    print(f"Histogramme MACD: {indicators['macd']['histogram']}")
    print(f"Bollinger Haut: ${indicators['bollinger']['upper']:,.2f}")
    print(f"Bollinger Milieu: ${indicators['bollinger']['middle']:,.2f}")
    print(f"Bollinger Bas: ${indicators['bollinger']['lower']:,.2f}")
    print(f"MA20: ${indicators['moving_averages']['ma20']:,.2f}")
    print(f"MA50: ${indicators['moving_averages']['ma50']:,.2f}")
    print(f"Tendance: {indicators['moving_averages']['trend']}")