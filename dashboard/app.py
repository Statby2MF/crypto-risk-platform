"""
Dashboard Crypto Risk Platform
Interface web pour visualiser les indicateurs et les risques
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import requests
from datetime import datetime
import numpy as np

# Importer nos modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.indicators import calculate_all_indicators
from src.risk_models import RiskModels
from src.alert_system import AlertSystem
from src.collector import get_historical_binance
from src.paper_trading import PaperTrading

# ============================================
# CONFIGURATION DE LA PAGE
# ============================================

st.set_page_config(
    page_title="Crypto Risk Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Couleurs
COLORS = {
    "primary": "#6C63FF",
    "success": "#00D2FF",
    "warning": "#FFB74D",
    "danger": "#FF4444",
}

# ============================================
# CSS PERSONNALISÉ
# ============================================

st.markdown("""
<style>
    .stApp { background-color: #0d0d1a; }
    .metric-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 20px;
        margin: 5px 0;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #6C63FF;
    }
    .metric-card .value {
        font-size: 28px;
        font-weight: 700;
        color: #FFFFFF;
    }
    .metric-card .label {
        color: #a0a0b8;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .footer {
        text-align: center;
        color: #4a4a5e;
        font-size: 12px;
        padding: 20px;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 30px;
    }
    h1, h2, h3 { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALISATION
# ============================================

risk_models = RiskModels()
alert_system = AlertSystem()

if "paper_trader" not in st.session_state:
    st.session_state.paper_trader = PaperTrading(initial_capital=10000)

paper_trader = st.session_state.paper_trader

# Mapping des cryptos
CRYPTO_MAP = {
    "Bitcoin (BTC)": {"symbol": "BTC", "binance": "BTCUSDT", "coingecko": "bitcoin"},
    "Ethereum (ETH)": {"symbol": "ETH", "binance": "ETHUSDT", "coingecko": "ethereum"},
    "Solana (SOL)": {"symbol": "SOL", "binance": "SOLUSDT", "coingecko": "solana"},
    "Ripple (XRP)": {"symbol": "XRP", "binance": "XRPUSDT", "coingecko": "ripple"},
    "Cardano (ADA)": {"symbol": "ADA", "binance": "ADAUSDT", "coingecko": "cardano"}
}

# ============================================
# FONCTIONS DE COLLECTE
# ============================================

def get_price_with_fallback(crypto_key):
    """Récupère le prix avec fallback"""
    crypto_info = CRYPTO_MAP.get(crypto_key)
    if not crypto_info:
        return None
    
    # 1. Binance
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={crypto_info['binance']}"
        response = requests.get(url, timeout=10)
        return float(response.json()['price'])
    except:
        pass
    
    # 2. CoinGecko
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_info['coingecko']}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        return float(response.json()[crypto_info['coingecko']]['usd'])
    except:
        pass
    
    # 3. Yahoo
    try:
        ticker = yf.Ticker(crypto_info['symbol'] + "-USD")
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except:
        pass
    
    return None

# ============================================
# SIDEBAR - CONFIGURATION
# ============================================

