from django.contrib import admin
from django.urls import path
from dashboard import views  # On importe nos vues

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'), # La page d'accueil pointera vers ta vue
]