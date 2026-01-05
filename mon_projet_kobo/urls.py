from django.contrib import admin
from django.urls import path,include
from dashboard import views  # On importe nos vues

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),

    path('', views.home, name='home'), # La page d'accueil pointera vers ta vue
]