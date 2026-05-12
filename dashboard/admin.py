
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Correction, BlogPost

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')

    # Pour voir un champ de choix déroulant pour le rôle dans le formulaire
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'phone', 'address', 'profile_image', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
@admin.register(Correction)
class CorrectionAdmin(admin.ModelAdmin):
    list_display = (
        "kobo_id",
        "column_name",
        "short_new_value",
        "modified_at",
        "is_deleted",
    )

    list_filter = ("is_deleted", "modified_at")

    search_fields = ("kobo_id", "column_name", "new_value")

    readonly_fields = ("modified_at",)

    def short_new_value(self, obj):
        return obj.new_value[:50]
    short_new_value.short_description = "Nouvelle valeur"


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "is_published",
        "created_at",
    )

    list_filter = ("is_published", "created_at", "author")

    search_fields = ("title", "content")

    prepopulated_fields = {"slug": ("title",)}

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    fieldsets = (
        ("Contenu", {
            "fields": (
                "title",
                "slug",
                "content",
                "image",
                "video_url",
            )
        }),
        ("Publication", {
            "fields": (
                "author",
                "is_published",
            )
        }),
    )

from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta

User = get_user_model()

def admin_dashboard(request):
    # utilisateurs inscrits aujourd'hui (ou 24h)
    new_users = User.objects.filter(date_joined__gte=now()-timedelta(days=1))

    return render(request, "dashboard/admin.html", {
        "users": User.objects.all(),
        "new_users": new_users,
    })




from django.contrib import admin
from .models import (
    Ecole, Eleve,
    AbsenceQuotidienneEleve, AbsenceMensuelleEleve,
    Enseignant, AbsenceQuotidienneEnseignant, AbsenceMensuelleEnseignant
)

@admin.register(Ecole)
class EcoleAdmin(admin.ModelAdmin):
    list_display = ("nouveau_code_ecole", "nom_ecole", "zone", "statut")
    search_fields = ("nom_ecole", "nouveau_code_ecole")

@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ("nom_prenom", "ecole", "classe", "sexe")
    search_fields = ("nom_prenom", "nni", "numero_reg")
    list_filter = ("sexe", "classe", "ecole")

@admin.register(AbsenceQuotidienneEleve)
class AbsenceQuotidienneEleveAdmin(admin.ModelAdmin):
    list_display = ("eleve", "date_absence", "total_absences")
    list_filter = ("date_absence", "eleve__ecole")

@admin.register(AbsenceMensuelleEleve)
class AbsenceMensuelleEleveAdmin(admin.ModelAdmin):
    list_display = ("eleve", "mois", "total_absences")
    list_filter = ("mois", "eleve__ecole")

@admin.register(Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ("nom_prenom", "ecole", "langue_travail", "sexe")
    search_fields = ("nom_prenom", "nni", "mle")
    list_filter = ("sexe", "langue_travail", "ecole")

@admin.register(AbsenceQuotidienneEnseignant)
class AbsenceQuotidienneEnseignantAdmin(admin.ModelAdmin):
    list_display = ("enseignant", "date_absence", "abs_justifiees", "abs_non_justifiees")
    list_filter = ("date_absence", "enseignant__ecole")

@admin.register(AbsenceMensuelleEnseignant)
class AbsenceMensuelleEnseignantAdmin(admin.ModelAdmin):
    list_display = ("enseignant", "mois", "abs_justifiees", "abs_non_justifiees")
    list_filter = ("mois", "enseignant__ecole")

