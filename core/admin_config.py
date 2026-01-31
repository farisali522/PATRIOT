from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse

class SuperUserAdminSite(admin.AdminSite):
    def has_permission(self, request):
        """
        Hanya izinkan Superuser untuk mengakses admin panel.
        Staff biasa (is_staff=True tapi is_superuser=False) akan ditolak.
        """
        return request.user.is_active and request.user.is_superuser

# Mengganti default admin site dengan custom admin site kita
admin.site.__class__ = SuperUserAdminSite
admin.site.site_header = "PATRIOT - Super Admin"
admin.site.site_title = "PATRIOT Portal"
admin.site.index_title = "Pusat Kendali Strategis"
