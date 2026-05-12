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
        ("Enseignant", "Enseignant")
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES)

    email = models.EmailField(unique=True)  # 🔥 IMPORTANT

    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
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


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Sexe(models.TextChoices):
    MASCULIN = 'M', 'Masculin'
    FEMININ = 'F', 'Féminin'

# =========================
# ECOLE
# =========================
class Ecole(models.Model):
    ancien_code_ecole = models.CharField(max_length=50, null=True, blank=True)
    nouveau_code_ecole = models.CharField(max_length=50, unique=True)
    nom_ecole = models.CharField(max_length=200)

    ancien_nom_ecole = models.CharField(max_length=200, null=True, blank=True)
    date_creation = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=50, null=True, blank=True)
    loc_admin = models.CharField(max_length=100, null=True, blank=True)
    loc_scol = models.CharField(max_length=100, null=True, blank=True)
    zone = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["nouveau_code_ecole"]),
            models.Index(fields=["nom_ecole"]),
        ]

    def __str__(self):
        return f"{self.nom_ecole} ({self.nouveau_code_ecole})"

# =========================
# ELEVE
# =========================
class Eleve(TimeStampedModel):
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='eleves')

    numero_reg = models.CharField(max_length=50, unique=True)
    kobo_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    nom_prenom = models.CharField(max_length=200)
    nni = models.CharField(max_length=50, unique=True)

    sexe = models.CharField(max_length=10, choices=Sexe.choices, null=True, blank=True)
    classe = models.CharField(max_length=50, null=True, blank=True)

    tel = models.CharField(max_length=20, null=True, blank=True)
    observations = models.TextField(null=True, blank=True)
    enseignant = models.CharField(max_length=200, null=True, blank=True)
    signature = models.URLField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["numero_reg"]),
            models.Index(fields=["ecole"]),
        ]

    def __str__(self):
        return self.nom_prenom

# =========================
# ABSENCE ELEVE QUOTIDIENNE
# =========================
class AbsenceQuotidienneEleve(TimeStampedModel):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='absences_quotidiennes')

    kobo_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    date_absence = models.DateField()
    total_absences = models.IntegerField(default=0)

    periodes = models.CharField(max_length=100, null=True, blank=True)
    observations = models.TextField(null=True, blank=True)
    enseignant = models.CharField(max_length=200, null=True, blank=True)
    signature = models.URLField(null=True, blank=True)

    class Meta:
        unique_together = ("eleve", "date_absence")
        indexes = [models.Index(fields=["date_absence"])]

    def save(self, *args, **kwargs):
        if self.total_absences < 0:
            raise ValueError("Le total d'absences ne peut pas être négatif")
        super().save(*args, **kwargs)

# =========================
# ABSENCE ELEVE MENSUELLE
# =========================
class AbsenceMensuelleEleve(TimeStampedModel):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='absences_mensuelles')

    kobo_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    mois = models.DateField(help_text="Stocke le 1er jour du mois concerné (ex: 2023-10-01)")
    total_absences = models.IntegerField(default=0)

    observations = models.TextField(null=True, blank=True)
    enseignant = models.CharField(max_length=200, null=True, blank=True)
    signature = models.URLField(null=True, blank=True)

    class Meta:
        unique_together = ("eleve", "mois")
        indexes = [models.Index(fields=["mois"])]

    def save(self, *args, **kwargs):
        if self.total_absences < 0:
            raise ValueError("Le total d'absences ne peut pas être négatif")
        super().save(*args, **kwargs)

# =========================
# ENSEIGNANT
# =========================
class Enseignant(TimeStampedModel):
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='enseignants')

    numero_reg = models.CharField(max_length=50, unique=True)
    kobo_id = models.CharField(max_length=100, unique=True, null=True, blank=True)

    nom_prenom = models.CharField(max_length=200)
    nni = models.CharField(max_length=50)
    mle = models.CharField(max_length=50)
    langue_travail = models.CharField(max_length=50)
    sexe = models.CharField(max_length=10, choices=Sexe.choices)

    tel = models.CharField(max_length=20, null=True, blank=True)
    observations = models.TextField(null=True, blank=True)
    directeur_nom = models.CharField(max_length=200, null=True, blank=True)
    signature_cachet = models.URLField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["numero_reg"]),
            models.Index(fields=["ecole"]),
        ]

    def __str__(self):
        return self.nom_prenom

# =========================
# ABSENCE ENSEIGNANT QUOTIDIENNE
# =========================
class AbsenceQuotidienneEnseignant(TimeStampedModel):
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name='absences_quotidiennes')

    kobo_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    date_absence = models.DateField()

    abs_justifiees = models.IntegerField(default=0)
    abs_non_justifiees = models.IntegerField(default=0)

    periodes = models.CharField(max_length=100, null=True, blank=True)
    observations = models.TextField(null=True, blank=True)
    directeur_nom = models.CharField(max_length=200, null=True, blank=True)
    signature_cachet = models.URLField(null=True, blank=True)

    class Meta:
        unique_together = ("enseignant", "date_absence")
        indexes = [models.Index(fields=["date_absence"])]

    def save(self, *args, **kwargs):
        if self.abs_justifiees < 0 or self.abs_non_justifiees < 0:
            raise ValueError("Les absences ne peuvent pas être négatives")
        super().save(*args, **kwargs)

# =========================
# ABSENCE ENSEIGNANT MENSUELLE
# =========================
class AbsenceMensuelleEnseignant(TimeStampedModel):
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name='absences_mensuelles')

    kobo_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    mois = models.DateField(help_text="Stocke le 1er jour du mois concerné")

    abs_justifiees = models.IntegerField(default=0)
    abs_non_justifiees = models.IntegerField(default=0)

    observations = models.TextField(null=True, blank=True)
    directeur_nom = models.CharField(max_length=200, null=True, blank=True)
    signature_cachet = models.URLField(null=True, blank=True)

    class Meta:
        unique_together = ("enseignant", "mois")
        indexes = [models.Index(fields=["mois"])]

    def save(self, *args, **kwargs):
        if self.abs_justifiees < 0 or self.abs_non_justifiees < 0:
            raise ValueError("Les absences ne peuvent pas être négatives")
        super().save(*args, **kwargs)

