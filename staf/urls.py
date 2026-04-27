from django.urls import path
from . import views

urlpatterns = [
    # Fitur 9 - Kelola Klaim Missing Miles (Staf)
    path('kelola-klaim/', views.klaim_list_staf, name='kelola_klaim'),
    path('kelola-klaim/<int:id>/proses/', views.klaim_proses, name='klaim_proses'),
    path('laporan/', views.laporan_transaksi, name='laporan_transaksi'),
    path('laporan/hapus/', views.laporan_transaksi_hapus, name='laporan_transaksi_hapus'),
]
