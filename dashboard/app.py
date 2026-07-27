"""
Dashboard Crypto Risk Platform
Interface web pour visualiser les indicateurs et les risques
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
# Configuration pour Render
import os
PORT = os.environ.get('PORT', 8501)
# Importer nos modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collector import get_price_yahoo
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
    /* Fond global */
    .stApp {{
        background-color: {COLORS['dark']};
    }}
    
    /* Cartes métriques */
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
    
    /* Titres */
    h1, h2, h3 {{
        color: {COLORS['text']} !important;
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background-color: {COLORS['card']};
    }}
    
    /* Métriques Streamlit */
    .stMetric {{
        background: {COLORS['card']};
        border-radius: 10px;
        padding: 10px;
    }}
    
    /* Footer */
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

# Liste des cryptomonnaies disponibles
CRYPTOS = {
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Solana (SOL)": "SOL-USD",
    "Ripple (XRP)": "XRP-USD",
    "Cardano (ADA)": "ADA-USD"
}

# ============================================
# SIDEBAR - CONFIGURATION
# ============================================

with st.sidebar:
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=50)
    st.markdown(f"<h2 style='color: {COLORS['primary']};'>⚙️ Configuration</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sélection de la crypto
    crypto_name = st.selectbox(
        "📈 Cryptomonnaie",
        list(CRYPTOS.keys()),
        index=0
    )
    symbol = CRYPTOS[crypto_name]
    crypto_short = crypto_name.split(" ")[0].upper()
    
    # Période d'analyse
    period = st.selectbox(
        "📅 Période d'historique",
        ["1mo", "3mo", "6mo", "1y", "2y"],
        index=1
    )
    
    st.markdown("---")
    
    # Bouton d'actualisation
    if st.button("🔄 Actualiser", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    
    # Informations
    st.markdown(f"""
    <div style='background: {COLORS['card']}; padding: 15px; border-radius: 10px;'>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>
            📊 <b>Données en temps réel</b><br>
            • Source: Yahoo Finance<br>
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

@st.cache_data(ttl=300)
def load_data(symbol, period):
    """Charge les données depuis Yahoo Finance"""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period)
    return hist

def get_current_price(symbol):
    """Récupère le prix actuel"""
    return get_price_yahoo(symbol)

# Charger les données
hist = load_data(symbol, period)

if hist.empty:
    st.error("❌ Impossible de charger les données")
    st.stop()

# Prix actuel
current_price = get_current_price(symbol)
if current_price is None:
    current_price = hist['Close'].iloc[-1]

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
        <p style='color: {'green' if hist['Close'].iloc[-1] > hist['Close'].iloc[-2] else 'red'};'>
            {((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100):.2f}%
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    rsi = indicators['rsi']
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
    action = action_result['action']
    emoji = "🟢" if "ACHETER" in action else "🔴" if "VENDRE" in action else "⚪"
    color = COLORS['success'] if "ACHETER" in action else COLORS['danger'] if "VENDRE" in action else COLORS['warning']
    st.markdown(f"""
    <div class='metric-card'>
        <p style='color: {COLORS['text_secondary']}; font-size: 14px;'>🎯 Signal</p>
        <p style='color: {color}; font-size: 22px; font-weight: bold;'>{action}</p>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>Score: {action_result['score']}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    var_99 = risk_result.get('var_99') if risk_result else None
    var_color = COLORS['danger'] if risk_result and risk_result.get('var_99_alerte', False) else COLORS['success']
    var_text = f"{var_99}%" if var_99 is not None else "N/A"
    st.markdown(f"""
    <div class='metric-card'>
        <p style='color: {COLORS['text_secondary']}; font-size: 14px;'>⚠️ VaR 99%</p>
        <p style='color: {var_color}; font-size: 24px; font-weight: bold;'>{var_text}</p>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>
            {'🔴 Risque élevé' if risk_result and risk_result.get('var_99_alerte', False) else '✅ Risque maîtrisé'}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col5:
    vol = risk_result.get('vol_actuelle') if risk_result else None
    vol_text = f"{vol}%" if vol is not None else "N/A"
    st.markdown(f"""
    <div class='metric-card'>
        <p style='color: {COLORS['text_secondary']}; font-size: 14px;'>🌊 Volatilité</p>
        <p style='color: {COLORS['text']}; font-size: 24px; font-weight: bold;'>{vol_text}</p>
        <p style='color: {COLORS['text_secondary']}; font-size: 12px;'>
            Théorique: {risk_result.get('vol_theorique', 'N/A')}%
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
        <p style='color: {COLORS['text_secondary']};'>RSI: <b style='color: {COLORS['text']};'>{indicators['rsi']:.1f}</b></p>
        <div style='background: #3D3D5C; height: 6px; border-radius: 3px;'>
            <div style='background: {COLORS['primary']}; width: {min(indicators['rsi'], 100)}%; height: 6px; border-radius: 3px;'></div>
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
        # VaR et ES dans une grille
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
        st.warning("Pas assez de données pour l'analyse des risques")

# ============================================
# DÉTAILS DE L'ANALYSE
# ============================================

st.markdown("---")
st.subheader("🔍 Détails de l'Analyse")

with st.expander("📋 Afficher les détails du signal"):
    st.markdown(f"""
    <div style='background: {COLORS['card']}; padding: 15px; border-radius: 10px;'>
        <p style='color: {COLORS['text']};'><b>Action:</b> {action_result['action']}</p>
        <p style='color: {COLORS['text']};'><b>Score:</b> {action_result['score']}</p>
        <p style='color: {COLORS['text']};'><b>Confiance:</b> {action_result['confidence']}</p>
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
            f"{indicators['rsi']:.1f}",
            f"{macd.get('macd', 0):.4f}",
            f"{macd.get('signal', 0):.4f}",
            f"${ma.get('ma20', 0):,.2f}",
            f"${ma.get('ma50', 0):,.2f}",
            f"{risk_result.get('var_95', 'N/A')}%" if risk_result else "N/A",
            f"{risk_result.get('var_99', 'N/A')}%" if risk_result else "N/A",
            f"{risk_result.get('es_95', 'N/A')}%" if risk_result else "N/A",
            f"{risk_result.get('es_99', 'N/A')}%" if risk_result else "N/A",
            f"{hill:.3f}" if hill is not None else "N/A",
            f"{risk_result.get('vol_actuelle', 'N/A')}%" if risk_result else "N/A"
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
    | Données: Yahoo Finance
    | ⚠️ Ceci n'est pas un conseil financier
</div>
""", unsafe_allow_html=True)