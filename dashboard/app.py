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

st.markdown(f"""
<style>
    .stApp {{
        background-color: {COLORS['dark']};
    }}
    .metric-card {{
        background: {COLORS['card']};
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #3D3D5C;
        margin: 5px 0;
    }}
    .metric-card:hover {{
        border-color: {COLORS['primary']};
        transition: 0.3s;
    }}
    h1, h2, h3 {{
        color: {COLORS['text']} !important;
    }}
    .stMetric {{
        background: {COLORS['card']};
        border-radius: 10px;
        padding: 10px;
    }}
    .footer {{
        text-align: center;
        color: {COLORS['text_secondary']};
        font-size: 12px;
        padding: 20px;
        border-top: 1px solid #3D3D5C;
        margin-top: 30px;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALISATION
# ============================================

risk_models = RiskModels()
alert_system = AlertSystem()

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
    """
    Récupère le prix depuis Binance
    """
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print(f"❌ Binance error: {e}")
        return None

def get_price_coingecko(coin_id):
    """
    Récupère le prix depuis CoinGecko
    """
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data[coin_id]['usd'])
    except Exception as e:
        print(f"❌ CoinGecko error: {e}")
        return None

def get_price_with_fallback(crypto_key):
    """
    Récupère le prix avec fallback: Binance → CoinGecko
    """
    crypto_info = CRYPTO_MAP.get(crypto_key)
    if not crypto_info:
        return None
    
    # 1. Essayer Binance
    price = get_price_binance(crypto_info["binance"])
    if price:
        return price
    
    # 2. Fallback sur CoinGecko
    price = get_price_coingecko(crypto_info["coingecko"])
    if price:
        return price
    
    return None

def get_historical_data(symbol, period="3mo"):
    """
    Récupère les données historiques depuis Yahoo Finance
    """
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
    st.markdown(f"<h2 style='color: {COLORS['primary']};'>⚙️ Configuration</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Sélection de la crypto
    crypto_key = st.selectbox(
        "📈 Cryptomonnaie",
        list(CRYPTO_MAP.keys()),
        index=0
    )
    crypto_info = CRYPTO_MAP[crypto_key]
    crypto_short = crypto_info["symbol"]
    
    # Période d'analyse
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
    
    st.markdown(f"""
    <div style='background: {COLORS['card']}; padding: 15px; border-radius: 10px;'>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>
            📊 <b>Données en temps réel</b><br>
            • Source: Binance / CoinGecko<br>
            • Mise à jour: À la demande
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <p style='color: #666; font-size: 11px; text-align: center;'>
        ⚠️ Ceci n'est pas un conseil financier
    </p>
    """, unsafe_allow_html=True)

# ============================================
# CHARGEMENT DES DONNÉES
# ============================================

# Prix actuel
current_price = get_price_with_fallback(crypto_key)

if current_price is None:
    st.error(f"❌ Impossible de récupérer le prix pour {crypto_key}")
    st.stop()

# Données historiques (pour les indicateurs)
hist = get_historical_data(crypto_info["symbol"], period)

if hist.empty:
    st.warning("⚠️ Données historiques limitées, utilisation de données simulées")
    # Créer des données simulées si Yahoo ne fonctionne pas
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    base_price = current_price
    prices = [base_price * (1 + np.random.randn() * 0.02) for _ in range(100)]
    prices = np.cumsum(prices) / 100 * base_price / 10 + base_price * 0.9
    hist = pd.DataFrame({
        'Close': prices,
        'Open': prices,
        'High': prices * 1.01,
        'Low': prices * 0.99
    }, index=dates)
    hist = hist.iloc[-50:]

prices = hist['Close'].tolist()
dates = hist.index.tolist()

# Calculer les indicateurs
indicators = calculate_all_indicators(prices)
risk_result = risk_models.analyze_risk(crypto_short, prices)

# Déterminer l'action
action_result = alert_system.determine_action(indicators, risk_result)

# ============================================
# EN-TÊTE
# ============================================

st.markdown(f"""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='color: {COLORS['primary']}; font-size: 3em;'>📊 Crypto Risk Platform</h1>
    <p style='color: {COLORS['text_secondary']}; font-size: 1.1em;'>
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
        <p style='color: {COLORS['text_secondary']}; font-size: 14px;'>💰 {crypto_short}</p>
        <p style='color: {COLORS['text']}; font-size: 28px; font-weight: bold;'>${current_price:,.2f}</p>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>
            {datetime.now().strftime('%H:%M:%S')}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    rsi = indicators.get('rsi', 50)
    rsi_color = "green" if rsi < 30 else "red" if rsi > 70 else "orange"
    st.markdown(f"""
    <div class='metric-card'>
        <p style='color: {COLORS['text_secondary']}; font-size: 14px;'>📊 RSI</p>
        <p style='color: {rsi_color}; font-size: 28px; font-weight: bold;'>{rsi:.1f}</p>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>
            {'Survendu 📉' if rsi < 30 else 'Suracheté 📈' if rsi > 70 else 'Neutre ⚪'}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    action = action_result.get('action', 'N/A')
    color = COLORS['success'] if "ACHETER" in action else COLORS['danger'] if "VENDRE" in action else COLORS['warning']
    st.markdown(f"""
    <div class='metric-card'>
        <p style='color: {COLORS['text_secondary']}; font-size: 14px;'>🎯 Signal</p>
        <p style='color: {color}; font-size: 22px; font-weight: bold;'>{action}</p>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>Score: {action_result.get('score', 0)}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    if risk_result:
        var_99 = risk_result.get('var_99')
        var_color = COLORS['danger'] if risk_result.get('var_99_alerte', False) else COLORS['success']
        var_text = f"{var_99}%" if var_99 is not None else "N/A"
    else:
        var_color = COLORS['warning']
        var_text = "N/A"
    st.markdown(f"""
    <div class='metric-card'>
        <p style='color: {COLORS['text_secondary']}; font-size: 14px;'>⚠️ VaR 99%</p>
        <p style='color: {var_color}; font-size: 24px; font-weight: bold;'>{var_text}</p>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>
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
        <p style='color: {COLORS['text_secondary']}; font-size: 14px;'>🌊 Volatilité</p>
        <p style='color: {COLORS['text']}; font-size: 24px; font-weight: bold;'>{vol_text}</p>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>
            Théorique: {vol_theorique}%
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# GRAPHIQUE DES PRIX
# ============================================

st.markdown("---")
st.subheader("📈 Évolution des Prix")

fig = go.Figure()

# Prix
fig.add_trace(go.Scatter(
    x=dates,
    y=prices,
    mode='lines',
    name=crypto_short,
    line=dict(color=COLORS['primary'], width=2),
    fill='tozeroy',
    fillcolor='rgba(108, 99, 255, 0.1)'
))

# Bandes de Bollinger
if indicators.get('bollinger'):
    bollinger = indicators['bollinger']
    fig.add_trace(go.Scatter(
        x=dates[-20:],
        y=[bollinger['upper']] * len(dates[-20:]),
        mode='lines',
        name='Bande haute',
        line=dict(color=COLORS['danger'], width=1, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=dates[-20:],
        y=[bollinger['middle']] * len(dates[-20:]),
        mode='lines',
        name='MA20',
        line=dict(color=COLORS['warning'], width=1, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=dates[-20:],
        y=[bollinger['lower']] * len(dates[-20:]),
        mode='lines',
        name='Bande basse',
        line=dict(color=COLORS['success'], width=1, dash='dash')
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
    
    # RSI
    st.markdown(f"""
    <div style='background: {COLORS['card']}; padding: 15px; border-radius: 10px; margin: 5px 0;'>
        <p style='color: {COLORS['text_secondary']};'>RSI: <b style='color: {COLORS['text']};'>{indicators.get('rsi', 'N/A')}</b></p>
        <div style='background: #3D3D5C; height: 6px; border-radius: 3px;'>
            <div style='background: {COLORS['primary']}; width: {min(indicators.get('rsi', 50), 100)}%; height: 6px; border-radius: 3px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # MACD
    macd = indicators.get('macd', {})
    st.markdown(f"""
    <div style='background: {COLORS['card']}; padding: 15px; border-radius: 10px; margin: 5px 0;'>
        <p style='color: {COLORS['text_secondary']};'>
            MACD: <b style='color: {COLORS['text']};'>{macd.get('macd', 0):.4f}</b>
            | Signal: <b style='color: {COLORS['text']};'>{macd.get('signal', 0):.4f}</b>
            | Hist: <b style='color: {'green' if macd.get('histogram', 0) > 0 else 'red'};'>{macd.get('histogram', 0):.4f}</b>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Moyennes mobiles
    ma = indicators.get('moving_averages', {})
    st.markdown(f"""
    <div style='background: {COLORS['card']}; padding: 15px; border-radius: 10px; margin: 5px 0;'>
        <p style='color: {COLORS['text_secondary']};'>
            MA20: <b style='color: {COLORS['text']};'>${ma.get('ma20', 0):,.2f}</b>
            | MA50: <b style='color: {COLORS['text']};'>${ma.get('ma50', 0):,.2f}</b>
        </p>
        <p style='color: {'green' if ma.get('trend') == 'HAUSSIÈRE' else 'red'};'>
            Tendance: {ma.get('trend', 'N/A')}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("---")
    st.subheader("⚠️ Analyse des Risques Extrêmes")
    
    if risk_result:
        risk_col1, risk_col2 = st.columns(2)
        
        with risk_col1:
            st.markdown(f"""
            <div style='background: {COLORS['card']}; padding: 12px; border-radius: 10px; margin: 3px 0;'>
                <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>VaR 95%</p>
                <p style='color: {COLORS['text']}; font-size: 20px; font-weight: bold;'>{risk_result.get('var_95', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: {COLORS['card']}; padding: 12px; border-radius: 10px; margin: 3px 0;'>
                <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>ES 95%</p>
                <p style='color: {COLORS['text']}; font-size: 20px; font-weight: bold;'>{risk_result.get('es_95', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with risk_col2:
            var_color = COLORS['danger'] if risk_result.get('var_99_alerte', False) else COLORS['success']
            st.markdown(f"""
            <div style='background: {COLORS['card']}; padding: 12px; border-radius: 10px; margin: 3px 0;'>
                <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>VaR 99%</p>
                <p style='color: {var_color}; font-size: 20px; font-weight: bold;'>{risk_result.get('var_99', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background: {COLORS['card']}; padding: 12px; border-radius: 10px; margin: 3px 0;'>
                <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>ES 99%</p>
                <p style='color: {COLORS['text']}; font-size: 20px; font-weight: bold;'>{risk_result.get('es_99', 'N/A')}%</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Hill
        hill = risk_result.get('hill_xi')
        hill_text = f"{hill:.3f}" if hill is not None else "N/A"
        hill_color = COLORS['warning'] if hill is not None and hill > 0 else COLORS['success']
        st.markdown(f"""
        <div style='background: {COLORS['card']}; padding: 12px; border-radius: 10px; margin: 3px 0;'>
            <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>Hill ξ (indice de queue)</p>
            <p style='color: {hill_color}; font-size: 20px; font-weight: bold;'>{hill_text}</p>
            <p style='color: {COLORS['text_secondary']}; font-size: 11px;'>
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
    <div style='background: {COLORS['card']}; padding: 15px; border-radius: 10px;'>
        <p style='color: {COLORS['text']};'><b>Action:</b> {action_result.get('action', 'N/A')}</p>
        <p style='color: {COLORS['text']};'><b>Score:</b> {action_result.get('score', 0)}</p>
        <p style='color: {COLORS['text']};'><b>Confiance:</b> {action_result.get('confidence', 'N/A')}</p>
        <p style='color: {COLORS['text_secondary']};'><b>Raisons:</b></p>
    """, unsafe_allow_html=True)
    
    for reason in action_result.get('reasons', []):
        st.write(f"- {reason}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# TABLEAU DES INDICATEURS
# ============================================

with st.expander("📊 Tableau des indicateurs"):
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
            f"{hill:.3f}" if hill is not None else "N/A",
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
    | Données: Binance / CoinGecko / Yahoo
    | ⚠️ Ceci n'est pas un conseil financier
</div>
""", unsafe_allow_html=True)
"Fix NoneType error and improve risk display"
