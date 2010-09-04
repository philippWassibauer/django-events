# -*- coding: utf-8 -*-
import datetime
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from venues.models import Venue

# each event should have an own folder for images
def eventimage_get_upload_to(instance, filename):
    return "event-images/%s/"%instance.event.slug
    
class EventImage(models.Model):
    event = models.ForeignKey('Event', related_name="images")
    image = models.ImageField(upload_to=eventimage_get_upload_to,
                              height_field="image_height",
                              width_field="image_width")
    
    def __unicode__(self):                                  
        return str(self.event)+" > "+str(self.image)


class EventCategory(models.Model):
    name = models.CharField(_("Category Name"), max_length=200)
    
    def __unicode__(self):                                  
        return self.name
    
    
class Event(models.Model):
    DRAFT_STATUS = 1
    PUBLIC_STATUS = 2
    STATUS_CHOICES = (
        (DRAFT_STATUS, _('Draft')),
        (PUBLIC_STATUS, _('Public')),
    )
    
    PUBLIC_PRIVACY = 1
    PRIVATE_PRIVACY = 2
    HIDDEN_PRIVACY = 3
    PRIVACY_CHOICES = (
        (PUBLIC_PRIVACY, _('public')),
        (PRIVATE_PRIVACY, _('private')),
        (HIDDEN_PRIVACY, _('hidden')),
    )
    
    title           = models.CharField("Titel", _('title'), max_length=200)
    slug            = models.SlugField("Url", _('slug'), unique=True,
                                       max_length=200)
    tease           = models.TextField(_('tease'),
                                       _('tease'), blank=True)
    description     = models.TextField(_("description"), _('description'))
    creator         = models.ForeignKey(User, related_name="events")
    categories      = models.ManyToManyField(EventCategory, related_name="events")
    
    status          = models.IntegerField(_("Status"), _('status'),
                                          choices=STATUS_CHOICES,
                                          default=DRAFT_STATUS)
    
    privacy          = models.IntegerField(_("Privacy"), _('Privacy'),
                                          choices=PRIVACY_CHOICES,
                                          default=PUBLIC_PRIVACY)
    
    location        = models.ForeignKey(Venue, related_name="hosted_events",
                                        blank=True, null=True)

    # in case no DB location is used
    location_name   = models.CharField(_('Location Name'), _('Location Name'),
                                       max_length=100, blank=True, null=True)
    
    location_adress = models.CharField(_('Adress'), _('Adress'),
                                       max_length=100, blank=True, null=True)
    
    location_zip_code   = models.CharField(_('ZipCode'), _('ZipCode'),
                                           max_length=10, blank=True, null=True)
    
    location_city   = models.CharField(_('City'), _('City'),
                                       max_length=40, blank=True, null=True)
    
    location_country   = models.CharField(_('Country'), _('Country'),
                                          max_length=20, blank=True, null=True)

    num_invites = models.IntegerField(_('num_invites'),_('num_invites'),
                                          blank=True, null=True, 
                        help_text=_(u"How many invites does this event have?"))
    
    num_additional_persons_per_invite = models.IntegerField("People per Invite",
                    blank=True, null=True, default=0,
                    help_text=u"How many people can each invite bring?")
    
    guests = models.ManyToManyField(User, related_name="attending")
    
    admin_content = models.BooleanField(_("Was created by Staff"),
                                        _('Was created by Staff'), default=False)
    
    allow_comments  = models.BooleanField(_("Comments?"),_('allow comments'),
                                          default=True)
    
    start_date	    = models.DateTimeField(_("Event Start"),_('start_date'))
    end_date	    = models.DateTimeField(_("Event End"),_('end_date'))
    
    invitations_start = models.DateTimeField(_("Registration Start"),
                                             _('invitations_start'),
                                             help_text=_(u"when does the registration start"),
                                             blank=True, null=True)
    
    invitations_deadline = models.DateTimeField(_("Registration End"),
                                                _('invitations_deadline'),
                                                help_text=_(u"when does the registration end"),
                                                blank=True, null=True)

    website = models.CharField(_('website'), blank=True, null=True,
                               max_length=200,
                               help_text=_(u"e.g. www.zweitwelt.com"))

    has_to_reserve =  models.BooleanField("Reserve",
                                          help_text=_(u'reserve by calling/email?'),
                                          default=True)
    
    send_emails_to_owner =  models.BooleanField(_("Owner is notified on registration"),
                                          help_text=_(u'Should the creator be notified when people register?'),
                                          default=True)

    created_at      = models.DateTimeField(_('created at'),
                                           default=datetime.datetime.now)
    
    updated_at      = models.DateTimeField(_('updated at'))

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
        return mark_safe(render_to_string('events/render_inline.html',
                                          { 'event': self }))

    def render_inline_big(self):
        return mark_safe(render_to_string('events/render_inline_big.html',
                                          { 'event': self }))

    def is_creator(self, user):
        return user == self.author

    def is_single_day(self):
        if (self.end_date - self.start_date).days <= 1:
            if self.end_date.day == self.start_date.day:
                return True
        return False
    
    def rendered(self):
        return mark_safe(render_to_string('events/event.html',
                                          { 'event':  self  }))

    def preview(self):
        return mark_safe(render_to_string('events/event_preview.html',
                                          { 'event': self  }))

    def profile_preview(self):
        return mark_safe(render_to_string('events/event_profile_preview.html',
                                          { 'event': self  }))      

    def is_invitation(self):
        return (self.type == 1)

    def is_invitation_active(self):
        return (self.invitations_start<datetime.datetime.now()\
                and self.invitations_deadline>datetime.datetime.now())
        
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
        return (self.start_date.date() \
                == (datetime.date.today() + datetime.timedelta(1)))

    def invitation_starts_today(self):
        return (self.invitations_start.date() == datetime.date.today())

    def has_ended_yesterday(self):
        return (self.end_date.date() \
                == (datetime.date.today() - datetime.timedelta(1)))

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
                send_reminder_mails(self, template_name="events/reminder_start.txt")
            if self.has_ended_yesterday():
                send_reminder_mails(self, 
                                    subject_prefix=_(u'recommend visited event'),
                                    template_name="events/reminder_end.txt")
    
    def save(self, force_insert=False, force_update=False):
        self.updated_at = datetime.datetime.now()
        super(Event, self).save(force_insert, force_update)
        