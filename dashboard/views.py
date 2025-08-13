from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect
from django.utils.http import http_date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from .api import get_equipments, get_equipment, get_equipment_relations, update_equipment, delete_equipment

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class EquipmentListView(APIView):
    """
    Vue pour lister et filtrer les équipements
    """
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        # Récupération des paramètres de requête
        filters = {}
        
        # Filtres de base
        for param in ['model', 'serial', 'barcode', 'status', 'location']:
            if param in request.query_params:
                filters[param] = request.query_params.get(param)
        
        # Filtres de date
        date_filters = {}
        for param in ['creation_date', 'dms']:
            if f'{param}_gte' in request.query_params:
                if 'date' not in date_filters:
                    date_filters[param] = {}
                date_filters[param]['gte'] = request.query_params.get(f'{param}_gte')
            if f'{param}_lte' in request.query_params:
                if param not in date_filters:
                    date_filters[param] = {}
                date_filters[param]['lte'] = request.query_params.get(f'{param}_lte')
        
        filters.update(date_filters)
        
        # Gestion du groupement
        group_by = request.query_params.get('group_by')
        
        # Si group_by est spécifié, on ignore la pagination et le tri
        if group_by:
            result = get_equipments(
                filters=filters,
                group_by=group_by
            )
            return Response(result)
        
        # Sinon, on applique la pagination et le tri
        try:
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)
        except (TypeError, ValueError):
            page = 1
            page_size = 20
        
        sort_field = request.query_params.get('sort', None)
        sort_order = -1 if request.query_params.get('order', 'desc').lower() == 'desc' else 1
        
        # Récupération des données avec pagination
        result = get_equipments(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_order=sort_order
        )
        
        return Response(result)

class EquipmentEditView(TemplateView):
    """
    Vue pour ajouter ou modifier un équipement
    """
    template_name = 'dashboard/equipment_edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_id = self.kwargs.get('pk')
        
        # Initialiser un équipement vide par défaut
        equipment = {}
        
        # Si c'est une modification, récupérer les données de l'équipement
        if equipment_id and equipment_id != 'ajouter':
            equipment = get_equipment(equipment_id)
            if not equipment:
                raise Http404("L'équipement demandé n'existe pas.")
        
        # Formater les données pour le template
        context['equipment'] = {
            '_id': str(equipment.get('_id', '')),
            'model': equipment.get('model', ''),
            'brand': equipment.get('brand', ''),
            'serial': equipment.get('serial', ''),
            'barcode': equipment.get('barcode', ''),
            'status': equipment.get('status', 'En stock'),
            'location': equipment.get('location', ''),
            'family': equipment.get('family', ''),
            'subfamily': equipment.get('subfamily', ''),
            'inventory_number': equipment.get('inventory_number', ''),
            'purchase_value': equipment.get('purchase_value', 0),
            'notes': equipment.get('notes', ''),
            'creation_date': equipment.get('creation_date', ''),
            'updated_at': equipment.get('updated_at', ''),
            'created_by': equipment.get('created_by', self.request.user.username if self.request.user.is_authenticated else 'Système'),
            'updated_by': equipment.get('updated_by', self.request.user.username if self.request.user.is_authenticated else 'Inconnu')
        }
        
        # Ajouter les listes pour les menus déroulants
        context['families'] = self.get_families()
        context['subfamilies'] = self.get_subfamilies()
        
        return context
    
    def get_families(self):
        """Récupérer la liste des familles depuis l'API"""
        # À implémenter : appeler l'API pour récupérer les familles
        # Pour l'instant, on retourne une liste statique
        return ["Informatique", "Réseau", "Périphériques", "Mobilier", "Autre"]
    
    def get_subfamilies(self):
        """Récupérer la liste des sous-familles depuis l'API"""
        # À implémenter : appeler l'API pour récupérer les sous-familles
        # Pour l'instant, on retourne une liste statique
        return [
            "Ordinateur portable", "Ordinateur de bureau", "Tablette", "Smartphone",
            "Routeur", "Switch", "Point d'accès", "Modem",
            "Écran", "Clavier", "Souris", "Imprimante"
        ]
    
    def post(self, request, *args, **kwargs):
        """Gérer la soumission du formulaire d'ajout/modification"""
        equipment_id = self.kwargs.get('pk')
        is_edit = equipment_id and equipment_id != 'ajouter'
        data = request.POST.dict()
        
        # Nettoyer les données
        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']
        
        # Convertir les champs numériques
        if 'purchase_value' in data and data['purchase_value']:
            try:
                data['purchase_value'] = float(data['purchase_value'])
            except (ValueError, TypeError):
                data['purchase_value'] = 0.0
        
        # Ajouter les métadonnées de l'utilisateur
        if request.user.is_authenticated:
            data['updated_by'] = request.user.username
            if not is_edit:  # Nouvel équipement
                data['created_by'] = request.user.username
        
        # Gérer l'ajout ou la mise à jour
        if is_edit:
            # Mise à jour d'un équipement existant
            success, response = update_equipment(equipment_id, data)
            success_message = "L'équipement a été mis à jour avec succès."
            error_message = f"Une erreur est survenue lors de la mise à jour de l'équipement: {{error}}"
            redirect_view = 'equipment-detail'
        else:
            # Création d'un nouvel équipement
            success, response = create_equipment(data)
            success_message = "L'équipement a été créé avec succès."
            error_message = f"Une erreur est survenue lors de la création de l'équipement: {{error}}"
            redirect_view = 'equipment-list'
        
        # Gérer la réponse
        if success:
            messages.success(request, success_message)
            if redirect_view == 'equipment-detail':
                return redirect(redirect_view, pk=equipment_id)
            else:
                return redirect(redirect_view)
        else:
            messages.error(
                request, 
                error_message.format(error=response.get('error', 'Erreur inconnue'))
            )
            return self.get(request, *args, **kwargs)


