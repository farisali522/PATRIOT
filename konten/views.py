from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import models, IntegrityError
from .models import Konten, TugasKonten, AkunMedsos, RiwayatMisi, KategoriKonten

# Landing Page
def landing_page(request):
    # Set default role jika belum ada
    if 'active_role' not in request.session:
        request.session['active_role'] = 'DCO'
    return render(request, 'landing.html')

@login_required
def switch_role(request, role_name):
    # Simpan role ke session
    request.session['active_role'] = role_name
    # Redirect kembali ke halaman sebelumnya
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_uploader'))

# Login Page
def login_page(request):
    return render(request, 'login.html')

from django.utils import timezone

# Dashboard Uploader
@login_required
def dashboard_uploader(request):
    # Hitung Statistik
    today = timezone.now().date()
    
    total_konten = Konten.objects.count()
    total_ig = Konten.objects.filter(platform='INSTAGRAM').count()
    total_tt = Konten.objects.filter(platform='TIKTOK').count()
    
    # Ambil Tugas yang Aktif Secara Tanggal (Hari ini ada di rentang Mulai - Selesai)
    tugas_aktif_list = TugasKonten.objects.filter(
        tanggal_mulai__lte=today, 
        tanggal_selesai__gte=today
    ).select_related('konten').order_by('-id')[:10]
    
    # Cek kelengkapan biodata dan akun medsos untuk CADRE
    biodata_lengkap = False
    has_verified_account = False
    total_poin = 0
    total_misi_selesai = 0
    
    if request.user.is_authenticated:
        profile = request.user.profile if hasattr(request.user, 'profile') else None
        biodata_lengkap = profile.is_biodata_complete if profile else False
        has_verified_account = AkunMedsos.objects.filter(
            owner=request.user, 
            status='VERIFIED'
        ).exists()
        
        # Hitung total poin dan misi selesai untuk CADRE
        total_poin = RiwayatMisi.objects.filter(user=request.user).aggregate(
            total=models.Sum('poin_didapat')
        )['total'] or 0
        
        total_misi_selesai = RiwayatMisi.objects.filter(user=request.user).count()
    
    context = {
        'total_konten': total_konten,
        'total_ig': total_ig,
        'total_tt': total_tt,
        # 'total_tugas': total_tugas, # Tidak perlu angka total lagi
        'tugas_aktif_list': tugas_aktif_list,
        'today': today,
        'biodata_lengkap': biodata_lengkap,
        'has_verified_account': has_verified_account,
        'total_poin': total_poin,
        'total_misi_selesai': total_misi_selesai,
    }
    return render(request, 'dashboard.html', context)

@login_required
def dashboard(request): # Cadangan jika ada yang panggil 'dashboard' saja
    return render(request, 'dashboard.html')

# Daftar Konten (Gallery)
@login_required
def daftar_konten(request):
    konten_list = Konten.objects.prefetch_related('daftar_tugas').all().order_by('-tanggal_upload')
    kategori_list = KategoriKonten.objects.all().order_by('nama')
    
    # Filter Platform
    platform = request.GET.get('platform')
    if platform and platform != 'ALL':
        konten_list = konten_list.filter(platform=platform)

    return render(request, 'konten/konten.html', {
        'daftar_konten': konten_list,
        'active_platform': platform or 'ALL',
        'kategori_list': kategori_list
    })

# Tambah Konten (Frontend)
@login_required
def tambah_konten(request):
    if request.method == 'POST':
        judul = request.POST.get('judul')
        platform = request.POST.get('platform')
        link_konten = request.POST.get('link_konten')
        kategori_id = request.POST.get('kategori')
        nama_kategori_baru = request.POST.get('nama_kategori_baru')
        deskripsi = request.POST.get('deskripsi')
        
        # Handle kategori: Prioritas Input Baru
        kategori_obj = None
        if nama_kategori_baru:
            # Case insensitive get or create logic manual prevent duplicate error if distinct case
            # Disini pakai simple get_or_create
            kategori_obj, created = KategoriKonten.objects.get_or_create(nama=nama_kategori_baru.strip())
        elif kategori_id:
            try:
                kategori_obj = KategoriKonten.objects.get(id=kategori_id)
            except KategoriKonten.DoesNotExist:
                kategori_obj = None
        
        try:
            Konten.objects.create(
                judul=judul,
                platform=platform,
                link_konten=link_konten,
                kategori=kategori_obj,
                deskripsi=deskripsi
            )
            messages.success(request, 'Konten berhasil ditambahkan!')
        except IntegrityError:
            messages.error(request, 'Gagal! Link konten ini sudah terdaftar. Silakan cek kembali.')
            return redirect('daftar_konten')
        return redirect('daftar_konten')
    return redirect('daftar_konten')

