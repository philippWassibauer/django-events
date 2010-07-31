from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from misc.utils import get_send_mail
send_mail = get_send_mail()

def send_reminder_mails(event,  
        subject_prefix=_(u'Erinnerung an Einladung: %(subject)s'),
        template_name="event/reminder_start.txt"):
    
    current_domain = Site.objects.get_current().domain
    subject = subject_prefix % {'subject': event.title}
    
    for guest in event.guests.all():
        if guest.email != "":
            message = render_to_string(template_name, {
                'site_url': 'http://%s' % current_domain,
                'event': event,
                'guest': guest,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                      [guest.email,])
