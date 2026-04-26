from django.urls import path
from . import views

urlpatterns = [
    # Fitur 8 - Claim Missing Miles
    path('klaim/', views.klaim_list, name='klaim_list'),
    path('klaim/buat/', views.klaim_buat, name='klaim_buat'),
    path('klaim/edit/<int:id>/', views.klaim_edit, name='klaim_edit'),
    path('klaim/hapus/<int:id>/', views.klaim_hapus, name='klaim_hapus'),

    # Fitur 10 - Transfer Miles
    path('transfer/', views.transfer_list, name='transfer_list'),
    path('transfer/buat/', views.transfer_buat, name='transfer_buat'),
]
