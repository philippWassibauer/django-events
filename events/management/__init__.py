from django.db.models import signals
from django.utils.translation import ugettext_noop as _

try:
    from notification import models as notification
    
    def create_notice_types(app, created_models, verbosity, **kwargs):
        try:
            notification.create_notice_type("event_new", _("New event"), _("A new event has been posted."), default=1)
            notification.create_notice_type("invitation_new", _("New invitation"), _("A new invitation has been posted."), default=1)
            notification.create_notice_type("invitation_confirmed_email", _("Invitation confirmed"), _("A user has confirmed to accept your invitation."), default=2)
            notification.create_notice_type("invitation_confirmed", _("Invitation confirmed"), _("A user has confirmed to accept your invitation."), default=1)
            notification.create_notice_type("invitation_confirmed_user", _("You have confirmed an Invitation"), _("Information to this Invitation"), default=2)
            notification.create_notice_type("invitation_canceled", _("You canceled an Invitation"), _("You canceled an Invitation"), default=2)
        except:
            pass

    signals.post_syncdb.connect(create_notice_types, sender=notification)
except ImportError:
    print "Skipping creation of NoticeTypes as notification app not found"
