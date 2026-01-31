from django.contrib import admin
from core import admin_config
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from konten.views import landing_page, login_page
from konten import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing'),
    path('login/', login_page, name='login'),
    path('dashboard/', views.dashboard_uploader, name='dashboard_uploader'),
    path('konten/', views.daftar_konten, name='daftar_konten'),
    path('konten/tambah/', views.tambah_konten, name='tambah_konten'),
    path('konten/tugas/tambah/<int:konten_id>/', views.tambah_tugas, name='tambah_tugas'),
    path('tugas/', views.daftar_tugas, name='daftar_tugas'),
    path('switch-role/<str:role_name>/', views.switch_role, name='switch_role'),
    path('manajemen-akun-medsos/', views.manajemen_akun_medsos, name='akun_medsos'),
    path('monitoring-akun-kader/', views.monitoring_akun_kader, name='monitoring_akun_kader'),
    path('verifikasi-akun/', views.verifikasi_akun_medsos, name='verifikasi_akun'),
    path('verifikasi-akun/proses/<int:akun_id>/<str:action>/', views.proses_verifikasi_akun, name='proses_verifikasi_akun'),
    path('sop/', views.sop_view, name='sop'),
    path('akun-medsos-kader/', views.akun_medsos_kader, name='akun_medsos_kader'),
    path('biodata-kader/', views.biodata_kader, name='biodata_kader'),
    path('misi/', views.misi_kader, name='misi_kader'),
    path('misi/konfirmasi/<int:tugas_id>/', views.konfirmasi_misi, name='konfirmasi_misi'),
    path('edit-akun-medsos/<int:akun_id>/', views.edit_akun_medsos, name='edit_akun_medsos'),
    path('verifikasi-laporan/', views.verifikasi_laporan_misi, name='verifikasi_laporan'),
    path('verifikasi-laporan/proses/<int:riwayat_id>/<str:action>/', views.proses_verifikasi_laporan, name='proses_verifikasi_laporan'),
    path('password/', views.ubah_password, name='ubah_password'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
