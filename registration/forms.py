from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.contrib.auth import get_user_model

from bootstrap_datepicker_plus import DatePickerInput

from .models import (
    Officials, Club, PlayerInfo, JerseyPicture, ProfilePicture,
    AgeProof, AddressProof, Invitations,
)


class ImageWidget(forms.ClearableFileInput):
    template_name = 'widgets/image.html'


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
        # fields = '__all__'

        widgets = {
            'role': forms.HiddenInput(),
            'date_of_birth': DatePickerInput(),
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
