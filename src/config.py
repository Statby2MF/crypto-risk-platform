"""
Configuration du projet
Charge les variables d'environnement depuis le fichier .env
"""
import os
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Email
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Cryptomonnaies par défaut
DEFAULT_CRYPTOS = ["BTC", "ETH"]

# Vérification que les variables sont chargées
def check_config():
    """Vérifie que la configuration est complète"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase non configuré")
    else:
        print("✅ Supabase configuré")
    
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        print("⚠️ Email non configuré")
    else:
        print("✅ Email configuré")

if __name__ == "__main__":
    check_config()