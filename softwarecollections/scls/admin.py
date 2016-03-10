from django.contrib import admin
from django.utils.translation import ungettext, ugettext as _
from .models import SoftwareCollection, OtherRepo, Repo, Score

class SoftwareCollectionAdmin(admin.ModelAdmin):
    list_display = ('slug', 'get_title_tag', 'get_copr_tags', 'review_req', 'approved', 'auto_sync', 'need_sync', 'last_synced', 'last_modified')
    list_filter  = ('review_req', 'approved', 'maintainer')
    ordering     = ('slug',)
    actions      = ('approve', 'request_sync')
    filter_horizontal = ('coprs', 'collaborators')

    def approve(self, request, queryset):
        rows_updated = queryset.update(review_req = False, approved = True)
        self.message_user(request, ungettext(
            '%(count)d selected collection was approved',
            '%(count)d selected collections were approved',
            rows_updated) % {'count': rows_updated}
        )
    approve.short_description = _('Approve selected software collections')

    def request_sync(self, request, queryset):
        rows_updated = queryset.update(need_sync = True)
        self.message_user(request, ungettext(
            'Sync was requested for %(count)d collection',
            'Sync was requested for %(count)d collections',
            rows_updated) % {'count': rows_updated}
        )
    request_sync.short_description = _('Request sync for selected software collections')

admin.site.register(OtherRepo)
admin.site.register(SoftwareCollection, SoftwareCollectionAdmin)
admin.site.register(Repo)
admin.site.register(Score)
