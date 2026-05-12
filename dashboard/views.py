from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db.models.functions import TruncMonth, TruncDay
from collections import defaultdict
from dateutil.parser import parse
from django.db.models import Sum, Count

from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
import requests
from django.core.mail import send_mail
from django.conf import settings
from .models import AbsenceMensuelleEleve, AbsenceMensuelleEnseignant, AbsenceQuotidienneEleve, AbsenceQuotidienneEnseignant, CustomUser, Correction, BlogPost, Ecole, Eleve, Enseignant
from .forms import CustomUserChangeForm, BlogPostForm



def home_view(request):
    return render(request, "dashboard/home.html")


def api_home_data(request):
    """API Power BI : Agrège les données de la base locale"""
    data = {}

    # Élèves
    data['eleves_sexe'] = list(Eleve.objects.values('sexe').annotate(total=Count('id')))
    data['eleves_classe'] = list(
        Eleve.objects.values('classe')
        .annotate(total=Count('id'))
        .order_by('-total')[:10]
    )

    # Absences quotidiennes élèves
    abs_q = list(
        AbsenceQuotidienneEleve.objects
        .annotate(day=TruncDay('date_absence'))
        .values('day')
        .annotate(total=Sum('total_absences'))
        .order_by('day')
    )
    for item in abs_q:
        item['day'] = item['day'].strftime("%Y-%m-%d")
    data['abs_eleves_q_evol'] = abs_q
#Absences Mensuelles Élèves
    raw_absences = AbsenceQuotidienneEleve.objects.values('date_absence', 'total_absences')

    mois_groupes = defaultdict(int)

    for item in raw_absences:
        if item['date_absence']:
            d = parse(str(item['date_absence']))
            cle_mois = d.strftime("%Y-%m")  # ex: "2025-11"
            mois_groupes[cle_mois] += item['total_absences'] or 0

    data['abs_eleves_m_evol'] = [
        {"month": mois, "total": total}
        for mois, total in sorted(mois_groupes.items())
    ]
    # Enseignants
    data['ens_sexe'] = list(Enseignant.objects.values('sexe').annotate(total=Count('id')))
    data['ens_langue'] = list(Enseignant.objects.values('langue_travail').annotate(total=Count('id')))
    data['abs_ens_q_pie'] = {
        "Justifiées": AbsenceQuotidienneEnseignant.objects.aggregate(total=Sum('abs_justifiees'))['total'] or 0,
        "Non Justifiées": AbsenceQuotidienneEnseignant.objects.aggregate(total=Sum('abs_non_justifiees'))['total'] or 0
    }

    abs_ens_q = list(
        AbsenceQuotidienneEnseignant.objects
        .annotate(day=TruncDay('date_absence'))
        .values('day')
        .annotate(just=Sum('abs_justifiees'), nj=Sum('abs_non_justifiees'))
        .order_by('day')
    )
    for item in abs_ens_q:
        item['day'] = item['day'].strftime("%Y-%m-%d")
    data['abs_ens_q_evol'] = abs_ens_q

    # Absences mensuelles enseignants (regroupement Python)
    raw_abs_ens = AbsenceMensuelleEnseignant.objects.values('mois', 'abs_justifiees', 'abs_non_justifiees')
    mois_groupes_ens = defaultdict(lambda: {"just": 0, "nj": 0})
    for item in raw_abs_ens:
        if item['mois']:
            d = parse(str(item['mois']))
            cle_mois = d.strftime("%Y-%m")
            mois_groupes_ens[cle_mois]["just"] += item['abs_justifiees'] or 0
            mois_groupes_ens[cle_mois]["nj"] += item['abs_non_justifiees'] or 0
    data['abs_ens_m_evol'] = [
        {"month": mois, "just": total["just"], "nj": total["nj"]}
        for mois, total in sorted(mois_groupes_ens.items())
    ]

    # Retour JSON
    return JsonResponse({
        "ecoles": list(Ecole.objects.values_list('nom_ecole', flat=True).distinct()),
        "mois": [d.strftime('%Y-%m') for d in AbsenceQuotidienneEleve.objects.dates('date_absence', 'month').order_by('-date_absence')],
        **data
        })

# ==================================================
# CONFIGURATION GLOBALE
# ==================================================
# ==================================================
# FONCTIONS D'AUTHENTIFICATION
# ==================================================


