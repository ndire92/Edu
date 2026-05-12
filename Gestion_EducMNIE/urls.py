# Gestion_EducMNIE/urls.py

from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns  # <-- AJOUT TRÈS IMPORTANT
from django.contrib.auth import views as auth_views

# Import vues dashboard
from dashboard import views

# =============================
# 1. URLs qui NE CHANGENT PAS de langue (APIs, Admin Django, Media)
# =============================
urlpatterns = [
    # --- APIs pour les tableaux interactifs ---
    path('api/eleves/', views.api_eleves, name='api_eleves'),
    path('api/eleves/<int:pk>/', views.api_eleves, name='api_eleves_detail'),
    path('api/enseignants/', views.api_enseignants, name='api_enseignants'),
    path('api/enseignants/<int:pk>/', views.api_enseignants, name='api_enseignants_detail'),
    path('api/abs_eleves_q/', views.api_abs_eleves_q, name='api_abs_eleves_q'),
    path('api/abs_eleves_q/<int:pk>/', views.api_abs_eleves_q, name='api_abs_eleves_q_detail'),
    path('api/abs_eleves_m/', views.api_abs_eleves_m, name='api_abs_eleves_m'),
    path('api/abs_eleves_m/<int:pk>/', views.api_abs_eleves_m, name='api_abs_eleves_m_detail'),
    path('api/abs_ens_q/', views.api_abs_ens_q, name='api_abs_ens_q'),
    path('api/abs_ens_q/<int:pk>/', views.api_abs_ens_q, name='api_abs_ens_q_detail'),
    path('api/abs_ens_m/', views.api_abs_ens_m, name='api_abs_ens_m'),
    path('api/abs_ens_m/<int:pk>/', views.api_abs_ens_m, name='api_abs_ens_m_detail'),
    path('api/home-data/', views.api_home_data, name='api_home_data'),

    # --- Admin Django & Outils ---
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('i18n/', include('django.conf.urls.i18n')), # Obligatoire pour le formulaire de langue
]

# --- Fichiers statiques (MEDIA) en DEBUG ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# =============================
# 2. URLs QUI CHANGENT DE LANGUE (Pages HTML)
# =============================
urlpatterns += i18n_patterns(
    # --- Accueil & Dashboard ---
    path('', views.home_view, name='home'), # La vraie page d'accueil Power BI
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # --- Authentification & Profil ---
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),

    # --- Blog & Vidéos ---
    path('blog/', views.blog_view, name='blog'),
    path('blog/create/', views.create_post_view, name='create_post'),
    path('blog/render-form/', views.render_create_post_form, name='render_create_post_form'),
    path('blog/render-list/', views.render_blog_list, name='render_blog_list'),
    path('blog/edit/<int:post_id>/', views.edit_post_view, name='edit_post'),
    path('blog/delete/<int:post_id>/', views.delete_post_view, name='delete_post'),
    path('blog/<str:slug>/', views.blog_detail_view, name='blog_detail'),
    path('videos/', views.videos_list_view, name='videos_list'),
    path('videos/<str:slug>/', views.video_detail_view, name='video_detail'),

    # --- Admin Panel Personnalisé ---
    path('admin-panel/', views.admin_view, name='admin_panel'),
    path('admin-panel/toggle/<int:user_id>/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin-panel/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/edit/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('admin/update-role/<int:user_id>/', views.admin_update_role, name='admin_update_role'),

    # --- Mot de passe oublié ---
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
)
