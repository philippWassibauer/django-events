# Template tag
from datetime import date, timedelta

from django import template
from events.models import Event # You need to change this if you like to add your own events to the calendar
from django.db.models import Q
from django.template import Library, Node, TemplateSyntaxError, TemplateDoesNotExist
from native_tags.decorators import function, comparison, filter
from django.template.loader import render_to_string
from native_tags.decorators import function, comparison, filter

register = template.Library()
import datetime
from datetime import date, timedelta
import random

def get_last_day_of_month(year, month):
    if (month == 12):
        year += 1
        month = 1
    else:
        month += 1
    return date(year, month, 1) - timedelta(1)

def get_users_last_accepted_events(user, count=3, template_name="events/latest_accepted_events.html"):
    accepted_events = Event.objects.filter(guests=user).order_by('-end_date')[0:count]
    return render_to_string(template_name, {"events": accepted_events})
get_users_last_accepted_events = function(get_users_last_accepted_events)
    
def month_cal(year, month, calendar_type="invitations", current_day=None):
    event_list = Event.objects.filter(\
                    Q(status=2)&(Q(start_date__month=month) \
                      & Q(start_date__year=year))|(Q(end_date__month=month) \
                      & Q(end_date__year=year))  )

    if calendar_type=="invitations":
        event_list = event_list.filter(type=1)\
                        .filter(invitations_start__lte=datetime.datetime.now(),\
                         invitations_deadline__gte=datetime.datetime.now())
    else:
        event_list = event_list.filter(type=0)

    first_day_of_month = date(year, month, 1)
    last_day_of_month = get_last_day_of_month(year, month)
    first_day_of_calendar = first_day_of_month - timedelta(first_day_of_month.weekday())
    last_day_of_calendar = last_day_of_month + timedelta(7 - last_day_of_month.weekday())

    month_cal = []
    week = []
    week_headers = []

    i = 0
    day = first_day_of_calendar
    while day <= last_day_of_calendar:
        if i < 7:
            week_headers.append(day)
        cal_day = {}
        cal_day['day'] = day
        cal_day['event'] = False
        for event in event_list:
            if day >= event.start_date.date() and day <= event.end_date.date():
                cal_day['event'] = True
        if day.month == month:
            cal_day['in_month'] = True
        else:
            cal_day['in_month'] = False
        week.append(cal_day)
        if day.weekday() == 6:
            month_cal.append(week)
            week = []
        i += 1
        day += timedelta(1)
    
    next_month = month+1
    previous_month = month-1
    next_year = year
    if(next_month>12):
        next_year = year+1
        next_month = 1

    previous_year = year
    if(previous_month<1):
        previous_year = year-1
        previous_month = 12

    return {'calendar': month_cal, 'current_day':current_day,
            'headers': week_headers, 'year': year, 'month': month,
            'next_month': next_month, 'next_year': next_year,
            'previous_month':previous_month,
            'previous_year': previous_year, 'calendar_type':calendar_type}

register.inclusion_tag('events/event_calendar.html')(month_cal)


def accepted_invitation_of_user(user):
    accepted_events = Event.objects.filter(guests=user, type=1).order_by('-start_date')
    return {'accepted_events':accepted_events, "user":user}
register.inclusion_tag('events/accepted_invitation_of_user.html')(accepted_invitation_of_user)


def current_events_of_user(user, viewing_user, in_profile=False):
    current_events = Event.objects.filter(author=user, type=0, \
                                          end_date__gt=datetime.datetime.now)\
                                         .order_by("end_date")
    return {'current_events':current_events,
            "user":viewing_user,
            "in_profile": in_profile}
register.inclusion_tag('events/current_events_of_user.html')(current_events_of_user)

def old_events_of_user(user, viewing_user, in_profile=False):
    old_events = Event.objects.filter(author=user, type=0, \
                                      end_date__lt=datetime.datetime.now)\
                              .order_by("end_date")
    return {'old_events':old_events, "user":viewing_user,
            "in_profile": in_profile}
register.inclusion_tag('events/old_events_of_user.html')(old_events_of_user)

def upcoming_invitations_of_user(user, viewing_user, in_profile=False):
    current_events = Event.objects.filter(author=user, type=1, \
                                          end_date__gte=datetime.datetime.now)\
                        .filter(invitations_start__gte=datetime.datetime.now())\
                        .order_by("end_date")
    return {'current_invitations':current_events,
            "user":viewing_user, "in_profile": in_profile}
register.inclusion_tag('events/upcoming_invitations_of_user.html')(upcoming_invitations_of_user)

