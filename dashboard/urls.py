from django.urls import path
from django.views.generic import TemplateView
from . import views
from .views import (
    EquipmentDetailView, 
    EquipmentEditView,
    EquipmentDeleteView
)
from .views_analytics import (
    EquipmentStatusDistributionView,
    EquipmentEvolutionView,
    EquipmentLocationView
)
from .views_locations import (
    LocationTemplateView,
    LocationListView,
    LocationDetailView,
    LocationEditView,
    LocationDeleteView,
    location_statistics,
    locations_map_data
)

urlpatterns = [
    # Page d'accueil du tableau de bord
    path('', views.DashboardView.as_view(), name='dashboard-home'),
    
    # Vues pour le menu latéral
    path('equipements/', TemplateView.as_view(template_name='dashboard/equipment_list.html'), name='equipment-list'),
    path('equipements/ajouter/', EquipmentEditView.as_view(), name='equipment-add'),
    path('equipements/<str:pk>/', EquipmentDetailView.as_view(), name='equipment-detail'),
    path('equipements/<str:pk>/modifier/', EquipmentEditView.as_view(), name='equipment-edit'),
    path('equipements/<str:pk>/supprimer/', EquipmentDeleteView.as_view(), name='equipment-delete'),
    path('localisations/', LocationTemplateView.as_view(), name='location-list'),
    path('localisations/ajouter/', LocationEditView.as_view(), name='location-add'),
    path('localisations/<str:pk>/', LocationDetailView.as_view(), name='location-detail'),
    path('localisations/<str:pk>/modifier/', LocationEditView.as_view(), name='location-edit'),
    path('localisations/<str:pk>/supprimer/', LocationDeleteView.as_view(), name='location-delete'),
    path('rapports/', TemplateView.as_view(template_name='dashboard/reports.html'), name='reports'),
    # path('admin-app/', TemplateView.as_view(template_name='dashboard/admin_home.html'), name='admin-app'),
    
    # API Endpoints
    path('api/equipments/', views.EquipmentListView.as_view(), name='api-equipment-list'),
    path('api/equipments/<str:pk>/', views.EquipmentDetailView.as_view(), name='api-equipment-detail'),
    path('api/equipments/<str:equipment_id>/<str:relation_type>/', 
         views.equipment_relations, name='api-equipment-relations'),
    path('api/equipments/export/csv/', views.export_equipments_csv, name='api-equipment-export-csv'),
    path('api/equipments/export/excel/', views.export_equipments_excel, name='api-equipment-export-excel'),
    # path('api/admin/overview/', views.admin_overview, name='api-admin-overview'),
    
    # API Locations (mettre les routes spécifiques AVANT la route générique <pk>)
    path('api/locations/stats/', location_statistics, name='api-location-stats'),
    path('api/locations/map-data/', locations_map_data, name='api-location-map-data'),
    path('api/locations/', LocationListView.as_view(), name='api-location-list'),
    path('api/locations/<str:pk>/', LocationDetailView.as_view(), name='api-location-detail'),
    
    # API Analytics
    path('api/analytics/status-distribution/', 
         EquipmentStatusDistributionView.as_view(), 
         name='api-status-distribution'),
    path('api/analytics/evolution/', 
         EquipmentEvolutionView.as_view(), 
         name='api-evolution'),
    path('api/analytics/locations/', 
         EquipmentLocationView.as_view(), 
         name='api-locations'),
    
    # Service des fichiers statiques en développement
    path('static/<path:path>', views.serve_static_dev, name='serve-static-dev'),
]
