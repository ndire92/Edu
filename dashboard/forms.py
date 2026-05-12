from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import BlogPost
from tinymce.widgets import TinyMCE




class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "username",
            "role",
            "phone",
            "address",
            "profile_image",
            "password1",
            "password2",
        ]
        labels = {
            "first_name": "Nom",
            "last_name": "Prénom",
            "email": "Adresse Email",
            "username": "Nom d’utilisateur",
            "role": "Rôle",
            "phone": "Numéro de téléphone",
            "address": "Adresse",
            "profile_image": "Image de profil",
            "password1": "Mot de passe",
            "password2": "Confirmation du mot de passe",
        }



class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "phone", "address", "profile_image"]
        labels = {
            "first_name": "Nom",
            "last_name": "Prénom",
            "email": "Adresse Email",
            "phone": "Numéro de téléphone",
            "address": "Adresse",
            "profile_image": "Image de profil",
        }



class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'image', 'video_url', 'is_published']

        widgets = {
            # TinyMCE
            'content': TinyMCE(attrs={'cols': 80, 'rows': 30}),


            # Title
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre attractif...'
            }),

            # Video URL
            # IMPORTANT: On utilise TextInput pour permettre de coller des liens sans "https://"
            'video_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Collez votre lien YouTube ici...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super(BlogPostForm, self).__init__(*args, **kwargs)

        # === CORRECTION CRUCIALE ===
        # On rend les champs Image et Vidéo NON OBLIGATOIRES
        # Cela permet de choisir "Vidéo" sans forcément avoir d'image
        self.fields['image'].required = False
        self.fields['video_url'].required = False

        # S'assurer que TinyMCE a la bonne classe CSS (optionnel si déjà dans meta)
        if 'content' in self.fields:
            self.fields['content'].widget.attrs.update({'class': 'form-control'})