from django.utils import timezone
from datetime import timedelta

@login_required
def tambah_tugas(request, konten_id):
    if request.method == 'POST':
        konten = Konten.objects.get(id=konten_id)
        jenis_tugas_list = request.POST.getlist('jenis_tugas[]')
        instruksi = request.POST.get('instruksi')
        
        # Validasi Timezone Aware
        today = timezone.localdate()
        tgl_mulai = request.POST.get('tanggal_mulai')
        tgl_selesai = request.POST.get('tanggal_selesai')
        
        # Konversi string ke date object untuk komparasi
        from datetime import datetime
        if tgl_mulai:
            tgl_mulai_obj = datetime.strptime(tgl_mulai, '%Y-%m-%d').date()
            if tgl_mulai_obj < today:
                tgl_mulai = today # Paksa jadi hari ini jika mundur
        else:
            tgl_mulai = today

        if not tgl_selesai:
            tgl_selesai = today + timedelta(days=3)

        poin = request.POST.get('poin') or 10

        # Tentukan boolean flags berdasarkan checkbox
        is_like = 'LIKE' in jenis_tugas_list
        is_komen = 'KOMEN' in jenis_tugas_list
        is_share = 'SHARE' in jenis_tugas_list
        is_follow = 'FOLLOW' in jenis_tugas_list
        is_reply = 'REPLY' in jenis_tugas_list
        
        # Buat SATU tugas dengan multiselect action
        if jenis_tugas_list: # Hanya simpan jika ada minimal 1 tugas dipilih
            TugasKonten.objects.create(
                konten=konten,
                is_like=is_like,
                is_komen=is_komen,
                is_share=is_share,
                is_follow=is_follow,
                is_reply=is_reply,
                instruksi=instruksi,
                tanggal_mulai=tgl_mulai,
                tanggal_selesai=tgl_selesai,
                poin=poin
            )
            
        return redirect('daftar_konten')
    return redirect('daftar_konten')

# Daftar Tugas (Manajemen)
@login_required
def daftar_tugas(request):
    today = timezone.localdate()
    
    # Tugas Aktif: Tanggal Selesai >= Hari Ini
    tugas_aktif = TugasKonten.objects.filter(
        tanggal_selesai__gte=today
    ).select_related('konten').order_by('tanggal_selesai')
    
    # Tugas Selesai/Riwayat: Tanggal Selesai < Hari Ini
    tugas_selesai = TugasKonten.objects.filter(
        tanggal_selesai__lt=today
    ).select_related('konten').order_by('-tanggal_selesai')[:20] 

    konten_list = Konten.objects.all().order_by('-tanggal_upload')
    
    context = {
        'tugas_aktif': tugas_aktif,
        'tugas_selesai': tugas_selesai,
        'konten_list': konten_list,
        'today': today
    }
    return render(request, 'konten/tugas.html', context)


def generate_profile_link(platform, username):
    # Bersihkan untuk URL (hilangkan @ jika ada di awal)
    clean_username = username.strip()
    if clean_username.startswith('@'):
        clean_username = clean_username[1:] # Buang karakter pertama (@)
    
    if platform == 'INSTAGRAM':
        return f"https://www.instagram.com/{clean_username}/"
    elif platform == 'TIKTOK':
        return f"https://www.tiktok.com/@{clean_username}"
    elif platform == 'FACEBOOK':
        return f"https://www.facebook.com/{clean_username}"
    elif platform == 'TWITTER':
        return f"https://twitter.com/{clean_username}"
    elif platform == 'YOUTUBE':
        return f"https://www.youtube.com/@{clean_username}"
    return f"#{clean_username}"

