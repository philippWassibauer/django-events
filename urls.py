from django.conf.urls.defaults import *
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template

from event.forms import InvitationForm, EventToInvitationForm

urlpatterns = patterns('event.views',
    url(r'^veranstaltung$', 'events', name="event_list_all"),

    url(r'^einladung-stornieren/(?P<invitation_id>\d+)', 'cancel_invitation', name="cancel_invitation"),

    url(r'^nachricht-schicken/(\d+)/$', 'send_message_to_guests', name="send_message_to_guests"),

    url(r'^veranstaltung/(?P<year>\d+)/(?P<month>\d+)$', 'events_month'
        , kwargs={'event_type':0}
        , name='events_month'),

    url(r'^veranstaltung/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)$', 'events_day'
        , kwargs={'event_type':0}
        , name='events_day'),

    url(r'^veranstaltung/neu/$', 'new', name='event_new'),
    url(r'^veranstaltung/angelegt/(?P<event_id>\d+)$', 'event_created',name='event_created'),
    url(r'^veranstaltung_zu_einladung/(?P<event_id>\d+)$', 'new', 
        {'form_class':InvitationForm,
         'event_type':1,
         'template_name':'event/event_to_invitation.html'},
        name='event_to_invitation'),
    )

urlpatterns += patterns('event.views',
    url(r'^einladung$', 'invitations', name="invitation_list_all"),
    url(r'^einladung/(?P<year>\d+)/(?P<month>\d+)$', 'events_month'
        , kwargs={'event_type':1}
        , name='invitations_month'),

    url(r'^einladung/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)$', 'events_day'
        , kwargs={'event_type':1}
        , name='invitations_day'),

    url(r'^einladung/neu/$', 'new', 
        kwargs={'form_class': InvitationForm, 'template_name': 'event/new_invitation.html', 'event_type': 1}, 
        name='invitation_new'),
    url(r'^einladung/annehmen/(?P<invitation_id>\d+)', 'accept_invitation', name='accept_invitation'),
    )

urlpatterns  += patterns('event.views',
    url(r'^your_events/$', 'your_events', name='event_list_yours'),
    url(r'^(?P<slug>[\w\.-]+)$', 'event', name="event"),

    url(r'^edit/(\d+)/$', 'edit', name='event_edit'),
    url(r'^destroy/(\d+)/$', 'destroy', name='event_destroy'),
    )

