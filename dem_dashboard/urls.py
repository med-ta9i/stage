"""
URL configuration for dem_dashboard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.admin.views.decorators import staff_member_required
from dashboard.views import EquipmentStatsAdminView

# Configuration de la documentation de l'API avec Swagger/OpenAPI
schema_view = get_schema_view(
   openapi.Info(
      title="API du Tableau de Bord DEM",
      default_version='v1',
      description="API pour la gestion des équipements du magasin DEM",
      terms_of_service="https://www.example.com/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Page d'accueil du tableau de bord
    path('', include('dashboard.urls')),
    
    # Interface d'administration Django
    path('admin/', admin.site.urls),
    path('admin/equipment-stats/', staff_member_required(EquipmentStatsAdminView.as_view()), name='admin-equipment-stats'),
    
    # API endpoints et documentation
    path('api/', include([
        path('', include('dashboard.urls')),  # Inclure les URLs de l'API sous /api/
        path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ])),
]
