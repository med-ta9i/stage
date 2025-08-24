from bson import ObjectId
from datetime import datetime
from .db import get_mongodb_connection

def get_locations(filters=None, page=1, page_size=20, sort_field=None, sort_order=1, group_by=None):
    """
    Récupérer la liste des localisations avec filtrage et pagination
    """
    try:
        db = get_mongodb_connection()
        collection = db['locations']
        
        # Filtre de base pour ne récupérer que les documents du CSV importé
        base_filter = {
            'site_name': {'$exists': True, '$ne': ''},
            'province': {'$exists': True},
            'region': {'$exists': True}
        }
        
        # Construire la requête de filtrage
        query = base_filter.copy()
        
        if filters:
            # Filtres de recherche textuelle
            if 'site_name' in filters and filters['site_name']:
                query['site_name'] = {'$regex': f'.*{filters["site_name"]}.*', '$options': 'i'}
            
            # Filtres exacts
            for field in ['province', 'region', 'category', 'snrt_rs']:
                if field in filters and filters[field]:
                    query[field] = filters[field]
            
            # Filtres de services
            if 'services' in filters:
                for service, value in filters['services'].items():
                    if value is not None:
                        query[f'services.{service}'] = value
        
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
        sort = [(sort_field, sort_order)] if sort_field else [('site_name', 1)]
        
        # Récupération des données avec pagination
        skip = (page - 1) * page_size
        cursor = collection.find(query).sort(sort).skip(skip).limit(page_size)
        
        # Conversion des ObjectId en chaînes pour la sérialisation JSON
        locations = []
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            
            # Conversion des dates en chaînes ISO
            date_fields = ['creation_date', 'imported_at']
            for field in date_fields:
                if field in doc and isinstance(doc[field], datetime):
                    doc[field] = doc[field].isoformat()
            
            locations.append(doc)
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': locations
        }
    
    except Exception as e:
        return {'error': str(e)}

def get_location(location_id):
    """
    Récupère une localisation par son ID
    """
    try:
        db = get_mongodb_connection()
        doc = db['locations'].find_one({'_id': ObjectId(location_id)})
        
        if not doc:
            return None
            
        # Conversion de l'ObjectId en chaîne
        doc['_id'] = str(doc['_id'])
        
        # Conversion des dates en chaînes ISO
        date_fields = ['creation_date', 'imported_at']
        for field in date_fields:
            if field in doc and isinstance(doc[field], datetime):
                doc[field] = doc[field].isoformat()
                
        return doc
    except:
        return None

def get_location_by_site_id(site_id):
    """
    Récupère une localisation par son site_id
    """
    try:
        db = get_mongodb_connection()
        doc = db['locations'].find_one({'site_id': site_id})
        
        if not doc:
            return None
            
        # Conversion de l'ObjectId en chaîne
        doc['_id'] = str(doc['_id'])
        
        # Conversion des dates en chaînes ISO
        date_fields = ['creation_date', 'imported_at']
        for field in date_fields:
            if field in doc and isinstance(doc[field], datetime):
                doc[field] = doc[field].isoformat()
                
        return doc
    except:
        return None

def create_location(location_data):
    """
    Crée une nouvelle localisation dans la base de données
    """
    try:
        db = get_mongodb_connection()
        collection = db['locations']
        
        # Ajouter les métadonnées
        now = datetime.utcnow()
        location_data['creation_date'] = now
        location_data['imported_at'] = now
        
        # Insérer la nouvelle localisation
        result = collection.insert_one(location_data)
        
        if result.inserted_id:
            return True, {'_id': str(result.inserted_id)}
        else:
            return False, {'error': 'Échec de la création de la localisation'}
            
    except Exception as e:
        return False, {'error': str(e)}

