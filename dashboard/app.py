"""
Dashboard Crypto Risk Platform
Interface web pour visualiser les indicateurs et les risques
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time
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

# Couleurs personnalisées
COLORS = {
    "primary": "#6C63FF",
    "secondary": "#FF6B6B",
    "success": "#00D2FF",
    "warning": "#FFB74D",
    "danger": "#FF4444",
    "dark": "#1E1E2E",
    "card": "#2D2D44",
    "text": "#FFFFFF",
    "text_secondary": "#A0A0B8"
}

# ============================================
# CSS PERSONNALISÉ
# ============================================

st.markdown("""
<style>
    .stApp {
        background-color: #0d0d1a;
    }
    .metric-card {
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 20px;
        margin: 5px 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #6C63FF;
        box-shadow: 0 8px 30px rgba(108,99,255,0.2);
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
    h1, h2, h3 {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALISATION
# ============================================

risk_models = RiskModels()
alert_system = AlertSystem()

# ============================================
# COMPTE DE TRADING DÉMO (SESSION)
# ============================================

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
# FONCTIONS DE COLLECTE DE DONNÉES
# ============================================

def get_price_binance(symbol):
    """Récupère le prix depuis Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"❌ Binance error: {e}")
        return None

def get_price_coingecko(coin_id):
    """Récupère le prix depuis CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data[coin_id]['usd'])
    except Exception as e:
        print(f"❌ CoinGecko error: {e}")
        return None

def get_price_with_fallback(crypto_key):
    """Récupère le prix avec fallback: Binance → CoinGecko"""
    crypto_info = CRYPTO_MAP.get(crypto_key)
    if not crypto_info:
        return None
    
    price = get_price_binance(crypto_info["binance"])
    if price:
        return price
    
    price = get_price_coingecko(crypto_info["coingecko"])
    if price:
        return price
    
    return None

def get_historical_data(symbol, period="3mo"):
    """Récupère les données historiques depuis Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        return hist
    except Exception as e:
        print(f"❌ Yahoo error: {e}")
        return pd.DataFrame()

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
        "📅 Période d'historique",
        ["1mo", "3mo", "6mo", "1y", "2y"],
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
            📊 <b>Données en temps réel</b><br>
            • Source: Binance / CoinGecko<br>
            • Mise à jour: À la demande
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================
    # COMPTE DE TRADING DÉMO
    # ============================================
    
    st.markdown("---")
    st.markdown("<h3 style='color: #00D2FF;'>💰 Compte Démo</h3>", unsafe_allow_html=True)
    
    # Prix actuels pour le portefeuille
    current_prices = {crypto_short: current_price}   # ← ACCOLADES {}
    
    # Résumé du compte
    summary = paper_trader.get_summary(current_prices)
    
    # Afficher le solde
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="💰 Solde",
            value=f"${paper_trader.balance:,.2f}"
        )
    with col2:
        profit_color = "green" if summary['profit'] > 0 else "red"
        st.metric(
            label="📈 P&L",
            value=f"${summary['profit']:,.2f}",
            delta=f"{summary['profit_pct']:.1f}%"
        )
    
    # Positions
    if summary['positions']:
        st.markdown("**📊 Positions:**")
        for pos in summary['positions']:
            st.text(f"{pos['crypto']}: {pos['quantity']:.4f} (${pos['value']:,.2f})")
    
    # Boutons d'action
    st.markdown("---")
    st.markdown("**📈 Actions:**")
    
    # Achat
    amount = st.number_input(
        "💰 Montant ($)",
        min_value=10,
        max_value=100000,
        value=100,
        step=50,
        key="trade_amount"
    )
    
    trade_crypto = st.selectbox(
        "📊 Crypto",
        ["BTC", "ETH", "SOL", "XRP", "ADA"],
        key="trade_crypto"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🟢 Acheter", use_container_width=True):
            # Prix pour la crypto sélectionnée
            crypto_price = current_price if trade_crypto == crypto_short else current_price * 0.95
            if paper_trader.buy(trade_crypto, crypto_price, amount=amount):
                st.success(f"✅ Achat {trade_crypto} effectué !")
                st.rerun()
            else:
                st.error("❌ Achat échoué (fonds insuffisants)")
    
    with col2:
        if st.button("🔴 Vendre", use_container_width=True):
            crypto_price = current_price if trade_crypto == crypto_short else current_price * 0.95
            if paper_trader.sell(trade_crypto, crypto_price):
                st.success(f"✅ Vente {trade_crypto} effectuée !")
                st.rerun()
            else:
                st.error("❌ Vente échouée (pas de position)")
    
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            paper_trader.reset()
            st.success("✅ Compte réinitialisé")
            st.rerun()
    
    # Historique des trades
    if summary['trades']:
        with st.expander("📋 Historique des trades"):
            for trade in summary['trades'][-5:]:
                emoji = "🟢" if trade['type'] == 'BUY' else "🔴"
                profit_text = f" ({trade.get('profit_pct', 0):.1f}%)" if trade['type'] == 'SELL' else ""
                st.text(f"{emoji} {trade['type']} {trade['crypto']} {trade['quantity']:.4f} @ ${trade['price']:,.2f}{profit_text}")
    
    st.markdown("---")
    st.markdown("""
    <p style='color: #666; font-size: 11px; text-align: center;'>
        ⚠️ Ceci n'est pas un conseil financier
    </p>
    """, unsafe_allow_html=True)

# ============================================
# CHARGEMENT DES DONNÉES - AVANT LES MÉTRIQUES
# ============================================

# Prix actuel
current_price = get_price_with_fallback(crypto_key)

if current_price is None:
    st.error(f"❌ Impossible de récupérer le prix pour {crypto_key}")
    st.stop()

# Données historiques depuis Binance (rapide)
try:
    hist_prices = get_historical_binance(crypto_info["binance"], limit=100)
    
    if hist_prices and len(hist_prices) > 20:
        dates = pd.date_range(end=datetime.now(), periods=len(hist_prices), freq='D')
        hist = pd.DataFrame({
            'Close': hist_prices,
            'Open': hist_prices,
            'High': hist_prices,
            'Low': hist_prices
        }, index=dates)
        st.success("✅ Données historiques chargées depuis Binance")
    else:
        raise Exception("Pas assez de données Binance")
        
except Exception as e:
    st.info("📊 Utilisation de Yahoo Finance pour l'historique")
    hist = get_historical_data(crypto_info["symbol"], period)
    
    if hist.empty:
        st.warning("⚠️ Données historiques limitées, utilisation de données simulées")
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        base_price = current_price
        prices = [base_price * (1 + np.random.randn() * 0.015) for _ in range(50)]
        prices = np.cumsum(prices) / 50 * base_price / 5 + base_price * 0.95
        hist = pd.DataFrame({
            'Close': prices,
            'Open': prices,
            'High': prices * 1.01,
            'Low': prices * 0.99
        }, index=dates)

prices = hist['Close'].tolist()
dates = hist.index.tolist()

# ============================================
# CALCUL DES INDICATEURS - APRÈS CHARGEMENT
# ============================================

indicators = calculate_all_indicators(prices)
risk_result = risk_models.analyze_risk(crypto_short, prices)
action_result = alert_system.determine_action(indicators, risk_result)

# ============================================
# EN-TÊTE
# ============================================

st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='color: #6C63FF; font-size: 3em;'>📊 Crypto Risk Platform</h1>
    <p style='color: #a0a0b8; font-size: 1.1em;'>
        Analyse des risques extrêmes et indicateurs techniques
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================
# MÉTRIQUES PRINCIPALES
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
    rsi_color = "#00D2FF" if rsi < 30 else "#FF4444" if rsi > 70 else "#FFB74D"
    rsi_text = "Survendu 📉" if rsi < 30 else "Suracheté 📈" if rsi > 70 else "Neutre ⚪"
    st.markdown(f"""
    <div class='metric-card'>
        <p class='label'>📊 RSI</p>
        <p class='value' style='color: {rsi_color};'>{rsi:.1f}</p>
        <p style='color: #a0a0b8; font-size: 12px;'>{rsi_text}</p>
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
        var_99 = risk_result.get('var_99')
        var_text = f"{var_99}%" if var_99 is not None else "N/A"
        var_color = "#FF4444" if risk_result.get('var_99_alerte', False) else "#00D2FF"
    else:
        var_text = "N/A"
        var_color = "#FFB74D"
    st.markdown(f"""
    <div class='metric-card'>
        <p class='label'>⚠️ VaR 99%</p>
        <p class='value' style='color: {var_color};'>{var_text}</p>
        <p style='color: #a0a0b8; font-size: 12px;'>
            {'🔴 Risque élevé' if risk_result and risk_result.get('var_99_alerte', False) else '✅ Risque maîtrisé' if risk_result else '⏳ Calcul...'}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    if risk_result:
        vol = risk_result.get('vol_actuelle')
        vol_text = f"{vol}%" if vol is not None else "N/A"
        vol_theorique = risk_result.get('vol_theorique', 'N/A')
    else:
        vol_text = "N/A"
        vol_theorique = "N/A"
    st.markdown(f"""
    <div class='metric-card'>
        <p class='label'>🌊 Volatilité</p>
        <p class='value'>{vol_text}</p>
        <p style='color: #a0a0b8; font-size: 12px;'>Théorique: {vol_theorique}%</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# GRAPHIQUE DES PRIX
# ============================================

st.markdown("---")
st.subheader("📈 Évolution des Prix")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=dates,
    y=prices,
    mode='lines',
    name=crypto_short,
    line=dict(color="#6C63FF", width=2),
    fill='tozeroy',
    fillcolor='rgba(108, 99, 255, 0.1)'
))

