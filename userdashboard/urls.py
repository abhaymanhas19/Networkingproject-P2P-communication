"""
URL configuration for userdashboard project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.views.generic.base import TemplateView
from django.urls import path, include

from django.conf.urls.static import static

from userdashboard.view import index_view, logout_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('baton/', include('baton.urls')),
    path('logout/', view=logout_view, name='logout'),

    path("", view=index_view, name="index"),

    # All Auth
    path("accounts/", include("allauth.urls")),
    #path("accounts/profile/", TemplateView.as_view(template_name="profile.html")),

    path("i18n/", include("django.conf.urls.i18n")),


    #Apps
    path("apps/" , include("apps.urls")),

    #Custom
    path("custom/" , include("custom.urls")),

    # Layouts
    path("layouts/", include("layouts.urls")),

    #Elements
    path("elements/", include("elements.urls")),

    #Docs
    #path("docs/", include("documentation.urls"))


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
