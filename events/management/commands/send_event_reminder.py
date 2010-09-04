from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = "Prepares mails for all events that begin today to remind my guests."

    def handle_noargs(self, **options):
        from events.models import Event
        for event in Event.objects.filter(status__exact=2):
            print "collecting mails for event (%(id)s): %(title)s" % {'id': event.id, 'title':event.title}
            event.remind_my_users()
