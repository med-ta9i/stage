from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
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

urlpatterns = [
    # Page d'accueil du tableau de bord
    path('', views.DashboardView.as_view(), name='dashboard-home'),
    
    # Vues pour le menu latéral
    path('equipements/', TemplateView.as_view(template_name='dashboard/equipment_list.html'), name='equipment-list'),
    path('equipements/ajouter/', EquipmentEditView.as_view(), name='equipment-add'),
    path('equipements/<str:pk>/', EquipmentDetailView.as_view(), name='equipment-detail'),
    path('equipements/<str:pk>/modifier/', EquipmentEditView.as_view(), name='equipment-edit'),
    path('equipements/<str:pk>/supprimer/', EquipmentDeleteView.as_view(), name='equipment-delete'),
    path('localisations/', TemplateView.as_view(template_name='dashboard/location_list.html'), name='location-list'),
    path('rapports/', TemplateView.as_view(template_name='dashboard/reports.html'), name='reports'),
    
    # API Endpoints
    path('api/equipments/', views.EquipmentListView.as_view(), name='api-equipment-list'),
    path('api/equipments/<str:pk>/', views.EquipmentDetailView.as_view(), name='api-equipment-detail'),
    path('api/equipments/<str:equipment_id>/<str:relation_type>/', 
         views.equipment_relations, name='api-equipment-relations'),
    
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