# Halaman Manajemen Akun Medsos (Role: Commander)
@login_required
def manajemen_akun_medsos(request):
    active_role = request.session.get('active_role', 'COMMANDER')
    
    if request.method == 'POST':
        platform = request.POST.get('platform')
        raw_username = request.POST.get('username').strip()
        
        # Normalisasi: Pastikan username selalu diawali @ saat disimpan ke DB
        username = raw_username if raw_username.startswith('@') else f"@{raw_username}"
        
        if platform and username:
            # Cek apakah akun ini sudah pernah didaftarkan oleh SIAPAPUN di sistem (Global & Case Insensitive)
            exists = AkunMedsos.objects.filter(platform=platform, username__iexact=username).exists()
            
            if exists:
                messages.error(request, f"Gagal! Akun {platform} {username} sudah diklaim oleh personil lain.")
            else:
                link_profil = generate_profile_link(platform, username)
                AkunMedsos.objects.create(
                    owner=request.user,
                    role_pemegang='COMMANDER', # Simpan sebagai aset Commander
                    platform=platform,
                    username=username,
                    link_profil=link_profil,
                    status='PENDING'
                )
                messages.success(request, f"Aset wilayah {platform} {username} berhasil ditambahkan!")
            
            # Redirect kembali ke halaman yang sama untuk mencegah re-submit saat refresh
            return redirect('akun_medsos')
            
    # Akun milik Commander sendiri (Hanya yang didaftarkan sebagai COMMANDER)
    akun_list = AkunMedsos.objects.filter(owner=request.user, role_pemegang='COMMANDER')
    
    # Statistik Dinamis (Hanya akun milik user ini sebagai Commander)
    stats = {
        'total': akun_list.count(),
        'ig': akun_list.filter(platform='INSTAGRAM').count(),
        'tt': akun_list.filter(platform='TIKTOK').count(),
        'fb': akun_list.filter(platform='FACEBOOK').count(),
    }
    
    # Akun milik Cadre bawahan (Subordinates)
    cadre_sub_ids = request.user.subordinates.values_list('user_id', flat=True)
    akun_cadre_list = AkunMedsos.objects.filter(owner_id__in=cadre_sub_ids)
    
    context = {
        'akun_list': akun_list,
        'akun_cadre_list': akun_cadre_list,
        'stats': stats,
    }
    return render(request, 'dewandpc/akun_medsos.html', context)

# Halaman Verifikasi Akun Medsos (Role: DCO)
@login_required
def verifikasi_akun_medsos(request):
    # Ambil semua akun yang statusnya PENDING
    akun_pending = AkunMedsos.objects.filter(status='PENDING').order_by('-tanggal_daftar')
    context = {
        'akun_pending': akun_pending,
    }
    return render(request, 'konten/verifikasi_akun.html', context)

@login_required
def proses_verifikasi_akun(request, akun_id, action):
    try:
        akun = AkunMedsos.objects.get(id=akun_id)
        if action == 'approve':
            akun.status = 'VERIFIED'
            messages.success(request, f"Akun {akun.username} ({akun.platform}) berhasil diverifikasi!")
        elif action == 'reject':
            akun.status = 'REJECTED'
            messages.warning(request, f"Pendaftaran akun {akun.username} ({akun.platform}) telah ditolak.")
        akun.save()
    except AkunMedsos.DoesNotExist:
        messages.error(request, "Akun tidak ditemukan.")
    
    return redirect('verifikasi_akun')

# Halaman SOP (Standard Operating Procedure)
@login_required
def sop_view(request):
    return render(request, 'sop.html')

from django.contrib import messages

# Halaman Manajemen Akun Medsos (Role: Cadre)
@login_required
def akun_medsos_kader(request):
    if request.method == 'POST':
        platform = request.POST.get('platform')
        raw_username = request.POST.get('username').strip()
        
        # Normalisasi: Pastikan username selalu diawali @ saat disimpan ke DB
        username = raw_username if raw_username.startswith('@') else f"@{raw_username}"
        
        if platform and username:
            # Cek duplikat secara GLOBAL dan Case-Insensitive (tidak peduli siapa yang mendaftarkan)
            exists = AkunMedsos.objects.filter(platform=platform, username__iexact=username).exists()
            
            if exists:
                messages.error(request, f"Gagal! Akun {platform} {username} sudah terdaftar di database PATRIOT.")
            else:
                link_profil = generate_profile_link(platform, username)
                AkunMedsos.objects.create(
                    owner=request.user,
                    role_pemegang='CADRE', # Simpan sebagai aset Cadre
                    platform=platform,
                    username=username,
                    link_profil=link_profil,
                    status='PENDING'
                )
                messages.success(request, f"Akun {platform} {username} berhasil didaftarkan dan menunggu verifikasi!")
            
            return redirect('akun_medsos_kader')
            
    # Hanya tampilkan akun yang didaftarkan sebagai CADRE
    akun_list = AkunMedsos.objects.filter(owner=request.user, role_pemegang='CADRE')
    
    # Cek kelengkapan biodata
    profile = request.user.profile if hasattr(request.user, 'profile') else None
    biodata_lengkap = profile.is_biodata_complete if profile else False
    
    context = {
        'akun_list': akun_list,
        'biodata_lengkap': biodata_lengkap,
    }
    return render(request, 'kader/akun_medsos.html', context)

