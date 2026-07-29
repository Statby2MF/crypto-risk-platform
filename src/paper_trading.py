"""
Système de trading démo (Paper Trading)
Simule des achats/ventes de cryptomonnaies avec capital virtuel
"""
from datetime import datetime
import json
from loguru import logger

class PaperTrading:
    def __init__(self, initial_capital=10000):
        """
        Initialise le compte de trading démo
        
        Args:
            initial_capital: Capital initial en USD (défaut: 10 000)
        """
        self.initial_capital = initial_capital
        self.balance = initial_capital
        self.positions = {}  # crypto -> quantité
        self.trades = []
        self.current_prices = {}
        
        logger.info(f"💰 Compte démo initialisé avec ${initial_capital:,.2f}")
    
    def buy(self, crypto, price, amount=None, quantity=None):
        """
        Acheter une crypto
        
        Args:
            crypto: Nom de la crypto (ex: "BTC")
            price: Prix unitaire
            amount: Montant en USD à investir
            quantity: Quantité à acheter
        
        Returns:
            bool: True si l'achat est réussi
        """
        # Déterminer la quantité
        if amount and not quantity:
            quantity = amount / price
        elif not amount and not quantity:
            logger.error("❌ Spécifiez amount ou quantity")
            return False
        
        total_cost = quantity * price
        
        # Vérifier les fonds
        if total_cost > self.balance:
            logger.error(f"❌ Fonds insuffisants: ${total_cost:,.2f} > ${self.balance:,.2f}")
            return False
        
        # Enregistrer la position
        if crypto in self.positions:
            self.positions[crypto] += quantity
        else:
            self.positions[crypto] = quantity
        
        self.balance -= total_cost
        self.current_prices[crypto] = price
        
        # Enregistrer le trade
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": "BUY",
            "crypto": crypto,
            "price": price,
            "quantity": quantity,
            "total": total_cost,
            "balance_after": self.balance
        }
        self.trades.append(trade)
        
        logger.info(f"✅ ACHAT {quantity:.6f} {crypto} à ${price:,.2f} (${total_cost:,.2f})")
        return True
    
    def sell(self, crypto, price, quantity=None):
        """
        Vendre une crypto
        
        Args:
            crypto: Nom de la crypto (ex: "BTC")
            price: Prix unitaire
            quantity: Quantité à vendre (si None, vend tout)
        
        Returns:
            bool: True si la vente est réussie
        """
        # Vérifier la position
        if crypto not in self.positions or self.positions[crypto] == 0:
            logger.error(f"❌ Pas de position pour {crypto}")
            return False
        
        # Si quantité non spécifiée, vendre tout
        if quantity is None:
            quantity = self.positions[crypto]
        elif quantity > self.positions[crypto]:
            quantity = self.positions[crypto]
            logger.warning(f"⚠️ Quantité ajustée à {quantity:.6f}")
        
        total_value = quantity * price
        
        # Mettre à jour la position
        self.positions[crypto] -= quantity
        self.balance += total_value
        self.current_prices[crypto] = price
        
        # Calculer la plus-value
        # Trouver le prix d'achat moyen
        buy_trades = [t for t in self.trades if t['type'] == 'BUY' and t['crypto'] == crypto]
        if buy_trades:
            avg_buy_price = sum(t['price'] * t['quantity'] for t in buy_trades) / sum(t['quantity'] for t in buy_trades)
            profit_pct = ((price - avg_buy_price) / avg_buy_price) * 100
        else:
            profit_pct = 0
        
        # Enregistrer le trade
        trade = {
            "timestamp": datetime.now().isoformat(),
            "type": "SELL",
            "crypto": crypto,
            "price": price,
            "quantity": quantity,
            "total": total_value,
            "balance_after": self.balance,
            "profit_pct": round(profit_pct, 2)
        }
        self.trades.append(trade)
        
        logger.info(f"✅ VENTE {quantity:.6f} {crypto} à ${price:,.2f} (${total_value:,.2f})")
        return True
    
    def get_portfolio_value(self, prices):
        """
        Calculer la valeur totale du portefeuille
        
        Args:
            prices: Dict des prix actuels {crypto: price}
        
        Returns:
            float: Valeur totale du portefeuille
        """
        total = self.balance
        for crypto, quantity in self.positions.items():
            if crypto in prices:
                total += quantity * prices[crypto]
                self.current_prices[crypto] = prices[crypto]
        return total
    
    def get_summary(self, prices):
        """
        Résumé du compte
        
        Args:
            prices: Dict des prix actuels {crypto: price}
        
        Returns:
            dict: Résumé complet
        """
        portfolio_value = self.get_portfolio_value(prices)
        profit = portfolio_value - self.initial_capital
        profit_pct = (profit / self.initial_capital) * 100
        
        # Positions détaillées
        positions_detail = []
        for crypto, quantity in self.positions.items():
            if quantity > 0 and crypto in prices:
                value = quantity * prices[crypto]
                positions_detail.append({
                    "crypto": crypto,
                    "quantity": quantity,
                    "price": prices[crypto],
                    "value": value
                })
        
        # Statistiques des trades
        buy_trades = [t for t in self.trades if t['type'] == 'BUY']
        sell_trades = [t for t in self.trades if t['type'] == 'SELL']
        
        return {
            "balance": self.balance,
            "portfolio_value": portfolio_value,
            "profit": profit,
            "profit_pct": profit_pct,
            "total_trades": len(self.trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "positions": positions_detail,
            "trades": self.trades[-20:]  # Derniers 20 trades
        }
    
    def reset(self):
        """
        Réinitialiser le compte
        """
        self.balance = self.initial_capital
        self.positions = {}
        self.trades = []
        self.current_prices = {}
        logger.info(f"🔄 Compte réinitialisé à ${self.initial_capital:,.2f}")
    
    def get_portfolio_summary(self, prices):
        """
        Afficher un résumé simple du portefeuille
        """
        summary = self.get_summary(prices)
        
        print("=" * 50)
        print("💰 PORTEFEUILLE DÉMO")
        print("=" * 50)
        print(f"Solde: ${summary['balance']:,.2f}")
        print(f"Valeur totale: ${summary['portfolio_value']:,.2f}")
        print(f"P&L: ${summary['profit']:,.2f} ({summary['profit_pct']:.2f}%)")
        print("-" * 50)
        print("POSITIONS:")
        for pos in summary['positions']:
            print(f"  {pos['crypto']}: {pos['quantity']:.6f} @ ${pos['price']:,.2f} = ${pos['value']:,.2f}")
        print("=" * 50)
        
        return summary


# Test du module
if __name__ == "__main__":
    # Créer un compte
    trader = PaperTrading(10000)
    
    # Simuler des trades
    prices = {"BTC": 50000, "ETH": 3000}
    
    # Acheter
    trader.buy("BTC", prices["BTC"], amount=5000)
    trader.buy("ETH", prices["ETH"], amount=2000)
    
    # Afficher le résumé
    trader.get_portfolio_summary(prices)
    
    # Vendre une partie
    trader.sell("BTC", prices["BTC"] * 1.05, quantity=0.05)
    
    # Afficher le résumé final
    trader.get_portfolio_summary({"BTC": 52500, "ETH": 3100})
