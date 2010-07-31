# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404, HttpResponsePermanentRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import date_based
from django.conf import settings
from django.db.models import Q
from profiles.models import Category,Profile
from geopy import geocoders
from event.forms import EventForm, InvitationForm
from event.models import Event
from trumer.utils import is_elevated_user
import datetime
from datetime import timedelta
from activity_stream.models import create_activity_item
from django.contrib.gis.maps.google.gmap import GoogleMap

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None


def events(request):
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    return HttpResponsePermanentRedirect(reverse('events_month',
                                                 kwargs={ 'year': current_year,
                                                          'month': current_month }))

def invitations(request):
    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    return HttpResponsePermanentRedirect(reverse('invitations_month',
                                                 kwargs={ 'year': current_year,
                                                          'month': current_month }))
    
def events_month(request, year, month, event_type=0):
    size = request.GET.get('size', 10)
    template_name = "event/events_month_%s.html" % event_type

    events = Event.objects.filter(type__exact=event_type, status__exact=2)

    if int(month) == datetime.datetime.now().month:
        events = events.filter(end_date__gte=datetime.datetime.now())
    else:
        events = events.filter(end_date__gte=datetime.datetime(int(year), int(month), 1, 0, 0, 0))

    # invitations can be prestored, only display active ones   
    if event_type==1:
        events = events.filter(invitations_start__lte=datetime.datetime.now(), invitations_deadline__gte=datetime.datetime.now())

    # filter categories
    selected_category = None
    if request.GET.get("selected_category"):
        try:
            selected_category = Category.objects.get(short_name=request.GET.get("selected_category"))
        except:
            selected_category = None

    if selected_category:
        events = events.filter(author__profile__categories=selected_category)  

    # filter titles   
    search_terms = request.GET.get('search', '')
    if search_terms:
        events = events.filter(title__icontains=search_terms)

    zip_code_or_adress = request.GET.get('zip_code_or_adress', '')
    display_map = request.GET.get('display_map', False)
    zoom = None
    point_of_interest = None
    bbox = None
    place = None
    
    if zip_code_or_adress or display_map:
        from django.contrib.gis.measure import D
        # get lat/lon for query
        from django.contrib.gis.geos import *

        g = geocoders.Google(settings.GOOGLE_MAPS_API_KEY)
        try:
            place, (lat, lng) = g.geocode(zip_code_or_adress+" salzburg austria")
        except:
            return render_to_response("trumer/invalid_geocode.html", {
                                        "zip_code_or_adress": zip_code_or_adress
                                    },
                                      context_instance=RequestContext(request))
        
        
        events = events.exclude(location__exact=None)
        
        page = request.GET.get("page", 0)
        if page:
            offset = int(size)*int(page)
        else:
            offset = 0
            
        page_events = events.order_by("end_date")[offset:offset+int(size)]
        
        event_location_ids = [event.location.id for event in page_events]
        
        pnt = fromstr("POINT("+str(lat)+" "+str(lng)+")", srid=4326)
        profiles = Profile.objects.filter(id__in=event_location_ids).exclude(is_location=False).filter(location__distance_lte=(pnt, D(km=500)))
        profiles = profiles.distance("POINT("+str(lat)+" "+str(lng)+")")
        profiles = profiles.order_by("distance")
        profiles = profiles.all()
        
        # get the amount of events needed
        
        point_of_interest = str(lat)+", "+str(lng)
        zoom = 9
        if size>24:
            size = 24
            
        for profile in profiles:
            for event in page_events:
                if event.location.id == profile.id:
                    if hasattr(profile, "current_events"):
                        profile.current_events.append(event)
                    else:
                        profile.current_events = [event]
        
        template_name = "event/geo_result_%s.html" % event_type
        return render_to_response(template_name, {
            "zip_code_or_adress": zip_code_or_adress,
            'search_terms': search_terms,
            "event_type": event_type,
            "events":events.distinct(),
            "profiles": profiles,
            "current_date": datetime.date(int(year),int(month), 1),
            "year": int(year),
            "month": int(month),
            "size": int(size),
            "selected_category": selected_category,
            'point_of_interest': point_of_interest,
            'GMAP': GoogleMap(),
            'categories': Category.objects.filter(parent=None).all(),
        }, context_instance=RequestContext(request))
    else:
        events = events.order_by("end_date")

    return render_to_response(template_name, {
        "zip_code_or_adress": zip_code_or_adress,
        'search_terms': search_terms,
        "event_type": event_type,
        "events":events.distinct(),
        "current_date": datetime.date(int(year),int(month), 1),
        "year": int(year),
        "month": int(month),
        "size": int(size),
        "selected_category": selected_category,
        'categories': Category.objects.filter(parent=None).all(),
    }, context_instance=RequestContext(request))

