from django.urls import path
from . import views

urlpatterns = [
    # Fitur 6 – CRUD Manajemen Data Member (Staf)
    path('kelola-member/',                  views.member_list,   name='member_list_staf'),
    path('kelola-member/tambah/',           views.member_tambah, name='member_tambah'),
    path('kelola-member/<str:email>/edit/', views.member_edit,   name='member_edit'),
    path('kelola-member/<str:email>/hapus/',views.member_hapus,  name='member_hapus'),

    # Fitur 9 - Kelola Klaim Missing Miles (Staf)
    path('kelola-klaim/', views.klaim_list_staf, name='kelola_klaim'),
    path('kelola-klaim/<int:id>/proses/', views.klaim_proses, name='klaim_proses'),
    path('laporan/', views.laporan_transaksi, name='laporan_transaksi'),
    path('laporan/hapus/', views.laporan_transaksi_hapus, name='laporan_transaksi_hapus'),

]
