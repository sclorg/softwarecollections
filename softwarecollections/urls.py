from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.contrib import admin
admin.autodiscover()

from softwarecollections import fas, scls

urlpatterns = i18n_patterns('',
    url(r'^admin/',     include(admin.site.urls)),
    url(r'^faq/$',      RedirectView.as_view(url='/en/docs/faq/')),
    url(r'^directory/', include(scls.urls)),
    url('',             include(fas.urls)),
    url(r'^((?P<path>.*)/|)$', 'softwarecollections.pages.views.page', name='page',
                        kwargs={'template_dir':'pages'}),
)