def register_view(request):
    if request.method == "POST":
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        username = email
        password = request.POST["password"]
        role = request.POST.get("role", "Enseignant")

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, "dashboard/register.html")

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=False  # sécurité
        )

        # 1️⃣ Récupérer les admins
        admins = CustomUser.objects.filter(role="Administrateur", is_active=True)
        admin_emails = [admin.email for admin in admins]

        # 2️⃣ URL de connexion
        login_url = request.build_absolute_uri(reverse("login"))

        # 3️⃣ Email
        subject = "Nouvelle demande d'inscription"
        message = f"""
Un nouvel utilisateur a créé un compte :

Nom : {first_name} {last_name}
Email : {email}
Rôle : {role}

👉 Se connecter pour activer le compte :
{login_url}

Merci.
"""

        if admin_emails:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=False
            )

        messages.success(
            request,
            "Votre compte a été créé avec succès. Veuillez attendre l'activation par l'administrateur."
        )

        return redirect("/")

    return render(request, "dashboard/register.html")


def login_view(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

            # SUPERUSER → admin Django
            if user.is_superuser:
                return redirect('/admin/')

            # ADMIN MÉTIER → admin-panel
            elif user.role == 'Administrateur':
                return redirect('/admin-panel/')

            # AUTRES → dashboard
            else:
                return redirect('/dashboard/')

        else:
            return render(request, "dashboard/login.html", {
                "error": "Identifiants invalides"
            })

    return render(request, "dashboard/login.html")


def logout_view(request):
    logout(request)
    return redirect("/login/")


# ==========================
# PROFIL
# ==========================
@login_required
def profile_view(request):
    return render(request, "dashboard/profile.html", {"user": request.user})


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect("/profile/")
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, "dashboard/edit_profile.html", {"form": form})


@login_required
def delete_account_view(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        return redirect("/")
    return render(request, "dashboard/delete_account.html")



# ==========================
# ADMIN DASHBOARD
# ==========================
@login_required
def admin_view(request):
    if not (request.user.is_superuser or request.user.role == 'Administrateur'):
        messages.warning(request, "Accès réservé aux administrateurs.")
        return redirect('/dashboard/')

    query = request.GET.get('q', '')
    if query:
        users = CustomUser.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(role__icontains=query)
        ).order_by('-date_joined')
    else:
        users = CustomUser.objects.all().order_by('-date_joined')

    return render(request, 'dashboard/admin.html', {
        'users': users,
        'query': query
    })


@login_required
def admin_toggle_user(request, user_id):
    if not (request.user.is_superuser or request.user.role == 'Administrateur'):
        messages.warning(request, "Accès interdit.")
        return redirect('/dashboard/')

    if request.method == "POST":
        user = get_object_or_404(CustomUser, id=user_id)

        user.is_active = not user.is_active
        user.save()  # 🔥 déclenche le signal email

        if user.is_active:
            messages.success(request, "Compte activé avec succès.")
        else:
            messages.warning(request, "Compte désactivé.")

    return redirect('/admin-panel/')


@login_required
def admin_delete_user(request, user_id):
    allowed_roles = ['Directeur', 'Administrateur', 'Inspecteur IEF']

    if not (request.user.is_superuser or request.user.role in allowed_roles):
        messages.warning(request, "Accès réservé.")
        return redirect('/dashboard/')

    user_to_delete = get_object_or_404(CustomUser, id=user_id)

    if user_to_delete == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
    else:
        user_to_delete.delete()
        messages.success(request, f"Utilisateur supprimé avec succès.")

    return redirect('/admin-panel/')


@login_required
def admin_edit_user(request, user_id):
    allowed_roles = ['Directeur', 'Administrateur', 'Superviseur']

    if not (request.user.is_superuser or request.user.role in allowed_roles):
        messages.warning(request, "Accès réservé aux administrateurs.")
        return redirect('/dashboard/')

    user_to_edit = get_object_or_404(CustomUser, id=user_id)

    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, request.FILES, instance=user_to_edit)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur modifié avec succès.")
            return redirect('/admin-panel/')
    else:
        form = CustomUserChangeForm(instance=user_to_edit)

    return render(request, "dashboard/edit_profile.html", {
        "form": form,
        "user": user_to_edit
    })
