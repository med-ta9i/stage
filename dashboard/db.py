import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Configuration MongoDB
MONGODB_CONFIG = {
    'default': {
        'name': os.getenv('DB_NAME', 'dem_dashboard'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 27017)),
        'tz_aware': True,
    }
}

def get_mongodb_connection(connection_alias='default'):
    """
    Crée et retourne une connexion à la base de données MongoDB.
    
    Args:
        connection_alias (str): Alias de la connexion à utiliser (par défaut: 'default')
        
    Returns:
        pymongo.database.Database: Instance de la base de données MongoDB
    """
    try:
        # Récupérer la configuration MongoDB
        db_config = MONGODB_CONFIG.get(connection_alias, MONGODB_CONFIG['default'])
        
        # Créer une connexion au serveur MongoDB
        client = MongoClient(
            host=db_config['host'],
            port=db_config['port'],
            tz_aware=db_config.get('tz_aware', True),
            serverSelectionTimeoutMS=5000  # Timeout de 5 secondes
        )
        
        # Tester la connexion
        client.admin.command('ping')
        
        # Retourner la base de données spécifiée
        return client[db_config['name']]
        
    except ConnectionFailure as e:
        print(f"Échec de la connexion à MongoDB: {e}")
        raise
    except Exception as e:
        print(f"Erreur inattendue lors de la connexion à MongoDB: {e}")
        raise