def update_location(location_id, update_data):
    """
    Met à jour une localisation existante
    """
    try:
        db = get_mongodb_connection()
        collection = db['locations']
        
        # Vérifier que la localisation existe
        if not collection.find_one({'_id': ObjectId(location_id)}):
            return False, {'error': 'Localisation non trouvée'}
        
        # Mettre à jour la date de modification
        update_data['updated_at'] = datetime.utcnow()
        
        # Mettre à jour la localisation
        result = collection.update_one(
            {'_id': ObjectId(location_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            return True, {'message': 'Localisation mise à jour avec succès'}
        else:
            return False, {'error': 'Aucune modification effectuée'}
            
    except Exception as e:
        return False, {'error': str(e)}

def delete_location(location_id):
    """
    Supprime une localisation de la base de données
    """
    try:
        db = get_mongodb_connection()
        collection = db['locations']
        
        # Vérifier que la localisation existe
        if not collection.find_one({'_id': ObjectId(location_id)}):
            return False, {'error': 'Localisation non trouvée'}
        
        # Supprimer la localisation
        result = collection.delete_one({'_id': ObjectId(location_id)})
        
        if result.deleted_count > 0:
            return True, {'message': 'Localisation supprimée avec succès'}
        else:
            return False, {'error': 'Échec de la suppression de la localisation'}
            
    except Exception as e:
        return False, {'error': str(e)}

def get_locations_statistics():
    """
    Récupère les statistiques des localisations
    """
    try:
        db = get_mongodb_connection()
        collection = db['locations']
        
        # Filtre de base aligné avec get_locations()
        base_filter = {
            'site_name': {'$exists': True, '$ne': ''},
            'province': {'$exists': True},
            'region': {'$exists': True}
        }
        
        # Statistiques générales
        total_locations = collection.count_documents(base_filter)
        
        # Répartition par région
        regions_pipeline = [
            {'$match': base_filter},
            {'$group': {'_id': '$region', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        regions = list(collection.aggregate(regions_pipeline))
        
        # Répartition par catégorie
        categories_pipeline = [
            {'$match': base_filter},
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        categories = list(collection.aggregate(categories_pipeline))
        
        # Services disponibles
        services_pipeline = [
            {'$match': base_filter},
            {'$project': {
                'tnt': '$services.tnt',
                'fm': '$services.fm',
                'am': '$services.am'
            }},
            {'$group': {
                '_id': None,
                'tnt_count': {'$sum': {'$cond': ['$tnt', 1, 0]}},
                'fm_count': {'$sum': {'$cond': ['$fm', 1, 0]}},
                'am_count': {'$sum': {'$cond': ['$am', 1, 0]}}
            }}
        ]
        services = list(collection.aggregate(services_pipeline))
        
        return {
            'total_locations': total_locations,
            'by_region': regions,
            'by_category': categories,
            'services': services[0] if services else {}
        }
        
    except Exception as e:
        return {'error': str(e)}

def get_locations_for_map():
    """
    Récupère les localisations avec coordonnées pour affichage sur carte
    """
    try:
        db = get_mongodb_connection()
        collection = db['locations']
        
        # Récupérer les localisations avec coordonnées sous différents schémas possibles
        query = {
            '$or': [
                {'coordinates.latitude': {'$ne': None}, 'coordinates.longitude': {'$ne': None}},
                {'lat': {'$ne': None}, 'lng': {'$ne': None}},
                {'latitude': {'$ne': None}, 'longitude': {'$ne': None}},
            ]
        }
        
        projection = {
            'site_name': 1,
            'province': 1,
            'region': 1,
            'category': 1,
            'coordinates': 1,
            'lat': 1,
            'lng': 1,
            'latitude': 1,
            'longitude': 1,
            'services': 1
        }
        
        locations = list(collection.find(query, projection))
        
        # Formater pour la carte
        map_data = []
        for loc in locations:
            # Extraire lat/lng sous différentes clés et convertir en float
            lat = None
            lng = None
            if isinstance(loc.get('coordinates'), dict):
                lat = loc['coordinates'].get('latitude', lat)
                lng = loc['coordinates'].get('longitude', lng)
            lat = loc.get('lat', lat)
            lng = loc.get('lng', lng)
            lat = loc.get('latitude', lat)
            lng = loc.get('longitude', lng)

            try:
                lat_f = float(lat) if lat is not None else None
                lng_f = float(lng) if lng is not None else None
            except (TypeError, ValueError):
                lat_f, lng_f = None, None

            if lat_f is None or lng_f is None:
                continue

            map_data.append({
                '_id': str(loc['_id']),
                'name': loc.get('site_name', ''),
                'province': loc.get('province', ''),
                'region': loc.get('region', ''),
                'category': loc.get('category', ''),
                'lat': lat_f,
                'lng': lng_f,
                'altitude': (loc.get('coordinates') or {}).get('altitude'),
                'services': loc.get('services', {})
            })
        
        return map_data
        
    except Exception:
        return []
