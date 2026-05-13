from django.urls import path
from . import views

urlpatterns = [
    path('identitas/',                      views.identitas_list,   name='identitas_list'),
    path('identitas/tambah/',               views.identitas_tambah, name='identitas_tambah'),
    path('identitas/<str:nomor>/edit/',     views.identitas_edit,   name='identitas_edit'),
    path('identitas/<str:nomor>/hapus/',    views.identitas_hapus,  name='identitas_hapus'),

    path('klaim/', views.klaim_list, name='klaim_list'),
    path('klaim/buat/', views.klaim_buat, name='klaim_buat'),
    path('klaim/edit/<int:id>/', views.klaim_edit, name='klaim_edit'),
    path('klaim/hapus/<int:id>/', views.klaim_hapus, name='klaim_hapus'),

    path('redeem/', views.redeem_list, name='redeem_list'),
    path('redeem/<str:kode_hadiah>/', views.redeem_buat, name='redeem_buat'),

    path('package/', views.package_list, name='package_list'),
    path('package/<str:package_id>/', views.package_beli, name='package_beli'),

    path('tier/', views.tier_info, name='tier_info'),

    path('transfer/', views.transfer_list, name='transfer_list'),
    path('transfer/buat/', views.transfer_buat, name='transfer_buat'),
]
