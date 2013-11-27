from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.contrib import admin
admin.autodiscover()

from .views import SCLsList, page

urlpatterns = i18n_patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^faq/$', RedirectView.as_view(url='/en/docs/faq/')),
    url(r'^directory/$', SCLsList.as_view(), name='SCLsList'),
    url(r'^((?P<path>.*)/|)$', page, name='page'),
)
