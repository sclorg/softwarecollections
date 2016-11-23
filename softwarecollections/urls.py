"""softwarecollections URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.views.static import serve
from django.contrib import admin
admin.autodiscover()

from softwarecollections import scls
from softwarecollections.pages.views import page

urlpatterns = i18n_patterns(
    url(r'^admin/',     include(admin.site.urls)),
    url(r'^captcha/',   include('captcha.urls')),
    url(r'^faq/$',      RedirectView.as_view(url='/en/docs/faq/', permanent=True)),
    url(r'^scls/',      include('softwarecollections.scls.urls', namespace='scls')),
    url('',             include('fas.urls')),
    url(r'^((?P<path>.*)/|)$', page, name='page', kwargs={'template_dir':'pages'}),
)

if settings.DEBUG:
    urlpatterns += [
        url(r'^repos/(?P<path>.*)$', serve, {'document_root': settings.REPOS_ROOT, 'show_indexes': True}),
        url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ]
