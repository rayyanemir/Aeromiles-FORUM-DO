from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('pengaturan_profil/', views.pengaturan_profil_view, name='pengaturan_profil'),
]