def current_invitations_of_user(user, viewing_user, in_profile=False):
    if in_profile:
        current_events = \
            Event.objects.filter(author=user, type=1, \
                                end_date__gte=datetime.datetime.now())\
                         .filter(invitations_start__lte=datetime.datetime.now())\
                         .order_by("end_date")
    else:
        current_events = Event.objects.filter(author=user, type=1,
                                              end_date__gte=datetime.datetime.now())\
                                      .filter(invitations_start__lte=datetime.datetime.now(), \
                                              invitations_deadline__gte=datetime.datetime.now())\
                                      .order_by("end_date")
    return {'current_invitations':current_events, "user":viewing_user,
            "in_profile": in_profile}
register.inclusion_tag('events/current_invitations_of_user.html')(current_invitations_of_user)

def old_invitations_of_user(user, viewing_user, in_profile=False):
    old_events = Event.objects.filter(author=user, type=1, end_date__lte=datetime.datetime.now).order_by("end_date")
    return {'old_invitations':old_events, "user":viewing_user, "in_profile": in_profile}
register.inclusion_tag('events/old_invitations_of_user.html')(old_invitations_of_user)


def event_profile_preview(event, user):
    return {'event':event, 'user':user}
register.inclusion_tag('events/event_profile_preview.html')(event_profile_preview)


def event_preview(event, user):
    return {'event':event, 'user':user}
register.inclusion_tag('events/event_preview.html')(event_preview)


def event_small_preview(event, user):
    return {'event':event, 'user':user}
register.inclusion_tag('events/event_small_preview.html')(event_small_preview)


def get_current_event(template_name='events/start_screen.html'):
    events = Event.objects.filter(type__exact=0, status__exact=2)
    now = datetime.datetime.now()
    in_2_weeks = now+timedelta(weeks=2)
    events_current = events.exclude(eventimage__exact=None).filter(end_date__gte=now, start_date__lte=in_2_weeks).order_by("end_date")
    events_started = events_current.filter(start_date__gte=datetime.datetime(int(now.year),
                                int(now.month), int(now.day),
                                0, 0, 0))
    if events_started.all():
        parameters = {'event':random.choice(events_started.all())}
    elif events_current.all():
        parameters = {'event':random.choice(events_current.all()[0:5])}
    else:
        parameters = {'event': None}
    return render_to_string(template_name, parameters)
get_current_event = function(get_current_event)


def get_current_invitation(template_name='events/start_screen.html'):
    invitations = Event.objects.filter(type__exact=1, status__exact=2)
    now = datetime.datetime.now()
    in_2_weeks = now+timedelta(weeks=2)
    invitations_current = invitations.exclude(eventimage__exact=None).filter(
                                             end_date__gte=now,
                                             invitations_start__lte=now,
                                             invitations_deadline__gte=now,
                                             start_date__lte=in_2_weeks)
    invitations_started = invitations_current.filter(start_date__gte=datetime.datetime(int(now.year),
                                int(now.month), int(now.day),
                                0, 0, 0))
    if invitations_started.all():
        # return a random element from any started invitation
        parameters = {'event':random.choice(invitations_started.all())}
    elif invitations_current.all():
        # return a random element from the five most current 
        parameters = {'event':random.choice(invitations_current.all()[0:5])}
    else:
        parameters = {'event': None}
        
    return render_to_string(template_name, parameters)
get_current_invitation = function(get_current_invitation)


class HasEventNode(Node):
    def __init__(self, user, type, varname):
        self.user = template.Variable(user)
        self.type = type
        self.varname = varname
    def render(self, context):
        if self.type == 1:
            context[self.varname] = Event.objects.filter(author=self.user.resolve(context), type=self.type, end_date__gte=datetime.datetime.now()).filter(invitations_start__lte=datetime.datetime.now(), invitations_deadline__gte=datetime.datetime.now())
        else:
            context[self.varname] = Event.objects.filter(author=self.user.resolve(context), type=self.type, end_date__gte=datetime.datetime.now())
        return ''

def has_events(parser, token):
    bits = token.contents.split()
    if len(bits) != 4:
        raise TemplateSyntaxError, "has_events tag takes exactly 3 arguments"
    if bits[2] != 'as':
        raise TemplateSyntaxError, "third argument to get_latest tag must be 'as'"
    return HasEventNode(bits[1], 0, bits[3])
has_events = register.tag(has_events)

def has_invitation(parser, token):
    bits = token.contents.split()
    if len(bits) != 4:
        raise TemplateSyntaxError, "has_events tag takes exactly 3 arguments"
    if bits[2] != 'as':
        raise TemplateSyntaxError, "third argument to get_latest tag must be 'as'"
    return HasEventNode(bits[1], 1, bits[3])
has_invitation = register.tag(has_invitation)

















