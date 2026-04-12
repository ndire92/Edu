
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


