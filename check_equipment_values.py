from pymongo import MongoClient

def check_equipment_values():
    try:
        # Connexion à MongoDB
        client = MongoClient('mongodb://localhost:27017/')
        db = client['dem_dashboard']
        collection = db['equipment']
        
        # Vérifier si le champ purchase_value existe
        total_documents = collection.count_documents({})
        with_purchase_value = collection.count_documents({'purchase_value': {'$exists': True, '$ne': None, '$gt': 0}})
        
        print(f"Documents avec purchase_value > 0: {with_purchase_value} / {total_documents}")
        
        # Afficher quelques documents avec des valeurs d'achat
        print("\nExemples de documents avec purchase_value:")
        for doc in collection.find({'purchase_value': {'$exists': True, '$gt': 0}}).limit(3):
            print(f"ID: {doc.get('_id')}, Statut: {doc.get('status')}, Valeur: {doc.get('purchase_value')} ({type(doc.get('purchase_value'))})")
        
        # Vérifier les types de données pour purchase_value
        print("\nTypes de données pour purchase_value:")
        pipeline = [
            {
                '$match': {
                    'purchase_value': {'$exists': True, '$ne': None}
                }
            },
            {
                '$project': {
                    'type': {'$type': '$purchase_value'}
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
        
        # Vérifier les valeurs de statut existantes
        print("\nValeurs de statut uniques:")
        status_values = collection.distinct('status')
        for status in status_values:
            count = collection.count_documents({'status': status})
            print(f"Status: '{status}' ({type(status)}), Nombre: {count}")
        
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    check_equipment_values()
