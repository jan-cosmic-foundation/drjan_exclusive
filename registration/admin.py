import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Participant, Child, Donation
# Register your models here.

class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


class ParticipantAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'first_name',
        'last_name',
        'email',
        'phone',
        'country',
        'coming_with_children',
        'children_count',
        'attending_gtc',
    )
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('attending_gtc', 'country', 'coming_with_children')
    actions = ["export_as_csv"]


class ChildAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('name', 'age')
    search_fields = ('name', 'age')
    actions = ["export_as_csv"]


class DonationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'reference', 'amount', 'project', 'paid')
    search_fields = ('name', 'email', 'reference', 'amount', 'paid')
    list_filter = ('paid',)


admin.site.register(Participant, ParticipantAdmin)
admin.site.register(Child, ChildAdmin)
admin.site.register(Donation, DonationAdmin)
