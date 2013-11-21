from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = i18n_patterns('',
    # Examples:
    # url(r'^$', 'softwarecollections.views.home', name='home'),
    # url(r'^softwarecollections/', include('softwarecollections.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('cms.urls')),
)
