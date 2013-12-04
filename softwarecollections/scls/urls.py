from django.conf.urls import patterns, url

urlpatterns = patterns('softwarecollections.scls.views',
    url(r'^$',      'roster',   name='all', kwargs={'type':'all'}),
    url(r'^my/$',   'roster',   name='my',  kwargs={'type':'my'}),
    url(r'^new/$',  'new',      name='new'),
    url(r'^detail/(?P<slug>.*)/$',
                    'detail',   name='detail'),
)
