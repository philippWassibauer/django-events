# -*- coding: utf-8 -*-
import datetime

from django.contrib.gis.db import models

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField
from tagging.models import Tag
from django.template import RequestContext
from django.contrib.auth.models import User
from photologue.models import ImageModel

from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from profiles.models import Profile
from activity_stream.models import create_activity_item, ActivityStreamItemSubject, ActivityStreamItem
from django.contrib.contenttypes import generic

class EventImage(ImageModel):
    event = models.OneToOneField('Event', primary_key=True)
    def __unicode__(self):                                  
        return str(self.event)
        
class Event(models.Model):
    """
    >>> import datetime
    >>> def create_event():
    >>>     e = Event()
    >>>     e.title = "title"
    >>>     e.slug = "slug"
    >>>     e.tease = "tease"
    >>>     e.body = "body"
    >>>     e.type = 1 # invitation
    >>>     e.author = User.objects.get(username="admin1")
    >>>     e.status = 2 # Freigeschalten
    >>>     e.location = Profile.objects.filter(is_location=True)[0]
    >>>     e.num_invites = 200
    >>>     e.start_date = datetime.datetime.today() + datetime.timedelta(1) # starts tommorrow
    >>>     e.end_date = datetime.datetime.today() + datetime.timedelta(2) # ends the day after tommorrow
    >>>     e.invitations_start = datetime.date.today() - datetime.timedelta(1)
    >>>     e.invitations_deadline  = datetime.date.today()
    >>>     return e

    # Test if mails feedback mail and reminder mails get sent
    >>> e = create_event()
    >>> e.end_date = datetime.datetime.today() - datetime.timedelta(1) # end_date was yesterday
    # Just for testing
    >>> e.start_date = datetime.datetime.today() + datetime.timedelta(1) # starts tommorrow
    >>> e.save()
    
    >>> e.guests.add(e.author)

    >>> e.remind_my_users()

    >>> from mailer import models as mailer
    >>> (mailer.Message.objects.all()) == 2
    True

    """
    STATUS_CHOICES = (
        (1, _('Entwurf')),
        (2, _('Freigeschalten')),
    )
    TYPE_CHOICES = (
        (0, _('Event')),
        (1, _('Einladung')),
    )
    title           = models.CharField("Titel", _('title'), max_length=200)
    slug            = models.SlugField("Url", _('slug'), unique=True, max_length=200)
    tease           = models.TextField("Kurzbeschreibung (in der Listenansicht sichtbar)", _('tease'), blank=True)
    body            = models.TextField("Beschreibung", _('body'))
    type            = models.IntegerField("Typ",_('type'), choices=TYPE_CHOICES, default=0)
    author          = models.ForeignKey(User, related_name="events")
    image           = models.ImageField("Bild", upload_to='event_image', blank=True, null=True)
    
    status          = models.IntegerField("Status", _('status'), choices=STATUS_CHOICES, default=2)
    location        = models.ForeignKey(Profile, related_name="hosted_events", blank=True, null=True)

    # in case no DB location is used
    location_name   = models.CharField("Gastgeber Name", _('Location Name'), max_length=100, blank=True, null=True)
    location_adress = models.CharField("Gastgeber Adresse", _('Location Name'), max_length=100, blank=True, null=True)
    location_zip_code   = models.CharField("Gastgeber PLZ", _('Location Name'), max_length=10, blank=True, null=True)
    location_city   = models.CharField("Gastgeber Stadt", _('Location Name'), max_length=40, blank=True, null=True)
    location_country   = models.CharField("Gastgeber Land", _('Location Name'), max_length=20, blank=True, null=True)

    tags            = TagField( _('Tags'), help_text=_(u"tag_help_text"))
    
    num_invites     = models.IntegerField("Anzahl der Einladungen",_('num_invites'), blank=True, null=True, 
                                          help_text=_(u"Wieviele individuelle Cardholder sollen diese Einladung annehmen können?"))
    num_additional_persons_per_invite = models.IntegerField("Personen pro Einladung", blank=True, null=True, default=0,
                                                 help_text=u"Wieviele Personen darf ein Cardholder (inkl. Cardholder) zur angenommenen Einladung mitnehmen?")
    guests          = models.ManyToManyField(User, related_name="attending")

    allow_comments  = models.BooleanField("Kommentare?",_('allow comments'), default=True)
    start_date	    = models.DateTimeField("Veranstaltungsanfang",_('start_date'))
    end_date	    = models.DateTimeField("Veranstaltungsende",_('end_date'))
    
    invitations_start = models.DateTimeField("Anmeldebeginn",_('invitations_start'), help_text=_(u"Beginn des Postings"), blank=True, null=True)
    invitations_deadline = models.DateTimeField("Anmeldeende", _('invitations_deadline'),  help_text=_(u"Ende des Postings"), blank=True, null=True)

    website = models.CharField(_('website'), blank=True, null=True, max_length=200, help_text=_(u"z.B.: www.einfachleben.com"))

    has_to_reserve =  models.BooleanField("Telefonische Vorreservierung", help_text=_(u'Wollen Sie, dass der eingeladene Gast vorreserviert?'), default=True)
    send_emails    =  models.BooleanField("Emailbenachrichtigung", help_text=_(u'Emailbenachrichtigung über jede einzelene angenommene Einladung. (ansonsten kann der Stand der angenommenen Einladungen unter  „Mein Konto“ in Anmeldungen abgerufen werden) '), default=True)

    created_at      = models.DateTimeField(_('created at'), default=datetime.datetime.now)
    updated_at      = models.DateTimeField(_('updated at'))

    activities = generic.GenericRelation(ActivityStreamItemSubject)
    
    objects = models.GeoManager()

    class Meta:
        verbose_name        = _('event')
        verbose_name_plural = _('events')
        ordering            = ('-start_date',)
        get_latest_by       = 'start_date'

    def get_website(self):
        if self.website:
            if self.website.find("http://") != -1:
                return self.website
            else:
                return "http://"+self.website
        else:
            return None
            
    def render_inline(self):
        return mark_safe(render_to_string('event/render_inline.html', { 'event': self }))

    def render_inline_big(self):
        return mark_safe(render_to_string('event/render_inline_big.html', { 'event': self }))

    def is_creator(self, user):
        return user == self.author

    def is_single_day(self):
        if (self.end_date - self.start_date).days <= 1:
            if self.end_date.day == self.start_date.day:
                return True
        return False

    def lasts_long(self):
        # lasts longer than 3 days
        return (self.start_date - self.end_date).days > 3
    
    def rendered(self):
        return mark_safe(render_to_string('event/event.html', { 'event':  self  }))

    def preview(self):
        return mark_safe(render_to_string('event/event_preview.html', { 'event': self  }))

    def profile_preview(self):
        return mark_safe(render_to_string('event/event_profile_preview.html', { 'event': self  }))      

    def is_invitation(self):
        return (self.type == 1)

    def is_invitation_active(self):
        return (self.invitations_start<datetime.datetime.now() and self.invitations_deadline>datetime.datetime.now())
        
    def __unicode__(self):
        return self.title

    def has_free_invites(self):
        return self.num_free_invites() > 0
    
    def num_free_invites(self):
        return self.num_invites-self.guests.all().count()

    def get_absolute_url(self):
        return ('event', None, { 'slug': self.slug })
    get_absolute_url = models.permalink(get_absolute_url)
    
    def starts_tomorrow(self):
        return (self.start_date.date() == (datetime.date.today()  + datetime.timedelta(1)))

    def invitation_starts_today(self):
        return (self.invitations_start.date() == datetime.date.today())

    def has_ended_yesterday(self):
        return (self.end_date.date() == (datetime.date.today() - datetime.timedelta(1)))

    def has_ended(self):
        return (self.end_date.date() < datetime.date.today())

    def is_upcoming(self):
        return (self.end_date.date() <= datetime.date.today() + datetime.timedelta(3))

    def ends_today(self):
        return (self.end_date.date() == datetime.date.today())

    def has_guest(self, user):
        return self.guests.filter(username=user.username).count() != 0
        
    def remind_my_users(self):
        from event.utils import send_reminder_mails
        if self.status == 2 and self.is_invitation():
            if self.starts_tomorrow():
                send_reminder_mails(self, template_name="event/reminder_start.txt")
            if self.has_ended_yesterday():
                send_reminder_mails(self, subject_prefix=u'Empfehlung für %(subject)s abgeben', template_name="event/reminder_end.txt")

            if self.invitation_starts_today(): # called once a day so we wont have duplicates
                if ActivityStreamItem.objects.filter(actor=self.author, subjects__object_id=self.id).count()==0:
                    create_activity_item("new_invitation", self.author, self)

    # used in recommendation app to send owner a information mail
    def owner(self):
        return self.author
    
    def save(self, force_insert=False, force_update=False):
        self.updated_at = datetime.datetime.now()
        super(Event, self).save(force_insert, force_update)
        if self.image:
            self.eventimage = EventImage(event=self)
            self.eventimage.image = self.image
            self.eventimage.save()

    
