from django.conf.urls import patterns, url

urlpatterns = patterns('softwarecollections.scls.views',
    url(r'^$',                                  'list_all',     name='list_all'),
    url(r'^user/$',                             'list_my',      name='list_my'),
    url(r'^user/(?P<username>.*)/$',            'list_user',    name='list_user'),
    url(r'^tag/(?P<name>.*)/$',                 'list_tag',     name='list_tag'),
    url(r'^new/$',                              'new',          name='new'),
    url(r'^(?P<slug>[^/]+/[^/]+)/$',            'detail',       name='detail'),
    url(r'^(?P<slug>[^/]+/[^/]+)/edit/$',       'edit',         name='edit'),
    url(r'^(?P<slug>[^/]+/[^/]+)/rate/$',       'rate',         name='rate'),
    url(r'^(?P<slug>[^/]+/[^/]+)/app_req/$',    'app_req',      name='app_req'),
    url(r'^(?P<slug>[^/]+/[^/]+)/sync_req/$',   'sync_req',     name='sync_req'),
)
urls = (urlpatterns, 'scls', 'scls')
