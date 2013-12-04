from django.conf.urls import patterns, url

urlpatterns = patterns('softwarecollections.scls.views',
    url(r'^$',      'directory',  name='all', kwargs={'type':'all'}),
    url(r'^my/$',   'directory',  name='my',  kwargs={'type':'my'}),
    url(r'^new/$',  'new',        name='new'),
)
