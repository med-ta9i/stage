# Tableau de Bord DEM

Application web de suivi des équipements pour le magasin DEM, offrant une vue d'ensemble des indicateurs clés de performance (KPI) et des fonctionnalités avancées de gestion des équipements.

## Fonctionnalités

- **Tableau de bord interactif** avec visualisation des KPI en temps réel
- **Gestion des équipements** : consultation, ajout, modification et suppression
- **Filtrage et recherche avancée** des équipements par différents critères
- **Visualisations graphiques** des données (graphiques, tableaux, indicateurs)
- **Gestion des statuts** des équipements (en stock, en service, maintenance, etc.)
- **Suivi des coûts** et de la valeur du stock
- **Recherche et export** des données

## Prérequis

- Python 3.8 ou supérieur
- MongoDB 4.4 ou supérieur
- Node.js et npm (pour les dépendances frontend)

## Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/med-ta9i/stage
   cd stage
   ```

2. **Créer et activer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # OU
   .\venv\Scripts\activate  # Sur Windows
   ```

3. **Installer les dépendances Python**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**
   Créez un fichier `.env` à la racine du projet avec les configurations suivantes :
   ```
   DEBUG=True
   SECRET_KEY=votre_secret_key_django
   MONGODB_URI=mongodb://localhost:27017/dem_dashboard
   ```

5. **Importer les données initiales** (si nécessaire)
   ```bash
   python manage.py import_data
   ```

6. **Démarrer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

7. **Accéder à l'application**
   - Interface principale : http://localhost:8000/
   - Interface d'administration : http://localhost:8000/admin/
   - Documentation de l'API : http://localhost:8000/api/docs/

## Structure du projet

```
dem_dashboard/
├── dashboard/                 # Application principale
│   ├── migrations/           # Fichiers de migration (si utilisation de l'ORM)
│   ├── static/               # Fichiers statiques (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   ├── templates/            # Templates HTML
│   │   └── dashboard/
│   ├── __init__.py
│   ├── admin.py             # Configuration de l'interface d'administration
│   ├── api.py               # Logique de l'API personnalisée
│   ├── apps.py              # Configuration de l'application
│   ├── db.py                # Connexion à MongoDB
│   ├── urls.py              # URLs de l'application
│   └── views.py             # Vues de l'application
├── dem_dashboard/            # Configuration du projet
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py          # Paramètres du projet
│   ├── urls.py              # URLs du projet
│   └── wsgi.py
├── scripts/                  # Scripts utilitaires
│   └── import_data.py       # Script d'import des données
├── .env.example             # Exemple de fichier d'environnement
├── .gitignore
├── manage.py
├── README.md
└── requirements.txt         # Dépendances Python
```

## API Endpoints

L'application expose une API REST accessible via les endpoints suivants :

- `GET /api/equipments/` - Liste paginée des équipements avec filtres
- `GET /api/equipments/<id>/` - Détails d'un équipement spécifique
- `GET /api/equipments/<id>/<relation>/` - Relations d'un équipement (designations, families, etc.)

### Filtres disponibles

- `model`: Filtre par modèle d'équipement
- `status`: Filtre par statut (en stock, en service, maintenance, etc.)
- `location`: Filtre par localisation
- `creation_date_gte`: Date de création supérieure ou égale à (format YYYY-MM-DD)
- `creation_date_lte`: Date de création inférieure ou égale à (format YYYY-MM-DD)

### Exemple de requête

```bash
# Récupérer les équipements en service
GET /api/equipments/?status=En%20service

# Récupérer les équipements créés en 2023
GET /api/equipments/?creation_date_gte=2023-01-01&creation_date_lte=2023-12-31
```

## Développement

### Structure des données

#### Collection `equipments`
```javascript
{
  "_id": ObjectId("..."),
  "model": "Modèle de l'équipement",
  "serial": "Numéro de série unique",
  "barcode": "Code-barres",
  "status": "En stock | En service | Maintenance | Hors service",
  "location": "Localisation physique",
  "price": 999.99,
  "purchase_date": ISODate("2023-01-01"),
  "warranty_expiry": ISODate("2025-01-01"),
  "notes": "Notes supplémentaires",
  "created_at": ISODate("2023-01-01T00:00:00Z"),
  "updated_at": ISODate("2023-01-01T00:00:00Z")
}
```

### Commandes utiles

- **Lancer les tests**
  ```bash
  python manage.py test
  ```

- **Créer un superutilisateur**
  ```bash
  python manage.py createsuperuser
  ```

- **Collecter les fichiers statiques** (pour la production)
  ```bash
  python manage.py collectstatic
  ```

## Déploiement

Pour le déploiement en production, il est recommandé d'utiliser :

1. **Serveur WSGI** : Gunicorn ou uWSGI
2. **Serveur Web** : Nginx ou Apache
3. **Base de données** : MongoDB en réplication pour la haute disponibilité

### Variables d'environnement de production

```
DEBUG=False
SECRET_KEY=votre_secret_key_tres_long_et_securise
MONGODB_URI=mongodb://utilisateur:motdepasse@serveur-mongodb:27017/dem_dashboard?authSource=admin
ALLOWED_HOSTS=.votredomaine.com,localhost,127.0.0.1
```


## Auteur

- M'hamed Taki - taki.mhamed.taki@gmail.com

## Remerciements

- L'équipe du magasin DEM pour leur confiance
- Les contributeurs des bibliothèques open source utilisées
