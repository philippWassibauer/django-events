# -*- coding: utf-8 -*-
from datetime import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import AdminDateWidget, AdminTimeWidget, AdminSplitDateTime
from django.template.loader import render_to_string

from event.models import Event
from profiles.models import Profile

from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.text import truncate_words
from widgets.widgets import AdvancedFileWidget

def is_startdate_before_enddate(start_date, end_date):
    if end_date <= start_date:
        raise forms.ValidationError(_("End date must be after start date."))
    return True

def is_date_before_now(date):
    import datetime
    if datetime.datetime.now() > date:
        raise forms.ValidationError(_("Date must be in the future"))


class InvitationTimeInput(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = [AdminDateWidget, AdminTimeWidget, AdminDateWidget, AdminTimeWidget, AdminDateWidget, AdminTimeWidget]
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        return render_to_string("event/invitation_timeform.html", {
            "only_on_date_widget": rendered_widgets[0],
            "only_on_time_widget": rendered_widgets[1],
            "start_date_widget": rendered_widgets[2],
            "start_time_widget": rendered_widgets[3],
            "end_date_widget": rendered_widgets[4],
            "end_time_widget": rendered_widgets[5],
            "is_one_day": self.is_one_day,
        })

    def decompress(self, value):
        if value:
            return [value.date(), value.time().replace(microsecond=0)]
        return [None, None]

    def render(self, name, value, attrs=None):
        if not isinstance(value, list):
            value = self.decompress(value)
        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id', None)
        if len(value)==4 and value[0]!=value[2]:
            self.is_one_day = False
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 0))
            output.append(self.widgets[0].render(name + '_%s' % 0, "", final_attrs))
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 1))
            output.append(self.widgets[1].render(name + '_%s' % 1, "", final_attrs))

            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 2))
            output.append(self.widgets[2].render(name + '_%s' % 2, value[0], final_attrs))
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 3))
            output.append(self.widgets[3].render(name + '_%s' % 3, value[1], final_attrs))
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 4))
            output.append(self.widgets[4].render(name + '_%s' % 4, value[2], final_attrs))
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 5))
            output.append(self.widgets[5].render(name + '_%s' % 5, value[3], final_attrs))
        else:
            self.is_one_day = True
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 0))
            output.append(self.widgets[0].render(name + '_%s' % 0, value[0], final_attrs))
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 1))
            output.append(self.widgets[1].render(name + '_%s' % 1, value[1], final_attrs))

            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 2))
            output.append(self.widgets[2].render(name + '_%s' % 2, "", final_attrs))
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 3))
            output.append(self.widgets[3].render(name + '_%s' % 3, "", final_attrs))
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 4))
            output.append(self.widgets[4].render(name + '_%s' % 4, "", final_attrs))
            final_attrs = dict(final_attrs, id='%s_%s' % (id_, 5))
            output.append(self.widgets[5].render(name + '_%s' % 5, "", final_attrs))

        return mark_safe(self.format_output(output))

class InvitationTimeInputField(forms.MultiValueField):
    widget=InvitationTimeInput

    def __init__(self, required=True, widget=None, label=None, initial=None):
        fields = (
            forms.DateTimeField(required=False),
            forms.DateTimeField(required=False),
            forms.DateTimeField(required=False),
        )
        super(InvitationTimeInputField,self).__init__(fields=fields, widget=widget, label=label, initial=initial)

    def compress(self,data_list):
        if data_list:
            return ','.join(data_list)
        return None

    def clean(self, value):
        if value[0] and value[1]:
            return (value[0], value[1])
        elif value[2] and value[3] and value[4] and value[5]:
            return (value[2], value[3], value[4], value[5])
        else:
            raise forms.ValidationError("Dieses Feld ist zwingend erforderlich.") 

class EventLocationForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('location_name', 'location_adress', 'location_zip_code', 'location_city', 'location_country') 


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ('location_name', 'location_adress', 'location_zip_code', 
                   'location_city', 'location_country', 'start_date', 'end_date', 
                   'status', 'allow_comments', 'tease', 'guests', 'author', 
                   'created_at', 'updated_at', 'publish', 'type', 'slug',

                   'num_invites', 'num_additional_persons_per_invite',
                   'has_to_reserve', 'send_emails',
                   'invitations_start', 'invitations_deadline')

    def __init__(self, user=None, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)

        self.user = user
        self.date_time_pattern = "%Y-%m-%d %H:%M:%S"
        self.time_pattern = "%H:%M:%S"
        self.date_pattern = "%Y-%m-%d"

        if self.fields.has_key('location'):
            self.fields['location'].widget = LocationInput(user, self.instance)
        if self.fields.has_key('image'):
            self.fields['image'].widget = AdvancedFileWidget()

        timeframe_values = self.create_timeframe_values()
        insertBefore = self.fields.keyOrder.index('website')
        self.fields.insert(insertBefore, 'timeframe_select', 
                           InvitationTimeInputField(label="Diese Veranstaltung ist:", initial=timeframe_values))
        
        if hasattr(self.fields, "num_invites"):
            moved_field = self.fields['num_invites']
            del self.fields['num_invites']
            insertBefore = self.fields.keyOrder.index('title')
            self.fields.insert(insertBefore, 'num_invites', 
                               moved_field)

    def create_timeframe_values(self):
        timeframe_values = ["", "", "", "", "", ""]
        if self.instance:
            if self.instance.start_date and self.instance.end_date:
                timeframe_values = [self.instance.start_date.strftime(self.date_pattern),
                                    self.instance.start_date.strftime(self.time_pattern),
                                    self.instance.end_date.strftime(self.date_pattern),
                                    self.instance.end_date.strftime(self.time_pattern)]
            elif self.instance.start_date:
                timeframe_values = [self.instance.start_date.strftime(self.date_pattern),
                                    self.instance.start_date.strftime(self.time_pattern)]
            else:
                timeframe_values = ["",""]
        return timeframe_values

    def clean_timeframe_select(self):
        timeframe_select = self.cleaned_data.get("timeframe_select")
        if len(timeframe_select[1]) == 5:
            list = []
            list[:] = timeframe_select[:]
            list[1] = list[1]+":00"
            timeframe_select = tuple(list)
        elif len(timeframe_select[1]) == 2:
            list = []
            list[:] = timeframe_select[:]
            list[1] = list[1]+":00:00"
            timeframe_select = tuple(list)

        try:
            if isinstance(timeframe_select, tuple):
                if len(timeframe_select) == 2:
                    self.instance.start_date = datetime.strptime('%s %s' % (timeframe_select[0], timeframe_select[1]), self.date_time_pattern)
                    self.instance.end_date = datetime.strptime('%s %s' % (timeframe_select[0], "23:59:59"), self.date_time_pattern)
                elif len(timeframe_select) == 4:
                    if len(timeframe_select[3]) == 5:
                        list = []
                        list[:] = timeframe_select[:]
                        list[3] = list[3]+":00"
                        timeframe_select = tuple(list)
                    self.instance.start_date = datetime.strptime('%s %s' % (timeframe_select[0], timeframe_select[1]), self.date_time_pattern)
                    self.instance.end_date = datetime.strptime('%s %s' % (timeframe_select[2], timeframe_select[3]), self.date_time_pattern)
        except:
            raise forms.ValidationError(_("The Date must be in the format YYYY-MM-DD and HH:MM:SS"))

        if not self.instance.end_date or not self.instance.start_date:
            raise forms.ValidationError("Anfang und Enddatum müssen angegeben werden")

        is_startdate_before_enddate( self.instance.start_date, self.instance.end_date)
        is_date_before_now(self.instance.end_date)

    def clean_end_date(self):
        end_date = self.cleaned_data.get("end_date")
        start_date = self.cleaned_data.get("start_date")
        if not end_date or not start_date:
            raise forms.ValidationError("Anfang und Enddatum müssen angegeben werden")

        is_startdate_before_enddate(start_date, end_date)
        is_date_before_now(end_date)
        return end_date

    # exclusive for Invitation Form
    def clean_invitations_deadline(self):
        invitations_deadline = self.cleaned_data.get("invitations_deadline")
        invitations_start = self.cleaned_data.get("invitations_start")
        if not invitations_start or not invitations_deadline:
            raise forms.ValidationError("Anfang und Enddatum müssen angegeben werden")

        is_startdate_before_enddate(invitations_start, invitations_deadline)
        is_date_before_now(invitations_deadline)
        return invitations_deadline

    # exclusive for Invitation Form
    def clean_num_invites(self):
        num_invites = self.cleaned_data["num_invites"]
        if not num_invites:
            raise forms.ValidationError(_("A minimum of one invitation must be set."))
        return num_invites

