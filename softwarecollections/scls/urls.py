from django.conf.urls import patterns, url

urlpatterns = patterns('softwarecollections.scls.views',
    url(r'^$',                          'all',      name='all'),
    url(r'^user/$',                     'my',       name='my'),
    url(r'^user/(?P<username>.*)/$',    'user',     name='user'),
    url(r'^new/$',                      'new',      name='new'),
    url(r'^detail/(?P<slug>.*)/$',      'detail',   name='detail'),
)
