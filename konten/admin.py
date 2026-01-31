from django.contrib import admin
from .models import Konten, TugasKonten, KategoriKonten

class TugasKontenInline(admin.TabularInline):
    model = TugasKonten
    extra = 5  # Menampilkan 5 baris kosong default

@admin.register(KategoriKonten)
class KategoriKontenAdmin(admin.ModelAdmin):
    list_display = ('nama', 'deskripsi')
    search_fields = ('nama',)

@admin.register(Konten)
class KontenAdmin(admin.ModelAdmin):
    list_display = ('judul', 'platform', 'kategori', 'tanggal_upload', 'uploader')
    list_filter = ('platform', 'kategori', 'tanggal_upload')
    search_fields = ('judul', 'link_konten')
    ordering = ('-tanggal_upload',)
    inlines = [TugasKontenInline]

@admin.register(TugasKonten)
class TugasKontenAdmin(admin.ModelAdmin):
    list_display = ('konten', 'is_like', 'is_komen', 'is_share', 'tanggal_mulai', 'tanggal_selesai')
    list_filter = ('is_like', 'is_komen', 'is_share', 'tanggal_selesai')
    search_fields = ('konten__judul', 'instruksi')
    ordering = ('-tanggal_selesai',)

from .models import Profile, AkunMedsos, RiwayatMisi

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'nama_lengkap', 'nik', 'nomor_hp', 'biodata_lengkap', 'tanggal_update')
    list_filter = ('role', 'biodata_lengkap', 'jenis_kelamin')
    search_fields = ('user__username', 'nama_lengkap', 'nik', 'nomor_hp')
    readonly_fields = ('tanggal_update', 'biodata_lengkap')
    
    fieldsets = (
        ('Informasi User', {
            'fields': ('user', 'role', 'commander')
        }),
        ('Biodata Pribadi', {
            'fields': ('nik', 'nama_lengkap', 'tempat_lahir', 'tanggal_lahir', 'jenis_kelamin')
        }),
        ('Kontak', {
            'fields': ('alamat_lengkap', 'nomor_hp')
        }),
        ('Dokumen', {
            'fields': ('foto_ktp',)
        }),
        ('Status', {
            'fields': ('biodata_lengkap', 'tanggal_update')
        }),
    )

@admin.register(AkunMedsos)
class AkunMedsosAdmin(admin.ModelAdmin):
    list_display = ('username', 'platform', 'owner', 'role_pemegang', 'status', 'tanggal_daftar')
    list_filter = ('platform', 'status', 'role_pemegang')
    search_fields = ('username', 'owner__username')
    ordering = ('-tanggal_daftar',)

@admin.register(RiwayatMisi)
class RiwayatMisiAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_misi_judul', 'akun_digunakan', 'poin_didapat', 'tanggal_selesai')
    list_filter = ('user', 'tugas', 'tanggal_selesai')
    search_fields = ('user__username', 'tugas__konten__judul', 'akun_digunakan__username')
    readonly_fields = ('tanggal_selesai',)

    def get_misi_judul(self, obj):
        return obj.tugas.konten.judul
    get_misi_judul.short_description = 'Judul Misi'
