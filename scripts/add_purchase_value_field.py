#!/usr/bin/env python3
"""
Script pour ajouter un champ purchase_value numérique basé sur le champ price existant.
Ce script doit être exécuté depuis le répertoire racine du projet.
"""
import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.decimal128 import Decimal128
import re

# Ajouter le répertoire parent au chemin Python pour pouvoir importer les modules du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

def get_mongodb_connection():
    """Établit une connexion à la base de données MongoDB."""
    try:
        # Récupérer la configuration depuis les variables d'environnement
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = int(os.getenv('DB_PORT', 27017))
        db_name = os.getenv('DB_NAME', 'dem_dashboard')
        
        # Se connecter à MongoDB
        client = MongoClient(
            host=db_host,
            port=db_port,
            serverSelectionTimeoutMS=5000  # Timeout de 5 secondes
        )
        
        # Tester la connexion
        client.admin.command('ping')
        
        # Retourner la base de données
        return client[db_name]
        
    except ConnectionFailure as e:
        print(f"Échec de la connexion à MongoDB: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur inattendue lors de la connexion à MongoDB: {e}")
        sys.exit(1)

def convert_price_to_float(price_str):
    """
    Convertit une chaîne de caractères représentant un prix en nombre flottant.
    Gère différents formats de prix, y compris les séparateurs de milliers et les décimales.
    """
    if not price_str or not isinstance(price_str, str):
        return None
    
    # Nettoyer la chaîne (supprimer les espaces, les symboles de devise, etc.)
    clean_str = price_str.strip().replace(' ', '').replace(',', '.').replace('€', '').replace('$', '').strip()
    
    # Vérifier si c'est un nombre décimal avec un point ou une virgule
    if re.match(r'^\d+([.,]\d+)?$', clean_str):
        # Remplacer la virgule par un point si nécessaire
        clean_str = clean_str.replace(',', '.')
        try:
            return float(clean_str)
        except (ValueError, TypeError):
            return None
    
    # Si la chaîne ne correspond à aucun format de nombre reconnu
    return None

def main():
    """Fonction principale du script."""
    print("Début du script d'ajout du champ purchase_value...")
    
    # Se connecter à la base de données
    db = get_mongodb_connection()
    collection = db['equipment']
    
    # Compter le nombre total de documents
    total_docs = collection.count_documents({})
    print(f"Nombre total d'équipements dans la base de données : {total_docs}")
    
    # Initialiser les compteurs
    updated_count = 0
    skipped_count = 0
    
    # Parcourir tous les documents de la collection
    for doc in collection.find({}):
        doc_id = doc.get('_id')
        price = doc.get('price')
        
        # Vérifier si le champ purchase_value existe déjà
        if 'purchase_value' in doc:
            print(f"Document {doc_id} : le champ purchase_value existe déjà, passage au suivant...")
            skipped_count += 1
            continue
        
        # Convertir le prix en nombre flottant
        purchase_value = None
        
        if price is not None:
            if isinstance(price, (int, float)):
                # Si le prix est déjà un nombre, l'utiliser directement
                purchase_value = float(price)
            elif isinstance(price, str):
                # Sinon, essayer de le convertir depuis une chaîne
                purchase_value = convert_price_to_float(price)
        
        # Mettre à jour le document avec le nouveau champ purchase_value
        update_result = collection.update_one(
            {'_id': doc_id},
            {'$set': {'purchase_value': purchase_value if purchase_value is not None else 0.0}}
        )
        
        if update_result.modified_count > 0:
            updated_count += 1
            if updated_count % 100 == 0:
                print(f"{updated_count} documents mis à jour...")
    
    # Afficher un résumé
    print("\nRésumé de la migration :")
    print(f"- Documents traités : {total_docs}")
    print(f"- Documents mis à jour : {updated_count}")
    print(f"- Documents ignorés (déjà à jour) : {skipped_count}")
    
    # Créer un index sur le champ purchase_value pour améliorer les performances des requêtes
    try:
        collection.create_index('purchase_value')
        print("Index créé sur le champ purchase_value")
    except Exception as e:
        print(f"Erreur lors de la création de l'index : {e}")
    
    print("Migration terminée avec succès !")

if __name__ == "__main__":
    main()
