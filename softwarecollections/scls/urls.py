from django.conf.urls import url

from . import views

# Explicitly namespace the URLs
app_name = "scls"

urlpatterns = [
    url(r'^$',                                      views.list_all,     name='list_all'),
    url(r'^user/$',                                 views.list_my,      name='list_my'),
    url(r'^user/(?P<username>.*)/$',                views.list_user,    name='list_user'),
    url(r'^tag/(?P<name>.*)/$',                     views.list_tag,     name='list_tag'),
    url(r'^new/$',                                  views.new,          name='new'),
    url(r'^coprnames/(?P<copr_username>[^/]+)/$',   views.coprnames,    name='coprnames'),
    url(r'^(?P<slug>[^/]+/[^/]+)/$',                views.detail,       name='detail'),
    url(r'^(?P<slug>[^/]+/[^/]+)/edit/$',           views.edit,         name='edit'),
    url(r'^(?P<slug>[^/]+/[^/]+)/acl/$',            views.acl,          name='acl'),
    url(r'^(?P<slug>[^/]+/[^/]+)/coprs/$',          views.coprs,        name='coprs'),
    url(r'^(?P<slug>[^/]+/[^/]+)/repos/$',          views.repos,        name='repos'),
    url(r'^(?P<slug>[^/]+/[^/]+)/delete/$',         views.delete,       name='delete'),
    url(r'^(?P<slug>[^/]+/[^/]+)/rate/$',           views.rate,         name='rate'),
    url(r'^(?P<slug>[^/]+/[^/]+)/review_req/$',     views.review_req,   name='review_req'),
    url(r'^(?P<slug>[^/]+/[^/]+)/sync_req/$',       views.sync_req,     name='sync_req'),
    url(r'^(?P<slug>[^/]+/[^/]+)/complain/$',       views.complain,     name='complain'),
    url(r'^(?P<slug>[^/]+/[^/]+/[^/]+)/download/(.*\.rpm)?$',
                                                    views.download,     name='download'),
    url(r'^health/?$',                              views.check_health, name='check_health'),
]
