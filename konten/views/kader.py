from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models
from konten.models import AkunMedsos, RiwayatMisi, TugasKonten
from .utils import generate_profile_link

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