@login_required
def admin_update_role(request, user_id):
    # Vérifie si l'utilisateur n'est pas superuser ET n'a pas le rôle Administrateur
    if not (request.user.is_superuser or request.user.role == "Administrateur"):
        messages.error(request, "Accès refusé.")
        return redirect('/dashboard/')

    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get("role")

        if new_role:
            user.role = new_role
            user.save()
            messages.success(request, "Rôle mis à jour.")

    return redirect('/admin-panel/')

# ==================================================
# FONCTION COMMUNE (Moteur de données)
# ==================================================
# DASHBOARD KOBO
# ==========================

# ===========from django.db.models.functions import TruncMonth, TruncDay



def home_view(request):
    return render(request, "dashboard/home.html")




#==========================================================
# SYSTÈME KOBO ACTUEL (RAPIDE, BASE DE DONNÉES)
# =====================================================================
from django.db.models import Sum, Count
from dashboard.kobo_config import FORM_UIDS

FORM_TITLES = {
    "eleves_registre": "Registre Élèves",
    "eleves_abs_q": "Absences Quotidiennes Élèves",
    "eleves_abs_m": "Absences Mensuelles Élèves",
    "ens_registre": "Registre Enseignants",
    "ens_abs_q": "Absences Quotidiennes Enseignants",
    "ens_abs_m": "Absences Mensuelles Enseignants",
}

@login_required
def dashboard_view(request):
    # Calcule les vrais stats depuis la base de données
    total_absences = AbsenceQuotidienneEleve.objects.aggregate(total=Sum("total_absences"))["total"] or 0

    # Ne montre dans le menu QUE les formulaires qui ont un UID configuré
    forms_list = [
        {"uid": key, "title": FORM_TITLES.get(key, key)}
        for key, uid in FORM_UIDS.items() if uid
    ]

    global_stats = {
        "total_records": Eleve.objects.count() + Enseignant.objects.count(),
        "total_present": Eleve.objects.count(),
        "total_absences": total_absences,
        "total_forms": len(forms_list)
    }

    return render(request, "dashboard/dashboard_table.html", {
        "forms_list": forms_list,
        "global_stats": global_stats,
        "can_edit": request.user.is_superuser or request.user.role in ['Directeur', 'Administrateur']
    })

# --- APIs pour les tableaux interactifs ---
import json
# ... vos autres imports ...

