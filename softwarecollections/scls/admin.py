from django.contrib import admin
from django.utils.translation import ungettext, ugettext as _
from .models import SoftwareCollection, Score

class SoftwareCollectionAdmin(admin.ModelAdmin):
    list_display = ('slug', 'title', 'get_copr_url_tag', 'review_req', 'approved', 'auto_sync', 'need_sync')
    list_filter  = ('maintainer', 'review_req', 'approved')
    ordering     = ('slug',)
    actions      = ('approve',)

    def approve(self, request, queryset):
        rows_updated = queryset.update(review_req = False, approved = True)
        self.message_user(request, ungettext(
            '%(count)d selected collection was approved',
            '%(count)d selected collections were approved',
            rows_updated) % {'count': rows_updated}
        )
    approve.short_description = _('Approve selected software collections')
        
admin.site.register(SoftwareCollection, SoftwareCollectionAdmin)
admin.site.register(Score)
