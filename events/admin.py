from events.models import *
from django.contrib import admin

class EventImageInline(admin.TabularInline):
    model = EventImage
    
class EventAdmin(admin.ModelAdmin):
    list_display        = ('title', 'start_date', 'end_date', "privacy", "creator", "status")
    list_filter         = ('title', "privacy", "creator", "status")
    search_fields       = ('title', 'body')
    
    inlines = [EventImageInline]

admin.site.register(Event, EventAdmin)
admin.site.register(EventImage)
admin.site.register(EventCategory)
