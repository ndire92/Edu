from django.contrib.auth.models import AbstractUser
from django.db import models
from tinymce.models import HTMLField
from django.utils.text import slugify
from django.utils import timezone
from tinymce import models as tinymce_models
from django.template.defaultfilters import slugify
from urllib.parse import urlparse, parse_qs

# =============================================
# ========
# UTILISATEUR PERSONNALISÉ
# =====================================================
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("Administrateur", "Administrateur"),
        ("Inspecteur IEF", "Inspecteur IEF"),
        ("Directeur", "Directeur"),
    ]
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    # Champs supplémentaires
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)
    
    # Contrôle d'activation
    is_active = models.BooleanField(default=False)

    # Date d'inscription
    date_joined = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

# =====================================================
# CORRECTION DES DONNÉES KOBO
# =====================================================
class Correction(models.Model):
    kobo_id = models.CharField(max_length=255)  # UUID de Kobo
    column_name = models.CharField(max_length=255)
    new_value = models.TextField()
    modified_at = models.DateTimeField(auto_now=True)
    # Pour suppression logique
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = (('kobo_id', 'column_name'),)
        ordering = ['-modified_at']

    def __str__(self):
        return f"Correction {self.kobo_id} ({self.column_name})"

# =====================================================

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = tinymce_models.HTMLField()
    image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    @property
    def embed_video_url(self):
        if not self.video_url:
            return None

        parsed = urlparse(self.video_url)

        # YouTube
        if "youtube.com" in parsed.netloc:
            video_id = parse_qs(parsed.query).get("v")
            if video_id:
                return f"https://www.youtube.com/embed/{video_id[0]}"
        if "youtu.be" in parsed.netloc:
            return f"https://www.youtube.com/embed/{parsed.path.lstrip('/')}"

        # Vimeo
        if "vimeo.com" in parsed.netloc:
            return f"https://player.vimeo.com/video/{parsed.path.lstrip('/')}"

        # Dailymotion
        if "dailymotion.com" in parsed.netloc:
            return f"https://www.dailymotion.com/embed{parsed.path}"

        # Sinon, on retourne l’URL brute (sera ouvert dans un <a>)
        return None

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)
