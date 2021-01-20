from django import forms
from django.forms.models import BaseModelFormSet
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import (
    Officials, Club, PlayerInfo, JerseyPicture, ProfilePicture,
    AgeProof, AddressProof, Invitations, ClubDetails, Grounds
)

from myapp.widgets import ImageInput


class SignUpFormClub(UserCreationForm):

    club_name = forms.CharField(
        label='Name of the Club', max_length=100, required=True)

    address = forms.CharField(
        label='Address of the Club', max_length=200, required=True,
        widget=forms.Textarea)

    contact_number = forms.CharField(
        label='Contact number', max_length=10, min_length=10, required=True)

    class Meta:
        model = get_user_model()
        fields = ('username', 'club_name', 'address', 'email',
                  'contact_number', 'password1', 'password2')


class SignUpFormPersonal(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2')


class dpFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        clubid = kwargs.pop('clubid', None)
        super().__init__(*args, **kwargs)
        if clubid is None:
            qs = ProfilePicture.objects.filter(checked=False)
        else:
            qs = ProfilePicture.objects.filter(
                user__club__pk=clubid).filter(checked=False)

        qs1 = qs.order_by('pk')
        self.queryset = qs1[:10]


class dpUploadForm(forms.ModelForm):
    class Meta:
        model = ProfilePicture
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
        model = ProfilePicture
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


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = ProfilePicture
        fields = ['image', 'x1', 'x2', 'y1', 'y2']

        widgets = {
            # 'image': ImageWidget(),
            'x1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class AgeProofForm(forms.ModelForm):
    class Meta:
        model = AgeProof
        fields = ['image', 'x1', 'x2', 'y1', 'y2']

        widgets = {
            # 'image': ImageWidget(),
            'x1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class AddressProofForm(forms.ModelForm):
    class Meta:
        model = AddressProof
        fields = ['image', 'x1', 'x2', 'y1', 'y2']

        widgets = {
            # 'image': ImageWidget(),
            'x1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class JerseyForm(forms.ModelForm):
    class Meta:
        model = JerseyPicture
        fields = ['image', 'x1', 'x2', 'y1', 'y2']

        widgets = {
            'x1': forms.HiddenInput(),
            'x2': forms.HiddenInput(),
            'y1': forms.HiddenInput(),
            'y2': forms.HiddenInput(),
        }


class OfficialsEditForm(forms.ModelForm):
    class Meta:
        model = Officials
        fields = ['first_name', 'last_name',
                  'date_of_birth', 'address',
                  'phone_number']


class OfficialsCreationForm(forms.ModelForm):
    image = forms.ImageField(max_length=255, label='Photo')
    x1 = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)
    x2 = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)
    y1 = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)
    y2 = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)

    class Meta:
        model = Officials
        fields = ['first_name', 'last_name', 'role',
                  'date_of_birth', 'address', 'phone_number',
                  'occupation']

        widgets = {
            'role': forms.HiddenInput(),
        }


class PlayerCreationForm(OfficialsCreationForm):
    height = forms.IntegerField(
        required=True, min_value=100, max_value=200,
        help_text="Height in Centimeters")
    weight = forms.IntegerField(
        required=True, help_text="Weight in Kilograms")
    prefered_foot = forms.ChoiceField(
        choices=[('', '---'), ]+PlayerInfo.foot_choices, required=True)
    favorite_position = forms.ChoiceField(
        choices=[('', '---'), ]+PlayerInfo.position_choices, required=True)
    address_proof = forms.ImageField(help_text="Document for address proof")
    age_proof = forms.ImageField(help_text="Documents for age proof")


class LinkPlayerForm(forms.ModelForm):
    class Meta:
        model = Invitations
        fields = ['player', 'profile']

        widgets = {
            'profile': forms.HiddenInput(),
        }

    def __init__(self, club, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Users = get_user_model()
        self.fields['player'].queryset = Users.objects.filter(
            Official__isnull=True).filter(
            club__isnull=True).filter(
            is_staff=False).filter(
            email_verified=True).exclude(
            invitations__club=club)


class abbrForm(forms.ModelForm):
    class Meta:
        model = ClubDetails
        fields = ['abbr', ]


class clubDetailsForm(forms.ModelForm):

    class Meta:
        model = ClubDetails
        fields = ['address', 'contact_number', 'date_of_formation']