if indicators.get('bollinger'):
    bollinger = indicators['bollinger']
    fig.add_trace(go.Scatter(
        x=dates[-20:],
        y=[bollinger['upper']] * len(dates[-20:]),
        mode='lines',
        name='Bande haute',
        line=dict(color="#FF4444", width=1, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=dates[-20:],
        y=[bollinger['middle']] * len(dates[-20:]),
        mode='lines',
        name='MA20',
        line=dict(color="#FFB74D", width=1, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=dates[-20:],
        y=[bollinger['lower']] * len(dates[-20:]),
        mode='lines',
        name='Bande basse',
        line=dict(color="#00D2FF", width=1, dash='dash')
    ))

fig.update_layout(
    height=400,
    template='plotly_dark',
    xaxis_title='Date',
    yaxis_title='Prix ($)',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)

# ============================================
# DEUX COLONNES : INDICATEURS + RISQUE
# ============================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("---")
    st.subheader("📊 Indicateurs Techniques")
    
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 5px 0;'>
        <p style='color: #a0a0b8;'>RSI: <b style='color: #FFFFFF;'>{indicators.get('rsi', 'N/A')}</b></p>
        <div style='background: #3D3D5C; height: 6px; border-radius: 3px;'>
            <div style='background: #6C63FF; width: {min(indicators.get('rsi', 50), 100)}%; height: 6px; border-radius: 3px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    macd = indicators.get('macd', {})
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 5px 0;'>
        <p style='color: #a0a0b8;'>
            MACD: <b style='color: #FFFFFF;'>{macd.get('macd', 0):.4f}</b>
            | Signal: <b style='color: #FFFFFF;'>{macd.get('signal', 0):.4f}</b>
            | Hist: <b style='color: {'#00D2FF' if macd.get('histogram', 0) > 0 else '#FF4444'};'>{macd.get('histogram', 0):.4f}</b>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    ma = indicators.get('moving_averages', {})
    trend_color = "#00D2FF" if ma.get('trend') == "HAUSSIÈRE" else "#FF4444"
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin: 5px 0;'>
        <p style='color: #a0a0b8;'>
            MA20: <b style='color: #FFFFFF;'>${ma.get('ma20', 0):,.2f}</b>
            | MA50: <b style='color: #FFFFFF;'>${ma.get('ma50', 0):,.2f}</b>
        </p>
        <p style='color: {trend_color};'>Tendance: {ma.get('trend', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("---")
    st.subheader("⚠️ Analyse des Risques Extrêmes")
    
    if risk_result:
        risk_col1, risk_col2 = st.columns(2)
        
        with risk_col1:
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 10px; margin: 3px 0;'>
                <p style='color: #a0a0b8; font-size: 12px;'>VaR 95%</p>
                <p style='color: #FFFFFF; font-size: 20px; font-weight: bold;'>{risk_result.get('var_95', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 10px; margin: 3px 0;'>
                <p style='color: #a0a0b8; font-size: 12px;'>ES 95%</p>
                <p style='color: #FFFFFF; font-size: 20px; font-weight: bold;'>{risk_result.get('es_95', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with risk_col2:
            var_color = "#FF4444" if risk_result.get('var_99_alerte', False) else "#00D2FF"
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 10px; margin: 3px 0;'>
                <p style='color: #a0a0b8; font-size: 12px;'>VaR 99%</p>
                <p style='color: {var_color}; font-size: 20px; font-weight: bold;'>{risk_result.get('var_99', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 10px; margin: 3px 0;'>
                <p style='color: #a0a0b8; font-size: 12px;'>ES 99%</p>
                <p style='color: #FFFFFF; font-size: 20px; font-weight: bold;'>{risk_result.get('es_99', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        hill = risk_result.get('hill_xi')
        hill_text = f"{hill:.3f}" if hill is not None else "N/A"
        hill_color = "#FFB74D" if hill is not None and hill > 0 else "#00D2FF"
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 10px; margin: 3px 0;'>
            <p style='color: #a0a0b8; font-size: 12px;'>Hill ξ (indice de queue)</p>
            <p style='color: {hill_color}; font-size: 20px; font-weight: bold;'>{hill_text}</p>
            <p style='color: #a0a0b8; font-size: 11px;'>
                { 'Queue lourde 🟡' if hill is not None and hill > 0 else 'Queue légère 🟢' }
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("⏳ Analyse des risques en cours...")

# ============================================
# DÉTAILS DE L'ANALYSE
# ============================================

st.markdown("---")
st.subheader("🔍 Détails de l'Analyse")

with st.expander("📋 Afficher les détails du signal"):
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;'>
        <p style='color: #FFFFFF;'><b>Action:</b> {action_result.get('action', 'N/A')}</p>
        <p style='color: #FFFFFF;'><b>Score:</b> {action_result.get('score', 0)}</p>
        <p style='color: #FFFFFF;'><b>Confiance:</b> {action_result.get('confidence', 'N/A')}</p>
        <p style='color: #a0a0b8;'><b>Raisons:</b></p>
    """, unsafe_allow_html=True)
    
    for reason in action_result.get('reasons', []):
        st.write(f"- {reason}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# TABLEAU DES INDICATEURS
# ============================================

with st.expander("📊 Tableau des indicateurs"):
    hill_value = risk_result.get('hill_xi') if risk_result else None
    data = {
        "Indicateur": ["Prix", "RSI", "MACD", "Signal MACD", "MA20", "MA50", "VaR 95%", "VaR 99%", "ES 95%", "ES 99%", "Hill ξ", "Volatilité"],
        "Valeur": [
            f"${current_price:,.2f}",
            f"{indicators.get('rsi', 'N/A')}",
            f"{macd.get('macd', 0):.4f}",
            f"{macd.get('signal', 0):.4f}",
            f"${ma.get('ma20', 0):,.2f}",
            f"${ma.get('ma50', 0):,.2f}",
            f"{risk_result.get('var_95', 'N/A') if risk_result else 'N/A'}%",
            f"{risk_result.get('var_99', 'N/A') if risk_result else 'N/A'}%",
            f"{risk_result.get('es_95', 'N/A') if risk_result else 'N/A'}%",
            f"{risk_result.get('es_99', 'N/A') if risk_result else 'N/A'}%",
            f"{hill_value:.3f}" if hill_value is not None else "N/A",
            f"{risk_result.get('vol_actuelle', 'N/A') if risk_result else 'N/A'}%"
        ]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================
# PIED DE PAGE
# ============================================

st.markdown("---")
st.markdown(f"""
<div class='footer'>
    🔍 Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    | Données: Binance / CoinGecko
    | ⚠️ Ceci n'est pas un conseil financier
</div>
""", unsafe_allow_html=True)
"Ajout du compte de trading démo"
"Fix: dictionnaire current_prices"
