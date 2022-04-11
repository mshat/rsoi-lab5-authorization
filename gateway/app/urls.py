from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += [
    path('api/v1/', include('gateway.urls')),
    path('', include('gateway.urls')),
]
