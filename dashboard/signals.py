from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser

@receiver(pre_save, sender=CustomUser)
def send_activation_email(sender, instance, **kwargs):
    # Si l'utilisateur est nouveau => pas d'email
    if not instance.pk:
        return

    # Récupérer l'ancien état
    old_user = CustomUser.objects.get(pk=instance.pk)

    # Si le compte passe de inactif -> actif
    if not old_user.is_active and instance.is_active:
        subject = "Votre compte a été activé 🎉"
        message = f"""
Bonjour {instance.first_name},

Votre compte a été activé par l’administrateur.

👉 Connectez-vous ici : {settings.SITE_URL}/login/

Merci !
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False
        )