with st.sidebar:
    st.markdown("<h2 style='color: #6C63FF;'>⚙️ Configuration</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    crypto_key = st.selectbox(
        "📈 Cryptomonnaie",
        list(CRYPTO_MAP.keys()),
        index=0
    )
    crypto_info = CRYPTO_MAP[crypto_key]
    crypto_short = crypto_info["symbol"]
    
    period = st.selectbox(
        "📅 Période",
        ["1mo", "3mo", "6mo", "1y"],
        index=1
    )
    
    st.markdown("---")
    
    if st.button("🔄 Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;'>
        <p style='color: #a0a0b8; font-size: 12px;'>
            📊 <b>Données</b><br>
            • Binance / CoinGecko<br>
            • Mise à jour: À la demande
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# CHARGEMENT DES DONNÉES
# ============================================

current_price = get_price_with_fallback(crypto_key)

if current_price is None:
    st.error(f"❌ Impossible de récupérer le prix pour {crypto_key}")
    st.stop()

# Historique
try:
    hist_prices = get_historical_binance(crypto_info["binance"], limit=100)
    if hist_prices and len(hist_prices) > 20:
        dates = pd.date_range(end=datetime.now(), periods=len(hist_prices), freq='D')
        hist = pd.DataFrame({'Close': hist_prices}, index=dates)
    else:
        raise Exception("Pas assez de données")
except:
    ticker = yf.Ticker(crypto_info["symbol"] + "-USD")
    hist = ticker.history(period=period)
    if hist.empty:
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        hist = pd.DataFrame({'Close': [current_price * (1 + np.random.randn() * 0.02) for _ in range(50)]}, index=dates)

prices = hist['Close'].tolist()
dates = hist.index.tolist()

# Indicateurs
indicators = calculate_all_indicators(prices)
risk_result = risk_models.analyze_risk(crypto_short, prices)
action_result = alert_system.determine_action(indicators, risk_result)

# ============================================
# SIDEBAR - COMPTE DÉMO (après chargement)
# ============================================

with st.sidebar:
    st.markdown("---")
    st.markdown("<h3 style='color: #00D2FF;'>💰 Compte Démo</h3>", unsafe_allow_html=True)
    
    current_prices = {crypto_short: current_price}
    summary = paper_trader.get_summary(current_prices)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("💰 Solde", f"${paper_trader.balance:,.2f}")
    with col2:
        profit_color = "green" if summary['profit'] > 0 else "red"
        st.metric("📈 P&L", f"${summary['profit']:,.2f}", f"{summary['profit_pct']:.1f}%")
    
    if summary['positions']:
        st.markdown("**📊 Positions:**")
        for pos in summary['positions']:
            st.text(f"{pos['crypto']}: {pos['quantity']:.4f}")
    
    st.markdown("---")
    st.markdown("**📈 Actions:**")
    
    amount = st.number_input("💰 Montant ($)", 10, 100000, 100, 50, key="trade_amount")
    trade_crypto = st.selectbox("📊 Crypto", ["BTC", "ETH", "SOL", "XRP", "ADA"], key="trade_crypto")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🟢 Acheter", use_container_width=True):
            crypto_price = current_price if trade_crypto == crypto_short else current_price * 0.95
            if paper_trader.buy(trade_crypto, crypto_price, amount=amount):
                st.success(f"✅ Achat {trade_crypto}")
                st.rerun()
            else:
                st.error("❌ Fonds insuffisants")
    
    with col2:
        if st.button("🔴 Vendre", use_container_width=True):
            crypto_price = current_price if trade_crypto == crypto_short else current_price * 0.95
            if paper_trader.sell(trade_crypto, crypto_price):
                st.success(f"✅ Vente {trade_crypto}")
                st.rerun()
            else:
                st.error("❌ Pas de position")
    
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            paper_trader.reset()
            st.success("✅ Réinitialisé")
            st.rerun()

# ============================================
# EN-TÊTE
# ============================================

st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='color: #6C63FF; font-size: 3em;'>📊 Crypto Risk Platform</h1>
    <p style='color: #a0a0b8;'>Analyse des risques extrêmes et indicateurs techniques</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================
# MÉTRIQUES
# ============================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <p class='label'>💰 {crypto_short}</p>
        <p class='value'>${current_price:,.2f}</p>
        <p style='color: #a0a0b8; font-size: 12px;'>{datetime.now().strftime('%H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    rsi = indicators.get('rsi', 50)
    color = "#00D2FF" if rsi < 30 else "#FF4444" if rsi > 70 else "#FFB74D"
    text = "Survendu 📉" if rsi < 30 else "Suracheté 📈" if rsi > 70 else "Neutre ⚪"
    st.markdown(f"""
    <div class='metric-card'>
        <p class='label'>📊 RSI</p>
        <p class='value' style='color: {color};'>{rsi:.1f}</p>
        <p style='color: #a0a0b8; font-size: 12px;'>{text}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    action = action_result.get('action', 'N/A')
    color = "#00D2FF" if "ACHETER" in action else "#FF4444" if "VENDRE" in action else "#FFB74D"
    st.markdown(f"""
    <div class='metric-card'>
        <p class='label'>🎯 Signal</p>
        <p class='value' style='color: {color}; font-size: 22px;'>{action}</p>
        <p style='color: #a0a0b8; font-size: 12px;'>Score: {action_result.get('score', 0)}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    if risk_result:
        var_text = f"{risk_result.get('var_99', 'N/A')}%"
        color = "#FF4444" if risk_result.get('var_99_alerte', False) else "#00D2FF"
    else:
        var_text = "N/A"
        color = "#FFB74D"
    st.markdown(f"""
    <div class='metric-card'>
        <p class='label'>⚠️ VaR 99%</p>
        <p class='value' style='color: {color};'>{var_text}</p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    vol_text = f"{risk_result.get('vol_actuelle', 'N/A')}%" if risk_result else "N/A"
    st.markdown(f"""
    <div class='metric-card'>
        <p class='label'>🌊 Volatilité</p>
        <p class='value'>{vol_text}</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# GRAPHIQUE
# ============================================

st.markdown("---")
st.subheader("📈 Évolution des Prix")

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name=crypto_short, line=dict(color="#6C63FF", width=2)))

if indicators.get('bollinger'):
    b = indicators['bollinger']
    fig.add_trace(go.Scatter(x=dates[-20:], y=[b['upper']]*len(dates[-20:]), mode='lines', name='Bande haute', line=dict(color="#FF4444", dash='dash')))
    fig.add_trace(go.Scatter(x=dates[-20:], y=[b['middle']]*len(dates[-20:]), mode='lines', name='MA20', line=dict(color="#FFB74D", dash='dot')))
    fig.add_trace(go.Scatter(x=dates[-20:], y=[b['lower']]*len(dates[-20:]), mode='lines', name='Bande basse', line=dict(color="#00D2FF", dash='dash')))

fig.update_layout(height=400, template='plotly_dark', hovermode='x unified')
st.plotly_chart(fig, use_container_width=True)

# ============================================
# INDICATEURS + RISQUE
# ============================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("---")
    st.subheader("📊 Indicateurs Techniques")
    
    macd = indicators.get('macd', {})
    ma = indicators.get('moving_averages', {})
    
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;'>
        <p>RSI: <b>{indicators.get('rsi', 'N/A')}</b></p>
        <p>MACD: <b>{macd.get('macd', 0):.4f}</b> | Signal: <b>{macd.get('signal', 0):.4f}</b></p>
        <p>MA20: <b>${ma.get('ma20', 0):,.2f}</b> | MA50: <b>${ma.get('ma50', 0):,.2f}</b></p>
        <p>Tendance: <b style='color: {'#00D2FF' if ma.get('trend') == 'HAUSSIÈRE' else '#FF4444'};'>{ma.get('trend', 'N/A')}</b></p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("---")
    st.subheader("⚠️ Risques Extrêmes")
    
    if risk_result:
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;'>
            <p>VaR 95%: <b>{risk_result.get('var_95', 'N/A')}%</b></p>
            <p>VaR 99%: <b>{risk_result.get('var_99', 'N/A')}%</b></p>
            <p>ES 95%: <b>{risk_result.get('es_95', 'N/A')}%</b></p>
            <p>ES 99%: <b>{risk_result.get('es_99', 'N/A')}%</b></p>
            <p>Hill ξ: <b>{risk_result.get('hill_xi', 'N/A')}</b></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("⏳ Analyse en cours...")

# ============================================
# TABLEAU
# ============================================

with st.expander("📊 Tableau des indicateurs"):
    data = {
        "Indicateur": ["Prix", "RSI", "MACD", "MA20", "MA50", "VaR 95%", "VaR 99%", "ES 95%", "ES 99%", "Hill ξ", "Volatilité"],
        "Valeur": [
            f"${current_price:,.2f}",
            f"{indicators.get('rsi', 'N/A')}",
            f"{macd.get('macd', 0):.4f}",
            f"${ma.get('ma20', 0):,.2f}",
            f"${ma.get('ma50', 0):,.2f}",
            f"{risk_result.get('var_95', 'N/A') if risk_result else 'N/A'}%",
            f"{risk_result.get('var_99', 'N/A') if risk_result else 'N/A'}%",
            f"{risk_result.get('es_95', 'N/A') if risk_result else 'N/A'}%",
            f"{risk_result.get('es_99', 'N/A') if risk_result else 'N/A'}%",
            f"{risk_result.get('hill_xi', 'N/A') if risk_result else 'N/A'}",
            f"{risk_result.get('vol_actuelle', 'N/A') if risk_result else 'N/A'}%"
        ]
    }
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

# ============================================
# PIED DE PAGE
# ============================================

st.markdown("---")
st.markdown(f"""
<div class='footer'>
    🔍 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | ⚠️ Pas un conseil financier
</div>
""", unsafe_allow_html=True)
"Fix: ordre des variables et simplification"
