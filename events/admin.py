from event.models import Event, EventImage
from django.contrib import admin

class EventAdmin(admin.ModelAdmin):
    list_display        = ('title', 'start_date', 'end_date', "type", "author", "status")
    list_filter         = ('title', 'start_date', "type", "author", "status")
    search_fields       = ('title', 'start_date')

admin.site.register(Event, EventAdmin)

admin.site.register(EventImage)