# Halaman Daftar Misi (Role: Cadre)
@login_required
def misi_kader(request):
    today = timezone.localdate()
    # Ambil misi (tugas) yang aktif dan belum kadaluarsa
    tugas_aktif = TugasKonten.objects.filter(
        aktif=True,
        tanggal_mulai__lte=today,
        tanggal_selesai__gte=today
    ).select_related('konten').order_by('-id')
    
    # Ambil semua akun milik user ini
    user_accounts = AkunMedsos.objects.filter(owner=request.user)
    
    # Ambil riwayat pengerjaan user ini untuk misi-misi yang aktif
    riwayat_user = RiwayatMisi.objects.filter(user=request.user, tugas__in=tugas_aktif)
    # Mapping: {tugas_id: [list_akun_id_yang_sudah_mengerjakan]}
    map_misi_selesai = {}
    for r in riwayat_user:
        if r.tugas_id not in map_misi_selesai:
            map_misi_selesai[r.tugas_id] = []
        map_misi_selesai[r.tugas_id].append(r.akun_digunakan_id)

    # Kategorikan platform akun
    verified_accounts = user_accounts.filter(status='VERIFIED')
    pending_accounts_all = user_accounts.filter(status='PENDING')
    
    # Flattening: Buat list tugas "per akun"
    tugas_per_akun = []
    
    for t in tugas_aktif:
        # Cari semua akun (apapun statusnya) yang cocok dengan platform tugas ini
        all_matching_accounts = user_accounts.filter(platform=t.konten.platform)
        
        if all_matching_accounts.exists():
            # Jika punya akun, buatkan 1 kartu untuk SETIAP akun yang terdaptar
            for akun in all_matching_accounts:
                is_done = RiwayatMisi.objects.filter(tugas=t, akun_digunakan=akun).exists()
                tugas_per_akun.append({
                    'id_tugas': t.id,
                    'tugas': t,
                    'akun': akun,
                    'is_done': is_done,
                    'status_akun': akun.status # VERIFIED, PENDING, atau REJECTED
                })
        else:
            # Jika BENAR-BENAR belum daftar akun sama sekali di platform ini
            tugas_per_akun.append({
                'id_tugas': t.id,
                'tugas': t,
                'akun': None,
                'is_done': False,
                'status_info': 'NOT_REGISTERED',
                'status_akun': 'NONE'
            })

    # Sorting Logic: Yang aktif (tidak disabled) harus paling atas
    # Urutan: 
    # 1. VERIFIED & Belum Selesai (Prioritas Utama)
    # 2. PENDING (Sedang Berusaha)
    # 3. VERIFIED & Sudah Selesai (Arsip)
    # 4. REJECTED / NONE (Bait)
    def sort_tugas(item):
        status = item.get('status_akun', 'NONE')
        is_done = item.get('is_done', False)
        
        if status == 'VERIFIED' and not is_done:
            return 0  # Paling Atas
        if status == 'PENDING':
            return 1
        if status == 'VERIFIED' and is_done:
            return 2
        return 3 # REJECTED atau NONE (Bawah)

    tugas_per_akun.sort(key=sort_tugas)

    # Hitung total poin potensial (poin dari tugas yang belum selesai)
    total_poin_potensial = sum(item['tugas'].poin for item in tugas_per_akun if item.get('status_akun') == 'VERIFIED' and not item['is_done'])

    # List platform unik (untuk filtering atau info tambahan jika perlu)
    verified_platforms = [p.upper() for p in verified_accounts.values_list('platform', flat=True).distinct()]
    pending_platforms = [p.upper() for p in pending_accounts_all.values_list('platform', flat=True).distinct()]
    
    # Cek kelengkapan biodata dan akun verified
    profile = request.user.profile if hasattr(request.user, 'profile') else None
    biodata_lengkap = profile.is_biodata_complete if profile else False
    has_verified_account = verified_accounts.exists()
    
    context = {
        'tugas_per_akun': tugas_per_akun,
        'verified_platforms': verified_platforms,
        'pending_platforms': pending_platforms,
        'total_poin_potensial': total_poin_potensial,
        'biodata_lengkap': biodata_lengkap,
        'has_verified_account': has_verified_account,
    }
    return render(request, 'kader/misi.html', context)

