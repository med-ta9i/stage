from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from .api_locations import (
    get_locations, get_location, get_location_by_site_id, 
    create_location, update_location, delete_location,
    get_locations_statistics, get_locations_for_map
)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class LocationListView(APIView):
    """
    Vue API pour lister et filtrer les localisations
    """
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        # Récupération des paramètres de requête
        filters = {}
        
        # Filtres de base
        for param in ['site_name', 'province', 'region', 'category', 'snrt_rs']:
            if param in request.query_params:
                filters[param] = request.query_params.get(param)
        
        # Filtres de services
        services_filters = {}
        for service in ['tnt', 'fm', 'am', 'administration']:
            if f'service_{service}' in request.query_params:
                value = request.query_params.get(f'service_{service}')
                if value.lower() in ['true', 'false']:
                    services_filters[service] = value.lower() == 'true'
        
        if services_filters:
            filters['services'] = services_filters
        
        # Gestion du groupement
        group_by = request.query_params.get('group_by')
        
        # Si group_by est spécifié, on ignore la pagination et le tri
        if group_by:
            result = get_locations(
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
        result = get_locations(
            filters=filters,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_order=sort_order
        )
        
        return Response(result)

class LocationDetailView(APIView):
    """
    Vue API pour récupérer une localisation spécifique
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        location = get_location(pk)
        if not location:
            return Response(
                {'error': 'Localisation non trouvée'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(location)

class LocationTemplateView(TemplateView):
    """
    Vue pour afficher la page de gestion des localisations
    """
    template_name = 'dashboard/location_list.html'
    
    def get_context_data(self, **kwargs):
        import time
        context = super().get_context_data(**kwargs)
        # Ajouter une version unique pour le cache-busting des fichiers statiques
        context['static_version'] = int(time.time())
        # Ajouter des données de contexte supplémentaires si nécessaire
        context['debug'] = settings.DEBUG
        return context

@api_view(['GET'])
def location_statistics(request):
    """
    Vue API pour les statistiques des localisations
    """
    stats = get_locations_statistics()
    return Response(stats)

@api_view(['GET'])
def locations_map_data(request):
    """
    Vue API pour récupérer les données des localisations pour la carte
    """
    map_data = get_locations_for_map()
    return Response(map_data)

class LocationEditView(TemplateView):
    """
    Vue pour ajouter ou modifier une localisation
    """
    template_name = 'dashboard/location_edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location_id = self.kwargs.get('pk')
        
        # Initialiser une localisation vide par défaut
        location = {}
        
        # Si c'est une modification, récupérer les données de la localisation
        if location_id and location_id != 'ajouter':
            location = get_location(location_id)
            if not location:
                raise Http404("La localisation demandée n'existe pas.")
        
        # Formater les données pour le template
        context['location'] = {
            '_id': str(location.get('_id', '')),
            'site_name': location.get('site_name', ''),
            'province': location.get('province', ''),
            'region': location.get('region', ''),
            'category': location.get('category', 'P'),
            'snrt_rs': location.get('snrt_rs', ''),
            'coordinates': location.get('coordinates', {}),
            'services': location.get('services', {}),
            'contact': location.get('contact', {}),
            'config_user': location.get('config_user', ''),
            'code': location.get('code', ''),
            'photo': location.get('photo', ''),
            'control': location.get('control', False)
        }
        
        # Listes pour les menus déroulants
        context['regions'] = self.get_regions()
        context['categories'] = self.get_categories()
        
        return context
    
    def get_regions(self):
        """Récupérer la liste des régions"""
        return [
            "Tanger-Tétouan-Al Hoceima", "L'Oriental", "Fès-Meknès",
            "Rabat-Salé-Kénitra", "Beni Mellal-Khénifra", "Grand Casablanca-Settat",
            "Marrakech-Safi", "Darâa-Tafilalet", "Sous-Massa",
            "Guelmim-Oued Noun", "Laâyoune-Saguia El Hamra", "Dakhla-Oued Ed Dahab"
        ]
    
    def get_categories(self):
        """Récupérer la liste des catégories"""
        return [
            {"value": "P", "label": "Principal"},
            {"value": "M", "label": "Moyen"},
            {"value": "G", "label": "Grand"},
            {"value": "A", "label": "Administratif"}
        ]
    
    def post(self, request, *args, **kwargs):
        """Gérer la soumission du formulaire d'ajout/modification"""
        location_id = self.kwargs.get('pk')
        is_edit = location_id and location_id != 'ajouter'
        data = request.POST.dict()
        
        # Nettoyer les données
        if 'csrfmiddlewaretoken' in data:
            del data['csrfmiddlewaretoken']
        
        # Structurer les données
        location_data = {
            'site_name': data.get('site_name', ''),
            'province': data.get('province', ''),
            'region': data.get('region', ''),
            'category': data.get('category', 'P'),
            'snrt_rs': data.get('snrt_rs', ''),
            'config_user': data.get('config_user', ''),
            'code': data.get('code', ''),
            'photo': data.get('photo', ''),
            'control': data.get('control') == 'on',
            
            # Coordonnées
            'coordinates': {
                'latitude': float(data.get('latitude', 0)) if data.get('latitude') else None,
                'longitude': float(data.get('longitude', 0)) if data.get('longitude') else None,
                'altitude': float(data.get('altitude', 0)) if data.get('altitude') else None
            },
            
            # Services
            'services': {
                'tnt': data.get('service_tnt') == 'on',
                'fm': data.get('service_fm') == 'on',
                'am': data.get('service_am') == 'on',
                'administration': data.get('service_administration') == 'on',
                'fh': data.get('service_fh') == 'on',
                'st': data.get('service_st') == 'on'
            },
            
            # Contact
            'contact': {
                'fixe': data.get('contact_fixe', ''),
                'gsm': data.get('contact_gsm', '')
            }
        }
        
        # Nettoyer les coordonnées si toutes sont nulles
        coords = location_data['coordinates']
        if not any([coords['latitude'], coords['longitude'], coords['altitude']]):
            location_data['coordinates'] = None
        
        # Ajouter les métadonnées de l'utilisateur
        if request.user.is_authenticated:
            location_data['updated_by'] = request.user.username
            if not is_edit:  # Nouvelle localisation
                location_data['created_by'] = request.user.username
        
        # Gérer l'ajout ou la mise à jour
        if is_edit:
            # Mise à jour d'une localisation existante
            success, response = update_location(location_id, location_data)
            success_message = "La localisation a été mise à jour avec succès."
            error_message = f"Une erreur est survenue lors de la mise à jour de la localisation: {response.get('error', 'Erreur inconnue')}"
            redirect_view = 'location-detail'
        else:
            # Création d'une nouvelle localisation
            success, response = create_location(location_data)
            success_message = "La localisation a été créée avec succès."
            error_message = f"Une erreur est survenue lors de la création de la localisation: {response.get('error', 'Erreur inconnue')}"
            redirect_view = 'location-list'
        
        # Gérer la réponse
        if success:
            messages.success(request, success_message)
            if redirect_view == 'location-detail':
                return redirect(redirect_view, pk=location_id)
            else:
                return redirect(redirect_view)
        else:
            messages.error(request, error_message)
            return self.get(request, *args, **kwargs)

class LocationDeleteView(DeleteView):
    """
    Vue pour supprimer une localisation
    """
    template_name = 'dashboard/location_confirm_delete.html'
    success_url = reverse_lazy('location-list')
    
    def get_object(self):
        location_id = self.kwargs.get('pk')
        location = get_location(location_id)
        if not location:
            raise Http404("La localisation demandée n'existe pas.")
        return location
    
    def delete(self, request, *args, **kwargs):
        location = self.get_object()
        location_id = str(location.get('_id', ''))
        
        # Supprimer la localisation via l'API
        success, response = delete_location(location_id)
        
        if success:
            messages.success(request, "La localisation a été supprimée avec succès.")
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(
                request, 
                f"Une erreur est survenue lors de la suppression de la localisation: {response.get('error', 'Erreur inconnue')}"
            )
            return redirect('location-detail', pk=location_id)
