from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os

class Profile(models.Model):
    ROLE_CHOICES = [
        ('DCO', 'Digital Command Officer'),
        ('COMMANDER', 'Commander'),
        ('CADRE', 'Cadre'),
    ]
    
    GENDER_CHOICES = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
    ]
    
    # Relasi User
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CADRE')
    commander = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    # Biodata Lengkap
    nik = models.CharField(max_length=16, blank=True, null=True, verbose_name="NIK (KTP)")
    nama_lengkap = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nama Lengkap")
    tempat_lahir = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tempat Lahir")
    tanggal_lahir = models.DateField(blank=True, null=True, verbose_name="Tanggal Lahir")
    jenis_kelamin = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, verbose_name="Jenis Kelamin")
    alamat_lengkap = models.TextField(blank=True, null=True, verbose_name="Alamat Lengkap")
    nomor_hp = models.CharField(max_length=15, blank=True, null=True, verbose_name="Nomor HP/WA")
    
    # Upload KTP
    foto_ktp = models.ImageField(upload_to='ktp/', blank=True, null=True, verbose_name="Foto KTP")
    
    # Metadata
    biodata_lengkap = models.BooleanField(default=False, verbose_name="Biodata Sudah Lengkap")
    tanggal_update = models.DateTimeField(auto_now=True, verbose_name="Terakhir Diupdate")

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    @property
    def is_biodata_complete(self):
        """Check if all required biodata fields are filled"""
        return all([
            self.nik,
            self.nama_lengkap,
            self.tempat_lahir,
            self.tanggal_lahir,
            self.jenis_kelamin,
            self.alamat_lengkap,
            self.nomor_hp,
            self.foto_ktp
        ])

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    instance.profile.save()

class KategoriKonten(models.Model):
    nama = models.CharField(max_length=50, unique=True, verbose_name="Nama Kategori")
    deskripsi = models.TextField(blank=True, null=True, verbose_name="Keterangan")

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name = "Kategori Konten"
        verbose_name_plural = "Master Kategori"

class Konten(models.Model):
    PLATFORM_CHOICES = [
        ('INSTAGRAM', 'Instagram'),
        ('TIKTOK', 'TikTok'),
        ('TWITTER', 'Twitter / X'),
        ('FACEBOOK', 'Facebook'),
        ('YOUTUBE', 'YouTube'),
    ]

    judul = models.CharField(max_length=255, verbose_name="Judul Konten")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='INSTAGRAM', verbose_name="Platform")
    link_konten = models.URLField(max_length=500, unique=True, verbose_name="Link Konten")
    kategori = models.ForeignKey(KategoriKonten, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori Konten")
    deskripsi = models.TextField(blank=True, null=True, verbose_name="Deskripsi Konten")
    
    # Metadata Tambahan (Otomatis/Opsional)
    tanggal_upload = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Diinput Oleh")

    def __str__(self):
        return f"[{self.platform}] {self.judul}"

    @property
    def get_embed_url(self):
        url = self.link_konten.strip()
        
        if self.platform == 'INSTAGRAM':
            # Bersihkan query params & hash
            clean_url = url.split('?')[0].split('#')[0]
            
            # Normalisasi domain agar seragam
            if 'instagr.am' in clean_url:
                clean_url = clean_url.replace('instagr.am', 'www.instagram.com')
            
            if 'instagram.com' in clean_url:
                # Paksa HTTPS dan www agar endpoint lebih stabil
                if '://' in clean_url:
                    parts = clean_url.split('://')
                    clean_url = f"https://www.instagram.com/{parts[1].split('instagram.com/')[1]}" if 'instagram.com/' in parts[1] else clean_url
                else:
                    clean_url = f"https://www.instagram.com/{clean_url.split('instagram.com/')[1]}" if 'instagram.com/' in clean_url else clean_url
                
                # Pastikan tidak double www atau https
                clean_url = clean_url.replace('https://www.www.', 'https://www.')
                
                # Ganti /reels/ atau /reel/ jadi /p/
                clean_url = clean_url.replace('/reels/', '/p/').replace('/reel/', '/p/')
                
                if not clean_url.endswith('/'):
                    clean_url += '/'
                
                # Hanya post (p) atau IGTV (tv) yang bisa di-embed
                if '/p/' in clean_url or '/tv/' in clean_url:
                    if 'embed' not in clean_url:
                        return f"{clean_url}embed/captioned/"
            return clean_url
        
        elif self.platform == 'TIKTOK':
            # Support Berbagai Format TikTok (Mobile, Shortlink, Desktop)
            # Format: https://www.tiktok.com/@user/video/123456789
            # Format: https://vt.tiktok.com/ZS.../
            
            clean_url = url.split('?')[0].split('#')[0]
            if not clean_url.endswith('/'):
                clean_url += '/'

            if 'video/' in clean_url:
                try:
                    video_id = clean_url.split('video/')[1].split('/')[0]
                    return f"https://www.tiktok.com/embed/v2/{video_id}?lang=id-ID"
                except: pass
            
            # Jika link pendek/mobile, kita tidak bisa ambil ID dengan mudah tanpa request
            # Tapi kita return original agar iframe mencoba me-load (meski tiktok sering blokir shortlink di iframe)
            return clean_url
        
        return url

    class Meta:
        verbose_name = "Konten Digital"
        verbose_name_plural = "Daftar Konten"
        ordering = ['-tanggal_upload']

class TugasKonten(models.Model):
    konten = models.ForeignKey(Konten, on_delete=models.CASCADE, related_name='daftar_tugas')
    
    # Checkbox Tugas Multi-Select
    is_like = models.BooleanField(default=False, verbose_name="Like")
    is_komen = models.BooleanField(default=False, verbose_name="Komentar")
    is_share = models.BooleanField(default=False, verbose_name="Share")
    is_follow = models.BooleanField(default=False, verbose_name="Follow")
    is_reply = models.BooleanField(default=False, verbose_name="Reply")
    
    instruksi = models.TextField(blank=True, help_text="Contoh: 'Komen dengan tagar #IndonesiaMaju'")
    
    # Rentang Tanggal Aktif Tugas
    tanggal_mulai = models.DateField(verbose_name="Mulai")
    tanggal_selesai = models.DateField(verbose_name="Selesai")
    
    poin = models.IntegerField(default=10, help_text="Poin untuk kader yang mengerjakan")
    aktif = models.BooleanField(default=True)

    def __str__(self):
        tugas = []
        if self.is_like: tugas.append('Like')
        if self.is_komen: tugas.append('Komen')
        if self.is_share: tugas.append('Share')
        if self.is_follow: tugas.append('Follow')
        if self.is_reply: tugas.append('Reply')
        label = ", ".join(tugas) if tugas else "Tugas Custom"
        return f"[{label}] - {self.konten.judul}"

    class Meta:
        verbose_name = "Tugas / Misi"
        verbose_name_plural = "Daftar Tugas"

class AkunMedsos(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Verifikasi'),
        ('VERIFIED', 'Terverifikasi'),
        ('REJECTED', 'Ditolak'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='akun_medsos')
    role_pemegang = models.CharField(max_length=20, default='CADRE') # Membedakan aset Kader vs Commander
    platform = models.CharField(max_length=20, choices=Konten.PLATFORM_CHOICES, default='INSTAGRAM')
    username = models.CharField(max_length=100)
    link_profil = models.URLField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    catatan_dco = models.TextField(blank=True, null=True, verbose_name="Catatan dari DCO")
    tanggal_daftar = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.platform}) - {self.status}"

    class Meta:
        verbose_name = "Aset Akun Medsos"
        verbose_name_plural = "Daftar Aset Medsos"
        unique_together = ('platform', 'username') # Kunci mati: Tidak boleh ada user + platform yang sama di seluruh sistem

