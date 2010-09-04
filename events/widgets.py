from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.contrib.gis.forms.fields import GeometryField
from django.contrib.gis.maps.google.gmap import GoogleMap
from django.conf import settings

class AdvancedFileWidget(forms.FileInput):
    def __init__(self, attrs={}):
        super(AdvancedFileWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            output.append('%s <a target="_blank" href="%s">%s</a> <br /><label>%s</label> ' % \
                (_('Currently:'), value.url, value, _('Change:')))
        output.append(super(AdvancedFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))