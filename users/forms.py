from django import forms

from django.utils.translation import ugettext_lazy as _

from . import models

from myapp.widgets import ImageInput


class UpdateClubOfficialsForm(forms.ModelForm):
    title = 'Edit Club Officials Profile'

    class Meta:
        model = models.ClubOfficialsProfile
        fields = ['name', 'nickname',
                  'dob', 'address', 'phone_number']


class UpdateClubForm(forms.ModelForm):
    title = 'Edit Club Profile'

    class Meta:
        model = models.ClubProfile
        fields = ['name', 'logo', 'address',
                  'pincode', 'year_of_formation', 'abbr']


class dpUploadForm(forms.ModelForm):
    class Meta:
        model = models.ProfilePicture
        fields = ['image', ]
        widgets = {
            'image': ImageInput()
        }


class dpEditForm(forms.ModelForm):
    xp1 = forms.DecimalField(min_value=0., max_value=1., localize=False,
                             widget=forms.HiddenInput, initial=0)
    xp2 = forms.DecimalField(min_value=0., max_value=1., localize=False,
                             widget=forms.HiddenInput, initial=0)
    yp1 = forms.DecimalField(min_value=0., max_value=1., localize=False,
                             widget=forms.HiddenInput, initial=0)
    yp2 = forms.DecimalField(min_value=0., max_value=1., localize=False,
                             widget=forms.HiddenInput, initial=0)

    class Meta:
        model = models.ProfilePicture
        fields = ['checked', ]
        widgets = {
            'checked': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.image:
            xp1, yp1, xp2, yp2 = self.instance.get_cropbox_frac()
            self.fields['xp1'].initial = xp1
            self.fields['xp2'].initial = xp2
            self.fields['yp1'].initial = yp1
            self.fields['yp2'].initial = yp2

    def save(self, commit=True):
        obj = super().save(commit=False)
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
