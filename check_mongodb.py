from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def check_mongodb_connection():
    try:
        # Essayer de se connecter à MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        
        # Vérifier la connexion
        client.admin.command('ismaster')
        print("✓ Connexion à MongoDB réussie")
        
        # Vérifier la base de données et la collection
        db = client.get_database('dem_dashboard')
        print(f"Base de données 'dem_dashboard' : {db.name}")
        
        # Vérifier la collection equipment
        if 'equipment' in db.list_collection_names():
            count = db.equipment.count_documents({})
            print(f"✓ Collection 'equipment' trouvée avec {count} documents")
            
            # Afficher un exemple de document
            if count > 0:
                print("\nExemple de document :")
                print(db.equipment.find_one())
                
                # Vérifier les statuts existants
                print("\nStatuts existants :")
                statuses = db.equipment.distinct('status')
                print(statuses)
            else:
                print("La collection 'equipment' est vide")
        else:
            print("✗ La collection 'equipment' n'existe pas")
            
    except ConnectionFailure as e:
        print(f"✗ Échec de la connexion à MongoDB: {e}")
    except Exception as e:
        print(f"✗ Erreur: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    check_mongodb_connection()
