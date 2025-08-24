#!/usr/bin/env python
"""
Script d'import des localisations depuis le fichier CSV vers MongoDB
"""
import os
import sys
import django
import csv
from datetime import datetime

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dem_dashboard.settings')
django.setup()

from dashboard.db import get_mongodb_connection

def clean_value(value):
    """Nettoie et convertit les valeurs du CSV"""
    if value is None or value == '':
        return None
    if value.lower() in ['true', 'false']:
        return value.lower() == 'true'
    try:
        # Essayer de convertir en nombre
        if '.' in str(value):
            return float(value)
        else:
            return int(value)
    except (ValueError, TypeError):
        return str(value).strip()

def parse_date(date_str):
    """Parse les dates du CSV"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        # Format: 2025-01-24T11:55:32.502Z
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except Exception:
        return None

def import_locations():
    """Import des localisations depuis le CSV"""
    
    # Connexion à MongoDB
    db = get_mongodb_connection()
    collection = db['locations']
    
    # Chemin vers le fichier CSV
    csv_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'data', 
        'MgtDB.Staff_site.csv'
    )
    
    if not os.path.exists(csv_file):
        print(f"Erreur: Fichier CSV non trouvé: {csv_file}")
        return
    
    print(f"Import des localisations depuis: {csv_file}")
    
    # Vider la collection existante (optionnel)
    choice = input("Voulez-vous vider la collection existante ? (y/N): ")
    if choice.lower() == 'y':
        collection.delete_many({})
        print("Collection vidée.")
    
    imported_count = 0
    error_count = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Préparer le document
                    location_doc = {
                        'site_id': clean_value(row.get('_id')),
                        'site_name': clean_value(row.get('Site')),
                        'province': clean_value(row.get('Province')),
                        'region': clean_value(row.get('Region')),
                        'snrt_rs': clean_value(row.get('SNRT_RS')),
                        
                        # Coordonnées géographiques
                        'coordinates': {
                            'latitude': clean_value(row.get('Latitude')),
                            'longitude': clean_value(row.get('Longitude')),
                            'altitude': clean_value(row.get('Altitude'))
                        },
                        
                        # Classification
                        'category': clean_value(row.get('Category')),
                        'services': {
                            'tnt': clean_value(row.get('TNT')),
                            'fm': clean_value(row.get('FM')),
                            'am': clean_value(row.get('AM')),
                            'administration': clean_value(row.get('Administration')),
                            'fh': clean_value(row.get('FH')),
                            'st': clean_value(row.get('ST'))
                        },
                        
                        # Contact et configuration
                        'config_user': clean_value(row.get('ConfigUser')),
                        'contact': {
                            'fixe': clean_value(row.get('Fixe')),
                            'gsm': clean_value(row.get('Gsm'))
                        },
                        
                        # Métadonnées
                        'code': clean_value(row.get('Code')),
                        'photo': clean_value(row.get('Photo')),
                        'files': clean_value(row.get('files')),
                        'control': clean_value(row.get('control')),
                        
                        # Dates
                        'creation_date': parse_date(row.get('CreationDate')),
                        'imported_at': datetime.utcnow()
                    }
                    
                    # Nettoyer les valeurs None dans coordinates
                    coords = location_doc['coordinates']
                    if coords['latitude'] is None and coords['longitude'] is None:
                        location_doc['coordinates'] = None
                    
                    # Insérer dans MongoDB
                    collection.insert_one(location_doc)
                    imported_count += 1
                    
                    if imported_count % 50 == 0:
                        print(f"Importé: {imported_count} localisations...")
                        
                except Exception as e:
                    error_count += 1
                    print(f"Erreur ligne {reader.line_num}: {str(e)}")
                    continue
    
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {str(e)}")
        return
    
    print("\n=== RÉSUMÉ DE L'IMPORT ===")
    print(f"Localisations importées: {imported_count}")
    print(f"Erreurs: {error_count}")
    print(f"Total traité: {imported_count + error_count}")
    
    # Créer des index pour optimiser les requêtes
    print("\nCréation des index...")
    try:
        collection.create_index("site_name")
        collection.create_index("region")
        collection.create_index("province")
        collection.create_index("category")
        collection.create_index([("coordinates.latitude", 1), ("coordinates.longitude", 1)])
        print("Index créés avec succès.")
    except Exception as e:
        print(f"Erreur lors de la création des index: {str(e)}")

if __name__ == "__main__":
    print("=== IMPORT DES LOCALISATIONS ===")
    import_locations()
    print("Import terminé.")