class InvitationForm(EventForm):
    # derived from EventForm
    class Meta:
        model = Event
        exclude = ('location_name', 'location_adress', 'location_zip_code', 
                   'location_city', 'location_country', 'start_date', 'end_date', 
                   'status', 'allow_comments', 'tease', 'guests', 'author', 
                   'created_at', 'updated_at', 'publish', 'type', 'slug')

    def __init__(self, *args, **kwargs):
        super(InvitationForm, self).__init__(*args, **kwargs)

        # exclusive for InvitationForm
        self.fields['num_invites'].required = True

        self.fields['num_additional_persons_per_invite'].widget = self.fields['num_additional_persons_per_invite'].hidden_widget()
        self.fields['num_additional_persons_per_invite'].widget.attrs['disabled'] = 'disabled'

        # used for functionality "Einladung mit Freikarten"
        self.fields['invitations_start'].widget = AdminSplitDateTime()
        self.fields['invitations_deadline'].widget = AdminSplitDateTime()

        timeframe_values = self.create_timeframe_values()
        del self.fields['timeframe_select']
        insertBefore = self.fields.keyOrder.index('invitations_start')
        self.fields.insert(insertBefore, 'timeframe_select', 
                           InvitationTimeInputField(label="Diese Einladung gilt:", initial=timeframe_values))

class EventToInvitationForm(InvitationForm):
    class Meta:
        model = Event
        exclude = ('location_name', 'location_adress', 'location_zip_code', 
                   'location_city', 'location_country', 'start_date', 'end_date', 
                   'status', 'allow_comments', 'tease', 'guests', 'author', 
                   'created_at', 'updated_at', 'publish', 'type', 'slug',

                   'title', 'body', 'image', 'location', 'tags')


class LocationForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user')

class LocationInput(forms.HiddenInput):
    def __init__(self, user, event, *args, **kwargs):
        self.user = user
        self.event = event
        self.errors = []

        if user.get_profile().is_location:
            self.is_location = user.get_profile().is_location
            self.location_id = user.get_profile().id
        else:
            self.is_location = False
            self.location_id = None

        super(LocationInput, self).__init__(*args, **kwargs)

    class Media:
        css = {
            'all': ('css/jquery.autocomplete.css',)
        }
        js = (
        )


    def render(self, name, value, attrs=None):
        if value:
            location = Profile.objects.get(pk=value)
        else:
            location = None

        location_form = LocationForm().as_table()
        event_location_form = EventLocationForm()

        output_string = render_to_string("event/location_select.html", {
            'errors': self.errors,
            'event': self.event,
            'location': location,
            'is_location': self.is_location,
            'location_id': self.location_id,
            'location_form': mark_safe(location_form),
            'event_location_form': event_location_form,
            'STATIC_URL': settings.STATIC_URL,
        })
        return mark_safe(output_string)

