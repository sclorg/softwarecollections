from django.conf.urls import patterns, url

urlpatterns = patterns('softwarecollections.scls.views',
    url(r'^$',                          'list_all',     name='list_all'),
    url(r'^user/$',                     'list_my',      name='list_my'),
    url(r'^user/(?P<username>.*)/$',    'list_user',    name='list_user'),
    url(r'^tag/(?P<name>.*)/$',         'list_tag',     name='list_tag'),
    url(r'^new/$',                      'new',          name='new'),
    url(r'^detail/(?P<slug>.*)/$',      'detail',       name='detail'),
    url(r'^edit/(?P<slug>.*)/$',        'edit',         name='edit'),
    url(r'^rate/$',                     'rate',         name='rate'),
)
urls = (urlpatterns, 'scls', 'scls')
