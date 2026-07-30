"""
URL configuration for config project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


def react_index(request, *args, **kwargs):
    index = settings.REACT_BUILD_DIR / 'index.html'
    if index.exists():
        return FileResponse(open(index, 'rb'), content_type='text/html')
    raise Http404('Frontend non buildé. Lancez : npm run build')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('core.urls')),
    path('api/', include('catalogue.urls')),
    path('api/', include('stock.urls')),
    path('api/', include('facturation.urls')),
    path('api/', include('depenses.urls')),
    path('api/', include('caisse.urls')),
    path('api/', include('dashboard.urls')),
    path('api/', include('apresvente.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Catch-all : toutes les routes non-API/admin/media/static -> React index.html
# (le build n'existe qu'en production ; en dev le frontend tourne via `npm run dev`)
urlpatterns += [
    re_path(r'^(?!api/|admin/|media/|static/).*$', react_index),
]
