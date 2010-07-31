import datetime
from haystack import indexes
from haystack.sites import site
from event.models import Event

from haystack.sites import site
#
#class EventIndex(indexes.SearchIndex):
#    text = indexes.CharField(document=True, use_template=True)
#    title = indexes.CharField(model_attr='title')
#    tease = indexes.CharField(model_attr='tease') 
#    creator = indexes.CharField(model_attr='author')
#
#    created_at = indexes.DateTimeField(model_attr='created_at')
#    updated_at = indexes.DateTimeField(model_attr='updated_at')
#    start_date = indexes.DateTimeField(model_attr='start_date')
#    end_date = indexes.DateTimeField(model_attr='end_date')
#    
#    event_type = indexes.IntegerField(model_attr='type')
#
#    tags = indexes.CharField(model_attr='tags')
#    
#    def get_query_set(self):
#        return Event.objects.filter(status=2)
#
#
#site.register(Event, EventIndex)
#