class EquipmentDeleteView(DeleteView):
    """
    Vue pour supprimer un équipement
    """
    template_name = 'dashboard/equipment_confirm_delete.html'
    success_url = reverse_lazy('equipment-list')
    
    def get_object(self):
        equipment_id = self.kwargs.get('pk')
        equipment = get_equipment(equipment_id)
        if not equipment:
            raise Http404("L'équipement demandé n'existe pas.")
        return equipment
    
    def delete(self, request, *args, **kwargs):
        equipment = self.get_object()
        equipment_id = str(equipment.get('_id', ''))
        
        # Supprimer l'équipement via l'API
        success, response = delete_equipment(equipment_id)
        
        if success:
            messages.success(request, "L'équipement a été supprimé avec succès.")
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(
                request, 
                f"Une erreur est survenue lors de la suppression de l'équipement: {response.get('error', 'Erreur inconnue')}"
            )
            return redirect('equipment-detail', pk=equipment_id)


class EquipmentDetailView(TemplateView):
    """
    Vue pour afficher la page de détail d'un équipement
    """
    template_name = 'dashboard/equipment_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipment_id = self.kwargs.get('pk')
        
        # Récupérer les données de l'équipement depuis l'API
        equipment = get_equipment(equipment_id)
        
        if not equipment:
            raise Http404("L'équipement demandé n'existe pas.")
        
        # Formater les données pour le template
        context['equipment'] = {
            '_id': str(equipment.get('_id', '')),
            'model': equipment.get('model', ''),
            'brand': equipment.get('brand', ''),
            'serial': equipment.get('serial', ''),
            'barcode': equipment.get('barcode', ''),
            'status': equipment.get('status', 'Inconnu'),
            'location': equipment.get('location', 'Non spécifiée'),
            'family': equipment.get('family', ''),
            'subfamily': equipment.get('subfamily', ''),
            'inventory_number': equipment.get('inventory_number', ''),
            'purchase_value': f"{equipment.get('purchase_value', 0):,.2f}",
            'notes': equipment.get('notes', ''),
            'creation_date': equipment.get('creation_date', ''),
            'updated_at': equipment.get('updated_at', '')
        }
        
        # Ajouter des données supplémentaires pour l'historique (exemple)
        context['history'] = [
            {
                'title': 'Modification du statut',
                'date': 'Il y a 2 jours',
                'description': 'Statut changé de "En stock" à "En service"',
                'user': 'Admin'
            },
            {
                'title': 'Mise à jour des informations',
                'date': 'Il y a 1 semaine',
                'description': 'Localisation mise à jour',
                'user': 'Technicien'
            }
        ]
        
        return context

@api_view(['GET'])
def equipment_relations(request, equipment_id, relation_type):
    """
    Vue pour les relations d'un équipement (designations, families, etc.)
    """
    if relation_type not in ['designations', 'families', 'locations', 'subfamilies']:
        return Response(
            {'error': 'Type de relation non valide'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    relations = get_equipment_relations(equipment_id, relation_type)
    return Response(relations)


class DashboardView(TemplateView):
    """
    Vue principale du tableau de bord
    """
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        import time
        context = super().get_context_data(**kwargs)
        # Ajouter une version unique pour le cache-busting des fichiers statiques
        context['static_version'] = int(time.time())
        # Ajouter des données de contexte supplémentaires si nécessaire
        context['debug'] = settings.DEBUG
        return context


def serve_static_dev(request, path):
    """
    Vue pour servir les fichiers statiques en mode développement
    """
    if settings.DEBUG:
        import os
        from django.views.static import serve
        from django.http import HttpResponse, HttpResponseNotFound
        
        # Chemin vers le dossier static de l'application
        static_dir = os.path.join(settings.BASE_DIR, 'dashboard', 'static')
        file_path = os.path.join(static_dir, path)
        
        # Vérifier si le fichier existe dans le dossier static de l'application
        if os.path.exists(file_path):
            # Définir les types MIME appropriés
            mime_types = {
                '.css': 'text/css',
                '.js': 'application/javascript',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.woff': 'application/font-woff',
                '.woff2': 'application/font-woff2',
                '.ttf': 'application/font-ttf',
                '.eot': 'application/vnd.ms-fontobject',
            }
            
            # Déterminer le type MIME en fonction de l'extension du fichier
            ext = os.path.splitext(path)[1].lower()
            content_type = mime_types.get(ext, 'application/octet-stream')
            
            # Lire le contenu du fichier
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Créer une réponse avec le bon type MIME
                response = HttpResponse(content, content_type=content_type)
                
                # Ajouter des en-têtes pour empêcher la mise en cache
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                # Ajouter un en-tête Last-Modified pour le cache navigateur
                stat = os.stat(file_path)
                response['Last-Modified'] = http_date(stat.st_mtime)
                
                return response
                
            except (IOError, OSError):
                pass
    
    # Retourner une réponse 404 si le fichier n'existe pas ou en cas d'erreur
    return HttpResponseNotFound('Fichier non trouvé')
    raise Http404("Le fichier demandé n'existe pas.")
