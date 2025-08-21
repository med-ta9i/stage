from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import json

def check_locations_data():
    try:
        # Connexion à MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        client.admin.command('ismaster')
        print("✓ Connexion à MongoDB réussie")
        
        # Vérifier la base de données
        db = client.get_database('dem_dashboard')
        print(f"Base de données : {db.name}")
        
        # Lister toutes les collections
        collections = db.list_collection_names()
        print(f"Collections disponibles : {collections}")
        
        # Vérifier la collection locations
        if 'locations' in collections:
            count = db.locations.count_documents({})
            print(f"✓ Collection 'locations' trouvée avec {count} documents")
            
            if count > 0:
                # Afficher un exemple de document
                print("\n=== Exemple de document ===")
                sample = db.locations.find_one()
                print(json.dumps(sample, indent=2, default=str))
                
                # Vérifier les champs principaux
                print("\n=== Statistiques des champs ===")
                print(f"Documents avec site_name: {db.locations.count_documents({'site_name': {'$exists': True, '$ne': ''}})}")
                print(f"Documents avec province: {db.locations.count_documents({'province': {'$exists': True, '$ne': ''}})}")
                print(f"Documents avec region: {db.locations.count_documents({'region': {'$exists': True, '$ne': ''}})}")
                
                # Vérifier les régions distinctes
                print("\n=== Régions distinctes ===")
                regions = db.locations.distinct('region')
                for region in regions[:10]:  # Afficher les 10 premières
                    print(f"- {region}")
                
                # Vérifier les services TNT et FM
                tnt_count = db.locations.count_documents({'services.tnt': True})
                fm_count = db.locations.count_documents({'services.fm': True})
                print(f"\n=== Services ===")
                print(f"Sites avec TNT: {tnt_count}")
                print(f"Sites avec FM: {fm_count}")
                
            else:
                print("⚠️ La collection 'locations' est vide")
        else:
            print("✗ La collection 'locations' n'existe pas")
            
        # Vérifier aussi la collection equipment pour comparaison
        if 'equipment' in collections:
            eq_count = db.equipment.count_documents({})
            print(f"\n=== Pour comparaison ===")
            print(f"Collection 'equipment' : {eq_count} documents")
            
    except ConnectionFailure as e:
        print(f"✗ Échec de la connexion à MongoDB: {e}")
    except Exception as e:
        print(f"✗ Erreur: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    check_locations_data()