def events_day(request, year, month, day, event_type=0):
    start_date = datetime.datetime(int(year), int(month), int(day), 0, 0)
    end_date = datetime.datetime(int(year), int(month), int(day), 23, 59)
    
    events = Event.objects.filter(type__exact=event_type).filter(status__exact=2).filter(
        (   Q(start_date__lte=end_date) & Q(end_date__gte=start_date))           )

    template_name = "event/events_day_%s.html" % event_type

    size = request.GET.get('size', 10)

    selected_category = None
    if request.GET.get("selected_category"):
        try:
            selected_category = Category.objects.get(short_name=request.GET.get("selected_category"))
        except:
            selected_category = None

    if selected_category:
        events = events.filter(author__profile__categories=selected_category)

    if event_type==1:
        events = events.filter(invitations_start__lte=datetime.datetime.now(), invitations_deadline__gte=datetime.datetime.now())
       
    events = events.order_by("end_date")
    
    return render_to_response(template_name, {
        "event_type": event_type,
        "events":events.distinct(),
        "current_date": datetime.date(int(year),int(month), int(day)),
        "year": int(year),
        "month": int(month),
        "day": int(day),
        "size": int(size),
        "selected_category": selected_category,
        'categories': Category.objects.filter(parent=None).all(),
    }, context_instance=RequestContext(request))

def event(request, slug,
         template_name="event/event.html"):
    event = get_object_or_404(Event, slug=slug)
    if not event:
        raise Http404

    if event.status == 1:
        raise Http404

    user_is_attending = event.has_guest(request.user)

    return render_to_response(template_name, {
        "event": event,
        "user_is_attending":user_is_attending, 
    }, context_instance=RequestContext(request))

def your_events(request, template_name="event/your_events.html"):
    return render_to_response(template_name, {
        "events": Event.objects.filter(author=request.user),
    }, context_instance=RequestContext(request))
your_events = login_required(your_events)

@user_passes_test(is_elevated_user)
def destroy(request, id):
    event = get_object_or_404(Event, id=id)
    user = request.user
    title = event.title
    if event.author != request.user:
        request.user.message_set.create(message="You can't delete events that aren't yours")
    else:
        event.delete()
        request.user.message_set.create(message=_("Successfully deleted Event '%s'") % title)
        
    return HttpResponseRedirect(reverse("location_edit_events", kwargs={'username': user.username}))

@user_passes_test(is_elevated_user)
def new(request, event_id=None,
        form_class=EventForm, 
        template_name="event/new_event.html", 
        event_type=0):
    
    trigger_names = [ { 'notification': 'event_new', 'activity': 'new_event' },
                      { 'notification': 'invitation_new', 'activity':  'new_invitation' }]
    event = None
    
    if request.method == "POST":
        event_form = form_class(request.user, request.POST, request.FILES)
        if event_id:
            event = Event.objects.get(pk=event_id)
            event.pk = None
            event.id = None
            event_form = form_class(request.user, request.POST, request.FILES, instance=event)
        if event_form.is_valid():
            event = event_form.save(commit=False)
            event.author = request.user
            if event_type:
                event.type = event_type

            from django.template.defaultfilters import slugify
            event.slug = slugify(event.title)

            from misc.utils import make_unique
            event.slug = make_unique(event.slug, lambda x: Event.objects.filter(slug__exact=x).count() == 0)

            if not event.image:
                template_event_id = request.GET.get("template_event_id", False)
                if template_event_id:
                    template_event = Event.objects.get(pk=template_event_id)
                    event.image = template_event.image

            if not event.location and \
                not (event.location_name or event.location_adress or event.location_city \
                 or event.location_zip_code or event.location_country):
                if request.POST.get("custom_location_name", False) and \
                   request.POST.get("custom_location_adress", False) and \
                   request.POST.get("custom_location_zip_code", False) and \
                   request.POST.get("custom_location_city", False):
                    event.location_name = request.POST.get("custom_location_name")
                    event.location_adress = request.POST.get("custom_location_adress")
                    event.location_city = request.POST.get("custom_location_city")
                    event.location_zip_code = request.POST.get("custom_location_zip_code")
                    event.location_country = request.POST.get("custom_location_country")
                else:
                    event_form.fields['location'].widget.errors = [u"Gastgeber muss angegeben werden"]
                    return render_to_response(template_name, {
                        "event_form": event_form
                    }, context_instance=RequestContext(request))
            event.save()
            
            if not event.is_invitation():
                create_activity_item(trigger_names[event.type]['activity'], 
                                     request.user, event)
            else:
                if event.is_invitation_active():
                    create_activity_item("new_invitation", 
                                     request.user, event)
                    
            if notification:
                notification.send([event.author], 
                                  trigger_names[event.type]['notification'], 
                                  {"event": event})

            
            return HttpResponseRedirect(reverse('event_created',
                                                kwargs={'event_id': event.id}))
            
        else:
            return render_to_response(template_name, {
                "event_form": event_form
            }, context_instance=RequestContext(request))

    template_event_id = request.GET.get("template_event_id", False)
    if template_event_id:
        template_event = Event.objects.get(pk=template_event_id)
        event_form = form_class(request.user, instance=template_event)
    elif event_id:
        event = Event.objects.get(pk=event_id)
        event.pk = None
        event.id = None
        event_form = form_class(request.user, instance=event)
    else:
        event_form = form_class(request.user)

    return render_to_response(template_name, {
        "event_form": event_form,
        "template_event_id": template_event_id,
    }, context_instance=RequestContext(request))


