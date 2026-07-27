"""
Système d'alertes et de décision pour le trading
"""
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from collections import deque
from loguru import logger
import sys
import os

# Ajouter le dossier parent au chemin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer nos modules
try:
    from src.config import EMAIL_USERNAME, EMAIL_PASSWORD
    from src.indicators import calculate_all_indicators
except ImportError:
    from config import EMAIL_USERNAME, EMAIL_PASSWORD
    from indicators import calculate_all_indicators


class AlertSystem:
    def __init__(self, config=None):
        """
        Initialise le système d'alertes
        """
        self.email_from = EMAIL_USERNAME
        self.email_to = EMAIL_USERNAME
        self.last_alerts = deque(maxlen=20)  # Garder les 20 derniers
        
        # Configuration des seuils
        self.thresholds = {
            'rsi_low': 30,        # RSI survendu
            'rsi_high': 70,       # RSI suracheté
            'var_95': -5.7,       # VaR 95% Bitcoin
            'var_99': -8.4,       # VaR 99% Bitcoin
            'var_99_eth': -14.3,  # VaR 99% Ethereum
        }
        
        logger.info("✅ Système d'alertes initialisé")
    
    def determine_action(self, indicators, risk_metrics=None):
        """
        Détermine l'action recommandée (ACHETER, VENDRE, ATTENDRE)
        """
        score = 0
        reasons = []
        
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', {})
        ma = indicators.get('moving_averages', {})
        
        # 1. RSI (poids 2)
        if rsi < self.thresholds['rsi_low']:
            score += 2
            reasons.append("✅ RSI survendu - opportunité d'achat")
        elif rsi > self.thresholds['rsi_high']:
            score -= 2
            reasons.append("🔴 RSI suracheté - risque de baisse")
        else:
            reasons.append("⚪ RSI neutre")
        
        # 2. MACD (poids 2)
        if macd.get('histogram', 0) > 0:
            score += 2
            reasons.append("✅ MACD haussier")
        else:
            score -= 2
            reasons.append("🔴 MACD baissier")
        
        # 3. Tendance (poids 2)
        if ma.get('trend') == "HAUSSIÈRE":
            score += 2
            reasons.append("✅ Tendance haussière")
        else:
            score -= 2
            reasons.append("🔴 Tendance baissière")
        
        # 4. Intégration des risques extrêmes (si disponibles)
        if risk_metrics:
            # VaR 99% (poids 2)
            var_99 = risk_metrics.get('var_99')
            var_99_seuil = risk_metrics.get('var_99_seuil')
            if var_99 is not None and var_99_seuil is not None:
                if var_99 < var_99_seuil:  # Risque élevé
                    score -= 2
                    reasons.append(f"🔴 VaR 99% dépassée ({var_99}% > {var_99_seuil}%)")
                elif var_99 < var_99_seuil * 0.7:  # Risque faible
                    score += 1
                    reasons.append(f"✅ VaR 99% sous le seuil ({var_99}%)")
            
            # Alerte VaR 95%
            var_95 = risk_metrics.get('var_95')
            var_95_seuil = risk_metrics.get('var_95_seuil')
            if var_95 is not None and var_95_seuil is not None:
                if var_95 < var_95_seuil:
                    score -= 1
                    reasons.append(f"⚠️ VaR 95% dépassée ({var_95}%)")
        
        # Décision finale
        if score >= 4:
            action = "🟢 ACHETER"
            confidence = "FORTE"
            logger.info(f"Signal ACHAT - Score: {score}")
        elif score >= 2:
            action = "🟡 ACHETER LÉGER"
            confidence = "MODÉRÉE"
            logger.info(f"Signal ACHAT LÉGER - Score: {score}")
        elif score <= -4:
            action = "🔴 VENDRE"
            confidence = "FORTE"
            logger.info(f"Signal VENTE - Score: {score}")
        elif score <= -2:
            action = "🟠 VENDRE LÉGER"
            confidence = "MODÉRÉE"
            logger.info(f"Signal VENTE LÉGER - Score: {score}")
        else:
            action = "⚪ ATTENDRE"
            confidence = "FAIBLE"
            logger.info(f"Signal ATTENDRE - Score: {score}")
        
        return {
            'action': action,
            'score': score,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def send_alert(self, crypto, price, action_result, indicators, risk_result=None):
        """
        Envoie une alerte par email avec les informations de risque
        """
        # Vérifier si on a déjà envoyé un signal similaire récemment
        for alert in self.last_alerts:
            if alert['action'] == action_result['action']:
                time_since = (datetime.now() - alert['timestamp']).seconds
                if time_since < 3600:  # 1 heure
                    logger.info("⏳ Signal déjà envoyé il y a moins d'1h")
                    return False
        
        # Construire le sujet
        subject = f"{action_result['action']} - {crypto} ${price:,.2f}"
        
        # Construire les raisons
        reasons_text = "\n".join([f"  • {r}" for r in action_result['reasons']])
        
        # Ajouter les informations de risque
        risk_text = ""
        if risk_result:
            risk_text = f"""
📊 RISQUE EXTRÊME (VaR/ES):
  • VaR 95%: {risk_result.get('var_95', 'N/A')}%
  • VaR 99%: {risk_result.get('var_99', 'N/A')}%
  • ES 95%: {risk_result.get('es_95', 'N/A')}%
  • ES 99%: {risk_result.get('es_99', 'N/A')}%
  • Hill ξ: {risk_result.get('hill_xi', 'N/A')}
  • Volatilité actuelle: {risk_result.get('vol_actuelle', 'N/A')}%
  • Volatilité théorique: {risk_result.get('vol_theorique', 'N/A')}%
  • Seuil VaR 99%: {risk_result.get('var_99_seuil', 'N/A')}%
"""
            
            if risk_result.get('var_99_alerte', False):
                risk_text += "\n  🔴 ALERTE CRITIQUE: VaR 99% dépassée !"
            elif risk_result.get('var_95_alerte', False):
                risk_text += "\n  🟠 ALERTE: VaR 95% dépassée !"
        
        # Construire le message complet
        message = f"""
{action_result['action']} - CONFIANCE {action_result['confidence']}

💰 {crypto}: ${price:,.2f}

📊 INDICATEURS:
  • RSI: {indicators['rsi']}
  • MACD: {indicators['macd']['macd']}
  • Signal MACD: {indicators['macd']['signal']}
  • Histogramme MACD: {indicators['macd']['histogram']}
  • MA20: ${indicators['moving_averages']['ma20']:,.2f}
  • MA50: ${indicators['moving_averages']['ma50']:,.2f}
  • Tendance: {indicators['moving_averages']['trend']}

🔍 ANALYSE:
{reasons_text}

🎯 SCORE: {action_result['score']}
{risk_text}
⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

⚠️ Ceci est une alerte automatique. La décision finale vous appartient.
        """
        
        try:
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_from, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            # Enregistrer l'alerte
            self.last_alerts.append({
                'timestamp': datetime.now(),
                'action': action_result['action'],
                'crypto': crypto,
                'price': price
            })
            
            logger.info(f"📧 Email envoyé: {action_result['action']} {crypto}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur email: {e}")
            return False
    
    def analyze_and_alert(self, crypto, prices, price, risk_result=None):
        """
        Analyse complète et envoie une alerte si nécessaire
        """
        logger.info(f"🔍 Analyse de {crypto}...")
        
        # 1. Calculer les indicateurs
        indicators = calculate_all_indicators(prices)
        
        # 2. Déterminer l'action
        action_result = self.determine_action(indicators, risk_result)
        
        # 3. Envoyer l'alerte si l'action est ACHETER ou VENDRE
        if "ACHETER" in action_result['action'] or "VENDRE" in action_result['action']:
            logger.info(f"🚨 Signal détecté: {action_result['action']}")
            self.send_alert(crypto, price, action_result, indicators, risk_result)
        else:
            logger.info("⚪ Pas de signal d'achat/vente")
        
        return {
            'crypto': crypto,
            'price': price,
            'indicators': indicators,
            'action': action_result
        }


# Test du système
if __name__ == "__main__":
    import random
    
    # Simuler des prix pour le test
    test_prices = [50000 + random.randint(-500, 500) for _ in range(100)]
    
    print("🔧 Test du système d'alertes")
    print("-" * 40)
    
    # Créer le système
    alert_system = AlertSystem()
    
    # Simuler des données de risque
    risk_data = {
        'var_95': -5.2,
        'var_99': -7.8,
        'es_95': -6.3,
        'es_99': -8.9,
        'hill_xi': 0.13,
        'vol_actuelle': 2.86,
        'vol_theorique': 2.86,
        'var_95_alerte': False,
        'var_99_alerte': False,
        'var_99_seuil': -8.4,
        'var_95_seuil': -5.7
    }
    
    # Tester l'analyse
    result = alert_system.analyze_and_alert(
        crypto="BTC",
        prices=test_prices,
        price=test_prices[-1],
        risk_result=risk_data
    )
    
    print(f"\n📊 Résultat:")
    print(f"   Action: {result['action']['action']}")
    print(f"   Score: {result['action']['score']}")
    print(f"   Confiance: {result['action']['confidence']}")