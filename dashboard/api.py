from bson import ObjectId
from datetime import datetime
from .db import get_mongodb_connection

def get_equipments(filters=None, page=1, page_size=20, sort_field=None, sort_order=1, group_by=None):
    """
    Récupère la liste des équipements avec pagination et filtrage
    """
    db = get_mongodb_connection()
    collection = db['equipment']
    
    # Construire la requête de filtrage
    query = {}
    if filters:
        for key, value in filters.items():
            if value is not None and value != '':
                if key in ['model', 'serial', 'barcode', 'status', 'location']:
                    query[key] = {'$regex': f'.*{value}.*', '$options': 'i'}
                elif key in ['creation_date', 'dms']:
                    # Gestion des plages de dates
                    if isinstance(value, dict):
                        date_query = {}
                        if 'gte' in value:
                            date_query['$gte'] = value['gte']
                        if 'lte' in value:
                            date_query['$lte'] = value['lte']
                        if date_query:
                            query[key] = date_query
    
    # Gestion du groupement si demandé
    if group_by:
        pipeline = [
            {'$match': query} if query else {'$match': {}},
            {'$group': {
                '_id': f'${group_by}',
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        
        results = list(collection.aggregate(pipeline))
        
        # Formater les résultats pour la réponse
        formatted_results = []
        for item in results:
            if item['_id']:  # Ne pas inclure les valeurs nulles
                formatted_results.append({
                    '_id': item['_id'],
                    'count': item['count']
                })
        
        return formatted_results
    
    # Si pas de groupement, on fait une requête normale avec pagination
    # Compter le nombre total de documents
    total = collection.count_documents(query)
    
    # Configuration du tri
    sort = [(sort_field, sort_order)] if sort_field else [('_id', 1)]
    
    # Récupération des données avec pagination
    skip = (page - 1) * page_size
    cursor = collection.find(query).sort(sort).skip(skip).limit(page_size)
    
    # Conversion des ObjectId en chaînes pour la sérialisation JSON
    equipments = []
    for doc in cursor:
        doc['_id'] = str(doc['_id'])
        
        # Conversion des dates en chaînes ISO
        date_fields = ['creation_date', 'dms', 'created_at', 'updated_at']
        for field in date_fields:
            if field in doc and isinstance(doc[field], datetime):
                doc[field] = doc[field].isoformat()
        
        equipments.append(doc)
    
    return {
        'total': total,
        'page': page,
        'page_size': page_size,
        'results': equipments
    }

def get_equipment(equipment_id):
    """
    Récupère un équipement par son ID
    """
    try:
        db = get_mongodb_connection()
        doc = db['equipment'].find_one({'_id': ObjectId(equipment_id)})
        
        if not doc:
            return None
            
        # Conversion de l'ObjectId en chaîne
        doc['_id'] = str(doc['_id'])
        
        # Conversion des dates en chaînes ISO
        date_fields = ['creation_date', 'dms', 'created_at', 'updated_at']
        for field in date_fields:
            if field in doc and isinstance(doc[field], datetime):
                doc[field] = doc[field].isoformat()
                
        return doc
    except Exception:
        return None

def get_equipment_relations(equipment_id, relation_type):
    """
    Récupère les relations d'un équipement (designations, families, etc.)
    """
    db = get_mongodb_connection()
    
    # Vérifier que l'équipement existe
    equipment = get_equipment(equipment_id)
    if not equipment:
        return None
    
    # Selon le type de relation demandé
    if relation_type == 'designations':
        collection = db['designations']
        return list(collection.find({'equipment_id': ObjectId(equipment_id)}))
    
    elif relation_type == 'families':
        collection = db['families']
        return list(collection.find({'equipment_id': ObjectId(equipment_id)}))
    
    elif relation_type == 'subfamilies':
        collection = db['subfamilies']
        return list(collection.find({'equipment_id': ObjectId(equipment_id)}))
    
    elif relation_type == 'locations':
        collection = db['locations']
        return list(collection.find({'equipment_id': ObjectId(equipment_id)}))
    
    return None


def create_equipment(equipment_data):
    """
    Crée un nouvel équipement dans la base de données
    
    Args:
        equipment_data (dict): Dictionnaire contenant les données de l'équipement
        
    Returns:
        tuple: (success, result) où success est un booléen et result est soit l'ID du nouvel équipement soit un message d'erreur
    """
    try:
        db = get_mongodb_connection()
        collection = db['equipment']
        
        # Ajouter les métadonnées
        now = datetime.utcnow()
        equipment_data['creation_date'] = now
        equipment_data['updated_at'] = now
        
        # Insérer le nouvel équipement
        result = collection.insert_one(equipment_data)
        
        if result.inserted_id:
            return True, {'_id': str(result.inserted_id)}
        else:
            return False, {'error': 'Échec de la création de l\'équipement'}
            
    except Exception as e:
        return False, {'error': str(e)}


def update_equipment(equipment_id, update_data):
    """
    Met à jour un équipement existant
    
    Args:
        equipment_id (str): ID de l'équipement à mettre à jour
        update_data (dict): Dictionnaire contenant les champs à mettre à jour
        
    Returns:
        tuple: (success, result) où success est un booléen et result est soit un message de succès soit un message d'erreur
    """
    try:
        db = get_mongodb_connection()
        collection = db['equipment']
        
        # Vérifier que l'équipement existe
        if not collection.find_one({'_id': ObjectId(equipment_id)}):
            return False, {'error': 'Équipement non trouvé'}
        
        # Mettre à jour la date de modification
        update_data['updated_at'] = datetime.utcnow()
        
        # Mettre à jour l'équipement
        result = collection.update_one(
            {'_id': ObjectId(equipment_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return True, {'message': 'Équipement mis à jour avec succès'}
        else:
            return False, {'error': 'Aucune modification effectuée'}
            
    except Exception as e:
        return False, {'error': str(e)}


def delete_equipment(equipment_id):
    """
    Supprime un équipement de la base de données
    
    Args:
        equipment_id (str): ID de l'équipement à supprimer
        
    Returns:
        tuple: (success, result) où success est un booléen et result est un message de succès ou d'erreur
    """
    try:
        db = get_mongodb_connection()
        collection = db['equipment']
        
        # Vérifier que l'équipement existe
        if not collection.find_one({'_id': ObjectId(equipment_id)}):
            return False, {'error': 'Équipement non trouvé'}
        
        # Supprimer l'équipement
        result = collection.delete_one({'_id': ObjectId(equipment_id)})
        
        if result.deleted_count > 0:
            return True, {'message': 'Équipement supprimé avec succès'}
        else:
            return False, {'error': 'Échec de la suppression de l\'équipement'}
            
    except Exception as e:
        return False, {'error': str(e)}
