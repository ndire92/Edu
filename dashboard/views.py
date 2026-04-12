from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
import requests
import pandas as pd
from django.core.mail import send_mail
from django.conf import settings
import plotly.express as px
from .models import CustomUser, Correction, BlogPost
from .forms import CustomUserChangeForm, BlogPostForm

# ==================================================
# CONFIGURATION GLOBALE
# ==================================================
API_TOKEN = "f585e3b36fa1739f8b0a27ba559f0992d2bf1d6f"
FORMS_CONFIG = [
    {'uid': 'aJtfPktL7aZKg2t7qZdp7v', 'title': 'Formulaire Principal'},
]

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

# ==================================================
# FONCTION COMMUNE (Moteur de données)
# ==================================================
# DASHBOARD KOBO
# ==========================

def _get_dashboard_data(request, forms_config=FORMS_CONFIG):
    """
    Fonction principale pour récupérer et traiter les données des formulaires.
    Intègre les corrections locales pour que les graphiques et stats soient à jour.
    """
    search_query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    filter_month = request.GET.get('filter_month', '')
    filter_teacher = request.GET.get('filter_teacher', '')
    filter_type = request.GET.get('filter_type', '')

    # Colonnes techniques à supprimer
    colonnes_a_supprimer = [
        '_validation_status', 'meta/instanceID', 'meta/rootUuid', '_xform_id_string',
        '_bamboo_dataset_id', '_tags', '__version__', '_status',
        '_submitted_by', '_geolocation', 'formhub/uuid'
    ]

    all_tables_data = []

    for form in forms_config:
        form_uid = form['uid']
        form_title = form.get('title', 'Titre Par Défaut')

        # --- 1. Récupération API Kobo ---
        url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_uid}/data/"
        headers = {"Authorization": f"Token {API_TOKEN}"}
        all_records = []

        while url and len(all_records) < 1000:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                all_records.extend(data['results'])
                url = data.get('next')
            else:
                break

        df = pd.DataFrame(all_records)

        table_context = {
            'uid': form_uid,
            'table_html_id': 'card-' + form_uid,
            'title': form_title,
            'headers': [],
            'page_obj': None,
            'chart_bar': None,
            'chart_line': None,
            'chart_pie': None,
            'total': 0,
            'stats': {'total': 0, 'present': 0, 'absent': 0, 'late': 0},
            'available_months': [],
            'available_teachers': []
        }

        if not df.empty:
            # --- 2. Renommage ID ---
            if '_id' in df.columns: df.rename(columns={'_id': 'id'}, inplace=True)
            if '_uuid' in df.columns: df.rename(columns={'_uuid': 'uuid'}, inplace=True)

            # --- 3. Gestion des images ---
            if '_attachments' in df.columns:
                for index, row in df.iterrows():
                    attachments = row['_attachments']
                    if isinstance(attachments, list):
                        for att in attachments:
                            question_name = att.get('question_xpath')
                            url_img = att.get('download_medium_url')
                            if url_img: url_img += f"?token={API_TOKEN}"
                            if question_name and url_img and question_name in df.columns:
                                df.at[index, question_name] = url_img
                df.drop(columns=['_attachments'], inplace=True)

            # --- 4. Suppression colonnes techniques ---
            df.drop(columns=colonnes_a_supprimer, inplace=True, errors='ignore')

            # --- 5. Colonnes pertinentes ---
            cols_pertinentes = [col for col in df.columns if not (df[col].astype(str).str.startswith('http', na=False).any())]

            # Colonne date
            col_date = None
            for col in df.columns:
                if 'date' in col.lower() or 'start' in col.lower():
                    col_date = col; break
            if not col_date and '_submission_time' in df.columns:
                col_date = '_submission_time'

            if col_date:
                df[col_date] = pd.to_datetime(df[col_date], errors='coerce')
                df.sort_values(col_date, inplace=True)
                df['MonthStr'] = df[col_date].dt.strftime('%Y-%m')
                table_context['available_months'] = sorted(df['MonthStr'].unique())

            # Colonne nom
            col_nom = None
            for col in cols_pertinentes:
                if 'nom' in col.lower() or 'name' in col.lower():
                    col_nom = col; break
            if not col_nom: col_nom = cols_pertinentes[0] if cols_pertinentes else None

            # Colonne observation/statut
            col_obs = None
            for col in df.columns:
                if 'obs' in col.lower() or 'statut' in col.lower() or 'presence' in col.lower():
                    col_obs = col; break

            # Colonne enseignant
            col_teacher = None
            for col in cols_pertinentes:
                if 'ens' in col.lower() or 'prof' in col.lower() or 'teacher' in col.lower() or 'classe' in col.lower():
                    col_teacher = col; break
            if col_teacher:
                table_context['available_teachers'] = sorted(df[col_teacher].dropna().unique())

            # --- 6. Application des filtres ---
            df_filtered = df.copy()
            if filter_month and col_date:
                df_filtered = df_filtered[df_filtered['MonthStr'] == filter_month]
            if filter_teacher and col_teacher:
                df_filtered = df_filtered[df_filtered[col_teacher] == filter_teacher]
            if filter_type and col_obs:
                df_filtered = df_filtered[df_filtered[col_obs].astype(str).str.upper() == filter_type.upper()]

            # --- 6b. Appliquer corrections locales avant stats et graphiques ---
            corrs = Correction.objects.all()
            cor_map = {}
            for c in corrs:
                if c.kobo_id not in cor_map:
                    cor_map[c.kobo_id] = {}
                cor_map[c.kobo_id][c.column_name] = c.new_value

            for idx, row in df_filtered.iterrows():
                r_uuid = row.get('uuid')
                if r_uuid and r_uuid in cor_map:
                    for col, new_val in cor_map[r_uuid].items():
                        df_filtered.at[idx, col] = new_val

            # --- 7. Graphiques ---
            # Barre
            if col_nom and not df_filtered.empty:
                count_abs = df_filtered[col_nom].value_counts().reset_index()
                count_abs.columns = [col_nom, 'Nb_Absences']
                count_abs['Nb_Absences'] = pd.to_numeric(count_abs['Nb_Absences'], errors='coerce').fillna(0)
                if not count_abs.empty:
                    fig_bar = px.bar(count_abs, x='Nb_Absences', y=col_nom, orientation='h',
                                       title=f"Top {col_nom}", text='Nb_Absences', color='Nb_Absences',
                                       color_continuous_scale='Viridis')
                    fig_bar.update_yaxes(autorange="reversed")
                    table_context['chart_bar'] = fig_bar.to_html(full_html=False, include_plotlyjs=False)

            # Courbe
            if col_date and not df_filtered.empty:
                df_line = df_filtered.dropna(subset=[col_date]).copy()
                if not df_line.empty:
                    df_evol = df_line.groupby(col_date).size().reset_index(name='Total')
                    fig_line = px.line(df_evol, x=col_date, y='Total', markers=True)
                    table_context['chart_line'] = fig_line.to_html(full_html=False, include_plotlyjs=False)

            # Camembert
            if col_obs and not df_filtered.empty:
                df_pie = df_filtered.copy()

                def normalize_status(x):
                    v = str(x).lower()
                    if v == 'p' or 'present' in v: return 'Présent'
                    if v == 'a' or 'abs' in v: return 'Absent'
                    if v == 'r' or 'retard' in v or 'late' in v: return 'Retard'
                    return None

                df_pie['Categorie'] = df_pie[col_obs].apply(normalize_status)
                df_pie = df_pie[df_pie['Categorie'].notna()]

                if not df_pie.empty:
                    count_obs = df_pie['Categorie'].value_counts().reset_index()
                    count_obs.columns = ['Type', 'Nombre']
                    count_obs['Type'] = pd.Categorical(count_obs['Type'], ['Présent', 'Absent', 'Retard'])
                    count_obs.sort_values('Type', inplace=True)
                    color_map = {'Présent': '#2ecc71', 'Absent': '#e74c3c', 'Retard': '#f1c40f'}
                    fig_pie = px.pie(count_obs, values='Nombre', names='Type',
                                     title=f"Répartition : {col_obs}", hole=0.3,
                                     color='Type', color_discrete_map=color_map)
                    table_context['chart_pie'] = fig_pie.to_html(full_html=False, include_plotlyjs=False)

            # --- 8. Recherche & Pagination ---
            df_display = df_filtered.astype(str)
            if search_query:
                mask = df_display.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                df_display = df_display[mask]

            if not df_display.empty:
                # Stats
                stats = {'total': len(df_display), 'present': 0, 'absent': 0, 'late': 0}
                if col_obs:
                    df_str_obs = df_display[col_obs].astype(str).str.upper()
                    stats['present'] = int(df_str_obs.str.contains('P').sum())
                    stats['absent'] = int(df_str_obs.str.contains('A').sum())
                    stats['late'] = int(df_str_obs.str.contains('R').sum())
                table_context['stats'] = stats

                # Préparer records pour template
                records = df_display.to_dict('records')
                for record in records:
                    # Appliquer corrections aux records pour l'affichage
                    r_uuid = record.get('uuid')
                    if r_uuid and r_uuid in cor_map:
                        record.update(cor_map[r_uuid])
                    record['kobo_id'] = record.get('uuid')  # Pour template buttons

                paginator = Paginator(records, 20)
                table_context['page_obj'] = paginator.get_page(page_number)
                table_context['headers'] = df_display.columns.tolist()
                table_context['total'] = paginator.count

        all_tables_data.append(table_context)

    return {
        'all_tables': all_tables_data,
        'query': search_query,
        'current_month': filter_month,
        'current_teacher': filter_teacher,
        'current_type': filter_type
    }