@login_required
def konfirmasi_misi(request, tugas_id):
    if request.method == 'POST':
        akun_id = request.POST.get('akun_id')
        try:
            tugas = TugasKonten.objects.get(id=tugas_id)
            akun = AkunMedsos.objects.get(id=akun_id, owner=request.user, status='VERIFIED')
            
            # Cek apakah platform cocok
            if akun.platform != tugas.konten.platform:
                messages.error(request, "Platform akun tidak sesuai dengan misi.")
                return redirect('misi_kader')

            # Cek apakah sudah pernah mengerjakan pakai akun ini
            exists = RiwayatMisi.objects.filter(tugas=tugas, akun_digunakan=akun).exists()
            if exists:
                messages.warning(request, f"Akun {akun.username} sudah melaporkan misi ini.")
            else:
                RiwayatMisi.objects.create(
                    user=request.user,
                    tugas=tugas,
                    akun_digunakan=akun,
                    poin_didapat=tugas.poin
                )
                messages.success(request, f"Misi berhasil dilaporkan menggunakan akun {akun.username}! +{tugas.poin} Poin.")
                
        except (TugasKonten.DoesNotExist, AkunMedsos.DoesNotExist):
            messages.error(request, "Data tidak valid atau akun belum terverifikasi.")
            
    return redirect('misi_kader')

# Halaman Biodata Kader
@login_required
def biodata_kader(request):
    # Ambil profile user
    profile = request.user.profile if hasattr(request.user, 'profile') else None
    
    if request.method == 'POST':
        # Update biodata
        profile.nik = request.POST.get('nik')
        profile.nama_lengkap = request.POST.get('nama_lengkap')
        profile.tempat_lahir = request.POST.get('tempat_lahir')
        profile.tanggal_lahir = request.POST.get('tanggal_lahir') or None
        profile.jenis_kelamin = request.POST.get('jenis_kelamin')
        profile.alamat_lengkap = request.POST.get('alamat_lengkap')
        profile.nomor_hp = request.POST.get('nomor_hp')
        
        # Handle file upload
        if request.FILES.get('foto_ktp'):
            profile.foto_ktp = request.FILES['foto_ktp']
        
        # Update status kelengkapan biodata
        profile.biodata_lengkap = profile.is_biodata_complete
        profile.save()
        
        messages.success(request, "Biodata berhasil diperbarui!")
        return redirect('biodata_kader')
    
    # Hitung total poin dari riwayat misi
    total_poin = RiwayatMisi.objects.filter(user=request.user).aggregate(
        total=models.Sum('poin_didapat')
    )['total'] or 0
    
    # Hitung jumlah misi yang sudah diselesaikan
    total_misi_selesai = RiwayatMisi.objects.filter(user=request.user).count()
    
    # Hitung jumlah akun medsos yang terverifikasi
    total_akun_verified = AkunMedsos.objects.filter(
        owner=request.user, 
        status='VERIFIED'
    ).count()
    
    context = {
        'profile': profile,
        'total_poin': total_poin,
        'total_misi_selesai': total_misi_selesai,
        'total_akun_verified': total_akun_verified,
    }
    return render(request, 'kader/biodata.html', context)

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def ubah_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validasi password lama
        if not request.user.check_password(old_password):
            messages.error(request, "Password lama tidak sesuai!")
            return redirect('ubah_password')
        
        # Validasi password baru dan konfirmasi
        if new_password != confirm_password:
            messages.error(request, "Password baru dan konfirmasi tidak cocok!")
            return redirect('ubah_password')
        
        # Validasi panjang password
        if len(new_password) < 8:
            messages.error(request, "Password minimal 8 karakter!")
            return redirect('ubah_password')
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session agar tidak logout
        update_session_auth_hash(request, request.user)
        
        messages.success(request, "Password berhasil diubah!")
        return redirect('ubah_password')
    
    return render(request, 'password.html')
