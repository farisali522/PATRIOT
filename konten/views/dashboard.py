from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import models
from konten.models import Konten, TugasKonten, AkunMedsos, RiwayatMisi

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
        # Inisialisasi active_role jika belum ada
        if 'active_role' not in request.session:
            request.session['active_role'] = request.user.profile.role
            
        profile = request.user.profile if hasattr(request.user, 'profile') else None
        biodata_lengkap = profile.is_biodata_complete if profile else False
        has_verified_account = AkunMedsos.objects.filter(
            owner=request.user, 
            status='VERIFIED'
        ).exists()
        
        # Hitung total poin dan misi selesai untuk CADRE (Hanya yang APPROVED)
        total_poin = RiwayatMisi.objects.filter(user=request.user, status='APPROVED').aggregate(
            total=models.Sum('poin_didapat')
        )['total'] or 0
        
        total_misi_selesai = RiwayatMisi.objects.filter(user=request.user, status='APPROVED').count()
        
        # Statistik Akun Medsos (Breakdown per role)
        if request.session.get('active_role') == 'COMMANDER':
            sub_ids = request.user.subordinates.values_list('user_id', flat=True)
            relevant_accounts = AkunMedsos.objects.filter(owner_id__in=sub_ids, role_pemegang='CADRE')
            stats_label = "AKUN CADRE"
        else:
            relevant_accounts = AkunMedsos.objects.filter(owner=request.user, role_pemegang='CADRE')
            stats_label = "AKUN SAYA"

        user_stats = {
            'total': relevant_accounts.count(),
            'ig': relevant_accounts.filter(platform='INSTAGRAM').count(),
            'tt': relevant_accounts.filter(platform='TIKTOK').count(),
            'fb': relevant_accounts.filter(platform='FACEBOOK').count(),
            'label': stats_label
        }
    
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
        'user_stats': user_stats,
    }
    return render(request, 'dashboard.html', context)

@login_required
def dashboard(request): # Cadangan jika ada yang panggil 'dashboard' saja
    return render(request, 'dashboard.html')
