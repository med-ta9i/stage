import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import pytz
from tqdm import tqdm

# Ajouter le répertoire parent au chemin Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer l'utilitaire de connexion MongoDB
from dashboard.db import get_mongodb_connection

def parse_date(date_str):
    """
    Convertit une chaîne de date en objet datetime
    
    Args:
        date_str (str/int/float): Chaîne ou nombre représentant une date (peut être un nombre pour les dates Excel)
        
    Returns:
        datetime: Objet datetime ou None si la conversion échoue
    """
    if not date_str or pd.isna(date_str):
        return None
    
    # Si c'est déjà un objet datetime, le retourner tel quel
    if isinstance(date_str, datetime):
        return date_str
    
    try:
        # Essayer de convertir en float pour détecter les dates Excel
        try:
            excel_date = float(date_str)
            # Si c'est un nombre, c'est probablement une date Excel
            # Les dates Excel sont le nombre de jours depuis 1900-01-01
            if 0 < excel_date < 100000:  # Plage raisonnable pour une date
                excel_epoch = datetime(1899, 12, 30)  # Excel compte à partir du 1900-01-01 comme 1
                return excel_epoch + timedelta(days=excel_date)
        except (ValueError, TypeError):
            pass
        
        # Convertir en chaîne et nettoyer
        date_str = str(date_str).strip()
        
        # Gérer les chaînes vides après conversion
        if not date_str:
            return None
        
        # Essayer de parser le format ISO 8601 avec timezone
        if 'T' in date_str:
            try:
                # Essayer avec le format ISO complet
                if '+' in date_str or 'Z' in date_str.upper():
                    # Remplacer Z par +00:00 pour la compatibilité
                    iso_str = date_str.upper().replace('Z', '+00:00')
                    return datetime.fromisoformat(iso_str)
                else:
                    # Essayer sans timezone
                    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')
            except (ValueError, AttributeError):
                pass
        
        # Essayer d'autres formats courants
        date_formats = [
            '%Y-%m-%d %H:%M:%S',  # 2023-01-01 12:00:00
            '%Y-%m-%d',           # 2023-01-01
            '%d/%m/%Y',           # 01/01/2023
            '%m/%d/%Y',           # 01/01/2023 (US)
            '%d/%m/%y',           # 01/01/23
            '%m/%d/%y',           # 01/01/23 (US)
            '%Y%m%d',             # 20230101
            '%d-%m-%Y',           # 01-01-2023
            '%m-%d-%Y',           # 01-01-2023 (US)
            '%d.%m.%Y',           # 01.01.2023
            '%Y/%m/%d',           # 2023/01/01
            '%d %b %Y',           # 01 Jan 2023
            '%d %B %Y',           # 01 January 2023
            '%b %d, %Y',          # Jan 01, 2023
            '%B %d, %Y'           # January 01, 2023
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Si aucun format ne correspond, essayer de parser avec dateutil
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except (ImportError, ValueError, OverflowError):
            pass
            
        return None
        
    except Exception as e:
        print(f"Erreur lors de la conversion de la date {date_str}: {e}")
        return None

def import_equipment(csv_path):
    """Importe les équipements depuis le fichier CSV"""
    print(f"\nImportation des équipements depuis {csv_path}...")
    
    try:
        # Se connecter à MongoDB
        db = get_mongodb_connection()
        collection = db['equipment']
        
        # Lire le fichier CSV
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Nettoyer les noms de colonnes
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Remplacer les valeurs NaN par None
        df = df.where(pd.notnull(df), None)
        
        # Convertir les colonnes de date
        date_columns = ['creationdate', 'dms']
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(parse_date)
        
        # Renommer les colonnes pour correspondre au modèle
        column_mapping = {
            'model': 'model',
            'serial': 'serial',
            'barcode': 'barcode',
            'prix': 'price',
            'price': 'price',  # En cas de doublon
            'devise': 'currency',
            'situation': 'status',
            'description': 'description',
            'configuser': 'config_user',
            'creationdate': 'creation_date',
            'dms': 'dms',
            'photo': 'photo',
            'power': 'power',
            'files': 'files',
            'localisation': 'location',
            'passog': 'pass_og'  # Nouveau champ
        }
        
        # Filtrer les colonnes qui existent dans le mapping
        df = df.rename(columns={k: v for k, v in column_mapping.items() 
                               if k in df.columns})
        
        # Nettoyer les colonnes en double
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Convertir en liste de dictionnaires
        equipment_data = df.to_dict('records')
        
        # Préparer la barre de progression
        total = len(equipment_data)
        inserted = 0
        updated = 0
        errors = 0
        
        # Désactiver temporairement l'index pour des performances optimales
        collection.drop_indexes()
        
        # Importer les données par lots
        batch_size = 1000
        for i in tqdm(range(0, total, batch_size), 
                     desc="Importation des équipements", 
                     unit="lots"):
            batch = equipment_data[i:i+batch_size]
            
            for item in batch:
                try:
                    # Préparer le document
                    doc = {}
                    for k, v in item.items():
                        if pd.notna(v) and v != '':
                            doc[k] = v
                    
                    # Mettre à jour ou insérer le document
                    result = collection.update_one(
                        {'_id': doc['_id']},
                        {'$set': doc},
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        inserted += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    errors += 1
                    print(f"\nErreur lors de l'import de l'équipement {item.get('_id')}: {e}")
        
        # Créer des index pour les requêtes fréquentes
        # Index sur serial (non unique car peut avoir des doublons)
        collection.create_index([('serial', 1)])
        
        # Index sur barcode (non unique pour éviter les erreurs de contrainte)
        collection.create_index([('barcode', 1)])
        
        # Créer d'autres index non-uniques pour les champs fréquemment utilisés dans les requêtes
        collection.create_index([('status', 1)])
        collection.create_index([('location', 1)])
        
        # Vérifier et nettoyer les doublons potentiels de barcode
        # Cette étape est effectuée après l'import pour garantir l'unicité
        pipeline = [
            {'$match': {
                'barcode': {
                    '$exists': True,
                    '$ne': None,
                    '$ne': '',
                    '$type': 'string'
                }
            }},
            {'$group': {
                '_id': '$barcode',
                'dups': {'$addToSet': '$_id'},
                'count': {'$sum': 1}
            }},
            {'$match': {'count': {'$gt': 1}}}
        ]
        
        # Pour chaque barcode en double, conserver uniquement le premier document
        for doc in collection.aggregate(pipeline):
            if not doc['_id']:  # Ignorer les valeurs vides
                continue
                
            # Garder le premier _id et marquer les autres pour suppression
            keep_id = doc['dups'].pop(0)
            
            # Mettre à jour les documents en double pour éviter les problèmes d'unicité
            # En ajoutant un suffixe unique aux codes-barres en double
            for i, dup_id in enumerate(doc['dups'], 1):
                new_barcode = f"{doc['_id']}_dup_{i}"
                collection.update_one(
                    {'_id': dup_id},
                    {'$set': {'barcode': new_barcode}}
                )
        
        # Afficher un résumé
        print(f"\nRésumé de l'importation:")
        print(f"- Documents insérés: {inserted}")
        print(f"- Documents mis à jour: {updated}")
        print(f"- Erreurs: {errors}")
        print(f"Total des documents dans la collection: {collection.count_documents({})}")
        
    except Exception as e:
        print(f"\nErreur lors de l'importation: {e}")
        raise

def import_relation_data(csv_path, relation_type):
    """
    Importe les données de relation (famille, localisation, etc.)
    
    Args:
        csv_path (str): Chemin vers le fichier CSV
        relation_type (str): Type de relation ('designation', 'family', 'location', 'subfamily')
    """
    print(f"\nImportation des données de {relation_type} depuis {csv_path}...")
    
    try:
        # Se connecter à MongoDB
        db = get_mongodb_connection()
        collection = db[f'equipment_{relation_type}']
        
        # Lire le fichier CSV
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Nettoyer les noms de colonnes
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Remplacer les valeurs NaN par None
        df = df.where(pd.notnull(df), None)
        
        # Préparer les données
        data = df.to_dict('records')
        total = len(data)
        inserted = 0
        updated = 0
        errors = 0
        
        # Désactiver temporairement les index
        collection.drop_indexes()
        
        # Importer les données par lots
        batch_size = 1000
        for i in tqdm(range(0, total, batch_size), 
                     desc=f"Importation des {relation_type}s", 
                     unit="lots"):
            batch = data[i:i+batch_size]
            
            for item in batch:
                try:
                    # Préparer le document
                    doc = {
                        '_id': str(item.get('_id')),
                        'equipment_id': str(item.get('equipment_id')),
                        f'{relation_type}_id': item.get(f'{relation_type}_id')
                    }
                    
                    # Nettoyer les valeurs None
                    doc = {k: v for k, v in doc.items() if v is not None}
                    
                    # Mettre à jour ou insérer le document
                    result = collection.update_one(
                        {'_id': doc['_id']},
                        {'$set': doc},
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        inserted += 1
                    else:
                        updated += 1
                        
                except Exception as e:
                    errors += 1
                    print(f"\nErreur lors de l'import de la relation {item.get('_id')}: {e}")
        
        # Créer des index pour les requêtes fréquentes
        collection.create_index([('equipment_id', 1)])
        collection.create_index([(f'{relation_type}_id', 1)])
        
        # Afficher un résumé
        print(f"\nRésumé de l'importation des {relation_type}s:")
        print(f"- Documents insérés: {inserted}")
        print(f"- Documents mis à jour: {updated}")
        print(f"- Erreurs: {errors}")
        print(f"Total des documents dans la collection: {collection.count_documents({})}")
        
    except Exception as e:
        print(f"\nErreur lors de l'importation des {relation_type}s: {e}")
        raise

def main():
    # Chemins des fichiers CSV
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    # Dictionnaire des fichiers CSV et de leurs types de relation
    import_mapping = {
        'MgtDB.Material_equipment.csv': ('equipment', import_equipment),
        'MgtDB.Material_equipment_Designation.csv': ('designation', import_relation_data),
        'MgtDB.Material_equipment_family.csv': ('family', import_relation_data),
        'MgtDB.Material_equipment_location.csv': ('location', import_relation_data),
        'MgtDB.Material_equipment_subfamily.csv': ('subfamily', import_relation_data)
    }
    
    # Vérifier que le répertoire des données existe
    if not os.path.exists(data_dir):
        print(f"Erreur: Le répertoire des données {data_dir} n'existe pas.")
        return
    
    # Vérifier la connexion à MongoDB
    try:
        db = get_mongodb_connection()
        print("Connexion à MongoDB établie avec succès!")
    except Exception as e:
        print(f"Erreur de connexion à MongoDB: {e}")
        return
    
    # Exécuter les imports dans l'ordre
    for filename, (relation_type, import_func) in import_mapping.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            try:
                if relation_type == 'equipment':
                    import_func(filepath)
                else:
                    import_func(filepath, relation_type)
                print(f"\n{'='*50}\n")
            except Exception as e:
                print(f"\nErreur lors de l'import de {filename}: {e}")
                print(f"\n{'='*50}\n")
        else:
            print(f"Avertissement: Fichier {filepath} non trouvé, ignoré\n")
    
    print("\nImportation terminée avec succès!")
    
    print("\nImportation des données terminée avec succès!")

if __name__ == "__main__":
    main()
