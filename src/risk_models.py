"""
Modèles de risque extrême
Basé sur les résultats du mémoire (VaR, ES, Hill, GARCH-EVT)
"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from loguru import logger

class RiskModels:
    """
    Modèles de risque extrême pour les cryptomonnaies
    """
    
    def __init__(self):
        """
        Initialise les modèles avec les seuils du mémoire
        """
        # Seuils du mémoire (2025-2026)
        self.thresholds = {
            'BTC': {
                'var_95': -5.7,      # VaR 95% GPD
                'var_99': -8.4,      # VaR 99% GPD
                'es_95': -7.4,       # ES 95% GPD
                'es_99': -9.4,       # ES 99% GPD
                'hill_xi': 0.13,     # Indice de queue
                'garch_vol': 2.86,   # Volatilité GARCH (%)
            },
            'ETH': {
                'var_95': -9.8,      # VaR 95% GPD
                'var_99': -14.3,     # VaR 99% GPD
                'es_95': -12.5,      # ES 95% GPD
                'es_99': -16.0,      # ES 99% GPD
                'hill_xi': 0.14,     # Indice de queue
                'garch_vol': 3.65,   # Volatilité GARCH (%)
            }
        }
        
        logger.info("✅ Modèles de risque initialisés")
    
    def get_thresholds(self, crypto):
        """
        Récupère les seuils pour une crypto donnée
        """
        if crypto in self.thresholds:
            return self.thresholds[crypto]
        else:
            # Valeurs par défaut si crypto non reconnue
            return self.thresholds['BTC']
    
    def calculate_returns(self, prices):
        """
        Calcule les rendements logarithmiques
        """
        if len(prices) < 2:
            return np.array([])
        
        returns = np.diff(np.log(prices)) * 100
        return returns
    
    def calculate_var_gpd(self, returns, confidence=0.95, threshold=-0.05):
        """
        Calcule la VaR avec la méthode GPD (Peaks-Over-Threshold)
        
        Args:
            returns: Liste des rendements
            confidence: Niveau de confiance (0.95 ou 0.99)
            threshold: Seuil pour la GPD (défaut: -5%)
        
        Returns:
            float: VaR en pourcentage
        """
        if len(returns) < 50:
            return None
        
        # Sélectionner les pertes (rendements négatifs)
        losses = returns[returns < 0]
        
        if len(losses) == 0:
            return None
        
        # Dépassements au-delà du seuil
        exceedances = losses[losses < threshold]
        
        if len(exceedances) < 10:
            # Pas assez de dépassements, utiliser la méthode empirique
            var = np.percentile(returns, (1 - confidence) * 100)
            return round(var, 2)
        
        # Estimations simplifiées des paramètres GPD
        # Dans une version complète, on utiliserait le maximum de vraisemblance
        excesses = -(exceedances - threshold)  # Convertir en positifs
        mean_excess = np.mean(excesses)
        shape = -0.33  # Résultat du mémoire pour BTC
        scale = mean_excess * (1 + shape)
        
        # Calcul de la VaR
        n = len(returns)
        n_u = len(exceedances)
        zeta = n_u / n
        
        var = threshold + (scale / shape) * ((((1 - confidence) / zeta) ** (-shape)) - 1)
        
        return round(var, 2)
    
    def calculate_es_gpd(self, returns, confidence=0.95, threshold=-0.05):
        """
        Calcule l'Expected Shortfall avec la méthode GPD
        """
        var = self.calculate_var_gpd(returns, confidence, threshold)
        
        if var is None:
            return None
        
        # ES = VaR / (1 - shape) (approximation pour queue lourde)
        shape = -0.33
        es = var / (1 - shape)
        
        return round(es, 2)
    
    def calculate_hill(self, returns, k=50):
        """
        Calcule l'estimateur de Hill (indice de queue)
        
        Args:
            returns: Liste des rendements
            k: Nombre de statistiques d'ordre
        
        Returns:
            float: Indice de queue ξ
        """
        if len(returns) < k + 1:
            return None
        
        # Prendre les pertes (rendements négatifs)
        losses = -returns[returns < 0]  # Convertir en positifs
        
        if len(losses) < k:
            return None
        
        # Trier les pertes en ordre décroissant
        sorted_losses = np.sort(losses)[::-1]
        
        # Estimateur de Hill
        log_ratios = np.log(sorted_losses[:k] / sorted_losses[k-1])
        hill = np.mean(log_ratios)
        
        return round(hill, 3)
    
    def analyze_risk(self, crypto, prices):
        """
        Analyse complète des risques
        
        Args:
            crypto: 'BTC' ou 'ETH'
            prices: Liste des prix historiques
        
        Returns:
            dict: Toutes les mesures de risque
        """
        logger.info(f"📊 Analyse des risques pour {crypto}")
        
        # 1. Calculer les rendements
        returns = self.calculate_returns(prices)
        
        if len(returns) < 50:
            logger.warning(f"⚠️ Pas assez de données pour {crypto}")
            return None
        
        # 2. Récupérer les seuils du mémoire
        thresholds = self.get_thresholds(crypto)
        
        # 3. Calculer les mesures
        var_95 = self.calculate_var_gpd(returns, 0.95)
        var_99 = self.calculate_var_gpd(returns, 0.99)
        es_95 = self.calculate_es_gpd(returns, 0.95)
        es_99 = self.calculate_es_gpd(returns, 0.99)
        hill = self.calculate_hill(returns)
        
        # 4. Volatilité actuelle
        vol_actuelle = np.std(returns) if len(returns) > 0 else 0
        
        # 5. Comparer avec les seuils du mémoire
        var_95_alerte = var_95 < thresholds['var_95']
        var_99_alerte = var_99 < thresholds['var_99']
        
        return {
            'crypto': crypto,
            'var_95': var_95,
            'var_99': var_99,
            'es_95': es_95,
            'es_99': es_99,
            'hill_xi': hill,
            'vol_actuelle': round(vol_actuelle, 2),
            'vol_theorique': thresholds['garch_vol'],
            'var_95_alerte': var_95_alerte,
            'var_99_alerte': var_99_alerte,
            'var_95_seuil': thresholds['var_95'],
            'var_99_seuil': thresholds['var_99'],
        }
    
    def get_risk_alert(self, crypto, prices):
        """
        Génère une alerte de risque si nécessaire
        """
        risk = self.analyze_risk(crypto, prices)
        
        if risk is None:
            return None
        
        alerts = []
        
        # 1. Alerte VaR 95%
        if risk['var_95_alerte']:
            alerts.append({
                'type': 'VAR_95',
                'severity': 'WARNING',
                'message': f"VaR 95% dépassée pour {crypto}",
                'actual': risk['var_95'],
                'threshold': risk['var_95_seuil']
            })
        
        # 2. Alerte VaR 99%
        if risk['var_99_alerte']:
            alerts.append({
                'type': 'VAR_99',
                'severity': 'CRITICAL',
                'message': f"VaR 99% dépassée pour {crypto}",
                'actual': risk['var_99'],
                'threshold': risk['var_99_seuil']
            })
        
        # 3. Alerte volatilité
        if risk['vol_actuelle'] > risk['vol_theorique'] * 1.5:
            alerts.append({
                'type': 'VOLATILITY',
                'severity': 'WARNING',
                'message': f"Volatilité anormalement élevée pour {crypto}",
                'actual': risk['vol_actuelle'],
                'threshold': risk['vol_theorique']
            })
        
        return {
            'risk': risk,
            'alerts': alerts
        }


# Test du module
if __name__ == "__main__":
    import random
    
    # Simuler des prix
    test_prices = [50000 + np.cumsum(np.random.randn(100) * 100)]
    test_prices = test_prices[0].tolist()
    
    print("🔧 Test des modèles de risque")
    print("-" * 40)
    
    risk_models = RiskModels()
    
    for crypto in ['BTC', 'ETH']:
        print(f"\n📊 Analyse de {crypto}")
        result = risk_models.analyze_risk(crypto, test_prices)
        if result:
            print(f"   VaR 95%: {result['var_95']}%")
            print(f"   VaR 99%: {result['var_99']}%")
            print(f"   Hill ξ: {result['hill_xi']}")
            print(f"   Alerte VaR 95%: {result['var_95_alerte']}")
            print(f"   Alerte VaR 99%: {result['var_99_alerte']}")