# --- APIs pour les tableaux interactifs ---
@login_required
def api_eleves(request, pk=None):
    if request.method == 'GET':
        if pk:
            # Récupérer UN SEUL élève (pour le formulaire d'édition)
            try:
                eleve = Eleve.objects.select_related('ecole').get(pk=pk)
                data = {
                    'id': eleve.id, 'numero_reg': eleve.numero_reg, 'nom_prenom': eleve.nom_prenom,
                    'nni': eleve.nni, 'sexe': eleve.sexe, 'tel': eleve.tel, 'classe': eleve.classe,
                    'observations': eleve.observations, 'enseignant': eleve.enseignant
                }
                return JsonResponse(data)
            except Eleve.DoesNotExist:
                return JsonResponse({'error': 'Non trouvé'}, status=404)

        # Récupérer TOUT (pour le tableau)
        data = list(Eleve.objects.select_related('ecole').values(
            'id', 'numero_reg', 'nom_prenom', 'nni', 'sexe', 'tel', 'classe',
            'observations', 'enseignant', 'ecole__nom_ecole'
        ))
        return JsonResponse(data, safe=False)

    # --- SÉCURITÉ : Seuls les admins peuvent modifier/supprimer ---
    is_admin = request.user.is_superuser or request.user.role in ['Directeur', 'Administrateur']
    if not is_admin:
        return JsonResponse({'error': 'Accès interdit'}, status=403)

    # --- MODIFIER (PUT) ---
    if request.method == 'PUT' and pk:
        try:
            eleve = Eleve.objects.get(pk=pk)
            data = json.loads(request.body)

            eleve.numero_reg = data.get('numero_reg', eleve.numero_reg)
            eleve.nom_prenom = data.get('nom_prenom', eleve.nom_prenom)
            eleve.nni = data.get('nni', eleve.nni)
            eleve.sexe = data.get('sexe', eleve.sexe)
            eleve.tel = data.get('tel', eleve.tel)
            eleve.classe = data.get('classe', eleve.classe)
            eleve.observations = data.get('observations', eleve.observations)
            eleve.enseignant = data.get('enseignant', eleve.enseignant)

            # Si on change l'école (géré séparément car c'est une ForeignKey)
            nom_ecole = data.get('ecole__nom_ecole')
            if nom_ecole:
                ecole, _ = Ecole.objects.get_or_create(nom_ecole=nom_ecole, defaults={"nouveau_code_ecole": "AUTO_"+nom_ecole[:5]})
                eleve.ecole = ecole

            eleve.save()
            return JsonResponse({'success': True})
        except Eleve.DoesNotExist:
            return JsonResponse({'error': 'Non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    # --- SUPPRIMER (DELETE) ---
    if request.method == 'DELETE' and pk:
        try:
            eleve = Eleve.objects.get(pk=pk)
            eleve.delete()
            return JsonResponse({'success': True})
        except Eleve.DoesNotExist:
            return JsonResponse({'error': 'Non trouvé'}, status=404)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt  # Nécessaire si vous appelez l'API depuis un frontend différent (ex: React/Vue)
from django.db import transaction

from dashboard.models import Ecole, Enseignant

# On crée un petit mixin pour renvoyer du JSON propre si non connecté
def login_required_json(view_func):
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentification requise'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapped_view

@login_required_json
@csrf_exempt # Retirez ce décorateur si vous appelez l'API depuis le même domaine (templates Django)
def api_enseignants(request, pk=None):

    # ==========================================
    # LECTURE (GET)
    # ==========================================
    if request.method == 'GET':
        if pk:
            try:
                ens = Enseignant.objects.select_related('ecole').get(pk=pk)
                return JsonResponse({
                    'id': ens.id, 'numero_reg': ens.numero_reg, 'nom_prenom': ens.nom_prenom,
                    'sexe': ens.sexe, 'mle': ens.mle, 'langue_travail': ens.langue_travail,
                    'ecole_id': ens.ecole.id if ens.ecole else None, # On renvoie l'ID
                    'ecole__nom_ecole': ens.ecole.nom_ecole if ens.ecole else None
                })
            except Enseignant.DoesNotExist:
                return JsonResponse({'error': 'Enseignant non trouvé'}, status=404)

        data = list(Enseignant.objects.select_related('ecole').values(
            'id', 'numero_reg', 'nom_prenom', 'sexe', 'mle', 'langue_travail', 'ecole__nom_ecole'
        ))
        return JsonResponse(data, safe=False)

    # ==========================================
    # PERMISSIONS (Pour PUT et DELETE)
    # ==========================================
    is_admin = request.user.is_superuser or getattr(request.user, 'role', '') in ['Directeur', 'Administrateur']
    if not is_admin:
        return JsonResponse({'error': 'Accès interdit'}, status=403)

    # ==========================================
    # SUPPRESSION (DELETE)
    # ==========================================
    if request.method == 'DELETE' and pk:
        try:
            Enseignant.objects.get(pk=pk).delete()
            return JsonResponse({'success': True})
        except Enseignant.DoesNotExist:
            return JsonResponse({'error': 'Enseignant non trouvé'}, status=404)

    # ==========================================
    # MISE À JOUR (PUT)
    # ==========================================
    if request.method == 'PUT' and pk:
        try:
            with transaction.atomic(): # Sécurité lors de la modification
                ens = Enseignant.objects.select_related('ecole').get(pk=pk)
                data = json.loads(request.body)

                # Mise à jour des champs simples
                ens.numero_reg = data.get('numero_reg', ens.numero_reg)
                ens.nom_prenom = data.get('nom_prenom', ens.nom_prenom)
                ens.sexe = data.get('sexe', ens.sexe)
                ens.mle = data.get('mle', ens.mle)
                ens.langue_travail = data.get('langue_travail', ens.langue_travail)

                # MISE À JOUR DE L'ÉCOLE (Sécurisé avec l'ID)
                ecole_id = data.get('ecole_id')
                if ecole_id:
                    # On vérifie que l'école existe bien avant de l'affecter
                    ens.ecole = Ecole.objects.get(pk=ecole_id)
                elif ecole_id is None and 'ecole_id' in data:
                    # Si le front envoie explicitement null, on détache l'enseignant de son école
                    ens.ecole = None

                ens.save()
                return JsonResponse({'success': True})

        except Ecole.DoesNotExist:
            return JsonResponse({'error': 'École spécifiée introuvable'}, status=400)
        except Enseignant.DoesNotExist:
            return JsonResponse({'error': 'Enseignant non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def api_abs_eleves_q(request, pk=None):
    if request.method == 'GET':
        data = list(AbsenceQuotidienneEleve.objects.select_related('eleve__ecole').values(
            'id', 'date_absence', 'eleve__nom_prenom', 'eleve__classe', 'total_absences', 'eleve__ecole__nom_ecole'
        ))
        return JsonResponse(data, safe=False)

# Pour les autres absences, on les met à jour aussi pour la suppression de base
@login_required
def api_abs_eleves_m(request, pk=None):

    # --- 1. RECUPERATION DES DONNEES (GET) ---
    if request.method == 'GET':
        # On récupère toutes les absences mensuelles
        # select_related permet de récupérer l'élève et son école en une seule requête SQL (très rapide)
        queryset = AbsenceMensuelleEleve.objects.select_related('eleve__ecole').all().order_by('-mois')

        # On convertit en dictionnaire pour l'API
        # Les clés correspondent EXACTEMENT aux "data: '...'" de ton JavaScript
        data = list(queryset.values(
            'id',                      # Indispensable pour les boutons Modifier/Supprimer
            'mois',                   # data: 'mois'
            'total_absences',         # data: 'total_absences'
            'eleve__nom_prenom',      # data: 'eleve__nom_prenom'
            'eleve__classe',          # data: 'eleve__classe'
            'eleve__ecole__nom_ecole' # data: 'eleve__ecole__nom_ecole'
        ))
        return JsonResponse(data, safe=False)

    # --- 2. DROITS ADMIN ---
    is_admin = request.user.is_superuser or request.user.role in ['Directeur', 'Administrateur']
    if not is_admin: return JsonResponse({'error': 'Interdit'}, status=403)

    # --- 3. SUPPRESSION (DELETE) ---
    if request.method == 'DELETE' and pk:
        try:
            AbsenceMensuelleEleve.objects.get(pk=pk).delete()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'error': 'Non trouvé'}, status=404)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def api_abs_ens_q(request, pk=None):

    if request.method == 'GET':

        data = list(
            AbsenceQuotidienneEnseignant.objects.select_related('enseignant')
            .values(
                'id',
                'date_absence',
                'abs_justifiees',
                'abs_non_justifiees',
                'enseignant__nom_prenom',
                'enseignant__mle',
                'enseignant__ecole__nom_ecole',
            )
        )

        return JsonResponse(data, safe=False)

    is_admin = request.user.is_superuser or request.user.role in ['Directeur', 'Administrateur']
    if not is_admin:
        return JsonResponse({'error': 'Interdit'}, status=403)

    if request.method == 'DELETE' and pk:
        try:
            AbsenceQuotidienneEnseignant.objects.get(pk=pk).delete()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'error': 'Non trouvé'}, status=404)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def api_abs_ens_m(request, pk=None):

    if request.method == 'GET':

        data = list(
            AbsenceMensuelleEnseignant.objects.select_related('enseignant')
            .values(
                'id',
                'mois',
                'abs_justifiees',
                'abs_non_justifiees',
                'enseignant__nom_prenom',
                'enseignant__mle',
                'enseignant__ecole__nom_ecole',
            )
        )

        return JsonResponse(data, safe=False)

    is_admin = request.user.is_superuser or request.user.role in ['Directeur', 'Administrateur']
    if not is_admin:
        return JsonResponse({'error': 'Interdit'}, status=403)

    if request.method == 'DELETE' and pk:
        try:
            AbsenceMensuelleEnseignant.objects.get(pk=pk).delete()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'error': 'Non trouvé'}, status=404)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

