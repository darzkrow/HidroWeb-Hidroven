from django.contrib import admin
from .models import Empresa
# Register your models here.
admin.site.site_header = "Panel de Administración"
admin.site.site_title = "Mi Sitio Admin"
admin.site.index_title = "Bienvenido al Panel de Administración"
admin.site.disable_action('delete_selected')

@admin.register(Empresa)
class EmpresaSetting(admin.ModelAdmin):
    list_display=('nombre','host','puerto','nombre_db','activo')
    search_fields =('nombre','host','puerto','nombre_db','activo')