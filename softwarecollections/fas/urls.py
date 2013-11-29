from django.conf.urls import patterns, url

urlpatterns = patterns('softwarecollections.fas.views',
    url(r'^login/$',    'login',    name='login'),
    url(r'^complete/$', 'complete', name='complete'),
    url(r'^logout/$',   'logout',   name='logout'),
)
