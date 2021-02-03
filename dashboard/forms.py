from django import forms
from django.utils.translation import ugettext_lazy as _
from . import models
from myapp.widgets import ImageInput


class imageEditForm(forms.Form):
    xp1 = forms.DecimalField(min_value=0., max_value=1., localize=False,
                             widget=forms.HiddenInput, initial=0)
    xp2 = forms.DecimalField(min_value=0., max_value=1., localize=False,
                             widget=forms.HiddenInput, initial=0)
    yp1 = forms.DecimalField(min_value=0., max_value=1., localize=False,
                             widget=forms.HiddenInput, initial=0)
    yp2 = forms.DecimalField(min_value=0., max_value=1., localize=False,
                             widget=forms.HiddenInput, initial=0)

    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if self.instance.image:
            xp1, yp1, xp2, yp2 = self.instance.get_cropbox_frac()
            self.fields['xp1'].initial = xp1
            self.fields['xp2'].initial = xp2
            self.fields['yp1'].initial = yp1
            self.fields['yp2'].initial = yp2

    def save(self, commit=True):
        obj = self.instance
        data = self.cleaned_data
        xp1, yp1, xp2, yp2 = self.instance.get_cropbox_frac()
        xp1, yp1 = data.get('xp1', xp1), data.get('yp1', yp1)
        xp2, yp2 = data.get('xp2', xp2), data.get('yp2', yp2)
        if xp1 >= xp2 or yp1 >= yp2:
            raise ValidationError("Incorrect Cropbox")
        obj.set_cropbox_frac(xp1, yp1, xp2, yp2)
        if commit:
            obj.save()
        return obj
