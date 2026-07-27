"""
Application principale - Crypto Risk Platform
Combine collecte, indicateurs, modèles de risque et alertes
"""
import time
import schedule
from datetime import datetime
from loguru import logger

# Importer nos modules
from src.collector import collect_all
from src.indicators import calculate_all_indicators
from src.alert_system import AlertSystem
from src.risk_models import RiskModels

# Initialiser les systèmes
alert_system = AlertSystem()
risk_models = RiskModels()

def run_analysis():
    """
    Exécute une analyse complète avec les modèles de risque
    """
    logger.info("=" * 50)
    logger.info(f"🔍 Analyse en cours - {datetime.now().strftime('%H:%M:%S')}")
    logger.info("=" * 50)
    
    # 1. Collecter les prix
    logger.info("📊 Collecte des données...")
    data = collect_all()
    
    if not data:
        logger.error("❌ Aucune donnée collectée")
        return
    
    # 2. Pour chaque crypto
    for crypto, info in data.items():
        price = info['price']
        
        logger.info(f"💰 {crypto}: ${price:,.2f}")
        
        try:
            import yfinance as yf
            symbol = "BTC-USD" if crypto == "BTC" else "ETH-USD"
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2mo")
            
            if not hist.empty:
                prices = hist['Close'].tolist()
                
                # 3. Calculer les indicateurs techniques
                indicators = calculate_all_indicators(prices)
                
                # 4. Analyser les risques extrêmes (mémoire)
                risk_result = risk_models.analyze_risk(crypto, prices)
                
                # 5. Analyser et alerter (système de trading) AVEC les données de risque
                trade_result = alert_system.analyze_and_alert(
                    crypto=crypto,
                    prices=prices,
                    price=price,
                    risk_result=risk_result  # <-- ON PASSE LES RISQUES ICI
                )
                
                # 6. Afficher les résultats
                logger.info(f"📊 Action trading: {trade_result['action']['action']}")
                logger.info(f"📊 Score: {trade_result['action']['score']}")
                
                if risk_result:
                    logger.info(f"📊 VaR 95%: {risk_result['var_95']}%")
                    logger.info(f"📊 VaR 99%: {risk_result['var_99']}%")
                    if risk_result.get('var_95_alerte', False):
                        logger.warning(f"⚠️ Alerte VaR 95% dépassée!")
                    if risk_result.get('var_99_alerte', False):
                        logger.error(f"🚨 Alerte VaR 99% dépassée!")
                
            else:
                logger.warning(f"⚠️ Pas d'historique pour {crypto}")
                
        except Exception as e:
            logger.error(f"❌ Erreur pour {crypto}: {e}")
    
    logger.info("=" * 50)
    logger.info("✅ Analyse terminée")
    logger.info("=" * 50)
    print("\n")

def run_once():
    """
    Exécute une seule analyse (pour test)
    """
    logger.info("🚀 Lancement d'une analyse unique...")
    run_analysis()

def run_scheduled():
    """
    Lance l'application en mode planifié
    """
    logger.info("🚀 Lancement du mode planifié")
    logger.info("⏰ Analyse toutes les heures")
    
    # Exécuter une première analyse
    run_analysis()
    
    # Planifier les analyses
    schedule.every(1).hour.do(run_analysis)
    
    logger.info("✅ Système en cours d'exécution")
    logger.info("🔴 Appuyez sur Ctrl+C pour arrêter")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except KeyboardInterrupt:
            logger.info("\n👋 Arrêt du système")
            break
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            time.sleep(60)

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("🤖 CRYPTO RISK PLATFORM")
    print("📊 Analyse techniques + Risques extrêmes (VaR, ES, Hill)")
    print("=" * 60)
    print("1. Analyse unique (test)")
    print("2. Mode planifié (toutes les heures)")
    print("3. Test des modèles de risque")
    print("=" * 60)
    
    choix = input("Choisissez une option (1/2/3): ")
    
    if choix == "1":
        run_once()
    elif choix == "2":
        run_scheduled()
    elif choix == "3":
        # Test des modèles de risque avec données simulées
        import random
        import numpy as np
        test_prices = [50000 + np.cumsum(np.random.randn(100) * 100)]
        test_prices = test_prices[0].tolist()
        
        logger.info("📊 Test des modèles de risque...")
        for crypto in ['BTC', 'ETH']:
            result = risk_models.analyze_risk(crypto, test_prices)
            if result:
                print(f"\n📊 {crypto}:")
                print(f"   VaR 95%: {result['var_95']}%")
                print(f"   VaR 99%: {result['var_99']}%")
                print(f"   Hill ξ: {result['hill_xi']}")
                print(f"   Volatilité actuelle: {result['vol_actuelle']}%")
                print(f"   Volatilité théorique: {result['vol_theorique']}%")
    else:
        print("❌ Option invalide")