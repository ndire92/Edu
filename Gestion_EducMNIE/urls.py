# Gestion_EducMNIE/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
# Import vues dashboard
from dashboard import views

# =============================
# URL PRINCIPALES
# =============================
urlpatterns = [

    # --- 1. Accueil & Dashboard ---
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # --- 2. Authentification & Profil ---
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/delete/', views.delete_account_view, name='delete_account'),

    # --- 3. Edition / Suppression des données Kobo ---
    path('edit/<str:kobo_id>/', views.edit_record, name='edit_record'),
    path('delete/<str:kobo_id>/', views.delete_record, name='delete_record'),

    # --- 4. Blog ---
    path('blog/', views.blog_view, name='blog'),
    path('blog/create/', views.create_post_view, name='create_post'),
    path('blog/render-form/', views.render_create_post_form, name='render_create_post_form'),
    path('blog/render-list/', views.render_blog_list, name='render_blog_list'),
    path('blog/edit/<int:post_id>/', views.edit_post_view, name='edit_post'),
    path('blog/delete/<int:post_id>/', views.delete_post_view, name='delete_post'),
    path('blog/<str:slug>/', views.blog_detail_view, name='blog_detail'),

    path('videos/', views.videos_list_view, name='videos_list'),
    path('videos/<str:slug>/', views.video_detail_view, name='video_detail'),

    # --- 5. API AJAX ---
    path('api/dashboard-data/', views.api_dashboard_data, name='api_dashboard_data'),

    # --- ADMIN PANEL PERSONNALISÉ ---
    path('admin-panel/', views.admin_view, name='admin_panel'),
    path('admin-panel/toggle/<int:user_id>/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin-panel/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/edit/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),

    # --- ADMIN DJANGO ---
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),

    # --- 8. I18n (Traduction / langues) ---
    path('i18n/', include('django.conf.urls.i18n')),


    # MOT DE PASSE OUBLIÉ
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='auth/password_reset.html'
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='auth/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='auth/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='auth/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]

# --- 9. Fichiers statiques (MEDIA) en DEBUG ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