# ==========================
# VUE PRINCIPALE DASHBOARD
# ==========================
@login_required
def dashboard_view(request):
    full_data = _get_dashboard_data(request, forms_config=FORMS_CONFIG)
    global_stats = {'total_records': 0, 'total_present': 0, 'total_absences': 0, 'total_forms': 0}

    for table in full_data.get('all_tables', []):
        stats = table.get('stats', {})
        global_stats['total_records'] += stats.get('total', 0)
        global_stats['total_present'] += stats.get('present', 0)
        global_stats['total_absences'] += stats.get('absent', 0)
        global_stats['total_forms'] += 1

    context = {
        'global_stats': global_stats,
        'all_tables': [],  # On cache au chargement, chargement via API
        'forms_list': FORMS_CONFIG,
        'can_edit': request.user.is_superuser or request.user.role in ['Directeur', 'Administrateur']
    }

    return render(request, 'dashboard/dashboard_table.html', context)




# ==========================
# EDIT / DELETE KOBO
# ==========================
@login_required
def edit_record(request, kobo_id):
    form_uid = FORMS_CONFIG[0]['uid']
    url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_uid}/data/{kobo_id}/"
    headers = {"Authorization": f"Token {API_TOKEN}"}

    if request.method == "POST":
        for key, value in request.POST.items():
            if key == 'csrfmiddlewaretoken':
                continue
            Correction.objects.update_or_create(
                kobo_id=kobo_id,
                column_name=key,
                defaults={'new_value': value}
            )
        return redirect("/dashboard/")
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return HttpResponse("Erreur récupération Kobo")

    data = response.json()
    corrections = Correction.objects.filter(kobo_id=kobo_id)
    corrections_dict = {c.column_name: c.new_value for c in corrections}
    editable_data = {k: corrections_dict.get(k, v) for k, v in data.items() if not k.startswith('_') and not k.startswith('meta/')}
    return render(request, 'dashboard/edit.html', {'kobo_id': kobo_id, 'data': editable_data})


