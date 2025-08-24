from django.views import View
from django.http import JsonResponse
from datetime import datetime, timedelta
from .api import get_mongodb_connection

class EquipmentStatusDistributionView(View):
    """
    Vue pour récupérer la répartition des équipements par statut
    """
    def get(self, request):
        try:
            db = get_mongodb_connection()
            collection = db['equipment']
            
            # Agrégation pour compter les équipements par statut normalisé
            pipeline = [
                # Étape 1: Normaliser les statuts
                {
                    '$addFields': {
                        'normalized_status': {
                            '$switch': {
                                'branches': [
                                    # Gérer les variantes de 'En service'
                                    {
                                        'case': { 
                                            '$or': [
                                                { '$eq': [{ '$toLower': '$status' }, 'en service'] },
                                                { '$eq': [{ '$toLower': '$status' }, 'en service.'] },
                                                { '$eq': ['$status', 'EN SERVICE'] },
                                                { '$eq': ['$status', 'En Service'] },
                                                { '$eq': ['$status', 'EN Service'] }
                                            ]
                                        },
                                        'then': 'En service'
                                    },
                                    # Gérer les variantes de 'En stock'
                                    {
                                        'case': { 
                                            '$or': [
                                                { '$eq': [{ '$toLower': '$status' }, 'en stock'] },
                                                { '$eq': ['$status', 'EN STOCK'] },
                                                { '$eq': ['$status', 'En Stock'] },
                                                { '$eq': ['$status', 'EN Stock'] }
                                            ]
                                        },
                                        'then': 'En stock'
                                    },
                                    # Gérer les variantes de 'En panne'
                                    {
                                        'case': { 
                                            '$or': [
                                                { '$eq': [{ '$toLower': '$status' }, 'en panne'] },
                                                { '$eq': ['$status', 'EN PANNE'] },
                                                { '$eq': ['$status', 'En Panne'] },
                                                { '$eq': ['$status', 'hs'] },
                                                { '$eq': ['$status', 'HS'] },
                                                { '$eq': ['$status', 'Hs'] }
                                            ]
                                        },
                                        'then': 'Hors service'
                                    }
                                ],
                                'default': '$status'  # Conserver la valeur d'origine si aucune correspondance
                            }
                        }
                    }
                },
                # Étape 2: Gérer les valeurs nulles ou vides
                {
                    '$addFields': {
                        'normalized_status': {
                            '$ifNull': ['$normalized_status', 'Non spécifié']
                        }
                    }
                },
                # Étape 3: Grouper par statut normalisé avec comptage
                {
                    '$group': {
                        '_id': '$normalized_status',
                        'count': { '$sum': 1 },
                        # Ajouter une valeur par défaut pour le calcul de la valeur totale
                        'total_value': { 
                            '$sum': { 
                                '$cond': [
                                    { '$and': [
                                        { '$ifNull': ['$purchase_value', False] },
                                        { '$gt': ['$purchase_value', 0] }
                                    ]},
                                    '$purchase_value',
                                    0
                                ]
                            } 
                        }
                    }
                },
                # Étape 4: Projeter les résultats
                {
                    '$project': {
                        'status': '$_id',
                        'count': 1,
                        'total_value': 1,
                        '_id': 0
                    }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            
            # Formater les résultats pour Chart.js
            labels = [item['status'] for item in results]
            counts = [item['count'] for item in results]
            values = [float(item.get('total_value', 0)) for item in results]
            
            return JsonResponse({
                'success': True,
                'data': {
                    'labels': labels,
                    'counts': counts,
                    'values': values
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

class EquipmentEvolutionView(View):
    """
    Vue pour récupérer l'évolution des stocks dans le temps
    """
    def get(self, request):
        try:
            db = get_mongodb_connection()
            collection = db['equipment']
            
            # Calculer la date d'il y a 12 mois
            one_year_ago = datetime.now() - timedelta(days=365)
            
            # Agrégation pour compter les équipements par mois et par statut normalisé
            pipeline = [
                # Étape 1: Filtrer par date et s'assurer que creation_date existe
                {
                    '$match': {
                        'creation_date': { 
                            '$exists': True,
                            '$ne': None,
                            '$gte': one_year_ago 
                        },
                        'status': { '$exists': True, '$ne': None }
                    }
                },
                # Étape 2: Normaliser les statuts
                {
                    '$addFields': {
                        'normalized_status': {
                            '$switch': {
                                'branches': [
                                    # Gérer les variantes de 'En service'
                                    {
                                        'case': { 
                                            '$or': [
                                                { '$eq': [{ '$toLower': '$status' }, 'en service'] },
                                                { '$eq': [{ '$toLower': '$status' }, 'en service.'] },
                                                { '$eq': ['$status', 'EN SERVICE'] },
                                                { '$eq': ['$status', 'En Service'] },
                                                { '$eq': ['$status', 'EN Service'] }
                                            ]
                                        },
                                        'then': 'En service'
                                    },
                                    # Gérer les variantes de 'En stock'
                                    {
                                        'case': { 
                                            '$or': [
                                                { '$eq': [{ '$toLower': '$status' }, 'en stock'] },
                                                { '$eq': ['$status', 'EN STOCK'] },
                                                { '$eq': ['$status', 'En Stock'] },
                                                { '$eq': ['$status', 'EN Stock'] }
                                            ]
                                        },
                                        'then': 'En stock'
                                    },
                                    # Gérer les variantes de 'En panne' et 'HS'
                                    {
                                        'case': { 
                                            '$or': [
                                                { '$eq': [{ '$toLower': '$status' }, 'en panne'] },
                                                { '$eq': ['$status', 'EN PANNE'] },
                                                { '$eq': ['$status', 'En Panne'] },
                                                { '$eq': ['$status', 'hs'] },
                                                { '$eq': ['$status', 'HS'] },
                                                { '$eq': ['$status', 'Hs'] }
                                            ]
                                        },
                                        'then': 'Hors service'
                                    }
                                ],
                                'default': 'Autre'  # Valeur par défaut pour les statuts non reconnus
                            }
                        }
                    }
                },
                # Étape 3: Grouper par mois et statut normalisé
                {
                    '$group': {
                        '_id': {
                            'year': { '$year': '$creation_date' },
                            'month': { '$month': '$creation_date' },
                            'status': '$normalized_status'
                        },
                        'count': { '$sum': 1 }
                    }
                },
                # Étape 4: Trier par année et mois
                {
                    '$sort': { '_id.year': 1, '_id.month': 1 }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            
            # Formater les résultats pour Chart.js
            months = {}
            statuses = set()
            
            for item in results:
                year = item['_id']['year']
                month = item['_id']['month']
                status = item['_id']['status']
                count = item['count']
                
                month_key = f"{year}-{month:02d}"
                statuses.add(status)
                
                if month_key not in months:
                    months[month_key] = {}
                
                months[month_key][status] = count
            
            # Créer les séries de données pour chaque statut
            sorted_months = sorted(months.keys())
            status_series = {status: [] for status in statuses}
            
            for month in sorted_months:
                for status in statuses:
                    status_series[status].append(months[month].get(status, 0))
            
            return JsonResponse({
                'success': True,
                'data': {
                    'labels': sorted_months,
                    'datasets': [
                        {
                            'label': status,
                            'data': status_series[status],
                            'borderColor': self._get_status_color(status),
                            'backgroundColor': self._get_status_color(status, 0.2),
                            'tension': 0.3
                        }
                        for status in statuses
                    ]
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    @staticmethod
    def _get_status_color(status, opacity=1):
        """Retourne une couleur en fonction du statut"""
        colors = {
            'En stock': f'rgba(54, 162, 235, {opacity})',
            'En service': f'rgba(75, 192, 192, {opacity})',
            'Hors service': f'rgba(255, 99, 132, {opacity})',
            'Maintenance': f'rgba(255, 206, 86, {opacity})',
            'En instance': f'rgba(153, 102, 255, {opacity})',
            'Autre': f'rgba(201, 203, 207, {opacity})',
        }
        return colors.get(status, f'rgba(201, 203, 207, {opacity})')

class EquipmentLocationView(View):
    """
    Vue pour récupérer la répartition géographique des équipements
    """
    def get(self, request):
        try:
            db = get_mongodb_connection()
            collection = db['equipment']
            
            # Agrégation pour compter les équipements par localisation
            pipeline = [
                {
                    '$match': {
                        'location': { '$exists': True, '$ne': '' }
                    }
                },
                {
                    '$group': {
                        '_id': '$location',
                        'count': { '$sum': 1 },
                        'total_value': { '$sum': '$purchase_value' }
                    }
                },
                {
                    '$sort': { 'count': -1 }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            
            # Formater les résultats pour la carte
            locations = []
            for item in results:
                # Ici, vous pourriez utiliser un service de géocodage pour obtenir les coordonnées
                # Pour l'instant, on retourne juste les noms des localisations
                locations.append({
                    'name': item['_id'],
                    'count': item['count'],
                    'total_value': float(item.get('total_value', 0))
                })
            
            return JsonResponse({
                'success': True,
                'data': locations
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