@user_passes_test(is_elevated_user)
def event_created(request, event_id, template_name="event/event_created.html"):
    event =  Event.objects.get(pk=event_id)
    return render_to_response(template_name, {
        "event": event,
    }, context_instance=RequestContext(request))

@user_passes_test(is_elevated_user)
def edit(request, id, form_class=EventForm, template_name="event/edit.html"):
    event = get_object_or_404(Event, id=id)
    
    if event.is_invitation():
        form_class = InvitationForm
        
    if request.method == "POST":
        if event.author != request.user:
            request.user.message_set.create(message="You can't edit events that aren't yours")
            return HttpResponseRedirect(reverse("blog_list_yours"))
        if request.POST["action"] == "update":
            event_form = form_class(request.user, request.POST, request.FILES, instance=event)
            if event_form.is_valid():
                event = event_form.save(commit=False)
                if not event.location:
                    if request.POST.get("custom_location_name", False) and request.POST.get("custom_location_adress", False) and \
                       request.POST.get("custom_location_zip_code", False) and request.POST.get("custom_location_city", False):
                        event.location_name = request.POST.get("custom_location_name")
                        event.location_adress = request.POST.get("custom_location_adress")
                        event.location_city = request.POST.get("custom_location_city")
                        event.location_zip_code = request.POST.get("custom_location_zip_code")
                        event.location_country = request.POST.get("custom_location_country")
                event.save()
                return HttpResponseRedirect(reverse('location_edit_events', kwargs={'username': request.user.username}))
        else:
            event_form = form_class(request.user,instance=event)
    else:
        event_form = form_class(request.user,instance=event)

    return render_to_response(template_name, {
        "event_form": event_form,
        "event": event,
    }, context_instance=RequestContext(request))

@login_required
def accept_invitation(request, invitation_id, template_name="event/accept_invitation.html"):
    event =  get_object_or_404(Event, id=invitation_id)

    if event and event.author != request.user:
        if not event.is_invitation_active():
            return render_to_response("error.html", {
                "text": u'Diese Einladung ist zur Zeit noch nicht freigeschalten und kann deswegen noch nicht angenommen werden',
                "title": "Fehler",
            }, context_instance=RequestContext(request))

        if not request.user.get_profile().can_accept_invitation(event.author):
            days_left = request.user.get_profile().days_to_next_invitation(event.author)
            return render_to_response("error.html", {
                "text": u'Sie haben in den letzten 3 Monaten bereits eine Einladung bei diesem Gastgeber angenommen. Sie können deshalb erst wieder in '+str(days_left)+' Tagen bei diesem Gastgeber eine Einladung annehmen',
                "title": "Einladung kann nicht angenommen werden",
            }, context_instance=RequestContext(request))

        if not request.user.get_profile().is_cardholder() and not request.user.get_profile().is_location:
            return HttpResponseRedirect(reverse('request_code') )
            
        if event.has_guest(request.user):
            return render_to_response("error.html", {
                "text": u'Sie sind bereits für diese Einladung angemeldet',
                "title": "Fehler",
            }, context_instance=RequestContext(request))

        if not event.has_free_invites():
            return render_to_response("error.html", {
                "text": u'Es sind leider schon alle Einladungen vergeben',
                "title": "Ausgebucht!",
            }, context_instance=RequestContext(request))

        event.guests.add(request.user)
        event.save();
        
        request.user.get_profile().accept_invitation()
        
        if notification:
            notification.send([request.user], "invitation_confirmed_user",
                              {"event": event, "new_guest": request.user})
            
            notice_type = "invitation_confirmed"
            if event.send_emails:
                notice_type = "invitation_confirmed_email"
            notification.send([event.author], notice_type,
                              {"event": event, "new_guest": request.user})

        return render_to_response(template_name, {
            "event": event,
        }, context_instance=RequestContext(request))
    else:
        return render_to_response("error.html", {
            "text": u'Man darf keine eigenen Einladungen annehmen',
            "title": "Fehler",
        }, context_instance=RequestContext(request))


@login_required
def cancel_invitation(request, invitation_id, template_name="event/remove_invitation.html"):
    event =  get_object_or_404(Event, id=invitation_id)
    if request.method == "POST":
        if event.has_guest(request.user):
            event.guests.remove(request.user)
            event.save()
            
            request.user.get_profile().reset_invitation()

        if notification:
            notification.send([event.author], "invitation_canceled",
                              {"event": event, "canceled_guest": request.user})

        return HttpResponseRedirect(reverse('your_accepted_invitations', args=(request.user.username,)))
    else:
        return render_to_response(template_name, {
            "event": event,
            "other_user": request.user,
        }, context_instance=RequestContext(request))


def send_message_to_guests(request, invitation_id, template_name="event/"):
    from messages.views import compose, ComposeForm
    invitation = get_object_or_404(Event, id=invitation_id)
    recipients = ""
    for guest in invitation.guests.all():
        recipients += "+"+guest.username
        
    return compose(request, recipients, form_class=ComposeForm,
        template_name='event/compose_to_guests.html', success_url=reverse("profile_detail", args=(request.user.username,)))