@login_required
def delete_record(request, kobo_id):
    form_uid = FORMS_CONFIG[0]['uid']
    url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_uid}/data/{kobo_id}/"
    headers = {"Authorization": f"Token {API_TOKEN}"}

    response = requests.delete(url, headers=headers)
    if response.status_code in [200, 204]:
        Correction.objects.filter(kobo_id=kobo_id).delete()
        messages.success(request, "Enregistrement supprimé.")
    else:
        messages.error(request, f"Erreur API {response.status_code}")
    return redirect("/dashboard/")
# ==================================================
# ==========================
# VUES API
# ==========================
@login_required
def api_dashboard_data(request):
    """
    API AJAX : Charge TOUS les tableaux Kobo.
    Utile pour le scrollIntoView ou le refresh dynamique.
    """
    uid = request.GET.get('uid')  # UID demandé pour scroll futur
    context = _get_dashboard_data(request, forms_config=FORMS_CONFIG)

    # Rendu du template partiel (Zone tableau)
    html_content = render_to_string('dashboard/table_content.html', context, request=request)
    
    return JsonResponse({'html': html_content})


# ==========================
# VUES PRINCIPALES
# ==========================

def home(request):
    """Vue d'accueil (Graphiques globaux)"""
    context = _get_dashboard_data(request)
    return render(request, 'dashboard/home.html', context)



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
