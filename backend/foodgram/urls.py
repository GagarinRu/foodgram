from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

from recipes.views import get_short_link


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<slug:slug>/', get_short_link, name='shortlink'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
