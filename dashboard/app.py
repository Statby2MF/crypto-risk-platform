"""
Dashboard Crypto Risk Platform - Version Design Amélioré
Interface web pour visualiser les indicateurs et les risques
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import requests
from datetime import datetime
import numpy as np
import time

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

# ============================================
# CSS DESIGN AMÉLIORÉ
# ============================================

st.markdown("""
<style>
    /* Fond avec dégradé */
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Cartes avec effet glassmorphisme */
    .card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 20px 24px;
        margin: 8px 0;
        transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        position: relative;
        overflow: hidden;
    }
    
    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(108, 99, 255, 0.05), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    
    .card:hover {
        transform: translateY(-4px);
        border-color: rgba(108, 99, 255, 0.3);
        box-shadow: 0 20px 60px rgba(108, 99, 255, 0.15);
    }
    
    .card:hover::before {
        opacity: 1;
    }
    
    .card .label {
        color: #8892b0;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    
    .card .value {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
    }
    
    .card .sub {
        color: #8892b0;
        font-size: 13px;
        margin-top: 4px;
    }
    
    /* Badges de statut */
    .badge-success {
        background: rgba(0, 210, 255, 0.15);
        color: #00D2FF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-danger {
        background: rgba(255, 68, 68, 0.15);
        color: #FF4444;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-warning {
        background: rgba(255, 183, 77, 0.15);
        color: #FFB74D;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Titres */
    .title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6C63FF 0%, #00D2FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin: 0;
        padding: 20px 0 10px 0;
    }
    
    .subtitle {
        text-align: center;
        color: #8892b0;
        font-size: 1.1rem;
        margin-bottom: 20px;
    }
    
    /* Sidebar améliorée */
    .css-1d391kg, .css-1lcbmhc {
        background: rgba(10, 10, 26, 0.9) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Métriques personnalisées */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 16px 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(108, 99, 255, 0.3);
        transform: translateY(-2px);
    }
    
    .metric-card .metric-label {
        color: #8892b0;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin-top: 4px;
    }
    
    .metric-card .metric-change {
        font-size: 13px;
        margin-top: 2px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #4a4a5e;
        font-size: 12px;
        padding: 30px 0 20px 0;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 30px;
    }
    
    /* Boutons stylisés */
    .stButton > button {
        background: linear-gradient(135deg, #6C63FF, #5a52d5) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 30px rgba(108, 99, 255, 0.3);
    }
    
    /* Scrollbar personnalisée */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
    }
    ::-webkit-scrollbar-thumb {
        background: #6C63FF;
        border-radius: 10px;
    }
    
    /* Animation de chargement */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 1.5s ease-in-out infinite;
        color: #8892b0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALISATION AVEC GESTION D'ERREUR
# ============================================

@st.cache_resource
def init_models():
    """Initialise les modèles avec gestion d'erreur"""
    try:
        risk_models = RiskModels()
        alert_system = AlertSystem()
        return risk_models, alert_system
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation: {e}")
        return None, None

risk_models, alert_system = init_models()

if risk_models is None:
    st.stop()

# Compte démo
if "paper_trader" not in st.session_state:
    st.session_state.paper_trader = PaperTrading(initial_capital=10000)
paper_trader = st.session_state.paper_trader

# Mapping des cryptos
CRYPTO_MAP = {
    "Bitcoin (BTC)": {"symbol": "BTC", "binance": "BTCUSDT", "coingecko": "bitcoin", "emoji": "₿"},
    "Ethereum (ETH)": {"symbol": "ETH", "binance": "ETHUSDT", "coingecko": "ethereum", "emoji": "⟠"},
    "Solana (SOL)": {"symbol": "SOL", "binance": "SOLUSDT", "coingecko": "solana", "emoji": "◎"},
    "Ripple (XRP)": {"symbol": "XRP", "binance": "XRPUSDT", "coingecko": "ripple", "emoji": "✕"},
    "Cardano (ADA)": {"symbol": "ADA", "binance": "ADAUSDT", "coingecko": "cardano", "emoji": "₳"}
}

# ============================================
# FONCTIONS DE COLLECTE AVEC COINCAP
# ============================================

# Importer CoinCap
from src.coincap_api import get_price_coincap, get_historical_coincap

def get_price_with_fallback(crypto_key):
    """Récupère le prix avec fallback: CoinCap → Binance → Yahoo"""
    crypto_info = CRYPTO_MAP.get(crypto_key)
    if not crypto_info:
        return None
    
    # 1. CoinCap (prioritaire)
    price = get_price_coincap(crypto_info["symbol"])
    if price:
        return price
    
    # 2. Binance
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={crypto_info['binance']}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return float(response.json()['price'])
    except:
        pass
    
    # 3. Yahoo Finance
    try:
        ticker = yf.Ticker(crypto_info["symbol"] + "-USD")
        data = ticker.history(period="1d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except:
        pass
    
    return None

def get_historical_safe(crypto_info, period="3mo"):
    """Récupère l'historique: CoinCap → Binance → Yahoo"""
    
    # 1. CoinCap (prioritaire)
    try:
        hist = get_historical_coincap(crypto_info["symbol"], period)
        if hist and len(hist) > 20:
            dates = pd.date_range(end=datetime.now(), periods=len(hist), freq='D')
            return pd.DataFrame({'Close': hist}, index=dates)
    except:
        pass
    
    # 2. Binance
    try:
        hist = get_historical_binance(crypto_info["binance"], limit=100)
        if hist and len(hist) > 20:
            dates = pd.date_range(end=datetime.now(), periods=len(hist), freq='D')
            return pd.DataFrame({'Close': hist}, index=dates)
    except:
        pass
    
    # 3. Yahoo Finance
    try:
        ticker = yf.Ticker(crypto_info["symbol"] + "-USD")
        hist = ticker.history(period=period)
        if not hist.empty:
            return hist
    except:
        pass
    
    # Données simulées en dernier recours
    dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
    base_price = 50000 if crypto_info["symbol"] == "BTC" else 3000
    prices = [base_price * (1 + np.random.randn() * 0.02) for _ in range(50)]
    prices = np.cumsum(prices) / 50 * base_price / 5 + base_price * 0.95
    return pd.DataFrame({'Close': prices}, index=dates)

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
    crypto_emoji = crypto_info["emoji"]
    
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
    <div style='background: rgba(255,255,255,0.03); padding: 15px; border-radius: 12px;'>
        <p style='color: #8892b0; font-size: 12px;'>
            📊 <b>Sources</b><br>
            • Binance / CoinGecko<br>
            • Mise à jour: à la demande
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# CHARGEMENT DES DONNÉES AVEC INDICATEUR
# ============================================

with st.spinner("⏳ Chargement des données..."):
    current_price = get_price_with_fallback(crypto_key)
    
    if current_price is None:
        st.error("""
        ❌ **Impossible de récupérer les prix**
        
        Vérifiez votre connexion internet ou réessayez plus tard.
        """)
        st.stop()
    
    hist = get_historical_safe(crypto_info, period)
    prices = hist['Close'].tolist()
    dates = hist.index.tolist()

# ============================================
# CALCUL DES INDICATEURS AVEC GESTION D'ERREUR
# ============================================

try:
    indicators = calculate_all_indicators(prices)
    risk_result = risk_models.analyze_risk(crypto_short, prices)
    action_result = alert_system.determine_action(indicators, risk_result)
except Exception as e:
    st.error(f"⚠️ Erreur lors du calcul des indicateurs: {e}")
    st.stop()

# ============================================
# SIDEBAR - COMPTE DÉMO
# ============================================

with st.sidebar:
    st.markdown("---")
    st.markdown("<h3 style='color: #00D2FF;'>💰 Compte Démo</h3>", unsafe_allow_html=True)
    
    current_prices = {crypto_short: current_price}
    summary = paper_trader.get_summary(current_prices)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric(
            label="💰 Solde",
            value=f"${paper_trader.balance:,.2f}",
            delta=f"{summary['profit_pct']:.1f}%"
        )
    with col2:
        profit_color = "inverse" if summary['profit'] > 0 else "normal"
        st.metric(
            label="📈 P&L",
            value=f"${summary['profit']:,.2f}",
            delta_color=profit_color
        )
    
    if summary['positions']:
        st.markdown("**📊 Positions:**")
        for pos in summary['positions']:
            st.markdown(f"""
            <div style='background: rgba(255,255,255,0.03); border-radius: 8px; padding: 6px 12px; margin: 4px 0;'>
                <span style='color: #ffffff;'>{pos['crypto']}</span>
                <span style='color: #8892b0; float: right;'>{pos['quantity']:.4f}</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("**📈 Actions:**")
    
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
        if st.button("🟢 Acheter", use_container_width=True, type="primary"):
            crypto_price = current_price if trade_crypto == crypto_short else current_price * 0.95
            if paper_trader.buy(trade_crypto, crypto_price, amount=amount):
                st.success(f"✅ Achat {trade_crypto} effectué !")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Fonds insuffisants")
    
    with col2:
        if st.button("🔴 Vendre", use_container_width=True):
            crypto_price = current_price if trade_crypto == crypto_short else current_price * 0.95
            if paper_trader.sell(trade_crypto, crypto_price):
                st.success(f"✅ Vente {trade_crypto} effectuée !")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Pas de position")
    
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            paper_trader.reset()
            st.success("✅ Compte réinitialisé")
            time.sleep(0.5)
            st.rerun()

# ============================================
# EN-TÊTE
# ============================================

st.markdown(f"""
<div style='text-align: center; padding: 10px 0;'>
    <h1 class='title'>📊 Crypto Risk Platform</h1>
    <p class='subtitle'>Analyse des risques extrêmes et indicateurs techniques</p>
    <p style='color: #4a4a5e; font-size: 13px;'>
        {crypto_emoji} {crypto_key} · Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================
# MÉTRIQUES PRINCIPALES
# ============================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>💰 {crypto_short}</div>
        <div class='metric-value'>${current_price:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    rsi = indicators.get('rsi', 50)
    badge = 'badge-success' if rsi < 30 else 'badge-danger' if rsi > 70 else 'badge-warning'
    label = 'Survendu 📉' if rsi < 30 else 'Suracheté 📈' if rsi > 70 else 'Neutre ⚪'
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>📊 RSI</div>
        <div class='metric-value' style='color: {'#00D2FF' if rsi < 30 else '#FF4444' if rsi > 70 else '#FFB74D'};'>{rsi:.1f}</div>
        <div class='metric-change'><span class='{badge}'>{label}</span></div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    action = action_result.get('action', 'N/A')
    badge = 'badge-success' if "ACHETER" in action else 'badge-danger' if "VENDRE" in action else 'badge-warning'
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>🎯 Signal</div>
        <div class='metric-value' style='font-size: 20px;'>{action}</div>
        <div class='metric-change'><span class='{badge}'>Score: {action_result.get('score', 0)}</span></div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    var_text = f"{risk_result.get('var_99', 'N/A')}%" if risk_result else "N/A"
    color = "#FF4444" if risk_result and risk_result.get('var_99_alerte', False) else "#00D2FF"
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>⚠️ VaR 99%</div>
        <div class='metric-value' style='color: {color};'>{var_text}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    vol_text = f"{risk_result.get('vol_actuelle', 'N/A')}%" if risk_result else "N/A"
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>🌊 Volatilité</div>
        <div class='metric-value'>{vol_text}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# GRAPHIQUE
# ============================================

st.markdown("---")
st.subheader("📈 Évolution des Prix")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=dates, y=prices, 
    mode='lines', 
    name=crypto_short,
    line=dict(color="#6C63FF", width=2.5),
    fill='tozeroy',
    fillcolor='rgba(108, 99, 255, 0.08)'
))

if indicators.get('bollinger'):
    b = indicators['bollinger']
    fig.add_trace(go.Scatter(
        x=dates[-20:], 
        y=[b['upper']]*len(dates[-20:]), 
        mode='lines', 
        name='Bande haute',
        line=dict(color="#FF4444", width=1, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=dates[-20:], 
        y=[b['middle']]*len(dates[-20:]), 
        mode='lines', 
        name='MA20',
        line=dict(color="#FFB74D", width=1, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=dates[-20:], 
        y=[b['lower']]*len(dates[-20:]), 
        mode='lines', 
        name='Bande basse',
        line=dict(color="#00D2FF", width=1, dash='dash')
    ))

fig.update_layout(
    height=400,
    template='plotly_dark',
    hovermode='x unified',
    margin=dict(l=0, r=0, t=10, b=0),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)
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
    <div style='background: rgba(255,255,255,0.03); padding: 20px; border-radius: 16px;'>
        <p style='color: #8892b0; margin-bottom: 8px;'>📈 RSI</p>
        <p style='color: #ffffff; font-size: 20px; font-weight: 600;'>{indicators.get('rsi', 'N/A')}</p>
        
        <p style='color: #8892b0; margin: 16px 0 8px 0;'>📊 MACD</p>
        <p style='color: #ffffff;'>{macd.get('macd', 0):.4f} <span style='color: #8892b0;'>| Signal:</span> {macd.get('signal', 0):.4f}</p>
        <p style='color: {'#00D2FF' if macd.get('histogram', 0) > 0 else '#FF4444'};'>Histogramme: {macd.get('histogram', 0):.4f}</p>
        
        <p style='color: #8892b0; margin: 16px 0 8px 0;'>📉 Moyennes mobiles</p>
        <p style='color: #ffffff;'>MA20: ${ma.get('ma20', 0):,.2f}</p>
        <p style='color: #ffffff;'>MA50: ${ma.get('ma50', 0):,.2f}</p>
        <p style='color: {'#00D2FF' if ma.get('trend') == 'HAUSSIÈRE' else '#FF4444'}; font-weight: 600;'>
            Tendance: {ma.get('trend', 'N/A')}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("---")
    st.subheader("⚠️ Risques Extrêmes")
    
    if risk_result:
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.03); padding: 20px; border-radius: 16px;'>
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px;'>
                <div>
                    <p style='color: #8892b0; font-size: 12px;'>VaR 95%</p>
                    <p style='color: #ffffff; font-size: 20px; font-weight: 600;'>{risk_result.get('var_95', 'N/A')}%</p>
                </div>
                <div>
                    <p style='color: #8892b0; font-size: 12px;'>VaR 99%</p>
                    <p style='color: {'#FF4444' if risk_result.get('var_99_alerte', False) else '#00D2FF'}; font-size: 20px; font-weight: 600;'>
                        {risk_result.get('var_99', 'N/A')}%
                    </p>
                </div>
                <div>
                    <p style='color: #8892b0; font-size: 12px;'>ES 95%</p>
                    <p style='color: #ffffff; font-size: 20px; font-weight: 600;'>{risk_result.get('es_95', 'N/A')}%</p>
                </div>
                <div>
                    <p style='color: #8892b0; font-size: 12px;'>ES 99%</p>
                    <p style='color: #ffffff; font-size: 20px; font-weight: 600;'>{risk_result.get('es_99', 'N/A')}%</p>
                </div>
            </div>
            <div style='margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.05);'>
                <p style='color: #8892b0; font-size: 12px;'>Hill ξ (indice de queue)</p>
                <p style='color: {'#FFB74D' if risk_result.get('hill_xi', 0) > 0 else '#00D2FF'}; font-size: 18px; font-weight: 600;'>
                    {risk_result.get('hill_xi', 'N/A')}
                    <span style='color: #8892b0; font-weight: 400; font-size: 14px;'>
                        {'Queue lourde 🟡' if risk_result.get('hill_xi', 0) > 0 else 'Queue légère 🟢'}
                    </span>
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("⏳ Analyse des risques en cours...")

# ============================================
# DÉTAILS DE L'ANALYSE
# ============================================

with st.expander("🔍 Détails de l'analyse", expanded=False):
    st.markdown(f"""
    <div style='background: rgba(255,255,255,0.03); padding: 16px; border-radius: 12px;'>
        <p><strong>Action:</strong> {action_result.get('action', 'N/A')}</p>
        <p><strong>Score:</strong> {action_result.get('score', 0)}</p>
        <p><strong>Confiance:</strong> {action_result.get('confidence', 'N/A')}</p>
        <p><strong>Raisons:</strong></p>
    """, unsafe_allow_html=True)
    
    for reason in action_result.get('reasons', []):
        st.markdown(f"- {reason}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# TABLEAU DES INDICATEURS
# ============================================

with st.expander("📊 Tableau complet des indicateurs", expanded=False):
    data = {
        "Indicateur": ["Prix", "RSI", "MACD", "Signal MACD", "MA20", "MA50", "Tendance", "VaR 95%", "VaR 99%", "ES 95%", "ES 99%", "Hill ξ", "Volatilité"],
        "Valeur": [
            f"${current_price:,.2f}",
            f"{indicators.get('rsi', 'N/A')}",
            f"{macd.get('macd', 0):.4f}",
            f"{macd.get('signal', 0):.4f}",
            f"${ma.get('ma20', 0):,.2f}",
            f"${ma.get('ma50', 0):,.2f}",
            f"{ma.get('trend', 'N/A')}",
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

st.markdown(f"""
<div class='footer'>
    🔍 Mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} · 📊 Données: Binance / CoinGecko · ⚠️ Pas un conseil financier
</div>
""", unsafe_allow_html=True)
"Intégration CoinCap comme source principale"
