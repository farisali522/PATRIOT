from django.contrib import admin
from .models import Konten, TugasKonten

class TugasKontenInline(admin.TabularInline):
    model = TugasKonten
    extra = 5  # Menampilkan 5 baris kosong default

@admin.register(Konten)
class KontenAdmin(admin.ModelAdmin):
    list_display = ('judul', 'platform', 'tanggal_upload', 'uploader')
    list_filter = ('platform', 'tanggal_upload')
    search_fields = ('judul', 'link_konten')
    ordering = ('-tanggal_upload',)
    inlines = [TugasKontenInline]

@admin.register(TugasKonten)
class TugasKontenAdmin(admin.ModelAdmin):
    list_display = ('konten', 'is_like', 'is_komen', 'is_share', 'tanggal_mulai', 'tanggal_selesai')
    list_filter = ('is_like', 'is_komen', 'is_share', 'tanggal_selesai')
    search_fields = ('konten__judul', 'instruksi')
    ordering = ('-tanggal_selesai',)

from .models import Profile, AkunMedsos

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'commander')
    list_filter = ('role',)
    search_fields = ('user__username', 'commander__username')

@admin.register(AkunMedsos)
class AkunMedsosAdmin(admin.ModelAdmin):
    list_display = ('username', 'platform', 'owner', 'role_pemegang', 'status', 'tanggal_daftar')
    list_filter = ('platform', 'status', 'role_pemegang')
    search_fields = ('username', 'owner__username')
    ordering = ('-tanggal_daftar',)
