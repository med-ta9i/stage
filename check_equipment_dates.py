from pymongo import MongoClient
from datetime import datetime, timedelta

def check_equipment_dates():
    try:
        # Connexion à MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['dem_dashboard']
        collection = db['equipment']
        
        # Vérifier si le champ creation_date existe
        count_with_creation_date = collection.count_documents({'creation_date': {'$exists': True}})
        total_documents = collection.count_documents({})
        
        print(f"Documents avec creation_date: {count_with_creation_date} / {total_documents}")
        
        # Afficher quelques documents avec des dates
        print("\nExemples de documents avec creation_date:")
        for doc in collection.find({'creation_date': {'$exists': True}}).limit(3):
            print(f"ID: {doc.get('_id')}, Date: {doc.get('creation_date')}, Statut: {doc.get('status')}")
            
        # Vérifier les types de données pour creation_date
        print("\nTypes de données pour creation_date:")
        pipeline = [
            {
                '$match': {
                    'creation_date': {'$exists': True}
                }
            },
            {
                '$project': {
                    'type': {'$type': '$creation_date'}
                }
            },
            {
                '$group': {
                    '_id': '$type',
                    'count': {'$sum': 1}
                }
            }
        ]
        
        type_results = list(collection.aggregate(pipeline))
        for result in type_results:
            print(f"Type: {result['_id']}, Nombre: {result['count']}")
        
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    check_equipment_dates()