class RiwayatMisi(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Verifikasi'),
        ('APPROVED', 'Disetujui'),
        ('REJECTED', 'Ditolak'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='riwayat_misi')
    tugas = models.ForeignKey(TugasKonten, on_delete=models.CASCADE, related_name='laporan_masuk')
    akun_digunakan = models.ForeignKey(AkunMedsos, on_delete=models.CASCADE)
    
    # Bukti per jenis tugas
    bukti_like = models.ImageField(upload_to='bukti_misi/like/', null=True, blank=True)
    bukti_komen = models.ImageField(upload_to='bukti_misi/komen/', null=True, blank=True)
    bukti_share = models.ImageField(upload_to='bukti_misi/share/', null=True, blank=True)
    bukti_follow = models.ImageField(upload_to='bukti_misi/follow/', null=True, blank=True)
    bukti_reply = models.ImageField(upload_to='bukti_misi/reply/', null=True, blank=True)
    
    foto_bukti = models.ImageField(upload_to='bukti_misi/', null=True, blank=True) # Silakan hapus nanti jika sudah migrasi total
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    catatan_verifikator = models.TextField(blank=True, null=True)
    tanggal_selesai = models.DateTimeField(auto_now_add=True)
    tanggal_verifikasi = models.DateTimeField(null=True, blank=True)
    poin_didapat = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.tugas.konten.judul} (@{self.akun_digunakan.username}) - {self.status}"

    class Meta:
        verbose_name = "Riwayat Misi"
        verbose_name_plural = "Riwayat Misi"
        unique_together = ('tugas', 'akun_digunakan') # 1 akun hanya bisa klaim 1 tugas sekali

# Signal untuk menghapus file fisik saat record dihapus (Anti-Sampah)
@receiver(post_delete, sender=RiwayatMisi)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Menghapus file dari filesystem saat record RiwayatMisi dihapus.
    """
    fields = ['bukti_like', 'bukti_komen', 'bukti_share', 'bukti_follow', 'bukti_reply', 'foto_bukti']
    for field_name in fields:
        field = getattr(instance, field_name)
        if field:
            if os.path.isfile(field.path):
                os.remove(field.path)