# --- 1. LISTE DES ARTICLES ---

def blog_view(request):
    # 1. Récupérer TOUS les articles pour la liste principale
    posts = BlogPost.objects.all().order_by('-created_at')

    # 2. Séparer images et vidéos
    images = posts.filter(image__isnull=False).exclude(image="")
    videos = posts.filter(video_url__isnull=False).exclude(video_url="")

    # 3. Pagination uniquement sur les articles avec image
    paginator = Paginator(images, 3)  # 3 articles par page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Pagination vidéos
    paginator_videos = Paginator(videos, 3)  # 3 vidéos par page
    page_number_videos = request.GET.get('video_page', 1)
    video_page_obj = paginator_videos.get_page(page_number_videos)



    # 5. Contexte
    context = {
        'page_obj': page_obj,       # Grille principale (images)
        'video_page_obj': video_page_obj,  # vidéos paginées


    }

    return render(request, 'dashboard/blog.html', context)

# --- 2. DÉTAIL D'UN ARTICLE ---

def blog_detail_view(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    return render(request, 'dashboard/blog_detail.html', {'post': post})


# --- 4. RENDER AJAX FORM CREATE ---
@login_required
def render_create_post_form(request):
    allowed_roles = ['Directeur', 'Administrateur', 'Superviseur']
    if not (request.user.is_superuser or request.user.role in allowed_roles):
        return JsonResponse({'html': '<p>Accès réservé.</p>'}, status=403)

    form = BlogPostForm()
    html = render_to_string('dashboard/create_form_only.html', {'form': form}, request=request)
    return JsonResponse({'html': html})


# --- 5. MODIFIER UN ARTICLE ---

@login_required
def edit_post_view(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    old_video_url = post.video_url  # 🔥 SAUVEGARDE

    allowed_roles = ['Administrateur', 'Superviseur']

    if not (
        post.author == request.user
        or request.user.role in allowed_roles
        or request.user.is_superuser
    ):
        messages.error(request, "Vous n'avez pas la permission de modifier cet article.")
        return redirect('blog')

    if request.method == "POST":
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)

            # 🔥 SI AUCUNE NOUVELLE VIDÉO → ON GARDE L’ANCIENNE
            if not form.cleaned_data.get('video_url'):
                post.video_url = old_video_url

            post.save()
            messages.success(request, "Article modifié avec succès.")
            return redirect('blog')
    else:
        form = BlogPostForm(instance=post)

    return render(request, 'dashboard/edit_post.html', {
        'form': form,
        'post': post
    })


# --- 3. CRÉER UN ARTICLE ---
@login_required
def create_post_view(request):
    allowed_roles = ['Directeur', 'Administrateur', 'Superviseur']
    if not (request.user.is_superuser or request.user.role in allowed_roles):
        messages.warning(request, "Vous n'avez pas le droit de publier.")
        return redirect('blog')  # 🔹 remplacé /blog/ par nom d'URL

    if request.method == "POST":
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()  # génère le slug si vide
            messages.success(request, "Article publié avec succès !")
            return redirect('blog')  # 🔹 idem
    else:
        form = BlogPostForm()

    return render(request, "dashboard/create_post.html", {"form": form})


# --- 6. SUPPRIMER UN ARTICLE ---
@login_required
def delete_post_view(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    allowed_roles = ['Administrateur', 'Superviseur']

    if not (post.author == request.user or request.user.role in allowed_roles or request.user.is_superuser):
        messages.error(request, "Vous n'avez pas la permission de supprimer cet article.")
        return redirect('/blog/')

    post.delete()
    messages.success(request, "Article supprimé avec succès.")
    return redirect('/blog/')


# --- 7. API AJAX : Liste partielle des articles ---

def render_blog_list(request):
    try:
        # 1️⃣ Tous les posts
        posts = BlogPost.objects.all().order_by('-created_at')

        # 2️⃣ Séparation ARTICLES (image uniquement) / VIDÉOS
        image_posts = posts.filter(
            image__isnull=False
        )

        video_posts = posts.filter(
            video_url__isnull=False
        )

        # 3️⃣ Pagination ARTICLES
        paginator = Paginator(image_posts, 3)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # 4️⃣ Pagination VIDÉOS
        paginator_videos = Paginator(video_posts, 3)
        video_page_number = request.GET.get('video_page', 1)
        video_page_obj = paginator_videos.get_page(video_page_number)

        # 5️⃣ Rendu HTML partiel
        html = render_to_string(
            'dashboard/blog_list_partial.html',
            {
                'page_obj': page_obj,               # articles image
                'video_page_obj': video_page_obj,   # vidéos
            },
            request=request
        )

        return JsonResponse({'html': html})

    except Exception as e:
        print("❌ Erreur render_blog_list :", e)
        return JsonResponse({'html': 'Erreur serveur'}, status=500)




def videos_list_view(request):
    videos = BlogPost.objects.filter(video_url__isnull=False).order_by('-created_at')
    return render(request, "dashboard/videos_list.html", {"videos": videos})


def video_detail_view(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    return render(request, "dashboard/video_detail.html", {"post": post})
