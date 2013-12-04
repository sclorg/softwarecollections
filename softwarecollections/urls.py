from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.contrib import admin
admin.autodiscover()

from .views import SCLsList

urlpatterns = i18n_patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^faq/$', RedirectView.as_view(url='/en/docs/faq/')),
    url(r'^directory/$', SCLsList.as_view(), name='SCLsList'),
    url('', include('softwarecollections.fas.urls', namespace='fas')),
    url(r'^((?P<path>.*)/|)$',  'softwarecollections.pages.views.page', name='page',
                        kwargs={'template_dir':'pages'}),
)
