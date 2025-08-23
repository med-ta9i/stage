# Tableau de Bord DEM

Application web de suivi des équipements pour le magasin DEM, offrant une vue d'ensemble des indicateurs clés de performance (KPI) et des fonctionnalités avancées de gestion des équipements.

## Fonctionnalités

- **Tableau de bord interactif** avec visualisation des KPI en temps réel
- **Gestion des équipements** : consultation, ajout, modification et suppression
- **Filtrage et recherche avancée** des équipements par différents critères
- **Visualisations graphiques** des données (graphiques, tableaux, indicateurs)
- **Gestion des statuts** des équipements (en stock, en service, maintenance, etc.)
- **Suivi des coûts** et de la valeur du stock
- **Recherche et export** des données (CSV, Excel)
- **Page Rapports** avec graphiques (répartition statuts, évolution, localisations)
- **Administration Django** avec page « Statistiques équipements » réservée au staff

## Prérequis

- Python 3.8 ou supérieur
- MongoDB 4.4 ou supérieur
- (Optionnel) Node.js et npm si vous souhaitez builder des assets frontend spécifiques

## Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/med-ta9i/stage
   cd stage
   ```

2. **Créer et activer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OU
   .\venv\Scripts\activate  # Windows
   ```

3. **Installer les dépendances Python**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**
   Créez un fichier `.env` à la racine du projet avec les configurations suivantes :
   ```env
   DEBUG=True
   SECRET_KEY=your_secure_django_secret
   # Configuration MongoDB (utilisée via PyMongo pour les données métier)
   DB_NAME=dem_dashboard
   DB_HOST=localhost
   DB_PORT=27017
   ```

5. **Initialiser la base Django (auth/admin/sessions via SQLite)**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **(Optionnel) Importer des données**
   Des scripts d’import existent dans `scripts/`. Exemple :
   ```bash
   python scripts/import_data.py
   ```

7. **Démarrer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

8. **Accéder à l'application**
   - Interface principale : http://localhost:8000/
   - Interface d'administration : http://localhost:8000/admin/
   - Statistiques admin (staff) : http://localhost:8000/admin/equipment-stats/
   - Documentation de l'API : http://localhost:8000/api/docs/ (Swagger) et http://localhost:8000/api/redoc/

## Architecture et stockage des données

- **Django (admin/auth/sessions)** : utilise SQLite (fichier `db.sqlite3`) pour les fonctionnalités internes du framework.
- **Données métier (équipements, localisations, etc.)** : stockées dans **MongoDB** et accédées via **PyMongo** (pas d’ORM Django).

## Structure du projet

```
dem_dashboard/
├── dashboard/                 # Application principale
│   ├── static/               # Fichiers statiques (CSS, JS, images)
│   ├── templates/            # Templates HTML
│   ├── admin.py              # Configuration de l'interface d'administration
│   ├── api.py                # Logique d’accès aux données équipements
│   ├── db.py                 # Connexion à MongoDB (PyMongo)
│   ├── urls.py               # URLs de l'application
│   └── views.py              # Vues (templates + API/exports)
├── dem_dashboard/            # Configuration du projet
│   ├── settings.py           # Paramètres du projet
│   └── urls.py               # URLs du projet
├── scripts/                  # Scripts utilitaires (imports, maintenance)
├── manage.py
├── README.md
└── requirements.txt          # Dépendances Python
```

## API Endpoints (extraits)

- `GET /api/equipments/` — Liste paginée des équipements avec filtres
- `GET /api/equipments/export/csv/` — Export CSV avec filtres
- `GET /api/equipments/export/excel/` — Export Excel avec filtres
- Analytics:
  - `GET /api/analytics/status-distribution/`
  - `GET /api/analytics/evolution/`
  - `GET /api/analytics/locations/`

### Filtres disponibles (liste non exhaustive)

- `model`, `status`, `location`, `search`
- `creation_date_gte` (YYYY-MM-DD)
- `creation_date_lte` (YYYY-MM-DD)

## Développement

### Exemple de document `equipment`
```javascript
{
  "_id": ObjectId("..."),
  "model": "...",
  "serial": "...",
  "barcode": "...",
  "status": "En stock | En service | Maintenance | Hors service",
  "location": "...",
  "purchase_value": 999.99,
  "creation_date": ISODate("2023-01-01T00:00:00Z"),
  "updated_at": ISODate("2023-01-01T00:00:00Z")
}
```

### Commandes utiles

- **Tests**
  ```bash
  python manage.py test
  ```
- **Créer un superutilisateur**
  ```bash
  python manage.py createsuperuser
  ```
- **Collecter les fichiers statiques** (prod)
  ```bash
  python manage.py collectstatic
  ```

## Notes sur les exports

- L’export Excel utilise `pandas`. Pour de meilleures performances/compatibilité, installez également `XlsxWriter` (ou `openpyxl`).
  ```bash
  pip install XlsxWriter
  ```

## Déploiement

Pour le déploiement en production :

1. **Serveur WSGI** : Gunicorn ou uWSGI
2. **Serveur Web** : Nginx ou Apache
3. **Base de données** : MongoDB en réplication pour la haute disponibilité

### Variables d'environnement de production (exemple)

```env
DEBUG=False
SECRET_KEY=votre_secret_key_tres_long_et_securise
DB_NAME=dem_dashboard
DB_HOST=localhost
DB_PORT=27017
ALLOWED_HOSTS=.votredomaine.com,localhost,127.0.0.1
```

## Auteur

- M'hamed Taki - taki.mhamed.taki@gmail.com

## Remerciements

- L'équipe du magasin DEM pour leur confiance
- Les contributeurs des bibliothèques open source utilisées
